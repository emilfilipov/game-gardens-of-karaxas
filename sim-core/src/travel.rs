use std::cmp::Ordering;
use std::collections::{BTreeMap, BTreeSet, BinaryHeap};

use serde::{Deserialize, Serialize};

use crate::{SettlementId, Tick};

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct RouteId(pub u64);

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SettlementNode {
    pub id: SettlementId,
    pub name: String,
    pub map_x: i32,
    pub map_y: i32,
    #[serde(default)]
    pub tier: SettlementTier,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize, Default)]
#[serde(rename_all = "snake_case")]
pub enum SettlementTier {
    Camp,
    Village,
    #[default]
    Town,
    City,
    Fortress,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct SettlementHooks {
    pub logistics_throughput_bp: u32,
    pub trade_liquidity_bp: u32,
    pub intelligence_surface_bp: u32,
    pub levy_capacity_bp: u32,
}

impl SettlementTier {
    pub fn hooks(self) -> SettlementHooks {
        match self {
            Self::Camp => SettlementHooks {
                logistics_throughput_bp: 550,
                trade_liquidity_bp: 250,
                intelligence_surface_bp: 450,
                levy_capacity_bp: 350,
            },
            Self::Village => SettlementHooks {
                logistics_throughput_bp: 800,
                trade_liquidity_bp: 550,
                intelligence_surface_bp: 700,
                levy_capacity_bp: 650,
            },
            Self::Town => SettlementHooks {
                logistics_throughput_bp: 1_100,
                trade_liquidity_bp: 950,
                intelligence_surface_bp: 950,
                levy_capacity_bp: 1_000,
            },
            Self::City => SettlementHooks {
                logistics_throughput_bp: 1_500,
                trade_liquidity_bp: 1_600,
                intelligence_surface_bp: 1_250,
                levy_capacity_bp: 1_450,
            },
            Self::Fortress => SettlementHooks {
                logistics_throughput_bp: 950,
                trade_liquidity_bp: 500,
                intelligence_surface_bp: 1_100,
                levy_capacity_bp: 1_800,
            },
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RouteEdge {
    pub id: RouteId,
    pub origin: SettlementId,
    pub destination: SettlementId,
    pub travel_hours: u32,
    pub base_risk: u32,
    pub is_sea_route: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum TravelPreference {
    Fastest,
    Safest,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct RiskModifiers {
    pub weather_bp: i32,
    pub conflict_bp: i32,
    pub espionage_bp: i32,
}

impl RiskModifiers {
    pub fn neutral() -> Self {
        Self {
            weather_bp: 0,
            conflict_bp: 0,
            espionage_bp: 0,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TravelPlan {
    pub settlements: Vec<SettlementId>,
    pub route_ids: Vec<RouteId>,
    pub total_travel_hours: u32,
    pub total_risk: u32,
}

impl TravelPlan {
    pub fn risk_band(&self) -> RouteRiskBand {
        classify_route_risk(self.total_risk)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RouteRiskBand {
    Low,
    Guarded,
    High,
    Severe,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TravelEstimate {
    pub departure_tick: Tick,
    pub arrival_tick: Tick,
    pub total_travel_hours: u32,
    pub total_risk: u32,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct TravelGraph {
    settlements: BTreeMap<SettlementId, SettlementNode>,
    routes: BTreeMap<RouteId, RouteEdge>,
    routes_by_origin: BTreeMap<SettlementId, Vec<RouteId>>,
}

impl TravelGraph {
    pub fn insert_settlement(&mut self, node: SettlementNode) {
        self.routes_by_origin.entry(node.id).or_default();
        self.settlements.insert(node.id, node);
    }

    pub fn insert_route(&mut self, mut route: RouteEdge) -> Result<(), &'static str> {
        if route.travel_hours == 0 {
            return Err("travel_hours must be greater than zero");
        }
        if route.origin == route.destination {
            return Err("route origin and destination must be different");
        }
        if !self.settlements.contains_key(&route.origin) || !self.settlements.contains_key(&route.destination) {
            return Err("route settlement missing from graph");
        }

        // Keep deterministic minimum weight if duplicate route id is reinserted.
        if let Some(existing) = self.routes.get(&route.id)
            && edge_weight(route.travel_hours, route.base_risk, TravelPreference::Fastest)
                > edge_weight(existing.travel_hours, existing.base_risk, TravelPreference::Fastest)
        {
            route.travel_hours = existing.travel_hours;
            route.base_risk = existing.base_risk;
        }

        self.routes.insert(route.id, route.clone());
        let list = self.routes_by_origin.entry(route.origin).or_default();
        if !list.contains(&route.id) {
            list.push(route.id);
            list.sort();
        }
        Ok(())
    }

    pub fn settlements(&self) -> impl Iterator<Item = &SettlementNode> {
        self.settlements.values()
    }

    pub fn routes(&self) -> impl Iterator<Item = &RouteEdge> {
        self.routes.values()
    }

    pub fn settlement(&self, settlement_id: SettlementId) -> Option<&SettlementNode> {
        self.settlements.get(&settlement_id)
    }

    pub fn settlement_hooks(&self, settlement_id: SettlementId) -> Option<SettlementHooks> {
        self.settlements.get(&settlement_id).map(|row| row.tier.hooks())
    }

    pub fn route(&self, route_id: RouteId) -> Option<&RouteEdge> {
        self.routes.get(&route_id)
    }

    pub fn adjacent_settlements(&self, origin: SettlementId) -> Vec<SettlementId> {
        let mut result = BTreeSet::new();
        if let Some(route_ids) = self.routes_by_origin.get(&origin) {
            for route_id in route_ids {
                if let Some(route) = self.routes.get(route_id) {
                    result.insert(route.destination);
                }
            }
        }
        result.into_iter().collect()
    }

    pub fn plan_route(
        &self,
        origin: SettlementId,
        destination: SettlementId,
        preference: TravelPreference,
        modifiers: RiskModifiers,
    ) -> Option<TravelPlan> {
        if origin == destination {
            return Some(TravelPlan {
                settlements: vec![origin],
                route_ids: Vec::new(),
                total_travel_hours: 0,
                total_risk: 0,
            });
        }
        if !self.settlements.contains_key(&origin) || !self.settlements.contains_key(&destination) {
            return None;
        }

        let mut frontier = BinaryHeap::new();
        let mut best: BTreeMap<SettlementId, PathScore> = BTreeMap::new();
        let mut prev: BTreeMap<SettlementId, (SettlementId, RouteId)> = BTreeMap::new();

        let initial = PathScore::zero();
        best.insert(origin, initial);
        frontier.push(QueueState {
            settlement: origin,
            score: initial,
        });

        while let Some(state) = frontier.pop() {
            let Some(known) = best.get(&state.settlement).copied() else {
                continue;
            };
            if state.score != known {
                continue;
            }
            if state.settlement == destination {
                break;
            }

            let Some(route_ids) = self.routes_by_origin.get(&state.settlement) else {
                continue;
            };

            for route_id in route_ids {
                let Some(route) = self.routes.get(route_id) else {
                    continue;
                };
                let segment_risk = adjusted_route_risk(route.base_risk, modifiers);
                let candidate = known.extend(route.travel_hours, segment_risk, preference);
                let current = best.get(&route.destination).copied();

                if current.map(|row| candidate < row).unwrap_or(true) {
                    best.insert(route.destination, candidate);
                    prev.insert(route.destination, (state.settlement, route.id));
                    frontier.push(QueueState {
                        settlement: route.destination,
                        score: candidate,
                    });
                }
            }
        }

        let final_score = best.get(&destination).copied()?;

        let mut settlements = vec![destination];
        let mut route_ids = Vec::new();
        let mut cursor = destination;
        while cursor != origin {
            let (parent, route_id) = *prev.get(&cursor)?;
            settlements.push(parent);
            route_ids.push(route_id);
            cursor = parent;
        }
        settlements.reverse();
        route_ids.reverse();

        Some(TravelPlan {
            settlements,
            route_ids,
            total_travel_hours: final_score.hours,
            total_risk: final_score.risk,
        })
    }

    pub fn estimate_arrival(&self, departure_tick: Tick, plan: &TravelPlan, ticks_per_hour: u32) -> TravelEstimate {
        let tph = ticks_per_hour.max(1);
        let travel_ticks = u64::from(plan.total_travel_hours) * u64::from(tph);
        TravelEstimate {
            departure_tick,
            arrival_tick: Tick(departure_tick.0.saturating_add(travel_ticks)),
            total_travel_hours: plan.total_travel_hours,
            total_risk: plan.total_risk,
        }
    }

    pub fn choke_points(&self) -> Vec<SettlementId> {
        let undirected = self.undirected_neighbors();

        let mut index = 0_u32;
        let mut indices: BTreeMap<SettlementId, u32> = BTreeMap::new();
        let mut lowlink: BTreeMap<SettlementId, u32> = BTreeMap::new();
        let mut articulation = BTreeSet::new();

        for settlement_id in self.settlements.keys().copied() {
            if indices.contains_key(&settlement_id) {
                continue;
            }

            let mut root_children = 0_u32;
            self.dfs_articulation(
                settlement_id,
                None,
                &undirected,
                &mut index,
                &mut indices,
                &mut lowlink,
                &mut articulation,
                &mut root_children,
            );

            if root_children <= 1 {
                articulation.remove(&settlement_id);
            }
        }

        articulation.into_iter().collect()
    }

    fn undirected_neighbors(&self) -> BTreeMap<SettlementId, BTreeSet<SettlementId>> {
        let mut neighbors: BTreeMap<SettlementId, BTreeSet<SettlementId>> = self
            .settlements
            .keys()
            .copied()
            .map(|id| (id, BTreeSet::new()))
            .collect();

        for route in self.routes.values() {
            neighbors.entry(route.origin).or_default().insert(route.destination);
            neighbors.entry(route.destination).or_default().insert(route.origin);
        }

        neighbors
    }

    #[allow(clippy::too_many_arguments)]
    fn dfs_articulation(
        &self,
        node: SettlementId,
        parent: Option<SettlementId>,
        neighbors: &BTreeMap<SettlementId, BTreeSet<SettlementId>>,
        index: &mut u32,
        indices: &mut BTreeMap<SettlementId, u32>,
        lowlink: &mut BTreeMap<SettlementId, u32>,
        articulation: &mut BTreeSet<SettlementId>,
        root_children: &mut u32,
    ) {
        indices.insert(node, *index);
        lowlink.insert(node, *index);
        *index += 1;

        let node_index = indices[&node];
        let mut children = 0_u32;

        let Some(next_neighbors) = neighbors.get(&node) else {
            return;
        };

        for next in next_neighbors {
            if Some(*next) == parent {
                continue;
            }

            if !indices.contains_key(next) {
                children += 1;
                if parent.is_none() {
                    *root_children += 1;
                }

                self.dfs_articulation(
                    *next,
                    Some(node),
                    neighbors,
                    index,
                    indices,
                    lowlink,
                    articulation,
                    root_children,
                );

                let child_low = lowlink[next];
                let current_low = lowlink[&node].min(child_low);
                lowlink.insert(node, current_low);

                if parent.is_some() && child_low >= node_index {
                    articulation.insert(node);
                }
            } else {
                let back_index = indices[next];
                let current_low = lowlink[&node].min(back_index);
                lowlink.insert(node, current_low);
            }
        }

        if parent.is_none() && children > 1 {
            articulation.insert(node);
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct PathScore {
    hours: u32,
    risk: u32,
    primary: u32,
    secondary: u32,
}

impl PathScore {
    fn zero() -> Self {
        Self {
            hours: 0,
            risk: 0,
            primary: 0,
            secondary: 0,
        }
    }

    fn extend(self, travel_hours: u32, segment_risk: u32, preference: TravelPreference) -> Self {
        let hours = self.hours.saturating_add(travel_hours);
        let risk = self.risk.saturating_add(segment_risk);
        let (primary, secondary) = edge_weight(hours, risk, preference);

        Self {
            hours,
            risk,
            primary,
            secondary,
        }
    }
}

impl Ord for PathScore {
    fn cmp(&self, other: &Self) -> Ordering {
        (self.primary, self.secondary, self.hours, self.risk).cmp(&(
            other.primary,
            other.secondary,
            other.hours,
            other.risk,
        ))
    }
}

impl PartialOrd for PathScore {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct QueueState {
    settlement: SettlementId,
    score: PathScore,
}

impl Ord for QueueState {
    fn cmp(&self, other: &Self) -> Ordering {
        // Reverse ordering so BinaryHeap pops the lowest score first.
        other
            .score
            .cmp(&self.score)
            .then_with(|| other.settlement.0.cmp(&self.settlement.0))
    }
}

impl PartialOrd for QueueState {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

fn edge_weight(hours: u32, risk: u32, preference: TravelPreference) -> (u32, u32) {
    match preference {
        TravelPreference::Fastest => (hours, risk),
        TravelPreference::Safest => (risk, hours),
    }
}

pub fn adjusted_route_risk(base_risk: u32, modifiers: RiskModifiers) -> u32 {
    let total_bp = 10_000_i64
        + i64::from(modifiers.weather_bp)
        + i64::from(modifiers.conflict_bp)
        + i64::from(modifiers.espionage_bp);
    let clamped_bp = total_bp.clamp(0, 50_000);
    let weighted = i64::from(base_risk).saturating_mul(clamped_bp);
    u32::try_from(weighted / 10_000).unwrap_or(u32::MAX)
}

pub fn classify_route_risk(total_risk: u32) -> RouteRiskBand {
    match total_risk {
        0..=14 => RouteRiskBand::Low,
        15..=29 => RouteRiskBand::Guarded,
        30..=54 => RouteRiskBand::High,
        _ => RouteRiskBand::Severe,
    }
}

pub fn sample_levant_travel_graph() -> TravelGraph {
    let mut graph = TravelGraph::default();

    graph.insert_settlement(SettlementNode {
        id: SettlementId(1),
        name: "Acre".to_string(),
        map_x: -280,
        map_y: 60,
        tier: SettlementTier::City,
    });
    graph.insert_settlement(SettlementNode {
        id: SettlementId(2),
        name: "Tyre".to_string(),
        map_x: -140,
        map_y: 40,
        tier: SettlementTier::Town,
    });
    graph.insert_settlement(SettlementNode {
        id: SettlementId(3),
        name: "Sidon".to_string(),
        map_x: -20,
        map_y: 20,
        tier: SettlementTier::Town,
    });
    graph.insert_settlement(SettlementNode {
        id: SettlementId(4),
        name: "Jerusalem".to_string(),
        map_x: 80,
        map_y: -90,
        tier: SettlementTier::City,
    });
    graph.insert_settlement(SettlementNode {
        id: SettlementId(5),
        name: "Kerak".to_string(),
        map_x: 280,
        map_y: -140,
        tier: SettlementTier::Fortress,
    });

    let routes = [
        RouteEdge {
            id: RouteId(10),
            origin: SettlementId(1),
            destination: SettlementId(2),
            travel_hours: 6,
            base_risk: 8,
            is_sea_route: false,
        },
        RouteEdge {
            id: RouteId(11),
            origin: SettlementId(2),
            destination: SettlementId(1),
            travel_hours: 6,
            base_risk: 8,
            is_sea_route: false,
        },
        RouteEdge {
            id: RouteId(12),
            origin: SettlementId(2),
            destination: SettlementId(3),
            travel_hours: 4,
            base_risk: 10,
            is_sea_route: false,
        },
        RouteEdge {
            id: RouteId(13),
            origin: SettlementId(3),
            destination: SettlementId(2),
            travel_hours: 4,
            base_risk: 10,
            is_sea_route: false,
        },
        RouteEdge {
            id: RouteId(14),
            origin: SettlementId(3),
            destination: SettlementId(4),
            travel_hours: 11,
            base_risk: 16,
            is_sea_route: false,
        },
        RouteEdge {
            id: RouteId(15),
            origin: SettlementId(4),
            destination: SettlementId(3),
            travel_hours: 11,
            base_risk: 16,
            is_sea_route: false,
        },
        RouteEdge {
            id: RouteId(16),
            origin: SettlementId(4),
            destination: SettlementId(5),
            travel_hours: 14,
            base_risk: 22,
            is_sea_route: false,
        },
        RouteEdge {
            id: RouteId(17),
            origin: SettlementId(5),
            destination: SettlementId(4),
            travel_hours: 14,
            base_risk: 22,
            is_sea_route: false,
        },
        RouteEdge {
            id: RouteId(18),
            origin: SettlementId(1),
            destination: SettlementId(4),
            travel_hours: 24,
            base_risk: 11,
            is_sea_route: true,
        },
        RouteEdge {
            id: RouteId(19),
            origin: SettlementId(4),
            destination: SettlementId(1),
            travel_hours: 24,
            base_risk: 11,
            is_sea_route: true,
        },
    ];

    for route in routes {
        graph
            .insert_route(route)
            .expect("sample graph routes should always validate");
    }

    graph
}

#[cfg(test)]
mod tests {
    use super::{
        RiskModifiers, RouteRiskBand, SettlementNode, SettlementTier, TravelGraph, TravelPreference,
        adjusted_route_risk, classify_route_risk, sample_levant_travel_graph,
    };
    use crate::{RouteEdge, RouteId, SettlementId, Tick};

    fn tiny_graph() -> TravelGraph {
        let mut graph = TravelGraph::default();
        graph.insert_settlement(SettlementNode {
            id: SettlementId(1),
            name: "A".to_string(),
            map_x: 0,
            map_y: 0,
            tier: SettlementTier::Village,
        });
        graph.insert_settlement(SettlementNode {
            id: SettlementId(2),
            name: "B".to_string(),
            map_x: 1,
            map_y: 0,
            tier: SettlementTier::Town,
        });
        graph.insert_settlement(SettlementNode {
            id: SettlementId(3),
            name: "C".to_string(),
            map_x: 2,
            map_y: 0,
            tier: SettlementTier::Town,
        });
        graph.insert_settlement(SettlementNode {
            id: SettlementId(4),
            name: "D".to_string(),
            map_x: 3,
            map_y: 0,
            tier: SettlementTier::Camp,
        });

        for route in [
            RouteEdge {
                id: RouteId(1),
                origin: SettlementId(1),
                destination: SettlementId(2),
                travel_hours: 4,
                base_risk: 20,
                is_sea_route: false,
            },
            RouteEdge {
                id: RouteId(2),
                origin: SettlementId(2),
                destination: SettlementId(4),
                travel_hours: 4,
                base_risk: 20,
                is_sea_route: false,
            },
            RouteEdge {
                id: RouteId(3),
                origin: SettlementId(1),
                destination: SettlementId(3),
                travel_hours: 3,
                base_risk: 40,
                is_sea_route: false,
            },
            RouteEdge {
                id: RouteId(4),
                origin: SettlementId(3),
                destination: SettlementId(4),
                travel_hours: 3,
                base_risk: 40,
                is_sea_route: false,
            },
        ] {
            graph.insert_route(route).expect("route should insert");
        }

        graph
    }

    #[test]
    fn fastest_and_safest_routes_choose_different_paths() {
        let graph = tiny_graph();

        let fastest = graph
            .plan_route(
                SettlementId(1),
                SettlementId(4),
                TravelPreference::Fastest,
                RiskModifiers::neutral(),
            )
            .expect("fastest path should exist");
        assert_eq!(fastest.total_travel_hours, 6);
        assert_eq!(fastest.total_risk, 80);
        assert_eq!(
            fastest.settlements,
            vec![SettlementId(1), SettlementId(3), SettlementId(4)]
        );

        let safest = graph
            .plan_route(
                SettlementId(1),
                SettlementId(4),
                TravelPreference::Safest,
                RiskModifiers::neutral(),
            )
            .expect("safest path should exist");
        assert_eq!(safest.total_travel_hours, 8);
        assert_eq!(safest.total_risk, 40);
        assert_eq!(
            safest.settlements,
            vec![SettlementId(1), SettlementId(2), SettlementId(4)]
        );
    }

    #[test]
    fn risk_modifiers_adjust_route_risk() {
        let risk = adjusted_route_risk(
            20,
            RiskModifiers {
                weather_bp: 2_000,
                conflict_bp: -500,
                espionage_bp: 500,
            },
        );
        assert_eq!(risk, 24);
    }

    #[test]
    fn choke_points_detect_bridge_settlement() {
        let graph = sample_levant_travel_graph();
        let choke_points = graph.choke_points();
        assert_eq!(choke_points, vec![SettlementId(4)]);
    }

    #[test]
    fn arrival_tick_estimate_is_deterministic() {
        let graph = tiny_graph();
        let plan = graph
            .plan_route(
                SettlementId(1),
                SettlementId(4),
                TravelPreference::Safest,
                RiskModifiers::neutral(),
            )
            .expect("path should exist");

        let estimate = graph.estimate_arrival(Tick(120), &plan, 4);
        assert_eq!(estimate.departure_tick, Tick(120));
        assert_eq!(estimate.arrival_tick, Tick(152));
    }

    #[test]
    fn adjacency_is_sorted_and_unique() {
        let graph = sample_levant_travel_graph();
        let adjacent = graph.adjacent_settlements(SettlementId(1));
        assert_eq!(adjacent, vec![SettlementId(2), SettlementId(4)]);
    }

    #[test]
    fn settlement_tier_hooks_are_available() {
        let graph = sample_levant_travel_graph();
        let hooks = graph
            .settlement_hooks(SettlementId(5))
            .expect("kerak hooks should exist");
        assert_eq!(hooks.levy_capacity_bp, 1_800);
        assert!(hooks.trade_liquidity_bp < hooks.levy_capacity_bp);
    }

    #[test]
    fn route_risk_band_classification_is_stable() {
        assert_eq!(classify_route_risk(0), RouteRiskBand::Low);
        assert_eq!(classify_route_risk(14), RouteRiskBand::Low);
        assert_eq!(classify_route_risk(15), RouteRiskBand::Guarded);
        assert_eq!(classify_route_risk(29), RouteRiskBand::Guarded);
        assert_eq!(classify_route_risk(30), RouteRiskBand::High);
        assert_eq!(classify_route_risk(54), RouteRiskBand::High);
        assert_eq!(classify_route_risk(55), RouteRiskBand::Severe);

        let graph = tiny_graph();
        let route = graph
            .plan_route(
                SettlementId(1),
                SettlementId(4),
                TravelPreference::Safest,
                RiskModifiers::neutral(),
            )
            .expect("path should exist");
        assert_eq!(route.risk_band(), RouteRiskBand::High);
    }
}
