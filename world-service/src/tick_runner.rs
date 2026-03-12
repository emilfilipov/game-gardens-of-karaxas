use std::collections::VecDeque;
use std::time::Instant;

use serde::Serialize;
use sha2::{Digest, Sha256};
use sim_core::{
    AdjustStandingOrder, ArmyId, AssignOfficeOrder, BattleInstanceRecord, BattleOrder, BattleResultRecord,
    BattleTickEvent, BattleWorld, CommandEnvelope, CommandPayload, CounterIntelSweepOrder, DeployBattleReserveOrder,
    EspionageOrder, EspionageTickEvent, EspionageWorld, EventEnvelope, EventPayload, FactionId, FactionPoliticalState,
    FactionStanding, ForceResolveBattleOrder, InformantState, IntelReportRecord, LogisticsTickEvent, LogisticsWorld,
    MarketState, OfficeAssignment, PoliticsOrder, PoliticsTickEvent, PoliticsWorld, RequestIntelReportOrder,
    SetBattleFormationOrder, SetTreatyStatusOrder, SettlementId, StartBattleEncounterOrder, SupplyStock,
    SupplyTransferOrder, Tick, TradeRoute, TradeShipmentOrder, TradeTickEvent, TradeWorld, TreatyRecord,
    sample_battle_world, sample_espionage_world, sample_logistics_world, sample_politics_world, sample_trade_world,
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

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct TradeStateSnapshot {
    pub markets: Vec<MarketState>,
    pub routes: Vec<TradeRoute>,
    pub pending_shipments: Vec<TradeShipmentOrder>,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct EspionageStateSnapshot {
    pub informants: Vec<InformantState>,
    pub pending_orders: Vec<EspionageOrder>,
    pub recent_reports: Vec<IntelReportRecord>,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct PoliticsStateSnapshot {
    pub factions: Vec<FactionPoliticalState>,
    pub standings: Vec<FactionStanding>,
    pub offices: Vec<OfficeAssignment>,
    pub treaties: Vec<TreatyRecord>,
    pub pending_orders: Vec<PoliticsOrder>,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct BattleStateSnapshot {
    pub instances: Vec<BattleInstanceRecord>,
    pub recent_results: Vec<BattleResultRecord>,
    pub pending_orders: Vec<BattleOrder>,
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
    trade: TradeWorld,
    espionage: EspionageWorld,
    politics: PoliticsWorld,
    battle: BattleWorld,
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
            trade: sample_trade_world(),
            espionage: sample_espionage_world(),
            politics: sample_politics_world(),
            battle: sample_battle_world(),
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

    pub fn trade_state(&self) -> TradeStateSnapshot {
        TradeStateSnapshot {
            markets: self.trade.markets().cloned().collect(),
            routes: self.trade.routes().cloned().collect(),
            pending_shipments: self.trade.pending_shipments().to_vec(),
        }
    }

    pub fn espionage_state(&self) -> EspionageStateSnapshot {
        EspionageStateSnapshot {
            informants: self.espionage.informants().copied().collect(),
            pending_orders: self.espionage.pending_orders().to_vec(),
            recent_reports: self.espionage.recent_reports().to_vec(),
        }
    }

    pub fn politics_state(&self) -> PoliticsStateSnapshot {
        PoliticsStateSnapshot {
            factions: self.politics.factions().copied().collect(),
            standings: self.politics.standings(),
            offices: self.politics.offices().copied().collect(),
            treaties: self.politics.treaties().copied().collect(),
            pending_orders: self.politics.pending_orders().to_vec(),
        }
    }

    pub fn battle_state(&self) -> BattleStateSnapshot {
        BattleStateSnapshot {
            instances: self.battle.instances().copied().collect(),
            recent_results: self.battle.recent_results().to_vec(),
            pending_orders: self.battle.pending_orders().to_vec(),
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

        let trade_tick = self.trade.advance_tick(tick_now);
        for event in trade_tick.events {
            let trace_id = format!("trade-{}-{}", tick_now.0, self.event_log.len());
            self.event_log
                .push(EventEnvelope::new(trace_id, trade_event_to_payload(event)));
        }

        let espionage_tick = self.espionage.advance_tick(tick_now);
        for event in espionage_tick.events {
            let trace_id = format!("espionage-{}-{}", tick_now.0, self.event_log.len());
            self.event_log
                .push(EventEnvelope::new(trace_id, espionage_event_to_payload(event)));
        }

        let politics_tick = self.politics.advance_tick(tick_now);
        for event in politics_tick.events {
            let trace_id = format!("politics-{}-{}", tick_now.0, self.event_log.len());
            self.event_log
                .push(EventEnvelope::new(trace_id, politics_event_to_payload(event)));
        }

        let battle_tick = self.battle.advance_tick(tick_now);
        for event in battle_tick.events {
            let trace_id = format!("battle-{}-{}", tick_now.0, self.event_log.len());
            self.event_log
                .push(EventEnvelope::new(trace_id, battle_event_to_payload(event)));
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
            } => {
                self.politics
                    .queue_order(PoliticsOrder::AdjustStanding(AdjustStandingOrder {
                        actor_faction,
                        target_faction,
                        delta_bp: relation_delta,
                    }));
                EventPayload::FactionStanceUpdated {
                    actor_faction,
                    target_faction,
                    relation_delta,
                    tick,
                }
            }
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
            CommandPayload::QueueTradeShipment {
                origin_settlement,
                destination_settlement,
                goods,
            } => {
                self.trade.queue_shipment(TradeShipmentOrder {
                    origin: origin_settlement,
                    destination: destination_settlement,
                    goods,
                });
                EventPayload::TradeShipmentQueued {
                    origin_settlement,
                    destination_settlement,
                    goods,
                    tick,
                }
            }
            CommandPayload::RecruitInformant {
                informant_id,
                handler_faction,
                target_faction,
                location,
                reliability_bp,
                deception_bp,
            } => {
                self.espionage
                    .queue_order(EspionageOrder::RecruitInformant(sim_core::RecruitInformantOrder {
                        informant_id,
                        handler_faction,
                        target_faction,
                        location,
                        reliability_bp,
                        deception_bp,
                    }));
                EventPayload::InformantRecruitQueued {
                    informant_id,
                    handler_faction,
                    target_faction,
                    location,
                    reliability_bp,
                    deception_bp,
                    tick,
                }
            }
            CommandPayload::RequestIntelReport {
                informant_id,
                subject_settlement,
            } => {
                self.espionage
                    .queue_order(EspionageOrder::RequestIntelReport(RequestIntelReportOrder {
                        informant_id,
                        subject_settlement,
                    }));
                EventPayload::IntelReportRequested {
                    informant_id,
                    subject_settlement,
                    tick,
                }
            }
            CommandPayload::CounterIntelSweep {
                defender_faction,
                settlement_id,
                intensity_bp,
            } => {
                self.espionage
                    .queue_order(EspionageOrder::CounterIntelSweep(CounterIntelSweepOrder {
                        defender_faction,
                        settlement_id,
                        intensity_bp,
                    }));
                EventPayload::CounterIntelSweepQueued {
                    defender_faction,
                    settlement_id,
                    intensity_bp,
                    tick,
                }
            }
            CommandPayload::AssignPoliticalOffice {
                faction_id,
                title,
                household_id,
            } => {
                self.politics
                    .queue_order(PoliticsOrder::AssignOffice(AssignOfficeOrder {
                        faction_id,
                        title,
                        household_id,
                    }));
                EventPayload::PoliticalOfficeAssigned {
                    faction_id,
                    title,
                    household_id,
                    replaced_household_id: None,
                    tick,
                }
            }
            CommandPayload::SetTreatyStatus {
                treaty_id,
                faction_a,
                faction_b,
                treaty_kind,
                active,
                trust_bp,
            } => {
                self.politics
                    .queue_order(PoliticsOrder::SetTreatyStatus(SetTreatyStatusOrder {
                        treaty_id,
                        faction_a,
                        faction_b,
                        treaty_kind,
                        active,
                        trust_bp,
                    }));
                EventPayload::TreatyStatusChanged {
                    treaty_id,
                    faction_a,
                    faction_b,
                    treaty_kind,
                    active,
                    trust_bp,
                    tick,
                }
            }
            CommandPayload::StartBattleEncounter {
                instance_id,
                encounter_id,
                location,
                attacker_army,
                defender_army,
                attacker_strength,
                defender_strength,
            } => {
                self.battle
                    .queue_order(BattleOrder::StartEncounter(StartBattleEncounterOrder {
                        instance_id,
                        encounter_id,
                        location,
                        attacker_army,
                        defender_army,
                        attacker_strength,
                        defender_strength,
                    }));
                EventPayload::BattleEncounterQueued {
                    instance_id,
                    encounter_id,
                    location,
                    attacker_army,
                    defender_army,
                    tick,
                }
            }
            CommandPayload::ForceResolveBattleInstance { instance_id } => {
                self.battle
                    .queue_order(BattleOrder::ForceResolve(ForceResolveBattleOrder { instance_id }));
                EventPayload::BattleResolveQueued { instance_id, tick }
            }
            CommandPayload::SetBattleFormation {
                instance_id,
                side,
                formation,
            } => {
                self.battle
                    .queue_order(BattleOrder::SetFormation(SetBattleFormationOrder {
                        instance_id,
                        side,
                        formation,
                    }));
                EventPayload::BattleFormationQueued {
                    instance_id,
                    side,
                    formation,
                    tick,
                }
            }
            CommandPayload::DeployBattleReserve {
                instance_id,
                side,
                reserve_strength,
            } => {
                self.battle
                    .queue_order(BattleOrder::DeployReserve(DeployBattleReserveOrder {
                        instance_id,
                        side,
                        reserve_strength,
                    }));
                EventPayload::BattleReserveQueued {
                    instance_id,
                    side,
                    reserve_strength,
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

fn trade_event_to_payload(event: TradeTickEvent) -> EventPayload {
    match event {
        TradeTickEvent::ShipmentExecuted {
            origin,
            destination,
            delivered,
            lost,
            tariff_bp,
            safety_bp,
            tick,
        } => EventPayload::TradeShipmentExecuted {
            origin_settlement: origin,
            destination_settlement: destination,
            delivered,
            lost,
            tariff_bp,
            safety_bp,
            tick,
        },
        TradeTickEvent::MarketPriceUpdated {
            settlement_id,
            price_index_bp,
            shortage_pressure_bp,
            tariff_pressure_bp,
            tick,
        } => EventPayload::MarketPriceUpdated {
            settlement_id,
            price_index_bp,
            shortage_pressure_bp,
            tariff_pressure_bp,
            tick,
        },
    }
}

fn espionage_event_to_payload(event: EspionageTickEvent) -> EventPayload {
    match event {
        EspionageTickEvent::InformantRecruited {
            informant_id,
            handler_faction,
            target_faction,
            location,
            reliability_bp,
            deception_bp,
            tick,
        } => EventPayload::InformantRecruited {
            informant_id,
            handler_faction,
            target_faction,
            location,
            reliability_bp,
            deception_bp,
            tick,
        },
        EspionageTickEvent::InformantStatusChanged {
            informant_id,
            status,
            reliability_bp,
            exposure_bp,
            tick,
        } => EventPayload::InformantStatusChanged {
            informant_id,
            status,
            reliability_bp,
            exposure_bp,
            tick,
        },
        EspionageTickEvent::IntelReportGenerated { report } => EventPayload::IntelReportGenerated {
            report,
            tick: report.tick,
        },
        EspionageTickEvent::CounterIntelSweepResolved {
            defender_faction,
            settlement_id,
            intensity_bp,
            detected_informants,
            neutralized_informants,
            tick,
        } => EventPayload::CounterIntelSweepResolved {
            defender_faction,
            settlement_id,
            intensity_bp,
            detected_informants,
            neutralized_informants,
            tick,
        },
    }
}

fn politics_event_to_payload(event: PoliticsTickEvent) -> EventPayload {
    match event {
        PoliticsTickEvent::FactionStandingUpdated {
            actor_faction,
            target_faction,
            previous_standing_bp,
            standing_bp,
            delta_bp,
            tick,
        } => EventPayload::PoliticalStandingUpdated {
            actor_faction,
            target_faction,
            previous_standing_bp,
            standing_bp,
            delta_bp,
            tick,
        },
        PoliticsTickEvent::OfficeAssigned {
            faction_id,
            title,
            household_id,
            replaced_household_id,
            tick,
        } => EventPayload::PoliticalOfficeAssigned {
            faction_id,
            title,
            household_id,
            replaced_household_id,
            tick,
        },
        PoliticsTickEvent::TreatyStatusChanged {
            treaty_id,
            faction_a,
            faction_b,
            treaty_kind,
            active,
            trust_bp,
            tick,
        } => EventPayload::TreatyStatusChanged {
            treaty_id,
            faction_a,
            faction_b,
            treaty_kind,
            active,
            trust_bp,
            tick,
        },
        PoliticsTickEvent::LegitimacyUpdated {
            faction_id,
            legitimacy_bp,
            stability_bp,
            influence_points,
            tick,
        } => EventPayload::PoliticalLegitimacyUpdated {
            faction_id,
            legitimacy_bp,
            stability_bp,
            influence_points,
            tick,
        },
    }
}

fn battle_event_to_payload(event: BattleTickEvent) -> EventPayload {
    match event {
        BattleTickEvent::EncounterCreated {
            instance_id,
            encounter_id,
            location,
            attacker_army,
            defender_army,
            tick,
        } => EventPayload::BattleInstanceCreated {
            instance_id,
            encounter_id,
            location,
            attacker_army,
            defender_army,
            tick,
        },
        BattleTickEvent::StepAdvanced {
            instance_id,
            step_index,
            attacker_strength,
            defender_strength,
            attacker_morale_bp,
            defender_morale_bp,
            tick,
        } => EventPayload::BattleInstanceStepAdvanced {
            instance_id,
            step_index,
            attacker_strength,
            defender_strength,
            attacker_morale_bp,
            defender_morale_bp,
            tick,
        },
        BattleTickEvent::FormationUpdated {
            instance_id,
            side,
            formation,
            tick,
        } => EventPayload::BattleFormationUpdated {
            instance_id,
            side,
            formation,
            tick,
        },
        BattleTickEvent::ReserveDeployed {
            instance_id,
            side,
            reserve_strength,
            total_strength_after_deploy,
            step_index,
            tick,
        } => EventPayload::BattleReserveDeployed {
            instance_id,
            side,
            reserve_strength,
            total_strength_after_deploy,
            step_index,
            tick,
        },
        BattleTickEvent::OutcomeScored {
            instance_id,
            attacker_outcome_score_bp,
            defender_outcome_score_bp,
            tick,
        } => EventPayload::BattleOutcomeScored {
            instance_id,
            attacker_outcome_score_bp,
            defender_outcome_score_bp,
            tick,
        },
        BattleTickEvent::InstanceResolved { result, tick } => EventPayload::BattleInstanceResolved { result, tick },
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

pub fn build_trade_shipment_command(
    trace_id: &str,
    origin_settlement: u64,
    destination_settlement: u64,
    food: u32,
    horses: u32,
    materiel: u32,
) -> CommandEnvelope {
    CommandEnvelope::new(
        trace_id,
        CommandPayload::QueueTradeShipment {
            origin_settlement: SettlementId(origin_settlement),
            destination_settlement: SettlementId(destination_settlement),
            goods: SupplyStock { food, horses, materiel },
        },
    )
}

#[allow(clippy::too_many_arguments)]
pub fn build_recruit_informant_command(
    trace_id: &str,
    informant_id: u64,
    handler_faction: u64,
    target_faction: u64,
    location: u64,
    reliability_bp: u32,
    deception_bp: u32,
) -> CommandEnvelope {
    CommandEnvelope::new(
        trace_id,
        CommandPayload::RecruitInformant {
            informant_id: sim_core::InformantId(informant_id),
            handler_faction: FactionId(handler_faction),
            target_faction: FactionId(target_faction),
            location: SettlementId(location),
            reliability_bp,
            deception_bp,
        },
    )
}

pub fn build_request_intel_report_command(
    trace_id: &str,
    informant_id: u64,
    subject_settlement: u64,
) -> CommandEnvelope {
    CommandEnvelope::new(
        trace_id,
        CommandPayload::RequestIntelReport {
            informant_id: sim_core::InformantId(informant_id),
            subject_settlement: SettlementId(subject_settlement),
        },
    )
}

pub fn build_counter_intel_sweep_command(
    trace_id: &str,
    defender_faction: u64,
    settlement_id: u64,
    intensity_bp: u32,
) -> CommandEnvelope {
    CommandEnvelope::new(
        trace_id,
        CommandPayload::CounterIntelSweep {
            defender_faction: FactionId(defender_faction),
            settlement_id: SettlementId(settlement_id),
            intensity_bp,
        },
    )
}

pub fn build_assign_political_office_command(
    trace_id: &str,
    faction_id: u64,
    title: sim_core::OfficeTitle,
    household_id: u64,
) -> CommandEnvelope {
    CommandEnvelope::new(
        trace_id,
        CommandPayload::AssignPoliticalOffice {
            faction_id: FactionId(faction_id),
            title,
            household_id: sim_core::HouseholdId(household_id),
        },
    )
}

#[allow(clippy::too_many_arguments)]
pub fn build_set_treaty_status_command(
    trace_id: &str,
    treaty_id: u64,
    faction_a: u64,
    faction_b: u64,
    treaty_kind: sim_core::TreatyKind,
    active: bool,
    trust_bp: u32,
) -> CommandEnvelope {
    CommandEnvelope::new(
        trace_id,
        CommandPayload::SetTreatyStatus {
            treaty_id,
            faction_a: FactionId(faction_a),
            faction_b: FactionId(faction_b),
            treaty_kind,
            active,
            trust_bp,
        },
    )
}

#[allow(clippy::too_many_arguments)]
pub fn build_start_battle_encounter_command(
    trace_id: &str,
    instance_id: u64,
    encounter_id: u64,
    location: u64,
    attacker_army: u64,
    defender_army: u64,
    attacker_strength: u32,
    defender_strength: u32,
) -> CommandEnvelope {
    CommandEnvelope::new(
        trace_id,
        CommandPayload::StartBattleEncounter {
            instance_id,
            encounter_id,
            location: SettlementId(location),
            attacker_army: ArmyId(attacker_army),
            defender_army: ArmyId(defender_army),
            attacker_strength,
            defender_strength,
        },
    )
}

pub fn build_force_resolve_battle_command(trace_id: &str, instance_id: u64) -> CommandEnvelope {
    CommandEnvelope::new(trace_id, CommandPayload::ForceResolveBattleInstance { instance_id })
}

pub fn build_set_battle_formation_command(
    trace_id: &str,
    instance_id: u64,
    side: sim_core::BattleSide,
    formation: sim_core::FormationStance,
) -> CommandEnvelope {
    CommandEnvelope::new(
        trace_id,
        CommandPayload::SetBattleFormation {
            instance_id,
            side,
            formation,
        },
    )
}

pub fn build_deploy_battle_reserve_command(
    trace_id: &str,
    instance_id: u64,
    side: sim_core::BattleSide,
    reserve_strength: u32,
) -> CommandEnvelope {
    CommandEnvelope::new(
        trace_id,
        CommandPayload::DeployBattleReserve {
            instance_id,
            side,
            reserve_strength,
        },
    )
}

#[cfg(test)]
mod tests {
    use sim_core::{BattleSide, FormationStance, OfficeTitle, TreatyKind};

    use super::{
        TickRunner, TickRunnerConfig, build_assign_political_office_command, build_counter_intel_sweep_command,
        build_deploy_battle_reserve_command, build_force_resolve_battle_command, build_move_army_command,
        build_recruit_informant_command, build_request_intel_report_command, build_set_battle_formation_command,
        build_set_stance_command, build_set_treaty_status_command, build_start_battle_encounter_command,
        build_supply_transfer_command, build_trade_shipment_command,
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

    #[test]
    fn trade_shipment_updates_market_state_over_ticks() {
        let mut runner = TickRunner::new(TickRunnerConfig::new(100, 10, 16));
        runner.queue_command(build_trade_shipment_command("trace-trade", 1, 3, 20, 5, 4));
        let _summary = runner.run_due_ticks(300);

        let state = runner.trade_state();
        let market3 = state
            .markets
            .iter()
            .find(|row| row.settlement_id.0 == 3)
            .expect("market 3 should exist");

        assert!(market3.stock.food > 90);
        assert!(market3.price_index_bp >= 10_000);
    }

    #[test]
    fn espionage_reports_and_sweeps_progress_over_ticks() {
        let mut runner = TickRunner::new(TickRunnerConfig::new(100, 10, 16));
        runner.queue_command(build_recruit_informant_command(
            "trace-recruit",
            9001,
            1,
            2,
            3,
            6_500,
            2_200,
        ));
        runner.queue_command(build_request_intel_report_command("trace-report", 9001, 5));
        runner.queue_command(build_counter_intel_sweep_command("trace-sweep", 2, 3, 8_000));
        let _summary = runner.run_due_ticks(0);

        let state = runner.espionage_state();
        assert!(state.recent_reports.iter().any(|row| row.informant_id.0 == 9001));
        assert!(state.informants.iter().any(|row| row.informant_id.0 == 9001));
    }

    #[test]
    fn political_offices_treaties_and_legitimacy_progress_over_ticks() {
        let mut runner = TickRunner::new(TickRunnerConfig::new(100, 10, 16));
        runner.queue_command(build_set_stance_command("trace-stance", 1, 2, 800));
        runner.queue_command(build_assign_political_office_command(
            "trace-office",
            1,
            OfficeTitle::Marshal,
            444,
        ));
        runner.queue_command(build_set_treaty_status_command(
            "trace-treaty",
            7001,
            1,
            3,
            TreatyKind::TradePact,
            true,
            6_500,
        ));
        let _summary = runner.run_due_ticks(200);

        let state = runner.politics_state();
        assert!(
            state
                .offices
                .iter()
                .any(|row| row.faction_id.0 == 1 && row.household_id.0 == 444)
        );
        assert!(state.treaties.iter().any(|row| row.treaty_id == 7001 && row.active));
        assert!(
            state
                .factions
                .iter()
                .any(|row| row.faction_id.0 == 1 && row.influence_points > 0)
        );
    }

    #[test]
    fn battle_instance_contract_advances_and_resolves() {
        let mut runner = TickRunner::new(TickRunnerConfig::new(100, 10, 16));
        runner.queue_command(build_start_battle_encounter_command(
            "trace-battle-start",
            1001,
            7001,
            3,
            7,
            8,
            230,
            220,
        ));
        runner.queue_command(build_set_battle_formation_command(
            "trace-battle-formation",
            1001,
            BattleSide::Attacker,
            FormationStance::Wedge,
        ));
        let _summary = runner.run_due_ticks(300);

        runner.queue_command(build_deploy_battle_reserve_command(
            "trace-battle-reserve",
            1001,
            BattleSide::Attacker,
            35,
        ));
        runner.queue_command(build_force_resolve_battle_command("trace-battle-resolve", 1001));
        let _summary = runner.run_due_ticks(600);

        let state = runner.battle_state();
        assert!(state.instances.iter().any(|row| row.instance_id == 1001));
        assert!(state.recent_results.iter().any(|row| row.instance_id == 1001));
        assert!(
            state
                .instances
                .iter()
                .any(|row| row.instance_id == 1001 && row.attacker_formation == FormationStance::Wedge)
        );
        assert!(
            state
                .instances
                .iter()
                .any(|row| row.instance_id == 1001 && row.attacker_reserve_deployed)
        );
    }
}
