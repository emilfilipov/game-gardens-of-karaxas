#[cfg(not(feature = "sandbox-ui"))]
fn main() {
    println!("client-app sandbox UI is disabled. Run with: cargo run -p client-app --features sandbox-ui");
}

#[cfg(feature = "sandbox-ui")]
mod sandbox {
    use bevy::asset::AssetPlugin;
    use bevy::prelude::*;
    use bevy_egui::{EguiContexts, EguiPlugin, egui};
    use sim_core::{
        RiskModifiers, SettlementId, TravelGraph, TravelPlan, TravelPreference, sample_levant_travel_graph,
    };

    const MAP_SCALE: f32 = 2.2;
    const CAMPAIGN_MINUTES_PER_REAL_SECOND: f64 = 5.0;

    #[derive(Component)]
    struct PlayerMarker;

    #[derive(Resource)]
    struct ClockState {
        uptime_seconds: f64,
        campaign_minutes: f64,
        sim_tick: u64,
        tick_timer: Timer,
    }

    impl Default for ClockState {
        fn default() -> Self {
            Self {
                uptime_seconds: 0.0,
                campaign_minutes: 8.0 * 60.0,
                sim_tick: 0,
                tick_timer: Timer::from_seconds(1.0, TimerMode::Repeating),
            }
        }
    }

    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    enum RiskPreset {
        Neutral,
        BorderUnrest,
        SecuredRoads,
    }

    impl RiskPreset {
        fn next(self) -> Self {
            match self {
                Self::Neutral => Self::BorderUnrest,
                Self::BorderUnrest => Self::SecuredRoads,
                Self::SecuredRoads => Self::Neutral,
            }
        }

        fn label(self) -> &'static str {
            match self {
                Self::Neutral => "Neutral",
                Self::BorderUnrest => "Border Unrest",
                Self::SecuredRoads => "Secured Roads",
            }
        }

