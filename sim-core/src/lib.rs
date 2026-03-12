//! Shared simulation-domain contracts for Ambitions of Peace.

use serde::{Deserialize, Serialize};

mod espionage;
mod logistics;
mod politics;
mod trade;
mod travel;

pub use espionage::{
    CounterIntelSweepOrder, EspionageOrder, EspionageTickEvent, EspionageTickResult, EspionageWorld, InformantState,
    InformantStatus, IntelReportRecord, RecruitInformantOrder, RequestIntelReportOrder, sample_espionage_world,
};
pub use logistics::{
    ArmyLogisticsState, LogisticsTickEvent, LogisticsTickResult, LogisticsWorld, SupplyStock, SupplyTransferOrder,
    sample_logistics_world,
};
pub use politics::{
    AdjustStandingOrder, AssignOfficeOrder, FactionPoliticalState, FactionStanding, OfficeAssignment, OfficeTitle,
    PoliticsOrder, PoliticsTickEvent, PoliticsTickResult, PoliticsWorld, SetTreatyStatusOrder, TreatyKind,
    TreatyRecord, sample_politics_world,
};
pub use trade::{
    MarketState, TradeRoute, TradeShipmentOrder, TradeTickEvent, TradeTickResult, TradeWorld, sample_trade_world,
};
pub use travel::{
    RiskModifiers, RouteEdge, RouteId, SettlementNode, TravelEstimate, TravelGraph, TravelPlan, TravelPreference,
    adjusted_route_risk, sample_levant_travel_graph,
};

/// Latest schema version for shared simulation payloads.
pub const SIM_SCHEMA_VERSION: u32 = 1;

/// Lowest schema version the current crate accepts.
pub const MIN_COMPATIBLE_SCHEMA_VERSION: u32 = 1;

macro_rules! id_type {
    ($name:ident) => {
        #[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
        pub struct $name(pub u64);
    };
}

id_type!(FactionId);
id_type!(SettlementId);
id_type!(HouseholdId);
id_type!(ArmyId);
id_type!(CharacterId);
id_type!(InformantId);

/// Canonical deterministic tick index used by authority services and replay checks.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct Tick(pub u64);

impl Tick {
    /// Returns the next deterministic tick value.
    pub fn next(self) -> Self {
        Self(self.0 + 1)
    }
}

/// Common payload envelope for deterministic command/event transport.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Envelope<T> {
    pub schema_version: u32,
    pub trace_id: String,
    pub payload: T,
}

