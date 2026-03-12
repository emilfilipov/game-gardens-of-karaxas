use std::collections::VecDeque;
use std::time::Instant;

use serde::Serialize;
use sha2::{Digest, Sha256};
use sim_core::{
    ArmyId, CommandEnvelope, CommandPayload, EventEnvelope, EventPayload, FactionId, LogisticsTickEvent,
    LogisticsWorld, SettlementId, SupplyStock, SupplyTransferOrder, Tick, sample_logistics_world,
};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TickRunnerConfig {
    pub tick_interval_ms: u64,
    pub snapshot_interval_ticks: u64,
    pub max_snapshots: usize,
}

impl TickRunnerConfig {
    pub fn new(tick_interval_ms: u64, snapshot_interval_ticks: u64, max_snapshots: usize) -> Self {
        Self {
            tick_interval_ms: tick_interval_ms.max(1),
            snapshot_interval_ticks: snapshot_interval_ticks.max(1),
            max_snapshots: max_snapshots.max(1),
        }
    }
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq, Default)]
pub struct TickMetrics {
    pub total_ticks: u64,
    pub total_processed_commands: u64,
    pub last_tick_lag_ms: u64,
    pub max_tick_lag_ms: u64,
    pub last_tick_duration_ms: u64,
    pub snapshot_count: usize,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct TickSnapshot {
    pub tick: Tick,
    pub event_count: usize,
    pub state_hash: String,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct TickAdvanceResult {
    pub ticks_executed: usize,
    pub current_tick: Tick,
    pub queue_depth: usize,
    pub metrics: TickMetrics,
    pub latest_snapshot: Option<TickSnapshot>,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct LogisticsArmySnapshot {
    pub army_id: u64,
    pub location: u64,
    pub troop_strength: u32,
    pub stock: SupplyStock,
    pub consumption_per_tick: SupplyStock,
    pub shortage_ticks: u32,
    pub cumulative_attrition: u32,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct LogisticsStateSnapshot {
    pub armies: Vec<LogisticsArmySnapshot>,
    pub pending_transfers: Vec<SupplyTransferOrder>,
}

pub struct TickRunner {
    config: TickRunnerConfig,
    current_tick: Tick,
    next_tick_due_ms: u64,
    queue: Vec<CommandEnvelope>,
    event_log: Vec<EventEnvelope>,
    snapshots: VecDeque<TickSnapshot>,
    metrics: TickMetrics,
    logistics: LogisticsWorld,
}

impl TickRunner {
    pub fn new(config: TickRunnerConfig) -> Self {
        Self {
            config,
            current_tick: Tick(0),
            next_tick_due_ms: 0,
            queue: Vec::new(),
            event_log: Vec::new(),
            snapshots: VecDeque::new(),
            metrics: TickMetrics::default(),
            logistics: sample_logistics_world(),
        }
    }

    pub fn queue_command(&mut self, command: CommandEnvelope) {
        self.queue.push(command);
    }

    pub fn run_due_ticks(&mut self, now_ms: u64) -> TickAdvanceResult {
        let mut executed = 0_usize;
        while now_ms >= self.next_tick_due_ms {
            self.run_single_tick(now_ms);
            self.next_tick_due_ms = self.next_tick_due_ms.saturating_add(self.config.tick_interval_ms);
            executed += 1;
        }

        TickAdvanceResult {
            ticks_executed: executed,
            current_tick: self.current_tick,
            queue_depth: self.queue.len(),
            metrics: self.metrics.clone(),
            latest_snapshot: self.snapshots.back().cloned(),
        }
    }

    pub fn current_tick(&self) -> Tick {
        self.current_tick
    }

    #[cfg(test)]
    pub fn snapshots(&self) -> &VecDeque<TickSnapshot> {
        &self.snapshots
    }

    #[cfg(test)]
    pub fn events(&self) -> &[EventEnvelope] {
        &self.event_log
    }

    pub fn queue_depth(&self) -> usize {
        self.queue.len()
    }

    pub fn logistics_state(&self) -> LogisticsStateSnapshot {
        let armies = self
            .logistics
            .armies()
            .map(|army| LogisticsArmySnapshot {
                army_id: army.army_id.0,
                location: army.location.0,
                troop_strength: army.troop_strength,
                stock: army.stock,
                consumption_per_tick: army.consumption_per_tick,
                shortage_ticks: army.shortage_ticks,
                cumulative_attrition: army.cumulative_attrition,
            })
            .collect();

        LogisticsStateSnapshot {
            armies,
            pending_transfers: self.logistics.pending_transfers().to_vec(),
        }
    }

    fn run_single_tick(&mut self, now_ms: u64) {
        let work_started = Instant::now();
        let lag_ms = now_ms.saturating_sub(self.next_tick_due_ms);

        self.current_tick = self.current_tick.next();
        let tick_now = self.current_tick;

        let mut commands = std::mem::take(&mut self.queue);
        commands.sort_by_key(|item| {
            let payload = serde_json::to_string(&item.payload).unwrap_or_default();
            format!("{}:{payload}", item.trace_id)
        });

        for command in commands {
            let events = self.process_command(command, tick_now);
            self.event_log.extend(events);
            self.metrics.total_processed_commands = self.metrics.total_processed_commands.saturating_add(1);
        }

        let logistics_tick = self.logistics.advance_tick(tick_now);
        for event in logistics_tick.events {
            let trace_id = format!("logistics-{}-{}", tick_now.0, self.event_log.len());
            self.event_log
                .push(EventEnvelope::new(trace_id, logistics_event_to_payload(event)));
        }

        self.metrics.total_ticks = self.metrics.total_ticks.saturating_add(1);
        self.metrics.last_tick_lag_ms = lag_ms;
        self.metrics.max_tick_lag_ms = self.metrics.max_tick_lag_ms.max(lag_ms);
        self.metrics.last_tick_duration_ms = u64::try_from(work_started.elapsed().as_millis()).unwrap_or(u64::MAX);

        if self.current_tick.0.is_multiple_of(self.config.snapshot_interval_ticks) {
            let snapshot = TickSnapshot {
                tick: self.current_tick,
                event_count: self.event_log.len(),
                state_hash: hash_events(&self.event_log),
            };
            self.snapshots.push_back(snapshot);
            while self.snapshots.len() > self.config.max_snapshots {
                self.snapshots.pop_front();
            }
            self.metrics.snapshot_count = self.snapshots.len();
        }
    }

    fn process_command(&mut self, command: CommandEnvelope, tick: Tick) -> Vec<EventEnvelope> {
        let trace_id = command.trace_id.clone();
        let payload = match command.payload {
            CommandPayload::IssueMoveArmy {
                army_id,
                origin,
                destination,
            } => {
                self.logistics.set_army_location(army_id, destination);
                EventPayload::ArmyMoved {
                    army_id,
                    origin,
                    destination,
                    tick,
                }
            }
            CommandPayload::SetFactionStance {
                actor_faction,
                target_faction,
                relation_delta,
            } => EventPayload::FactionStanceUpdated {
                actor_faction,
                target_faction,
                relation_delta,
                tick,
            },
            CommandPayload::QueueSupplyTransfer {
                from_army,
                to_army,
                stock,
            } => {
                self.logistics.queue_transfer(SupplyTransferOrder {
                    from_army,
                    to_army,
                    stock,
                });
                EventPayload::SupplyTransferQueued {
                    from_army,
                    to_army,
                    stock,
                    tick,
                }
            }
        };

        vec![EventEnvelope::new(trace_id, payload)]
    }
}

fn logistics_event_to_payload(event: LogisticsTickEvent) -> EventPayload {
    match event {
        LogisticsTickEvent::SupplyTransferApplied {
            from_army,
            to_army,
            moved,
            tick,
        } => EventPayload::SupplyTransferApplied {
            from_army,
            to_army,
            stock: moved,
            tick,
        },
        LogisticsTickEvent::ArmySupplyConsumed {
            army_id,
            consumed,
            remaining,
            troop_strength,
            shortage_ticks,
            tick,
        } => EventPayload::ArmySupplyConsumed {
            army_id,
            consumed,
            remaining,
            troop_strength,
            shortage_ticks,
            tick,
        },
        LogisticsTickEvent::ArmyAttritionApplied {
            army_id,
            attrition,
            troop_strength,
            shortage_ticks,
            tick,
        } => EventPayload::ArmyAttritionApplied {
            army_id,
            attrition,
            troop_strength,
            shortage_ticks,
            tick,
        },
    }
}

fn hash_events(events: &[EventEnvelope]) -> String {
    let mut hasher = Sha256::new();
    for event in events {
        let encoded = serde_json::to_vec(event).unwrap_or_default();
        hasher.update(encoded);
    }
    hex::encode(hasher.finalize())
}

pub fn build_move_army_command(trace_id: &str, army_id: u64, origin: u64, destination: u64) -> CommandEnvelope {
    CommandEnvelope::new(
        trace_id,
        CommandPayload::IssueMoveArmy {
            army_id: ArmyId(army_id),
            origin: SettlementId(origin),
            destination: SettlementId(destination),
        },
    )
}

pub fn build_set_stance_command(
    trace_id: &str,
    actor_faction: u64,
    target_faction: u64,
    relation_delta: i32,
) -> CommandEnvelope {
    CommandEnvelope::new(
        trace_id,
        CommandPayload::SetFactionStance {
            actor_faction: FactionId(actor_faction),
            target_faction: FactionId(target_faction),
            relation_delta,
        },
    )
}

pub fn build_supply_transfer_command(
    trace_id: &str,
    from_army: u64,
    to_army: u64,
    food: u32,
    horses: u32,
    materiel: u32,
) -> CommandEnvelope {
    CommandEnvelope::new(
        trace_id,
        CommandPayload::QueueSupplyTransfer {
            from_army: ArmyId(from_army),
            to_army: ArmyId(to_army),
            stock: SupplyStock { food, horses, materiel },
        },
    )
}

#[cfg(test)]
mod tests {
    use super::{
        TickRunner, TickRunnerConfig, build_move_army_command, build_set_stance_command, build_supply_transfer_command,
    };

    #[test]
    fn deterministic_processing_is_order_stable() {
        let config = TickRunnerConfig::new(100, 1, 16);

        let mut a = TickRunner::new(config.clone());
        a.queue_command(build_set_stance_command("trace-b", 3, 4, -2));
        a.queue_command(build_move_army_command("trace-a", 7, 1, 2));
        a.run_due_ticks(0);

        let mut b = TickRunner::new(config);
        b.queue_command(build_move_army_command("trace-a", 7, 1, 2));
        b.queue_command(build_set_stance_command("trace-b", 3, 4, -2));
        b.run_due_ticks(0);

        assert_eq!(a.events(), b.events());
        assert_eq!(a.snapshots(), b.snapshots());
    }

    #[test]
    fn snapshots_follow_interval() {
        let mut runner = TickRunner::new(TickRunnerConfig::new(100, 2, 16));
        runner.run_due_ticks(450);

        let ticks: Vec<u64> = runner.snapshots().iter().map(|row| row.tick.0).collect();
        assert_eq!(ticks, vec![2, 4]);
    }

    #[test]
    fn lag_metrics_capture_delay() {
        let mut runner = TickRunner::new(TickRunnerConfig::new(100, 10, 16));
        let summary = runner.run_due_ticks(350);

        assert_eq!(summary.ticks_executed, 4);
        assert_eq!(summary.metrics.total_ticks, 4);
        assert_eq!(summary.metrics.max_tick_lag_ms, 350);
        assert_eq!(summary.metrics.last_tick_lag_ms, 50);
    }

    #[test]
    fn logistics_transfer_and_consumption_progress_with_ticks() {
        let mut runner = TickRunner::new(TickRunnerConfig::new(100, 10, 16));
        runner.queue_command(build_supply_transfer_command("trace-logistics", 7, 8, 12, 0, 0));
        let _summary = runner.run_due_ticks(0);

        let state = runner.logistics_state();
        let army8 = state
            .armies
            .iter()
            .find(|row| row.army_id == 8)
            .expect("army 8 should exist");

        assert!(army8.stock.food >= 12);
    }
}
