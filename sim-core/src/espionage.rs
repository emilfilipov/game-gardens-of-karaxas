use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use crate::{FactionId, InformantId, SettlementId, Tick};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum InformantStatus {
    Active,
    Dormant,
    Burned,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct InformantState {
    pub informant_id: InformantId,
    pub handler_faction: FactionId,
    pub target_faction: FactionId,
    pub location: SettlementId,
    pub reliability_bp: u32,
    pub deception_bp: u32,
    pub exposure_bp: u32,
    pub status: InformantStatus,
    pub reports_submitted: u32,
    pub last_report_tick: Option<Tick>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct RecruitInformantOrder {
    pub informant_id: InformantId,
    pub handler_faction: FactionId,
    pub target_faction: FactionId,
    pub location: SettlementId,
    pub reliability_bp: u32,
    pub deception_bp: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct RequestIntelReportOrder {
    pub informant_id: InformantId,
    pub subject_settlement: SettlementId,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct CounterIntelSweepOrder {
    pub defender_faction: FactionId,
    pub settlement_id: SettlementId,
    pub intensity_bp: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum EspionageOrder {
    RecruitInformant(RecruitInformantOrder),
    RequestIntelReport(RequestIntelReportOrder),
    CounterIntelSweep(CounterIntelSweepOrder),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct IntelReportRecord {
    pub informant_id: InformantId,
    pub handler_faction: FactionId,
    pub target_faction: FactionId,
    pub subject_settlement: SettlementId,
    pub confidence_bp: u32,
    pub reliability_bp: u32,
    pub false_report: bool,
    pub exposure_bp: u32,
    pub tick: Tick,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum EspionageTickEvent {
    InformantRecruited {
        informant_id: InformantId,
        handler_faction: FactionId,
        target_faction: FactionId,
        location: SettlementId,
        reliability_bp: u32,
        deception_bp: u32,
        tick: Tick,
    },
    InformantStatusChanged {
        informant_id: InformantId,
        status: InformantStatus,
        reliability_bp: u32,
        exposure_bp: u32,
        tick: Tick,
    },
    IntelReportGenerated {
        report: IntelReportRecord,
    },
    CounterIntelSweepResolved {
        defender_faction: FactionId,
        settlement_id: SettlementId,
        intensity_bp: u32,
        detected_informants: Vec<InformantId>,
        neutralized_informants: Vec<InformantId>,
        tick: Tick,
    },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct EspionageTickResult {
    pub events: Vec<EspionageTickEvent>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EspionageWorld {
    informants: BTreeMap<InformantId, InformantState>,
    pending_orders: Vec<EspionageOrder>,
    recent_reports: Vec<IntelReportRecord>,
    passive_report_interval_ticks: u64,
    max_recent_reports: usize,
}

impl Default for EspionageWorld {
    fn default() -> Self {
        Self {
            informants: BTreeMap::new(),
            pending_orders: Vec::new(),
            recent_reports: Vec::new(),
            passive_report_interval_ticks: 3,
            max_recent_reports: 24,
        }
    }
}

impl EspionageWorld {
    pub fn insert_informant(&mut self, informant: InformantState) -> Result<(), &'static str> {
        if informant.handler_faction == informant.target_faction {
            return Err("handler_faction and target_faction must differ");
        }
        if informant.reliability_bp > 10_000 {
            return Err("reliability_bp must be <= 10000");
        }
        if informant.deception_bp > 10_000 {
            return Err("deception_bp must be <= 10000");
        }
        if informant.exposure_bp > 10_000 {
            return Err("exposure_bp must be <= 10000");
        }
        self.informants.insert(informant.informant_id, informant);
        Ok(())
    }

    pub fn set_passive_report_interval_ticks(&mut self, interval: u64) {
        self.passive_report_interval_ticks = interval.max(1);
    }

    pub fn informants(&self) -> impl Iterator<Item = &InformantState> {
        self.informants.values()
    }

    pub fn pending_orders(&self) -> &[EspionageOrder] {
        &self.pending_orders
    }

    pub fn recent_reports(&self) -> &[IntelReportRecord] {
        &self.recent_reports
    }

    pub fn informant(&self, informant_id: InformantId) -> Option<&InformantState> {
        self.informants.get(&informant_id)
    }

    pub fn queue_order(&mut self, order: EspionageOrder) {
        self.pending_orders.push(order);
    }

    pub fn advance_tick(&mut self, tick: Tick) -> EspionageTickResult {
        let mut events = Vec::new();
        self.apply_pending_orders(tick, &mut events);
        self.apply_informant_drift(tick, &mut events);

        if tick.0.is_multiple_of(self.passive_report_interval_ticks) {
            self.generate_passive_reports(tick, &mut events);
        }

        EspionageTickResult { events }
    }

    fn apply_pending_orders(&mut self, tick: Tick, events: &mut Vec<EspionageTickEvent>) {
        let mut queued = std::mem::take(&mut self.pending_orders);
        queued.sort_by_key(|order| serde_json::to_string(order).unwrap_or_default());

        for order in queued {
            match order {
                EspionageOrder::RecruitInformant(order) => self.apply_recruit_order(order, tick, events),
                EspionageOrder::RequestIntelReport(order) => {
                    if let Some(event) =
                        self.generate_report(order.informant_id, order.subject_settlement, tick, 920, 420)
                    {
                        events.push(event);
                    }
                }
                EspionageOrder::CounterIntelSweep(order) => self.apply_counter_sweep(order, tick, events),
            }
        }
    }

    fn apply_recruit_order(&mut self, order: RecruitInformantOrder, tick: Tick, events: &mut Vec<EspionageTickEvent>) {
        if self.informants.contains_key(&order.informant_id) {
            return;
        }

        let informant = InformantState {
            informant_id: order.informant_id,
            handler_faction: order.handler_faction,
            target_faction: order.target_faction,
            location: order.location,
            reliability_bp: order.reliability_bp.min(10_000),
            deception_bp: order.deception_bp.min(10_000),
            exposure_bp: 1_900,
            status: InformantStatus::Active,
            reports_submitted: 0,
            last_report_tick: None,
        };

        self.informants.insert(order.informant_id, informant);
        events.push(EspionageTickEvent::InformantRecruited {
            informant_id: order.informant_id,
            handler_faction: order.handler_faction,
            target_faction: order.target_faction,
            location: order.location,
            reliability_bp: order.reliability_bp.min(10_000),
            deception_bp: order.deception_bp.min(10_000),
            tick,
        });
    }

    fn apply_counter_sweep(&mut self, order: CounterIntelSweepOrder, tick: Tick, events: &mut Vec<EspionageTickEvent>) {
        let mut detected_informants = Vec::new();
        let mut neutralized_informants = Vec::new();

        let ids: Vec<InformantId> = self.informants.keys().copied().collect();
        for informant_id in ids {
            let Some(informant) = self.informants.get_mut(&informant_id) else {
                continue;
            };
            if informant.target_faction != order.defender_faction
                || informant.location != order.settlement_id
                || informant.status == InformantStatus::Burned
            {
                continue;
            }

            let detection_threshold = order
                .intensity_bp
                .saturating_add(informant.exposure_bp / 2)
                .saturating_add((10_000_u32.saturating_sub(informant.reliability_bp)) / 3)
                .min(9_900);
            let roll = deterministic_roll_bp(
                tick,
                informant_id,
                order.settlement_id,
                order.defender_faction,
                informant.handler_faction,
                77_u64.saturating_add(u64::from(informant.reports_submitted)),
            );

            if roll < detection_threshold {
                detected_informants.push(informant_id);

                if informant.exposure_bp >= 9_500 || roll < detection_threshold / 3 {
                    informant.status = InformantStatus::Burned;
                    informant.exposure_bp = 10_000;
                    neutralized_informants.push(informant_id);
                    events.push(EspionageTickEvent::InformantStatusChanged {
                        informant_id,
                        status: InformantStatus::Burned,
                        reliability_bp: informant.reliability_bp,
                        exposure_bp: informant.exposure_bp,
                        tick,
                    });
                } else {
                    informant.status = InformantStatus::Dormant;
                    informant.exposure_bp = informant.exposure_bp.saturating_add(1_200).min(9_800);
                    informant.reliability_bp = informant.reliability_bp.saturating_sub(360);
                    events.push(EspionageTickEvent::InformantStatusChanged {
                        informant_id,
                        status: InformantStatus::Dormant,
                        reliability_bp: informant.reliability_bp,
                        exposure_bp: informant.exposure_bp,
                        tick,
                    });
                }
            }
        }

        detected_informants.sort();
        neutralized_informants.sort();
        events.push(EspionageTickEvent::CounterIntelSweepResolved {
            defender_faction: order.defender_faction,
            settlement_id: order.settlement_id,
            intensity_bp: order.intensity_bp.min(10_000),
            detected_informants,
            neutralized_informants,
            tick,
        });
    }

    fn apply_informant_drift(&mut self, tick: Tick, events: &mut Vec<EspionageTickEvent>) {
        let ids: Vec<InformantId> = self.informants.keys().copied().collect();
        for informant_id in ids {
            let Some(informant) = self.informants.get_mut(&informant_id) else {
                continue;
            };
            if informant.status == InformantStatus::Burned {
                continue;
            }

            let previous_status = informant.status;

            let exposure_decay = match informant.status {
                InformantStatus::Active => 85,
                InformantStatus::Dormant => 220,
                InformantStatus::Burned => 0,
            };
            informant.exposure_bp = informant.exposure_bp.saturating_sub(exposure_decay);
            informant.reliability_bp = if informant.reliability_bp < 6_600 {
                informant.reliability_bp.saturating_add(25).min(10_000)
            } else {
                informant.reliability_bp.saturating_sub(6)
            };

            if informant.exposure_bp >= 9_900 {
                informant.status = InformantStatus::Burned;
            } else if informant.exposure_bp >= 7_300 && informant.status == InformantStatus::Active {
                informant.status = InformantStatus::Dormant;
            } else if informant.exposure_bp <= 4_200 && informant.status == InformantStatus::Dormant {
                informant.status = InformantStatus::Active;
            }

            if informant.status != previous_status {
                events.push(EspionageTickEvent::InformantStatusChanged {
                    informant_id,
                    status: informant.status,
                    reliability_bp: informant.reliability_bp,
                    exposure_bp: informant.exposure_bp,
                    tick,
                });
            }
        }
    }

    fn generate_passive_reports(&mut self, tick: Tick, events: &mut Vec<EspionageTickEvent>) {
        let ids: Vec<InformantId> = self.informants.keys().copied().collect();
        for informant_id in ids {
            let Some(informant) = self.informants.get(&informant_id) else {
                continue;
            };
            if informant.status != InformantStatus::Active {
                continue;
            }

            if let Some(event) = self.generate_report(informant_id, informant.location, tick, 420, -220) {
                events.push(event);
            }
        }
    }

    fn generate_report(
        &mut self,
        informant_id: InformantId,
        subject_settlement: SettlementId,
        tick: Tick,
        mission_exposure_bp: u32,
        confidence_bias_bp: i32,
    ) -> Option<EspionageTickEvent> {
        let informant = self.informants.get_mut(&informant_id)?;
        if informant.status == InformantStatus::Burned {
            return None;
        }

        let status_deception_bp = match informant.status {
            InformantStatus::Active => 0,
            InformantStatus::Dormant => 900,
            InformantStatus::Burned => 0,
        };
        let deception_threshold = informant
            .deception_bp
            .saturating_add(informant.exposure_bp / 3)
            .saturating_add(status_deception_bp)
            .min(10_000);
        let roll = deterministic_roll_bp(
            tick,
            informant_id,
            subject_settlement,
            informant.target_faction,
            informant.handler_faction,
            13_u64.saturating_add(u64::from(informant.reports_submitted)),
        );
        let false_report = roll < deception_threshold;

        let mut confidence_bp = i32::try_from(informant.reliability_bp)
            .unwrap_or(i32::MAX)
            .saturating_sub(i32::try_from(informant.exposure_bp / 4).unwrap_or(i32::MAX))
            .saturating_add(confidence_bias_bp)
            .clamp(700, 9_800);
        if false_report {
            confidence_bp = confidence_bp.saturating_sub(1_200).max(500);
        }
        let confidence_bp = u32::try_from(confidence_bp).unwrap_or(500);

        informant.reports_submitted = informant.reports_submitted.saturating_add(1);
        informant.last_report_tick = Some(tick);
        informant.exposure_bp = informant
            .exposure_bp
            .saturating_add(mission_exposure_bp)
            .saturating_add(if false_report { 450 } else { 180 })
            .min(10_000);
        informant.reliability_bp = if false_report {
            informant.reliability_bp.saturating_sub(220)
        } else {
            informant.reliability_bp.saturating_add(40).min(10_000)
        };

        let report = IntelReportRecord {
            informant_id,
            handler_faction: informant.handler_faction,
            target_faction: informant.target_faction,
            subject_settlement,
            confidence_bp,
            reliability_bp: informant.reliability_bp,
            false_report,
            exposure_bp: informant.exposure_bp,
            tick,
        };
        self.recent_reports.push(report);
        while self.recent_reports.len() > self.max_recent_reports {
            self.recent_reports.remove(0);
        }

        Some(EspionageTickEvent::IntelReportGenerated { report })
    }
}

fn deterministic_roll_bp(
    tick: Tick,
    informant_id: InformantId,
    settlement_id: SettlementId,
    faction_a: FactionId,
    faction_b: FactionId,
    salt: u64,
) -> u32 {
    let mut value = tick
        .0
        .wrapping_mul(6_364_136_223_846_793_005)
        .wrapping_add(informant_id.0.wrapping_mul(1_442_695_040_888_963_407))
        .wrapping_add(settlement_id.0.wrapping_mul(0x9E37_79B9_7F4A_7C15))
        .wrapping_add(faction_a.0.wrapping_mul(0xBF58_476D_1CE4_E5B9))
        .wrapping_add(faction_b.0.wrapping_mul(0x94D0_49BB_1331_11EB))
        .wrapping_add(salt);
    value ^= value >> 30;
    value = value.wrapping_mul(0xBF58_476D_1CE4_E5B9);
    value ^= value >> 27;
    value = value.wrapping_mul(0x94D0_49BB_1331_11EB);
    value ^= value >> 31;

    u32::try_from(value % 10_000).unwrap_or(0)
}

pub fn sample_espionage_world() -> EspionageWorld {
    let mut world = EspionageWorld::default();

    world
        .insert_informant(InformantState {
            informant_id: InformantId(1001),
            handler_faction: FactionId(1),
            target_faction: FactionId(2),
            location: SettlementId(3),
            reliability_bp: 7_200,
            deception_bp: 1_500,
            exposure_bp: 2_900,
            status: InformantStatus::Active,
            reports_submitted: 2,
            last_report_tick: Some(Tick(4)),
        })
        .expect("sample informant 1001 should be valid");
    world
        .insert_informant(InformantState {
            informant_id: InformantId(1002),
            handler_faction: FactionId(3),
            target_faction: FactionId(1),
            location: SettlementId(5),
            reliability_bp: 6_600,
            deception_bp: 2_300,
            exposure_bp: 7_600,
            status: InformantStatus::Dormant,
            reports_submitted: 3,
            last_report_tick: Some(Tick(5)),
        })
        .expect("sample informant 1002 should be valid");

    world
}

#[cfg(test)]
mod tests {
    use crate::{FactionId, InformantId, SettlementId, Tick};

    use super::{
        CounterIntelSweepOrder, EspionageOrder, EspionageTickEvent, InformantState, InformantStatus,
        RecruitInformantOrder, RequestIntelReportOrder, sample_espionage_world,
    };

    #[test]
    fn recruit_and_report_emit_reliability_metadata() {
        let mut world = sample_espionage_world();
        world.queue_order(EspionageOrder::RecruitInformant(RecruitInformantOrder {
            informant_id: InformantId(2001),
            handler_faction: FactionId(1),
            target_faction: FactionId(4),
            location: SettlementId(4),
            reliability_bp: 6_400,
            deception_bp: 2_200,
        }));
        world.queue_order(EspionageOrder::RequestIntelReport(RequestIntelReportOrder {
            informant_id: InformantId(2001),
            subject_settlement: SettlementId(5),
        }));

        let result = world.advance_tick(Tick(7));
        let report = result.events.iter().find_map(|event| match event {
            EspionageTickEvent::IntelReportGenerated { report } => Some(*report),
            _ => None,
        });

        assert!(result
            .events
            .iter()
            .any(|event| matches!(event, EspionageTickEvent::InformantRecruited { informant_id, .. } if *informant_id == InformantId(2001))));
        let report = report.expect("report event should be generated");
        assert!(report.confidence_bp > 0);
        assert!(report.reliability_bp > 0);
        assert_eq!(world.recent_reports().last().copied(), Some(report));
    }

    #[test]
    fn high_deception_informant_can_emit_false_report() {
        let mut world = sample_espionage_world();
        world
            .insert_informant(InformantState {
                informant_id: InformantId(3001),
                handler_faction: FactionId(2),
                target_faction: FactionId(5),
                location: SettlementId(2),
                reliability_bp: 4_000,
                deception_bp: 10_000,
                exposure_bp: 2_000,
                status: InformantStatus::Active,
                reports_submitted: 0,
                last_report_tick: None,
            })
            .expect("informant should insert");

        world.queue_order(EspionageOrder::RequestIntelReport(RequestIntelReportOrder {
            informant_id: InformantId(3001),
            subject_settlement: SettlementId(2),
        }));
        let result = world.advance_tick(Tick(8));

        assert!(result.events.iter().any(
            |event| matches!(event, EspionageTickEvent::IntelReportGenerated { report } if report.informant_id == InformantId(3001) && report.false_report)
        ));
    }

    #[test]
    fn counter_intel_sweep_detects_and_burns_exposed_asset() {
        let mut world = sample_espionage_world();
        world
            .insert_informant(InformantState {
                informant_id: InformantId(4444),
                handler_faction: FactionId(1),
                target_faction: FactionId(2),
                location: SettlementId(3),
                reliability_bp: 2_600,
                deception_bp: 3_200,
                exposure_bp: 9_800,
                status: InformantStatus::Active,
                reports_submitted: 2,
                last_report_tick: Some(Tick(5)),
            })
            .expect("informant should insert");

        world.queue_order(EspionageOrder::CounterIntelSweep(CounterIntelSweepOrder {
            defender_faction: FactionId(2),
            settlement_id: SettlementId(3),
            intensity_bp: 8_000,
        }));
        let result = world.advance_tick(Tick(9));

        assert!(result.events.iter().any(
            |event| matches!(event, EspionageTickEvent::CounterIntelSweepResolved { detected_informants, .. } if detected_informants.contains(&InformantId(4444)))
        ));

        let informant = world
            .informant(InformantId(4444))
            .expect("informant should still exist in world");
        assert_eq!(informant.status, InformantStatus::Burned);
    }

    #[test]
    fn dormant_informant_reactivates_after_exposure_cools() {
        let mut world = sample_espionage_world();
        world
            .insert_informant(InformantState {
                informant_id: InformantId(7777),
                handler_faction: FactionId(4),
                target_faction: FactionId(1),
                location: SettlementId(5),
                reliability_bp: 6_500,
                deception_bp: 2_000,
                exposure_bp: 4_250,
                status: InformantStatus::Dormant,
                reports_submitted: 1,
                last_report_tick: Some(Tick(2)),
            })
            .expect("informant should insert");

        let result = world.advance_tick(Tick(10));

        assert!(result.events.iter().any(|event| matches!(
            event,
            EspionageTickEvent::InformantStatusChanged {
                informant_id,
                status: InformantStatus::Active,
                ..
            } if *informant_id == InformantId(7777)
        )));
        let informant = world.informant(InformantId(7777)).expect("informant should exist");
        assert_eq!(informant.status, InformantStatus::Active);
    }

    #[test]
    fn passive_reports_emit_on_interval_for_active_assets() {
        let mut world = sample_espionage_world();
        world.set_passive_report_interval_ticks(2);

        let result = world.advance_tick(Tick(2));
        assert!(result.events.iter().any(
            |event| matches!(event, EspionageTickEvent::IntelReportGenerated { report } if report.informant_id == InformantId(1001))
        ));
        assert!(!world.recent_reports().is_empty());
    }
}
