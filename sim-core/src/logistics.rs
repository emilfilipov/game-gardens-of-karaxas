use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use crate::{ArmyId, SettlementId, Tick};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct SupplyStock {
    pub food: u32,
    pub horses: u32,
    pub materiel: u32,
}

impl SupplyStock {
    pub const fn new(food: u32, horses: u32, materiel: u32) -> Self {
        Self { food, horses, materiel }
    }

    pub fn is_empty(self) -> bool {
        self.food == 0 && self.horses == 0 && self.materiel == 0
    }

    pub fn total_units(self) -> u32 {
        self.food.saturating_add(self.horses).saturating_add(self.materiel)
    }

    pub fn saturating_add_assign(&mut self, other: Self) {
        self.food = self.food.saturating_add(other.food);
        self.horses = self.horses.saturating_add(other.horses);
        self.materiel = self.materiel.saturating_add(other.materiel);
    }

    pub fn drain_up_to(&mut self, requested: Self) -> Self {
        let moved = Self {
            food: self.food.min(requested.food),
            horses: self.horses.min(requested.horses),
            materiel: self.materiel.min(requested.materiel),
        };
        self.food = self.food.saturating_sub(moved.food);
        self.horses = self.horses.saturating_sub(moved.horses);
        self.materiel = self.materiel.saturating_sub(moved.materiel);
        moved
    }