        fn modifiers(self) -> RiskModifiers {
            match self {
                Self::Neutral => RiskModifiers::neutral(),
                Self::BorderUnrest => RiskModifiers {
                    weather_bp: 0,
                    conflict_bp: 2_500,
                    espionage_bp: 500,
                },
                Self::SecuredRoads => RiskModifiers {
                    weather_bp: 0,
                    conflict_bp: -1_000,
                    espionage_bp: -1_500,
                },
            }
        }
    }

    #[derive(Resource)]
    struct TravelSandbox {
        graph: TravelGraph,
        current_settlement: SettlementId,
        destination_cursor: usize,
        destinations: Vec<SettlementId>,
        active_plan: Option<TravelPlan>,
        active_segment_index: usize,
        active_segment_elapsed_hours: f32,
        preference: TravelPreference,
        risk_preset: RiskPreset,
        last_plan_summary: String,
    }

    impl TravelSandbox {
        fn new(graph: TravelGraph) -> Self {
            let destinations = graph.settlements().map(|row| row.id).collect::<Vec<_>>();

            Self {
                graph,
                current_settlement: SettlementId(1),
                destination_cursor: 0,
                destinations,
                active_plan: None,
                active_segment_index: 0,
                active_segment_elapsed_hours: 0.0,
                preference: TravelPreference::Fastest,
                risk_preset: RiskPreset::Neutral,
                last_plan_summary: "Press Enter to plan route".to_string(),
            }
        }

        fn selected_destination(&self) -> SettlementId {
            self.destinations
                .get(self.destination_cursor)
                .copied()
                .unwrap_or(self.current_settlement)
        }

        fn selected_destination_name(&self) -> String {
            let id = self.selected_destination();
            self.graph
                .settlement(id)
                .map(|row| row.name.clone())
                .unwrap_or_else(|| format!("Settlement {}", id.0))
        }

        fn plan_selected_route(&mut self) {
            let destination = self.selected_destination();
            let modifiers = self.risk_preset.modifiers();
            let Some(plan) = self
                .graph
                .plan_route(self.current_settlement, destination, self.preference, modifiers)
            else {
                self.active_plan = None;
                self.active_segment_index = 0;
                self.active_segment_elapsed_hours = 0.0;
                self.last_plan_summary = format!("No route from {} to {}", self.current_settlement.0, destination.0);
                return;
            };

            if plan.settlements.len() <= 1 {
                self.active_plan = None;
                self.active_segment_index = 0;
                self.active_segment_elapsed_hours = 0.0;
                self.last_plan_summary = "Already at destination".to_string();
                return;
            }

            self.last_plan_summary = format!(
                "Planned {} -> {} | {}h | risk {}",
                self.current_settlement.0, destination.0, plan.total_travel_hours, plan.total_risk
            );
            self.active_plan = Some(plan);
            self.active_segment_index = 0;
            self.active_segment_elapsed_hours = 0.0;
        }
    }

    pub fn run() {
        App::new()
            .insert_resource(ClearColor(Color::srgb(0.055, 0.07, 0.09)))
            .insert_resource(ClockState::default())
            .insert_resource(TravelSandbox::new(sample_levant_travel_graph()))
            .add_plugins(DefaultPlugins.set(AssetPlugin {
                file_path: "client-app/assets".to_string(),
                ..default()
            }))
            .add_plugins(EguiPlugin::default())
            .add_systems(Startup, setup_scene)
            .add_systems(
                Update,
                (
                    update_clocks,
                    handle_input,
                    animate_player,
                    draw_map_gizmos,
                    sync_player_when_idle,
                    ui_panel,
                ),
            )
            .run();
    }

    fn setup_scene(mut commands: Commands, asset_server: Res<AssetServer>, sandbox: Res<TravelSandbox>) {
        commands.spawn(Camera2d);

        let player_position = settlement_position(&sandbox.graph, sandbox.current_settlement);
        let texture = asset_server.load("player_circle.png");
        commands.spawn((
            Sprite::from_image(texture),
            Transform::from_xyz(player_position.x, player_position.y, 10.0).with_scale(Vec3::splat(0.35)),
            PlayerMarker,
        ));
    }

    fn update_clocks(time: Res<Time>, mut clocks: ResMut<ClockState>) {
        let delta = time.delta_secs_f64();
        clocks.uptime_seconds += delta;
        clocks.campaign_minutes += delta * CAMPAIGN_MINUTES_PER_REAL_SECOND;

        let finished = clocks.tick_timer.tick(time.delta()).times_finished_this_tick();
        if finished > 0 {
            clocks.sim_tick = clocks.sim_tick.saturating_add(u64::from(finished));
        }
    }

    fn handle_input(keys: Res<ButtonInput<KeyCode>>, mut sandbox: ResMut<TravelSandbox>) {
        if keys.just_pressed(KeyCode::Tab) {
            if !sandbox.destinations.is_empty() {
                sandbox.destination_cursor = (sandbox.destination_cursor + 1) % sandbox.destinations.len();
            }
        }

        if keys.just_pressed(KeyCode::KeyR) {
            sandbox.preference = match sandbox.preference {
                TravelPreference::Fastest => TravelPreference::Safest,
                TravelPreference::Safest => TravelPreference::Fastest,
            };
        }

        if keys.just_pressed(KeyCode::KeyM) {
            sandbox.risk_preset = sandbox.risk_preset.next();
        }

        if keys.just_pressed(KeyCode::Enter) {
            sandbox.plan_selected_route();
        }
    }

    fn animate_player(
        time: Res<Time>,
        mut sandbox: ResMut<TravelSandbox>,
        mut player_query: Single<&mut Transform, With<PlayerMarker>>,
    ) {
        let (from_id, to_id, plan_len, segment_hours) = {
            let Some(plan) = sandbox.active_plan.as_ref() else {
                return;
            };

            if sandbox.active_segment_index + 1 >= plan.settlements.len() {
                sandbox.active_plan = None;
                return;
            }

            let segment_hours = plan
                .route_ids
                .get(sandbox.active_segment_index)
                .and_then(|route_id| sandbox.graph.route(*route_id))
                .map(|route| route.travel_hours as f32)
                .unwrap_or(1.0)
                .max(1.0);

            (
                plan.settlements[sandbox.active_segment_index],
                plan.settlements[sandbox.active_segment_index + 1],
                plan.settlements.len(),
                segment_hours,
            )
        };

        let from = settlement_position(&sandbox.graph, from_id);
        let to = settlement_position(&sandbox.graph, to_id);
        let campaign_hours_per_real_second = (CAMPAIGN_MINUTES_PER_REAL_SECOND as f32) / 60.0;
        sandbox.active_segment_elapsed_hours += time.delta_secs() * campaign_hours_per_real_second;
        let t = (sandbox.active_segment_elapsed_hours / segment_hours).clamp(0.0, 1.0);
        let position = from.lerp(to, t);
        player_query.translation.x = position.x;
        player_query.translation.y = position.y;

        if sandbox.active_segment_elapsed_hours >= segment_hours {
            sandbox.current_settlement = to_id;
            sandbox.active_segment_index += 1;
            sandbox.active_segment_elapsed_hours = 0.0;

            if sandbox.active_segment_index + 1 >= plan_len {
                sandbox.active_plan = None;
                sandbox.last_plan_summary = format!("Arrived at settlement {}", sandbox.current_settlement.0);
            }
        }
    }

    fn sync_player_when_idle(
        sandbox: Res<TravelSandbox>,
        mut player_query: Single<&mut Transform, With<PlayerMarker>>,
    ) {
        if sandbox.active_plan.is_some() {
            return;
        }

        let position = settlement_position(&sandbox.graph, sandbox.current_settlement);
        player_query.translation.x = position.x;
        player_query.translation.y = position.y;
    }

    fn draw_map_gizmos(mut gizmos: Gizmos, sandbox: Res<TravelSandbox>) {
        for route in sandbox.graph.routes() {
            let from = settlement_position(&sandbox.graph, route.origin);
            let to = settlement_position(&sandbox.graph, route.destination);

            let risk_normalized = (route.base_risk as f32 / 40.0).clamp(0.0, 1.0);
            let color = Color::srgb(0.25 + risk_normalized * 0.6, 0.72 - risk_normalized * 0.45, 0.36);
            gizmos.line_2d(from, to, color);
        }

        let selected_destination = sandbox.selected_destination();
        for settlement in sandbox.graph.settlements() {
            let mut color = Color::srgb(0.72, 0.72, 0.72);
            if settlement.id == sandbox.current_settlement {
                color = Color::srgb(0.2, 0.95, 0.25);
            } else if settlement.id == selected_destination {
                color = Color::srgb(0.95, 0.75, 0.15);
            }

            gizmos.circle_2d(
                Vec2::new(settlement.map_x as f32 * MAP_SCALE, settlement.map_y as f32 * MAP_SCALE),
                7.0,
                color,
            );
        }
    }

    fn ui_panel(mut egui_contexts: EguiContexts, clocks: Res<ClockState>, sandbox: Res<TravelSandbox>) {
        let Ok(ctx) = egui_contexts.ctx_mut() else {
            return;
        };

        let day = (clocks.campaign_minutes / (24.0 * 60.0)).floor() as u64 + 1;
        let minutes_of_day = (clocks.campaign_minutes % (24.0 * 60.0)) as u64;
        let hour = minutes_of_day / 60;
        let minute = minutes_of_day % 60;

        let preference = match sandbox.preference {
            TravelPreference::Fastest => "Fastest",
            TravelPreference::Safest => "Safest",
        };

        let (active_hours, active_risk) = sandbox
            .active_plan
            .as_ref()
            .map(|row| (row.total_travel_hours, row.total_risk))
            .unwrap_or((0, 0));

        egui::Window::new("Ambitions of Peace - Sandbox")
            .anchor(egui::Align2::LEFT_TOP, [12.0, 12.0])
            .resizable(false)
            .show(ctx, |ui| {
                ui.label(format!("Real Uptime: {:.1}s", clocks.uptime_seconds));
                ui.label(format!("Campaign Clock: Day {} {:02}:{:02}", day, hour, minute));
                ui.label(format!("Simulation Tick: {}", clocks.sim_tick));
                ui.separator();
                ui.label(format!(
                    "Current Settlement: {}",
                    sandbox
                        .graph
                        .settlement(sandbox.current_settlement)
                        .map(|row| row.name.as_str())
                        .unwrap_or("Unknown")
                ));
                ui.label(format!("Selected Destination: {}", sandbox.selected_destination_name()));
                ui.label(format!("Path Preference: {} (press R)", preference));
                ui.label(format!("Risk Profile: {} (press M)", sandbox.risk_preset.label()));
                ui.label("Press Tab to cycle destination, Enter to dispatch route.");
                if sandbox.active_plan.is_some() {
                    ui.label(format!("Active Route: {}h, risk {}", active_hours, active_risk));
                } else {
                    ui.label("Active Route: none");
                }
                ui.separator();
                ui.label(format!("Status: {}", sandbox.last_plan_summary));
            });
    }

    fn settlement_position(graph: &TravelGraph, settlement_id: SettlementId) -> Vec2 {
        let Some(node) = graph.settlement(settlement_id) else {
            return Vec2::ZERO;
        };

        Vec2::new(node.map_x as f32 * MAP_SCALE, node.map_y as f32 * MAP_SCALE)
    }
}

#[cfg(feature = "sandbox-ui")]
fn main() {
    sandbox::run();
}
