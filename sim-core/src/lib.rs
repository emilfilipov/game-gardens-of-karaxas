//! Shared simulation-domain contracts for Ambitions of Peace.

use serde::{Deserialize, Serialize};

mod logistics;
mod travel;

pub use logistics::{
    ArmyLogisticsState, LogisticsTickEvent, LogisticsTickResult, LogisticsWorld, SupplyStock, SupplyTransferOrder,
    sample_logistics_world,
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
        ArmyId, CommandEnvelope, CommandPayload, EventPayload, MIN_COMPATIBLE_SCHEMA_VERSION, SIM_SCHEMA_VERSION,
        SchemaCompatibility, SettlementId, Tick, evaluate_schema_version,
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
}