    pub fn missing_from(requested: Self, consumed: Self) -> Self {
        Self {
            food: requested.food.saturating_sub(consumed.food),
            horses: requested.horses.saturating_sub(consumed.horses),
            materiel: requested.materiel.saturating_sub(consumed.materiel),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ArmyLogisticsState {
    pub army_id: ArmyId,
    pub location: SettlementId,
    pub troop_strength: u32,
    pub stock: SupplyStock,
    pub consumption_per_tick: SupplyStock,
    pub shortage_ticks: u32,
    pub cumulative_attrition: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct SupplyTransferOrder {
    pub from_army: ArmyId,
    pub to_army: ArmyId,
    pub stock: SupplyStock,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum LogisticsTickEvent {
    SupplyTransferApplied {
        from_army: ArmyId,
        to_army: ArmyId,
        moved: SupplyStock,
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

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct LogisticsTickResult {
    pub events: Vec<LogisticsTickEvent>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct LogisticsWorld {
    armies: BTreeMap<ArmyId, ArmyLogisticsState>,
    pending_transfers: Vec<SupplyTransferOrder>,
}

impl LogisticsWorld {
    pub fn insert_army(&mut self, army: ArmyLogisticsState) -> Result<(), &'static str> {
        if army.troop_strength == 0 {
            return Err("troop_strength must be greater than zero");
        }
        self.armies.insert(army.army_id, army);
        Ok(())
    }

    pub fn army(&self, army_id: ArmyId) -> Option<&ArmyLogisticsState> {
        self.armies.get(&army_id)
    }

    pub fn armies(&self) -> impl Iterator<Item = &ArmyLogisticsState> {
        self.armies.values()
    }

    pub fn pending_transfers(&self) -> &[SupplyTransferOrder] {
        &self.pending_transfers
    }

    pub fn queue_transfer(&mut self, transfer: SupplyTransferOrder) {
        self.pending_transfers.push(transfer);
    }

    pub fn set_army_location(&mut self, army_id: ArmyId, location: SettlementId) {
        if let Some(army) = self.armies.get_mut(&army_id) {
            army.location = location;
        }
    }

    pub fn advance_tick(&mut self, tick: Tick) -> LogisticsTickResult {
        let mut events = Vec::new();
        self.apply_transfers(tick, &mut events);

        let army_ids: Vec<ArmyId> = self.armies.keys().copied().collect();
        for army_id in army_ids {
            let Some(army) = self.armies.get_mut(&army_id) else {
                continue;
            };

            let requested = army.consumption_per_tick;
            let consumed = army.stock.drain_up_to(requested);
            let missing = SupplyStock::missing_from(requested, consumed);

            if missing.total_units() > 0 {
                army.shortage_ticks = army.shortage_ticks.saturating_add(1);
                let pressure = army.shortage_ticks.min(6);
                let shortage_penalty = missing.food / 5 + (missing.horses + missing.materiel) / 8;
                let raw_attrition = 1_u32.saturating_add(pressure).saturating_add(shortage_penalty);
                let attrition = raw_attrition.min(army.troop_strength);
                if attrition > 0 {
                    army.troop_strength = army.troop_strength.saturating_sub(attrition);
                    army.cumulative_attrition = army.cumulative_attrition.saturating_add(attrition);
                    events.push(LogisticsTickEvent::ArmyAttritionApplied {
                        army_id,
                        attrition,
                        troop_strength: army.troop_strength,
                        shortage_ticks: army.shortage_ticks,
                        tick,
                    });
                }
            } else {
                army.shortage_ticks = 0;
            }

            events.push(LogisticsTickEvent::ArmySupplyConsumed {
                army_id,
                consumed,
                remaining: army.stock,
                troop_strength: army.troop_strength,
                shortage_ticks: army.shortage_ticks,
                tick,
            });
        }

        LogisticsTickResult { events }
    }

    fn apply_transfers(&mut self, tick: Tick, events: &mut Vec<LogisticsTickEvent>) {
        let mut queued = std::mem::take(&mut self.pending_transfers);
        queued.sort_by_key(|order| {
            (
                order.from_army,
                order.to_army,
                order.stock.food,
                order.stock.horses,
                order.stock.materiel,
            )
        });

        for order in queued {
            if order.from_army == order.to_army {
                continue;
            }

            let Some(mut from) = self.armies.remove(&order.from_army) else {
                continue;
            };
            let Some(mut to) = self.armies.remove(&order.to_army) else {
                self.armies.insert(order.from_army, from);
                continue;
            };

            let moved = from.stock.drain_up_to(order.stock);
            if !moved.is_empty() {
                to.stock.saturating_add_assign(moved);
                events.push(LogisticsTickEvent::SupplyTransferApplied {
                    from_army: order.from_army,
                    to_army: order.to_army,
                    moved,
                    tick,
                });
            }

            self.armies.insert(order.from_army, from);
            self.armies.insert(order.to_army, to);
        }
    }
}

pub fn sample_logistics_world() -> LogisticsWorld {
    let mut world = LogisticsWorld::default();
    world
        .insert_army(ArmyLogisticsState {
            army_id: ArmyId(7),
            location: SettlementId(1),
            troop_strength: 180,
            stock: SupplyStock::new(40, 20, 14),
            consumption_per_tick: SupplyStock::new(6, 2, 1),
            shortage_ticks: 0,
            cumulative_attrition: 0,
        })
        .expect("sample army 7 should be valid");
    world
        .insert_army(ArmyLogisticsState {
            army_id: ArmyId(8),
            location: SettlementId(3),
            troop_strength: 150,
            stock: SupplyStock::new(8, 4, 3),
            consumption_per_tick: SupplyStock::new(5, 2, 1),
            shortage_ticks: 0,
            cumulative_attrition: 0,
        })
        .expect("sample army 8 should be valid");
    world
        .insert_army(ArmyLogisticsState {
            army_id: ArmyId(11),
            location: SettlementId(5),
            troop_strength: 120,
            stock: SupplyStock::new(15, 7, 6),
            consumption_per_tick: SupplyStock::new(4, 1, 1),
            shortage_ticks: 0,
            cumulative_attrition: 0,
        })
        .expect("sample army 11 should be valid");
    world
}

#[cfg(test)]
mod tests {
    use crate::Tick;

    use super::{LogisticsTickEvent, SupplyStock, SupplyTransferOrder, sample_logistics_world};

    #[test]
    fn transfer_is_applied_before_consumption() {
        let mut world = sample_logistics_world();
        world.queue_transfer(SupplyTransferOrder {
            from_army: crate::ArmyId(7),
            to_army: crate::ArmyId(8),
            stock: SupplyStock::new(10, 0, 0),
        });

        let result = world.advance_tick(Tick(1));
        let transfer = result.events.iter().find_map(|event| {
            if let LogisticsTickEvent::SupplyTransferApplied {
                from_army,
                to_army,
                moved,
                ..
            } = event
            {
                Some((*from_army, *to_army, *moved))
            } else {
                None
            }
        });

        assert_eq!(
            transfer,
            Some((crate::ArmyId(7), crate::ArmyId(8), SupplyStock::new(10, 0, 0)))
        );
    }

    #[test]
    fn shortage_drives_attrition_over_time() {
        let mut world = sample_logistics_world();
        let initial_strength = world.army(crate::ArmyId(8)).expect("army should exist").troop_strength;

        world.advance_tick(Tick(1));
        world.advance_tick(Tick(2));
        world.advance_tick(Tick(3));
        world.advance_tick(Tick(4));

        let army = world.army(crate::ArmyId(8)).expect("army should exist");
        assert!(army.troop_strength < initial_strength);
        assert!(army.cumulative_attrition > 0);
        assert!(army.shortage_ticks > 0);
    }

    #[test]
    fn shortage_ticks_reset_after_restock_and_stable_tick() {
        let mut world = sample_logistics_world();
        world.advance_tick(Tick(1));
        world.advance_tick(Tick(2));

        world.queue_transfer(SupplyTransferOrder {
            from_army: crate::ArmyId(7),
            to_army: crate::ArmyId(8),
            stock: SupplyStock::new(40, 10, 10),
        });
        world.advance_tick(Tick(3));

        let army_after_transfer = world.army(crate::ArmyId(8)).expect("army should exist");
        assert_eq!(army_after_transfer.shortage_ticks, 0);
    }
}
