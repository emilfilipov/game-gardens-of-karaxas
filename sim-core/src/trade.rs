use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use crate::{SettlementId, SupplyStock, Tick};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MarketState {
    pub settlement_id: SettlementId,
    pub stock: SupplyStock,
    pub target_stock: SupplyStock,
    pub price_index_bp: u32,
    pub shortage_pressure_bp: u32,
    pub tariff_pressure_bp: u32,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TradeRoute {
    pub route_id: u64,
    pub origin: SettlementId,
    pub destination: SettlementId,
    pub throughput_per_tick: SupplyStock,
    pub tariff_bp: u32,
    pub safety_bp: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct TradeShipmentOrder {
    pub origin: SettlementId,
    pub destination: SettlementId,
    pub goods: SupplyStock,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum TradeTickEvent {
    ShipmentExecuted {
        origin: SettlementId,
        destination: SettlementId,
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
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct TradeTickResult {
    pub events: Vec<TradeTickEvent>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TradeWorld {
    markets: BTreeMap<SettlementId, MarketState>,
    routes: BTreeMap<u64, TradeRoute>,
    pending_shipments: Vec<TradeShipmentOrder>,
    price_recompute_interval_ticks: u64,
}

impl Default for TradeWorld {
    fn default() -> Self {
        Self {
            markets: BTreeMap::new(),
            routes: BTreeMap::new(),
            pending_shipments: Vec::new(),
            price_recompute_interval_ticks: 3,
        }
    }
}

impl TradeWorld {
    pub fn set_price_recompute_interval_ticks(&mut self, interval: u64) {
        self.price_recompute_interval_ticks = interval.max(1);
    }

    pub fn insert_market(&mut self, market: MarketState) {
        self.markets.insert(market.settlement_id, market);
    }

    pub fn insert_route(&mut self, route: TradeRoute) -> Result<(), &'static str> {
        if route.origin == route.destination {
            return Err("trade route origin and destination must be different");
        }
        if route.safety_bp > 10_000 {
            return Err("safety_bp must be <= 10000");
        }
        if !self.markets.contains_key(&route.origin) || !self.markets.contains_key(&route.destination) {
            return Err("trade route references unknown market");
        }
        self.routes.insert(route.route_id, route);
        Ok(())
    }

    pub fn markets(&self) -> impl Iterator<Item = &MarketState> {
        self.markets.values()
    }

    pub fn routes(&self) -> impl Iterator<Item = &TradeRoute> {
        self.routes.values()
    }

    pub fn pending_shipments(&self) -> &[TradeShipmentOrder] {
        &self.pending_shipments
    }

    pub fn queue_shipment(&mut self, order: TradeShipmentOrder) {
        self.pending_shipments.push(order);
    }

    pub fn market(&self, settlement_id: SettlementId) -> Option<&MarketState> {
        self.markets.get(&settlement_id)
    }

    pub fn advance_tick(&mut self, tick: Tick) -> TradeTickResult {
        let mut events = Vec::new();
        self.apply_shipments(tick, &mut events);

        if tick.0.is_multiple_of(self.price_recompute_interval_ticks) {
            self.recompute_prices(tick, &mut events);
        }

        TradeTickResult { events }
    }

    fn apply_shipments(&mut self, tick: Tick, events: &mut Vec<TradeTickEvent>) {
        let mut queued = std::mem::take(&mut self.pending_shipments);
        queued.sort_by_key(|order| {
            (
                order.origin,
                order.destination,
                order.goods.food,
                order.goods.horses,
                order.goods.materiel,
            )
        });

        for order in queued {
            let Some(route) = self.pick_route(order.origin, order.destination).cloned() else {
                continue;
            };

            let Some(mut origin_market) = self.markets.remove(&order.origin) else {
                continue;
            };
            let Some(mut destination_market) = self.markets.remove(&order.destination) else {
                self.markets.insert(order.origin, origin_market);
                continue;
            };

            let route_limited_goods = SupplyStock {
                food: order.goods.food.min(route.throughput_per_tick.food),
                horses: order.goods.horses.min(route.throughput_per_tick.horses),
                materiel: order.goods.materiel.min(route.throughput_per_tick.materiel),
            };
            let launched = origin_market.stock.drain_up_to(route_limited_goods);

            let delivered = SupplyStock {
                food: launched.food.saturating_mul(route.safety_bp) / 10_000,
                horses: launched.horses.saturating_mul(route.safety_bp) / 10_000,
                materiel: launched.materiel.saturating_mul(route.safety_bp) / 10_000,
            };
            let lost = SupplyStock {
                food: launched.food.saturating_sub(delivered.food),
                horses: launched.horses.saturating_sub(delivered.horses),
                materiel: launched.materiel.saturating_sub(delivered.materiel),
            };

            destination_market.stock.saturating_add_assign(delivered);
            let tariff_delta = route
                .tariff_bp
                .saturating_mul(delivered.total_units())
                .saturating_div(15)
                .min(4_000);
            destination_market.tariff_pressure_bp = destination_market
                .tariff_pressure_bp
                .saturating_add(tariff_delta)
                .min(9_000);

            if delivered.total_units() > 0 || lost.total_units() > 0 {
                events.push(TradeTickEvent::ShipmentExecuted {
                    origin: order.origin,
                    destination: order.destination,
                    delivered,
                    lost,
                    tariff_bp: route.tariff_bp,
                    safety_bp: route.safety_bp,
                    tick,
                });
            }

            self.markets.insert(order.origin, origin_market);
            self.markets.insert(order.destination, destination_market);
        }
    }

    fn recompute_prices(&mut self, tick: Tick, events: &mut Vec<TradeTickEvent>) {
        let market_ids: Vec<SettlementId> = self.markets.keys().copied().collect();

        for market_id in market_ids {
            let Some(market) = self.markets.get_mut(&market_id) else {
                continue;
            };

            let target_total = market.target_stock.total_units().max(1);
            let stock_total = market.stock.total_units();
            let shortage_units = target_total.saturating_sub(stock_total);
            let surplus_units = stock_total.saturating_sub(target_total);

            let shortage_pressure_bp = shortage_units.saturating_mul(10_000) / target_total;
            market.shortage_pressure_bp = shortage_pressure_bp.min(12_000);

            let shortage_price_up = shortage_pressure_bp / 2;
            let surplus_price_down = (surplus_units.saturating_mul(10_000) / target_total) / 3;

            let raw_price = 10_000_i32
                .saturating_add(i32::try_from(shortage_price_up).unwrap_or(i32::MAX))
                .saturating_add(i32::try_from(market.tariff_pressure_bp).unwrap_or(i32::MAX))
                .saturating_sub(i32::try_from(surplus_price_down).unwrap_or(i32::MAX));
            let clamped_price = raw_price.clamp(6_000, 20_000);
            market.price_index_bp = u32::try_from(clamped_price).unwrap_or(20_000);

            events.push(TradeTickEvent::MarketPriceUpdated {
                settlement_id: market.settlement_id,
                price_index_bp: market.price_index_bp,
                shortage_pressure_bp: market.shortage_pressure_bp,
                tariff_pressure_bp: market.tariff_pressure_bp,
                tick,
            });

            market.tariff_pressure_bp = market.tariff_pressure_bp.saturating_mul(3) / 4;
        }
    }

    fn pick_route(&self, origin: SettlementId, destination: SettlementId) -> Option<&TradeRoute> {
        self.routes
            .values()
            .filter(|route| route.origin == origin && route.destination == destination)
            .min_by_key(|route| route.route_id)
    }
}

pub fn sample_trade_world() -> TradeWorld {
    let mut world = TradeWorld::default();

    world.insert_market(MarketState {
        settlement_id: SettlementId(1),
        stock: SupplyStock::new(220, 85, 70),
        target_stock: SupplyStock::new(190, 70, 60),
        price_index_bp: 9_400,
        shortage_pressure_bp: 0,
        tariff_pressure_bp: 0,
    });
    world.insert_market(MarketState {
        settlement_id: SettlementId(3),
        stock: SupplyStock::new(90, 30, 24),
        target_stock: SupplyStock::new(150, 55, 40),
        price_index_bp: 11_500,
        shortage_pressure_bp: 0,
        tariff_pressure_bp: 0,
    });
    world.insert_market(MarketState {
        settlement_id: SettlementId(5),
        stock: SupplyStock::new(140, 65, 52),
        target_stock: SupplyStock::new(160, 70, 55),
        price_index_bp: 10_400,
        shortage_pressure_bp: 0,
        tariff_pressure_bp: 0,
    });

    world
        .insert_route(TradeRoute {
            route_id: 1,
            origin: SettlementId(1),
            destination: SettlementId(3),
            throughput_per_tick: SupplyStock::new(26, 8, 6),
            tariff_bp: 800,
            safety_bp: 8_600,
        })
        .expect("sample route 1 must be valid");
    world
        .insert_route(TradeRoute {
            route_id: 2,
            origin: SettlementId(3),
            destination: SettlementId(5),
            throughput_per_tick: SupplyStock::new(20, 6, 5),
            tariff_bp: 600,
            safety_bp: 9_000,
        })
        .expect("sample route 2 must be valid");
    world
        .insert_route(TradeRoute {
            route_id: 3,
            origin: SettlementId(5),
            destination: SettlementId(1),
            throughput_per_tick: SupplyStock::new(24, 10, 8),
            tariff_bp: 500,
            safety_bp: 9_200,
        })
        .expect("sample route 3 must be valid");

    world
}

#[cfg(test)]
mod tests {
    use crate::Tick;

    use super::{SupplyStock, TradeShipmentOrder, sample_trade_world};

    #[test]
    fn shipment_respects_throughput_and_safety() {
        let mut world = sample_trade_world();
        world.queue_shipment(TradeShipmentOrder {
            origin: crate::SettlementId(1),
            destination: crate::SettlementId(3),
            goods: SupplyStock::new(120, 40, 30),
        });

        let result = world.advance_tick(Tick(1));
        let shipment = result
            .events
            .iter()
            .find_map(|event| match event {
                super::TradeTickEvent::ShipmentExecuted { delivered, lost, .. } => Some((*delivered, *lost)),
                _ => None,
            })
            .expect("shipment event should be emitted");

        assert!(shipment.0.food <= 26);
        assert!(shipment.0.horses <= 8);
        assert!(shipment.0.materiel <= 6);
        assert!(shipment.1.total_units() > 0);
    }

    #[test]
    fn shortage_and_tariff_pressure_raise_prices() {
        let mut world = sample_trade_world();
        let baseline_price = world
            .market(crate::SettlementId(3))
            .expect("market should exist")
            .price_index_bp;

        world.queue_shipment(TradeShipmentOrder {
            origin: crate::SettlementId(1),
            destination: crate::SettlementId(3),
            goods: SupplyStock::new(20, 6, 5),
        });
        world.advance_tick(Tick(1));
        world.advance_tick(Tick(2));
        world.advance_tick(Tick(3));

        let market = world.market(crate::SettlementId(3)).expect("market should exist");
        assert!(market.price_index_bp >= baseline_price);
        assert!(market.shortage_pressure_bp > 0 || market.tariff_pressure_bp > 0);
    }

    #[test]
    fn surplus_reduces_price_pressure() {
        let mut world = sample_trade_world();
        world.queue_shipment(TradeShipmentOrder {
            origin: crate::SettlementId(1),
            destination: crate::SettlementId(5),
            goods: SupplyStock::new(80, 25, 20),
        });
        world
            .insert_route(super::TradeRoute {
                route_id: 99,
                origin: crate::SettlementId(1),
                destination: crate::SettlementId(5),
                throughput_per_tick: SupplyStock::new(80, 25, 20),
                tariff_bp: 100,
                safety_bp: 10_000,
            })
            .expect("route should insert");

        let before = world
            .market(crate::SettlementId(5))
            .expect("market should exist")
            .price_index_bp;

        world.advance_tick(Tick(1));
        world.advance_tick(Tick(2));
        world.advance_tick(Tick(3));

        let after = world
            .market(crate::SettlementId(5))
            .expect("market should exist")
            .price_index_bp;
        assert!(after <= before.saturating_add(1_000));
    }
}