impl<T> Envelope<T> {
    pub fn new(trace_id: impl Into<String>, payload: T) -> Self {
        Self {
            schema_version: SIM_SCHEMA_VERSION,
            trace_id: trace_id.into(),
            payload,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum CommandPayload {
    IssueMoveArmy {
        army_id: ArmyId,
        origin: SettlementId,
        destination: SettlementId,
    },
    SetFactionStance {
        actor_faction: FactionId,
        target_faction: FactionId,
        relation_delta: i32,
    },
    QueueSupplyTransfer {
        from_army: ArmyId,
        to_army: ArmyId,
        stock: SupplyStock,
    },
    QueueTradeShipment {
        origin_settlement: SettlementId,
        destination_settlement: SettlementId,
        goods: SupplyStock,
    },
    RecruitInformant {
        informant_id: InformantId,
        handler_faction: FactionId,
        target_faction: FactionId,
        location: SettlementId,
        reliability_bp: u32,
        deception_bp: u32,
    },
    RequestIntelReport {
        informant_id: InformantId,
        subject_settlement: SettlementId,
    },
    CounterIntelSweep {
        defender_faction: FactionId,
        settlement_id: SettlementId,
        intensity_bp: u32,
    },
    AssignPoliticalOffice {
        faction_id: FactionId,
        title: OfficeTitle,
        household_id: HouseholdId,
    },
    SetTreatyStatus {
        treaty_id: u64,
        faction_a: FactionId,
        faction_b: FactionId,
        treaty_kind: TreatyKind,
        active: bool,
        trust_bp: u32,
    },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum EventPayload {
    ArmyMoved {
        army_id: ArmyId,
        origin: SettlementId,
        destination: SettlementId,
        tick: Tick,
    },
    FactionStanceUpdated {
        actor_faction: FactionId,
        target_faction: FactionId,
        relation_delta: i32,
        tick: Tick,
    },
    SupplyTransferQueued {
        from_army: ArmyId,
        to_army: ArmyId,
        stock: SupplyStock,
        tick: Tick,
    },
    SupplyTransferApplied {
        from_army: ArmyId,
        to_army: ArmyId,
        stock: SupplyStock,
        tick: Tick,
    },
    ArmySupplyConsumed {
        army_id: ArmyId,
        consumed: SupplyStock,
        remaining: SupplyStock,
        troop_strength: u32,
        shortage_ticks: u32,
        tick: Tick,
    },
    ArmyAttritionApplied {
        army_id: ArmyId,
        attrition: u32,
        troop_strength: u32,
        shortage_ticks: u32,
        tick: Tick,
    },
    TradeShipmentQueued {
        origin_settlement: SettlementId,
        destination_settlement: SettlementId,
        goods: SupplyStock,
        tick: Tick,
    },
    TradeShipmentExecuted {
        origin_settlement: SettlementId,
        destination_settlement: SettlementId,
        delivered: SupplyStock,
        lost: SupplyStock,
        tariff_bp: u32,
        safety_bp: u32,
        tick: Tick,
    },
    MarketPriceUpdated {
        settlement_id: SettlementId,
        price_index_bp: u32,
        shortage_pressure_bp: u32,
        tariff_pressure_bp: u32,
        tick: Tick,
    },
    InformantRecruited {
        informant_id: InformantId,
        handler_faction: FactionId,
        target_faction: FactionId,
        location: SettlementId,
        reliability_bp: u32,
        deception_bp: u32,
        tick: Tick,
    },
    InformantRecruitQueued {
        informant_id: InformantId,
        handler_faction: FactionId,
        target_faction: FactionId,
        location: SettlementId,
        reliability_bp: u32,
        deception_bp: u32,
        tick: Tick,
    },
    IntelReportRequested {
        informant_id: InformantId,
        subject_settlement: SettlementId,
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
        tick: Tick,
    },
    CounterIntelSweepResolved {
        defender_faction: FactionId,
        settlement_id: SettlementId,
        intensity_bp: u32,
        detected_informants: Vec<InformantId>,
        neutralized_informants: Vec<InformantId>,
        tick: Tick,
    },
    CounterIntelSweepQueued {
        defender_faction: FactionId,
        settlement_id: SettlementId,
        intensity_bp: u32,
        tick: Tick,
    },
    PoliticalStandingUpdated {
        actor_faction: FactionId,
        target_faction: FactionId,
        previous_standing_bp: i32,
        standing_bp: i32,
        delta_bp: i32,
        tick: Tick,
    },
    PoliticalOfficeAssigned {
        faction_id: FactionId,
        title: OfficeTitle,
        household_id: HouseholdId,
        replaced_household_id: Option<HouseholdId>,
        tick: Tick,
    },
    TreatyStatusChanged {
        treaty_id: u64,
        faction_a: FactionId,
        faction_b: FactionId,
        treaty_kind: TreatyKind,
        active: bool,
        trust_bp: u32,
        tick: Tick,
    },
    PoliticalLegitimacyUpdated {
        faction_id: FactionId,
        legitimacy_bp: u32,
        stability_bp: u32,
        influence_points: u32,
        tick: Tick,
    },
}

pub type CommandEnvelope = Envelope<CommandPayload>;
pub type EventEnvelope = Envelope<EventPayload>;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SchemaCompatibility {
    Compatible,
    UpgradeRequired { current: u32, min_supported: u32 },
    UnsupportedFuture { current: u32, max_supported: u32 },
}

/// Checks whether an incoming schema version can be safely processed.
pub fn evaluate_schema_version(version: u32) -> SchemaCompatibility {
    if version < MIN_COMPATIBLE_SCHEMA_VERSION {
        SchemaCompatibility::UpgradeRequired {
            current: version,
            min_supported: MIN_COMPATIBLE_SCHEMA_VERSION,
        }
    } else if version > SIM_SCHEMA_VERSION {
        SchemaCompatibility::UnsupportedFuture {
            current: version,
            max_supported: SIM_SCHEMA_VERSION,
        }
    } else {
        SchemaCompatibility::Compatible
    }
}

#[cfg(test)]
mod tests {
    use super::{
        ArmyId, CommandEnvelope, CommandPayload, EventPayload, FactionId, HouseholdId, InformantId, InformantStatus,
        IntelReportRecord, MIN_COMPATIBLE_SCHEMA_VERSION, OfficeTitle, SIM_SCHEMA_VERSION, SchemaCompatibility,
        SettlementId, Tick, TreatyKind, evaluate_schema_version,
    };

    #[test]
    fn tick_advances_monotonically() {
        let t0 = Tick(41);
        let t1 = t0.next();
        assert_eq!(t1.0, 42);
    }

    #[test]
    fn schema_compatibility_is_enforced() {
        assert_eq!(
            evaluate_schema_version(SIM_SCHEMA_VERSION),
            SchemaCompatibility::Compatible
        );
        assert_eq!(
            evaluate_schema_version(MIN_COMPATIBLE_SCHEMA_VERSION.saturating_sub(1)),
            SchemaCompatibility::UpgradeRequired {
                current: 0,
                min_supported: MIN_COMPATIBLE_SCHEMA_VERSION,
            }
        );
        assert_eq!(
            evaluate_schema_version(SIM_SCHEMA_VERSION + 1),
            SchemaCompatibility::UnsupportedFuture {
                current: SIM_SCHEMA_VERSION + 1,
                max_supported: SIM_SCHEMA_VERSION,
            }
        );
    }

    #[test]
    fn command_envelope_roundtrip_is_stable() {
        let envelope = CommandEnvelope::new(
            "trace-1",
            CommandPayload::IssueMoveArmy {
                army_id: ArmyId(7),
                origin: SettlementId(3),
                destination: SettlementId(9),
            },
        );

        let json = serde_json::to_string(&envelope).expect("serialize command envelope");
        let decoded: CommandEnvelope = serde_json::from_str(&json).expect("deserialize command envelope");

        assert_eq!(decoded, envelope);
    }

    #[test]
    fn event_payload_roundtrip_is_stable() {
        let payload = EventPayload::ArmyMoved {
            army_id: ArmyId(22),
            origin: SettlementId(10),
            destination: SettlementId(11),
            tick: Tick(512),
        };

        let json = serde_json::to_string(&payload).expect("serialize event payload");
        let decoded: EventPayload = serde_json::from_str(&json).expect("deserialize event payload");

        assert_eq!(decoded, payload);
    }

    #[test]
    fn espionage_command_payload_roundtrip_is_stable() {
        let envelope = CommandEnvelope::new(
            "trace-espionage-command",
            CommandPayload::CounterIntelSweep {
                defender_faction: FactionId(2),
                settlement_id: SettlementId(3),
                intensity_bp: 7_500,
            },
        );

        let json = serde_json::to_string(&envelope).expect("serialize command envelope");
        let decoded: CommandEnvelope = serde_json::from_str(&json).expect("deserialize command envelope");

        assert_eq!(decoded, envelope);
    }

    #[test]
    fn espionage_event_payload_roundtrip_is_stable() {
        let payload = EventPayload::IntelReportGenerated {
            report: IntelReportRecord {
                informant_id: InformantId(9001),
                handler_faction: FactionId(1),
                target_faction: FactionId(2),
                subject_settlement: SettlementId(5),
                confidence_bp: 6_200,
                reliability_bp: 6_800,
                false_report: false,
                exposure_bp: 4_100,
                tick: Tick(42),
            },
            tick: Tick(42),
        };

        let json = serde_json::to_string(&payload).expect("serialize event payload");
        let decoded: EventPayload = serde_json::from_str(&json).expect("deserialize event payload");

        assert_eq!(decoded, payload);
    }

    #[test]
    fn espionage_status_event_roundtrip_is_stable() {
        let payload = EventPayload::InformantStatusChanged {
            informant_id: InformantId(9002),
            status: InformantStatus::Dormant,
            reliability_bp: 5_500,
            exposure_bp: 7_800,
            tick: Tick(88),
        };

        let json = serde_json::to_string(&payload).expect("serialize event payload");
        let decoded: EventPayload = serde_json::from_str(&json).expect("deserialize event payload");

        assert_eq!(decoded, payload);
    }

    #[test]
    fn politics_command_payload_roundtrip_is_stable() {
        let envelope = CommandEnvelope::new(
            "trace-politics-command",
            CommandPayload::AssignPoliticalOffice {
                faction_id: FactionId(2),
                title: OfficeTitle::Marshal,
                household_id: HouseholdId(501),
            },
        );

        let json = serde_json::to_string(&envelope).expect("serialize command envelope");
        let decoded: CommandEnvelope = serde_json::from_str(&json).expect("deserialize command envelope");

        assert_eq!(decoded, envelope);
    }

    #[test]
    fn politics_event_payload_roundtrip_is_stable() {
        let payload = EventPayload::TreatyStatusChanged {
            treaty_id: 99,
            faction_a: FactionId(1),
            faction_b: FactionId(3),
            treaty_kind: TreatyKind::TradePact,
            active: true,
            trust_bp: 6_200,
            tick: Tick(77),
        };

        let json = serde_json::to_string(&payload).expect("serialize event payload");
        let decoded: EventPayload = serde_json::from_str(&json).expect("deserialize event payload");

        assert_eq!(decoded, payload);
    }
}
