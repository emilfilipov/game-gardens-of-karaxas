use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use crate::{ArmyId, SettlementId, Tick};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum BattleInstanceStatus {
    Active,
    Resolved,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct BattleInstanceRecord {
    pub instance_id: u64,
    pub encounter_id: u64,
    pub location: SettlementId,
    pub attacker_army: ArmyId,
    pub defender_army: ArmyId,
    pub initial_attacker_strength: u32,
    pub initial_defender_strength: u32,
    pub attacker_strength: u32,
    pub defender_strength: u32,
    pub attacker_morale_bp: u32,
    pub defender_morale_bp: u32,
    pub step_cursor: u32,
    pub started_tick: Tick,
    pub last_step_tick: Tick,
    pub status: BattleInstanceStatus,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct BattleResultRecord {
    pub instance_id: u64,
    pub encounter_id: u64,
    pub winner_army: ArmyId,
    pub loser_army: ArmyId,
    pub attacker_remaining_strength: u32,
    pub defender_remaining_strength: u32,
    pub total_steps: u32,
    pub started_tick: Tick,
    pub resolved_tick: Tick,
    pub writeback_signature: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct StartBattleEncounterOrder {
    pub instance_id: u64,
    pub encounter_id: u64,
    pub location: SettlementId,
    pub attacker_army: ArmyId,
    pub defender_army: ArmyId,
    pub attacker_strength: u32,
    pub defender_strength: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct ForceResolveBattleOrder {
    pub instance_id: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum BattleOrder {
    StartEncounter(StartBattleEncounterOrder),
    ForceResolve(ForceResolveBattleOrder),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum BattleTickEvent {
    EncounterCreated {
        instance_id: u64,
        encounter_id: u64,
        location: SettlementId,
        attacker_army: ArmyId,
        defender_army: ArmyId,
        tick: Tick,
    },
    StepAdvanced {
        instance_id: u64,
        step_index: u32,
        attacker_strength: u32,
        defender_strength: u32,
        attacker_morale_bp: u32,
        defender_morale_bp: u32,
        tick: Tick,
    },
    InstanceResolved {
        result: BattleResultRecord,
        tick: Tick,
    },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct BattleTickResult {
    pub events: Vec<BattleTickEvent>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BattleWorld {
    instances: BTreeMap<u64, BattleInstanceRecord>,
    pending_orders: Vec<BattleOrder>,
    recent_results: Vec<BattleResultRecord>,
    max_recent_results: usize,
    max_steps_per_instance: u32,
}

impl Default for BattleWorld {
    fn default() -> Self {
        Self {
            instances: BTreeMap::new(),
            pending_orders: Vec::new(),
            recent_results: Vec::new(),
            max_recent_results: 32,
            max_steps_per_instance: 120,
        }
    }
}

impl BattleWorld {
    pub fn queue_order(&mut self, order: BattleOrder) {
        self.pending_orders.push(order);
    }

    pub fn instances(&self) -> impl Iterator<Item = &BattleInstanceRecord> {
        self.instances.values()
    }

    pub fn pending_orders(&self) -> &[BattleOrder] {
        &self.pending_orders
    }

    pub fn recent_results(&self) -> &[BattleResultRecord] {
        &self.recent_results
    }

    pub fn instance(&self, instance_id: u64) -> Option<&BattleInstanceRecord> {
        self.instances.get(&instance_id)
    }

    pub fn advance_tick(&mut self, tick: Tick) -> BattleTickResult {
        let mut events = Vec::new();
        self.apply_orders(tick, &mut events);
        self.advance_instances(tick, &mut events);
        BattleTickResult { events }
    }

    fn apply_orders(&mut self, tick: Tick, events: &mut Vec<BattleTickEvent>) {
        let mut queued = std::mem::take(&mut self.pending_orders);
        queued.sort_by_key(|order| {
            let priority = match order {
                BattleOrder::StartEncounter(_) => 0_u8,
                BattleOrder::ForceResolve(_) => 1_u8,
            };
            let payload = serde_json::to_string(order).unwrap_or_default();
            (priority, payload)
        });

        for order in queued {
            match order {
                BattleOrder::StartEncounter(order) => self.apply_start_encounter(order, tick, events),
                BattleOrder::ForceResolve(order) => self.apply_force_resolve(order, tick, events),
            }
        }
    }

    fn apply_start_encounter(
        &mut self,
        order: StartBattleEncounterOrder,
        tick: Tick,
        events: &mut Vec<BattleTickEvent>,
    ) {
        if self.instances.contains_key(&order.instance_id) {
            return;
        }
        if order.attacker_army == order.defender_army {
            return;
        }
        if order.attacker_strength == 0 || order.defender_strength == 0 {
            return;
        }

        let overlapping_army_active = self.instances.values().any(|row| {
            row.status == BattleInstanceStatus::Active
                && (row.attacker_army == order.attacker_army
                    || row.attacker_army == order.defender_army
                    || row.defender_army == order.attacker_army
                    || row.defender_army == order.defender_army)
        });
        if overlapping_army_active {
            return;
        }

        self.instances.insert(
            order.instance_id,
            BattleInstanceRecord {
                instance_id: order.instance_id,
                encounter_id: order.encounter_id,
                location: order.location,
                attacker_army: order.attacker_army,
                defender_army: order.defender_army,
                initial_attacker_strength: order.attacker_strength,
                initial_defender_strength: order.defender_strength,
                attacker_strength: order.attacker_strength,
                defender_strength: order.defender_strength,
                attacker_morale_bp: 10_000,
                defender_morale_bp: 10_000,
                step_cursor: 0,
                started_tick: tick,
                last_step_tick: tick,
                status: BattleInstanceStatus::Active,
            },
        );

        events.push(BattleTickEvent::EncounterCreated {
            instance_id: order.instance_id,
            encounter_id: order.encounter_id,
            location: order.location,
            attacker_army: order.attacker_army,
            defender_army: order.defender_army,
            tick,
        });
    }

    fn apply_force_resolve(&mut self, order: ForceResolveBattleOrder, tick: Tick, events: &mut Vec<BattleTickEvent>) {
        let Some(instance) = self.instances.get(&order.instance_id).copied() else {
            return;
        };
        if instance.status != BattleInstanceStatus::Active {
            return;
        }
        let Some(record) = self.instances.get_mut(&order.instance_id) else {
            return;
        };
        record.last_step_tick = tick;

        let result = build_result(*record, tick);
        record.status = BattleInstanceStatus::Resolved;
        self.recent_results.push(result);
        while self.recent_results.len() > self.max_recent_results {
            self.recent_results.remove(0);
        }

        events.push(BattleTickEvent::InstanceResolved { result, tick });
    }

    fn advance_instances(&mut self, tick: Tick, events: &mut Vec<BattleTickEvent>) {
        let instance_ids: Vec<u64> = self.instances.keys().copied().collect();
        for instance_id in instance_ids {
            let Some(instance) = self.instances.get(&instance_id).copied() else {
                continue;
            };
            if instance.status != BattleInstanceStatus::Active {
                continue;
            }

            let Some(record) = self.instances.get_mut(&instance_id) else {
                continue;
            };
            record.step_cursor = record.step_cursor.saturating_add(1);

            let attacker_loss = compute_loss(
                tick,
                record.instance_id,
                record.step_cursor,
                record.defender_strength,
                record.defender_morale_bp,
                17,
            )
            .min(record.attacker_strength);
            let defender_loss = compute_loss(
                tick,
                record.instance_id,
                record.step_cursor,
                record.attacker_strength,
                record.attacker_morale_bp,
                29,
            )
            .min(record.defender_strength);

            record.attacker_strength = record.attacker_strength.saturating_sub(attacker_loss);
            record.defender_strength = record.defender_strength.saturating_sub(defender_loss);
            record.attacker_morale_bp = record
                .attacker_morale_bp
                .saturating_sub(attacker_loss.saturating_mul(9).saturating_add(45))
                .max(100);
            record.defender_morale_bp = record
                .defender_morale_bp
                .saturating_sub(defender_loss.saturating_mul(9).saturating_add(45))
                .max(100);
            record.last_step_tick = tick;

            events.push(BattleTickEvent::StepAdvanced {
                instance_id,
                step_index: record.step_cursor,
                attacker_strength: record.attacker_strength,
                defender_strength: record.defender_strength,
                attacker_morale_bp: record.attacker_morale_bp,
                defender_morale_bp: record.defender_morale_bp,
                tick,
            });

            let should_resolve = record.attacker_strength == 0
                || record.defender_strength == 0
                || record.attacker_morale_bp <= 1_000
                || record.defender_morale_bp <= 1_000
                || record.step_cursor >= self.max_steps_per_instance;
            if should_resolve {
                let result = build_result(*record, tick);
                record.status = BattleInstanceStatus::Resolved;
                self.recent_results.push(result);
                while self.recent_results.len() > self.max_recent_results {
                    self.recent_results.remove(0);
                }
                events.push(BattleTickEvent::InstanceResolved { result, tick });
            }
        }
    }
}

fn compute_loss(
    tick: Tick,
    instance_id: u64,
    step_cursor: u32,
    opposing_strength: u32,
    opposing_morale_bp: u32,
    salt: u64,
) -> u32 {
    let roll = deterministic_roll(
        tick.0
            .wrapping_add(instance_id.wrapping_mul(6_364_136_223_846_793_005))
            .wrapping_add(u64::from(step_cursor).wrapping_mul(1_442_695_040_888_963_407))
            .wrapping_add(u64::from(opposing_strength))
            .wrapping_add(u64::from(opposing_morale_bp))
            .wrapping_add(salt),
    );

    let pressure = roll % 130 + 45;
    let scaled = pressure.saturating_mul(opposing_strength.max(1)) / 850;
    let morale_bonus = opposing_morale_bp / 1_600;
    scaled.saturating_add(morale_bonus).clamp(1, 240)
}

fn build_result(record: BattleInstanceRecord, resolved_tick: Tick) -> BattleResultRecord {
    let attacker_score = record
        .attacker_strength
        .saturating_mul(14)
        .saturating_add(record.attacker_morale_bp / 2);
    let defender_score = record
        .defender_strength
        .saturating_mul(14)
        .saturating_add(record.defender_morale_bp / 2);
    let (winner_army, loser_army) = if attacker_score >= defender_score {
        (record.attacker_army, record.defender_army)
    } else {
        (record.defender_army, record.attacker_army)
    };

    BattleResultRecord {
        instance_id: record.instance_id,
        encounter_id: record.encounter_id,
        winner_army,
        loser_army,
        attacker_remaining_strength: record.attacker_strength,
        defender_remaining_strength: record.defender_strength,
        total_steps: record.step_cursor,
        started_tick: record.started_tick,
        resolved_tick,
        writeback_signature: u64::from(deterministic_roll(
            record
                .instance_id
                .wrapping_mul(131)
                .wrapping_add(record.encounter_id.wrapping_mul(977))
                .wrapping_add(record.started_tick.0.wrapping_mul(37))
                .wrapping_add(resolved_tick.0.wrapping_mul(53))
                .wrapping_add(u64::from(record.attacker_strength))
                .wrapping_add(u64::from(record.defender_strength)),
        )),
    }
}

fn deterministic_roll(seed: u64) -> u32 {
    let mut value = seed;
    value ^= value >> 30;
    value = value.wrapping_mul(0xBF58_476D_1CE4_E5B9);
    value ^= value >> 27;
    value = value.wrapping_mul(0x94D0_49BB_1331_11EB);
    value ^= value >> 31;
    u32::try_from(value % 10_000).unwrap_or(0)
}

pub fn sample_battle_world() -> BattleWorld {
    BattleWorld::default()
}

#[cfg(test)]
mod tests {
    use crate::{ArmyId, SettlementId, Tick};

    use super::{
        BattleInstanceStatus, BattleOrder, BattleTickEvent, ForceResolveBattleOrder, StartBattleEncounterOrder,
        sample_battle_world,
    };

    #[test]
    fn encounter_advances_and_resolves_with_deterministic_steps() {
        let mut world = sample_battle_world();
        world.queue_order(BattleOrder::StartEncounter(StartBattleEncounterOrder {
            instance_id: 1001,
            encounter_id: 7001,
            location: SettlementId(3),
            attacker_army: ArmyId(7),
            defender_army: ArmyId(8),
            attacker_strength: 220,
            defender_strength: 210,
        }));

        let mut resolved = false;
        for tick in 1..=140_u64 {
            let result = world.advance_tick(Tick(tick));
            if result.events.iter().any(
                |event| matches!(event, BattleTickEvent::InstanceResolved { result, .. } if result.instance_id == 1001),
            ) {
                resolved = true;
                break;
            }
        }

        assert!(resolved);
        let instance = world.instance(1001).expect("instance should exist");
        assert_eq!(instance.status, BattleInstanceStatus::Resolved);
        assert!(!world.recent_results().is_empty());
    }

    #[test]
    fn overlapping_army_active_encounter_is_rejected() {
        let mut world = sample_battle_world();
        world.queue_order(BattleOrder::StartEncounter(StartBattleEncounterOrder {
            instance_id: 1001,
            encounter_id: 7001,
            location: SettlementId(3),
            attacker_army: ArmyId(7),
            defender_army: ArmyId(8),
            attacker_strength: 200,
            defender_strength: 200,
        }));
        world.advance_tick(Tick(1));

        world.queue_order(BattleOrder::StartEncounter(StartBattleEncounterOrder {
            instance_id: 1002,
            encounter_id: 7002,
            location: SettlementId(4),
            attacker_army: ArmyId(8),
            defender_army: ArmyId(11),
            attacker_strength: 180,
            defender_strength: 190,
        }));
        world.advance_tick(Tick(2));

        assert!(world.instance(1001).is_some());
        assert!(world.instance(1002).is_none());
    }

    #[test]
    fn force_resolve_finishes_active_instance() {
        let mut world = sample_battle_world();
        world.queue_order(BattleOrder::StartEncounter(StartBattleEncounterOrder {
            instance_id: 1003,
            encounter_id: 7003,
            location: SettlementId(5),
            attacker_army: ArmyId(12),
            defender_army: ArmyId(13),
            attacker_strength: 160,
            defender_strength: 150,
        }));
        world.advance_tick(Tick(1));

        world.queue_order(BattleOrder::ForceResolve(ForceResolveBattleOrder { instance_id: 1003 }));
        let result = world.advance_tick(Tick(2));

        assert!(result.events.iter().any(
            |event| matches!(event, BattleTickEvent::InstanceResolved { result, .. } if result.instance_id == 1003)
        ));
        let instance = world.instance(1003).expect("instance should exist");
        assert_eq!(instance.status, BattleInstanceStatus::Resolved);
    }
}
