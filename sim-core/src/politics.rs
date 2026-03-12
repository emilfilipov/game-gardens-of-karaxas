use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use crate::{FactionId, HouseholdId, Tick};

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum OfficeTitle {
    Chancellor,
    Marshal,
    Steward,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum TreatyKind {
    TradePact,
    NonAggression,
    MilitaryAccess,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct FactionPoliticalState {
    pub faction_id: FactionId,
    pub legitimacy_bp: u32,
    pub stability_bp: u32,
    pub influence_points: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct FactionStanding {
    pub actor_faction: FactionId,
    pub target_faction: FactionId,
    pub standing_bp: i32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct OfficeAssignment {
    pub faction_id: FactionId,
    pub title: OfficeTitle,
    pub household_id: HouseholdId,
    pub assigned_tick: Tick,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct TreatyRecord {
    pub treaty_id: u64,
    pub faction_a: FactionId,
    pub faction_b: FactionId,
    pub treaty_kind: TreatyKind,
    pub active: bool,
    pub trust_bp: u32,
    pub signed_tick: Tick,
    pub last_updated_tick: Tick,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct AssignOfficeOrder {
    pub faction_id: FactionId,
    pub title: OfficeTitle,
    pub household_id: HouseholdId,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct SetTreatyStatusOrder {
    pub treaty_id: u64,
    pub faction_a: FactionId,
    pub faction_b: FactionId,
    pub treaty_kind: TreatyKind,
    pub active: bool,
    pub trust_bp: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct AdjustStandingOrder {
    pub actor_faction: FactionId,
    pub target_faction: FactionId,
    pub delta_bp: i32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum PoliticsOrder {
    AdjustStanding(AdjustStandingOrder),
    AssignOffice(AssignOfficeOrder),
    SetTreatyStatus(SetTreatyStatusOrder),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum PoliticsTickEvent {
    FactionStandingUpdated {
        actor_faction: FactionId,
        target_faction: FactionId,
        previous_standing_bp: i32,
        standing_bp: i32,
        delta_bp: i32,
        tick: Tick,
    },
    OfficeAssigned {
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
    LegitimacyUpdated {
        faction_id: FactionId,
        legitimacy_bp: u32,
        stability_bp: u32,
        influence_points: u32,
        tick: Tick,
    },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct PoliticsTickResult {
    pub events: Vec<PoliticsTickEvent>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PoliticsWorld {
    factions: BTreeMap<FactionId, FactionPoliticalState>,
    standings: BTreeMap<(FactionId, FactionId), i32>,
    offices: BTreeMap<(FactionId, OfficeTitle), OfficeAssignment>,
    treaties: BTreeMap<u64, TreatyRecord>,
    pending_orders: Vec<PoliticsOrder>,
    legitimacy_recompute_interval_ticks: u64,
}

impl Default for PoliticsWorld {
    fn default() -> Self {
        Self {
            factions: BTreeMap::new(),
            standings: BTreeMap::new(),
            offices: BTreeMap::new(),
            treaties: BTreeMap::new(),
            pending_orders: Vec::new(),
            legitimacy_recompute_interval_ticks: 2,
        }
    }
}

impl PoliticsWorld {
    pub fn insert_faction(&mut self, faction: FactionPoliticalState) {
        self.factions.insert(faction.faction_id, faction);
    }

    pub fn queue_order(&mut self, order: PoliticsOrder) {
        self.pending_orders.push(order);
    }

    pub fn set_legitimacy_recompute_interval_ticks(&mut self, interval: u64) {
        self.legitimacy_recompute_interval_ticks = interval.max(1);
    }

    pub fn factions(&self) -> impl Iterator<Item = &FactionPoliticalState> {
        self.factions.values()
    }

    pub fn standings(&self) -> Vec<FactionStanding> {
        self.standings
            .iter()
            .map(|((actor_faction, target_faction), standing_bp)| FactionStanding {
                actor_faction: *actor_faction,
                target_faction: *target_faction,
                standing_bp: *standing_bp,
            })
            .collect()
    }

    pub fn offices(&self) -> impl Iterator<Item = &OfficeAssignment> {
        self.offices.values()
    }

    pub fn treaties(&self) -> impl Iterator<Item = &TreatyRecord> {
        self.treaties.values()
    }

    pub fn pending_orders(&self) -> &[PoliticsOrder] {
        &self.pending_orders
    }

    pub fn faction(&self, faction_id: FactionId) -> Option<&FactionPoliticalState> {
        self.factions.get(&faction_id)
    }

    pub fn standing(&self, actor_faction: FactionId, target_faction: FactionId) -> i32 {
        self.standings
            .get(&(actor_faction, target_faction))
            .copied()
            .unwrap_or(0)
    }

    pub fn advance_tick(&mut self, tick: Tick) -> PoliticsTickResult {
        let mut events = Vec::new();
        self.apply_orders(tick, &mut events);

        if tick.0.is_multiple_of(self.legitimacy_recompute_interval_ticks) {
            self.recompute_legitimacy(tick, &mut events);
        }

        PoliticsTickResult { events }
    }

    fn apply_orders(&mut self, tick: Tick, events: &mut Vec<PoliticsTickEvent>) {
        let mut queued = std::mem::take(&mut self.pending_orders);
        queued.sort_by_key(|order| serde_json::to_string(order).unwrap_or_default());

        for order in queued {
            match order {
                PoliticsOrder::AdjustStanding(order) => self.apply_standing_delta(order, tick, events),
                PoliticsOrder::AssignOffice(order) => self.apply_office_assignment(order, tick, events),
                PoliticsOrder::SetTreatyStatus(order) => self.apply_treaty_status(order, tick, events),
            }
        }
    }

    fn apply_standing_delta(&mut self, order: AdjustStandingOrder, tick: Tick, events: &mut Vec<PoliticsTickEvent>) {
        if order.actor_faction == order.target_faction {
            return;
        }
        if !self.factions.contains_key(&order.actor_faction) || !self.factions.contains_key(&order.target_faction) {
            return;
        }

        let key = (order.actor_faction, order.target_faction);
        let current = self.standings.get(&key).copied().unwrap_or(0);
        let updated = current.saturating_add(order.delta_bp).clamp(-10_000, 10_000);
        self.standings.insert(key, updated);

        let mirrored_key = (order.target_faction, order.actor_faction);
        let mirrored_current = self.standings.get(&mirrored_key).copied().unwrap_or(0);
        let mirrored_delta = order.delta_bp / 2;
        let mirrored_updated = mirrored_current.saturating_add(mirrored_delta).clamp(-10_000, 10_000);
        self.standings.insert(mirrored_key, mirrored_updated);

        if let Some(actor) = self.factions.get_mut(&order.actor_faction) {
            if order.delta_bp >= 0 {
                actor.legitimacy_bp = actor.legitimacy_bp.saturating_add(20).min(10_000);
            } else {
                actor.legitimacy_bp = actor.legitimacy_bp.saturating_sub(24).max(900);
            }
        }

        events.push(PoliticsTickEvent::FactionStandingUpdated {
            actor_faction: order.actor_faction,
            target_faction: order.target_faction,
            previous_standing_bp: current,
            standing_bp: updated,
            delta_bp: order.delta_bp,
            tick,
        });
    }

    fn apply_office_assignment(&mut self, order: AssignOfficeOrder, tick: Tick, events: &mut Vec<PoliticsTickEvent>) {
        if !self.factions.contains_key(&order.faction_id) {
            return;
        }

        let key = (order.faction_id, order.title);
        let replaced_household_id = self.offices.get(&key).map(|row| row.household_id);
        self.offices.insert(
            key,
            OfficeAssignment {
                faction_id: order.faction_id,
                title: order.title,
                household_id: order.household_id,
                assigned_tick: tick,
            },
        );

        if let Some(faction) = self.factions.get_mut(&order.faction_id) {
            faction.legitimacy_bp = faction.legitimacy_bp.saturating_add(80).min(10_000);
            faction.stability_bp = faction.stability_bp.saturating_add(110).min(10_000);
            faction.influence_points = faction.influence_points.saturating_add(3);
        }

        events.push(PoliticsTickEvent::OfficeAssigned {
            faction_id: order.faction_id,
            title: order.title,
            household_id: order.household_id,
            replaced_household_id,
            tick,
        });
    }

    fn apply_treaty_status(&mut self, order: SetTreatyStatusOrder, tick: Tick, events: &mut Vec<PoliticsTickEvent>) {
        if order.faction_a == order.faction_b {
            return;
        }
        if !self.factions.contains_key(&order.faction_a) || !self.factions.contains_key(&order.faction_b) {
            return;
        }

        let trust_bp = order.trust_bp.min(10_000);
        let existing = self.treaties.get(&order.treaty_id).copied();
        let signed_tick = existing.map(|row| row.signed_tick).unwrap_or(tick);
        self.treaties.insert(
            order.treaty_id,
            TreatyRecord {
                treaty_id: order.treaty_id,
                faction_a: order.faction_a,
                faction_b: order.faction_b,
                treaty_kind: order.treaty_kind,
                active: order.active,
                trust_bp,
                signed_tick,
                last_updated_tick: tick,
            },
        );

        let standing_delta = if order.active {
            i32::try_from(trust_bp / 120).unwrap_or(i32::MAX)
        } else {
            -i32::try_from(trust_bp / 100).unwrap_or(i32::MAX)
        };
        self.apply_standing_delta(
            AdjustStandingOrder {
                actor_faction: order.faction_a,
                target_faction: order.faction_b,
                delta_bp: standing_delta,
            },
            tick,
            events,
        );

        events.push(PoliticsTickEvent::TreatyStatusChanged {
            treaty_id: order.treaty_id,
            faction_a: order.faction_a,
            faction_b: order.faction_b,
            treaty_kind: order.treaty_kind,
            active: order.active,
            trust_bp,
            tick,
        });
    }

    fn recompute_legitimacy(&mut self, tick: Tick, events: &mut Vec<PoliticsTickEvent>) {
        let faction_ids: Vec<FactionId> = self.factions.keys().copied().collect();
        for faction_id in faction_ids {
            let Some(faction) = self.factions.get_mut(&faction_id) else {
                continue;
            };

            let office_count =
                u32::try_from(self.offices.keys().filter(|(id, _)| *id == faction_id).count()).unwrap_or(0);
            let active_treaties = u32::try_from(
                self.treaties
                    .values()
                    .filter(|row| row.active && (row.faction_a == faction_id || row.faction_b == faction_id))
                    .count(),
            )
            .unwrap_or(0);

            let mut standing_sum = 0_i32;
            let mut standing_count = 0_i32;
            for ((actor, _target), standing_bp) in &self.standings {
                if *actor == faction_id {
                    standing_sum = standing_sum.saturating_add(*standing_bp);
                    standing_count += 1;
                }
            }
            let standing_avg = if standing_count > 0 {
                standing_sum / standing_count
            } else {
                0
            };

            let legitimacy_target = 5_500_i32
                .saturating_add(i32::try_from(office_count.saturating_mul(180)).unwrap_or(i32::MAX))
                .saturating_add(i32::try_from(active_treaties.saturating_mul(120)).unwrap_or(i32::MAX))
                .saturating_add(standing_avg / 3)
                .clamp(1_000, 10_000);
            let legitimacy_target_u32 = u32::try_from(legitimacy_target).unwrap_or(1_000);
            let legitimacy_prev = faction.legitimacy_bp;
            faction.legitimacy_bp = smooth_toward(faction.legitimacy_bp, legitimacy_target_u32, 180);

            let stability_target = 5_200_i32
                .saturating_add(i32::try_from(active_treaties.saturating_mul(140)).unwrap_or(i32::MAX))
                .saturating_add(i32::try_from(office_count.saturating_mul(110)).unwrap_or(i32::MAX))
                .saturating_add(standing_avg / 2)
                .clamp(900, 10_000);
            faction.stability_bp = smooth_toward(
                faction.stability_bp,
                u32::try_from(stability_target).unwrap_or(900),
                220,
            );

            let influence_gain = (faction.legitimacy_bp / 900)
                .saturating_add(active_treaties)
                .saturating_add(office_count);
            faction.influence_points = faction.influence_points.saturating_add(influence_gain.max(1));

            if faction.legitimacy_bp != legitimacy_prev || tick.0.is_multiple_of(4) {
                events.push(PoliticsTickEvent::LegitimacyUpdated {
                    faction_id,
                    legitimacy_bp: faction.legitimacy_bp,
                    stability_bp: faction.stability_bp,
                    influence_points: faction.influence_points,
                    tick,
                });
            }
        }
    }
}

fn smooth_toward(current: u32, target: u32, step: u32) -> u32 {
    if current == target {
        return current;
    }
    if current < target {
        current.saturating_add(step).min(target)
    } else {
        current.saturating_sub(step).max(target)
    }
}

pub fn sample_politics_world() -> PoliticsWorld {
    let mut world = PoliticsWorld::default();

    world.insert_faction(FactionPoliticalState {
        faction_id: FactionId(1),
        legitimacy_bp: 6_100,
        stability_bp: 5_800,
        influence_points: 24,
    });
    world.insert_faction(FactionPoliticalState {
        faction_id: FactionId(2),
        legitimacy_bp: 5_900,
        stability_bp: 5_300,
        influence_points: 21,
    });
    world.insert_faction(FactionPoliticalState {
        faction_id: FactionId(3),
        legitimacy_bp: 5_300,
        stability_bp: 4_900,
        influence_points: 18,
    });

    world.queue_order(PoliticsOrder::AdjustStanding(AdjustStandingOrder {
        actor_faction: FactionId(1),
        target_faction: FactionId(2),
        delta_bp: 1_200,
    }));
    world.queue_order(PoliticsOrder::AdjustStanding(AdjustStandingOrder {
        actor_faction: FactionId(2),
        target_faction: FactionId(3),
        delta_bp: -1_400,
    }));
    let _ = world.advance_tick(Tick(1));

    world.queue_order(PoliticsOrder::AssignOffice(AssignOfficeOrder {
        faction_id: FactionId(1),
        title: OfficeTitle::Chancellor,
        household_id: HouseholdId(101),
    }));
    let _ = world.advance_tick(Tick(2));

    world.queue_order(PoliticsOrder::SetTreatyStatus(SetTreatyStatusOrder {
        treaty_id: 5001,
        faction_a: FactionId(1),
        faction_b: FactionId(3),
        treaty_kind: TreatyKind::TradePact,
        active: true,
        trust_bp: 6_000,
    }));
    let _ = world.advance_tick(Tick(3));

    world
}

#[cfg(test)]
mod tests {
    use crate::{FactionId, HouseholdId, Tick};

    use super::{
        AdjustStandingOrder, AssignOfficeOrder, OfficeTitle, PoliticsOrder, PoliticsTickEvent, SetTreatyStatusOrder,
        TreatyKind, sample_politics_world,
    };

    #[test]
    fn standing_delta_updates_relations_and_legitimacy() {
        let mut world = sample_politics_world();
        let before = world
            .faction(FactionId(1))
            .expect("faction 1 should exist")
            .legitimacy_bp;
        let before_standing = world.standing(FactionId(1), FactionId(2));

        world.queue_order(PoliticsOrder::AdjustStanding(AdjustStandingOrder {
            actor_faction: FactionId(1),
            target_faction: FactionId(2),
            delta_bp: 900,
        }));
        let result = world.advance_tick(Tick(6));

        let after = world
            .faction(FactionId(1))
            .expect("faction 1 should exist")
            .legitimacy_bp;
        let after_standing = world.standing(FactionId(1), FactionId(2));

        assert!(after_standing > before_standing);
        assert!(after >= before);
        assert!(result.events.iter().any(
            |event| matches!(event, PoliticsTickEvent::FactionStandingUpdated { actor_faction, target_faction, .. } if *actor_faction == FactionId(1) && *target_faction == FactionId(2))
        ));
    }

    #[test]
    fn office_assignment_replaces_existing_holder() {
        let mut world = sample_politics_world();
        world.queue_order(PoliticsOrder::AssignOffice(AssignOfficeOrder {
            faction_id: FactionId(1),
            title: OfficeTitle::Marshal,
            household_id: HouseholdId(201),
        }));
        world.advance_tick(Tick(7));

        world.queue_order(PoliticsOrder::AssignOffice(AssignOfficeOrder {
            faction_id: FactionId(1),
            title: OfficeTitle::Marshal,
            household_id: HouseholdId(202),
        }));
        let result = world.advance_tick(Tick(8));

        assert!(result.events.iter().any(
            |event| matches!(event, PoliticsTickEvent::OfficeAssigned { title: OfficeTitle::Marshal, replaced_household_id: Some(id), .. } if *id == HouseholdId(201))
        ));
    }

    #[test]
    fn treaty_activation_and_breaking_shift_standing() {
        let mut world = sample_politics_world();
        let before = world.standing(FactionId(2), FactionId(1));

        world.queue_order(PoliticsOrder::SetTreatyStatus(SetTreatyStatusOrder {
            treaty_id: 9001,
            faction_a: FactionId(2),
            faction_b: FactionId(1),
            treaty_kind: TreatyKind::NonAggression,
            active: true,
            trust_bp: 7_200,
        }));
        world.advance_tick(Tick(9));
        let active = world.standing(FactionId(2), FactionId(1));

        world.queue_order(PoliticsOrder::SetTreatyStatus(SetTreatyStatusOrder {
            treaty_id: 9001,
            faction_a: FactionId(2),
            faction_b: FactionId(1),
            treaty_kind: TreatyKind::NonAggression,
            active: false,
            trust_bp: 7_200,
        }));
        let result = world.advance_tick(Tick(10));
        let after_break = world.standing(FactionId(2), FactionId(1));

        assert!(active > before);
        assert!(after_break < active);
        assert!(result.events.iter().any(
            |event| matches!(event, PoliticsTickEvent::TreatyStatusChanged { treaty_id, active: false, .. } if *treaty_id == 9001)
        ));
    }

    #[test]
    fn deterministic_ordering_keeps_outcome_stable() {
        let mut a = sample_politics_world();
        a.queue_order(PoliticsOrder::AdjustStanding(AdjustStandingOrder {
            actor_faction: FactionId(1),
            target_faction: FactionId(3),
            delta_bp: 350,
        }));
        a.queue_order(PoliticsOrder::AssignOffice(AssignOfficeOrder {
            faction_id: FactionId(3),
            title: OfficeTitle::Steward,
            household_id: HouseholdId(301),
        }));
        let _ = a.advance_tick(Tick(11));

        let mut b = sample_politics_world();
        b.queue_order(PoliticsOrder::AssignOffice(AssignOfficeOrder {
            faction_id: FactionId(3),
            title: OfficeTitle::Steward,
            household_id: HouseholdId(301),
        }));
        b.queue_order(PoliticsOrder::AdjustStanding(AdjustStandingOrder {
            actor_faction: FactionId(1),
            target_faction: FactionId(3),
            delta_bp: 350,
        }));
        let _ = b.advance_tick(Tick(11));

        let factions_a: Vec<_> = a.factions().copied().collect();
        let factions_b: Vec<_> = b.factions().copied().collect();
        assert_eq!(factions_a, factions_b);
        assert_eq!(a.standings(), b.standings());
    }
}
