use bevy::prelude::*;
use bevy_egui::{EguiContexts, EguiPlugin, egui};
use reqwest::blocking::Client;
use reqwest::header::{AUTHORIZATION, CONTENT_TYPE};
use serde::Deserialize;
use serde::de::DeserializeOwned;
use sim_core::{SettlementId, TravelGraph, sample_levant_travel_graph};
use std::env;
use std::sync::Mutex;
use std::sync::mpsc::{self, Receiver, Sender, TryRecvError};
use std::thread;
use std::time::Duration;

const DEFAULT_API_BASE_URL: &str = "http://127.0.0.1:8000";
const DEFAULT_CLIENT_VERSION: &str = "dev-0.1.0";
const DEFAULT_CONTENT_VERSION_KEY: &str = "runtime_gameplay_v1";
const MAP_SCALE: f32 = 2.3;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
enum ShellPhase {
    #[default]
    Login,
    Authenticating,
    CharacterSelect,
    Bootstrapping,
    CampaignReady,
}

impl ShellPhase {
    fn label(self) -> &'static str {
        match self {
            Self::Login => "Login",
            Self::Authenticating => "Authenticating",
            Self::CharacterSelect => "Character Select",
            Self::Bootstrapping => "World Bootstrap",
            Self::CampaignReady => "Campaign Entry",
        }
    }
}

#[derive(Clone, Debug)]
struct SessionContext {
    access_token: String,
    refresh_token: String,
    session_id: String,
    user_id: u64,
    display_name: String,
}

#[derive(Clone, Debug)]
struct CharacterSummary {
    id: u64,
    name: String,
    level: i32,
    is_selected: bool,
}

#[derive(Clone, Debug)]
struct CampaignBootstrapSummary {
    character_id: u64,
    character_name: String,
    level_name: String,
    level_description: String,
    instance_id: String,
    instance_kind: String,
    spawn_world_x: i32,
    spawn_world_y: i32,
    spawn_world_z: f32,
    yaw_deg: f32,
    camera_profile_key: String,
}

#[derive(Resource, Clone)]
struct BackendConfig {
    base_url: String,
    client_version: String,
    client_content_version_key: String,
}

impl BackendConfig {
    fn from_env() -> Self {
        let base_url = env::var("AOP_API_BASE_URL")
            .unwrap_or_else(|_| DEFAULT_API_BASE_URL.to_string())
            .trim()
            .trim_end_matches('/')
            .to_string();
        let client_version = env::var("AOP_CLIENT_VERSION")
            .unwrap_or_else(|_| DEFAULT_CLIENT_VERSION.to_string())
            .trim()
            .to_string();
        let client_content_version_key = env::var("AOP_CLIENT_CONTENT_VERSION_KEY")
            .unwrap_or_else(|_| DEFAULT_CONTENT_VERSION_KEY.to_string())
            .trim()
            .to_string();

        Self {
            base_url,
            client_version,
            client_content_version_key,
        }
    }
}

#[derive(Resource)]
struct BackendBridge {
    request_tx: Sender<BackendRequest>,
    response_rx: Mutex<Receiver<BackendResponse>>,
}

#[derive(Resource, Default)]
struct ShellState {
    phase: ShellPhase,
    status_line: String,
    request_in_flight: bool,
    email: String,
    password: String,
    otp_code: String,
    session: Option<SessionContext>,
    characters: Vec<CharacterSummary>,
    selected_character_id: Option<u64>,
    campaign_bootstrap: Option<CampaignBootstrapSummary>,
}

impl ShellState {
    fn from_env_handoff() -> Self {
        let mut state = Self {
            phase: ShellPhase::Login,
            status_line: "Ready. Enter account credentials to continue.".to_string(),
            email: env::var("AOP_HANDOFF_EMAIL").unwrap_or_default(),
            password: String::new(),
            ..Self::default()
        };

        let access_token = env::var("AOP_HANDOFF_ACCESS_TOKEN").ok().and_then(trimmed_nonempty);
        let session_id = env::var("AOP_HANDOFF_SESSION_ID").ok().and_then(trimmed_nonempty);

        if let (Some(access_token), Some(session_id)) = (access_token, session_id) {
            let refresh_token = env::var("AOP_HANDOFF_REFRESH_TOKEN")
                .ok()
                .and_then(trimmed_nonempty)
                .unwrap_or_default();
            let user_id = env::var("AOP_HANDOFF_USER_ID")
                .ok()
                .and_then(|value| value.parse::<u64>().ok())
                .unwrap_or(0);
            let display_name = env::var("AOP_HANDOFF_DISPLAY_NAME")
                .ok()
                .and_then(trimmed_nonempty)
                .unwrap_or_else(|| "Handoff User".to_string());

            state.session = Some(SessionContext {
                access_token,
                refresh_token,
                session_id,
                user_id,
                display_name,
            });
            state.phase = ShellPhase::CharacterSelect;
            state.status_line = "Launcher handoff session loaded. Fetching characters...".to_string();
        }

        state
    }
}

#[derive(Resource, Default)]
struct CampaignScene {
    marker_entity: Option<Entity>,
    active_character_id: Option<u64>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum FogVisibility {
    Visible,
    Shrouded,
    Obscured,
}

#[derive(Clone, Debug)]
struct SettlementRenderNode {
    id: SettlementId,
    name: String,
    map_x: f32,
    map_y: f32,
    fog: FogVisibility,
}

#[derive(Clone, Debug)]
struct RouteRenderEdge {
    origin: SettlementId,
    destination: SettlementId,
    is_sea_route: bool,
}

#[derive(Clone, Debug)]
struct MovingMapMarker {
    label: String,
    origin: SettlementId,
    destination: SettlementId,
    progress: f32,
    speed: f32,
}

#[derive(Resource)]
struct CampaignMapSurface {
    graph: TravelGraph,
    settlements: Vec<SettlementRenderNode>,
    routes: Vec<RouteRenderEdge>,
    army_markers: Vec<MovingMapMarker>,
    caravan_markers: Vec<MovingMapMarker>,
    zoom: f32,
}

impl CampaignMapSurface {
    fn sample() -> Self {
        let graph = sample_levant_travel_graph();
        let settlements = graph
            .settlements()
            .map(|row| {
                let fog = match row.id.0 {
                    1..=3 => FogVisibility::Visible,
                    4..=5 => FogVisibility::Shrouded,
                    _ => FogVisibility::Obscured,
                };
                SettlementRenderNode {
                    id: row.id,
                    name: row.name.clone(),
                    map_x: row.map_x as f32,
                    map_y: row.map_y as f32,
                    fog,
                }
            })
            .collect::<Vec<_>>();
        let routes = graph
            .routes()
            .map(|row| RouteRenderEdge {
                origin: row.origin,
                destination: row.destination,
                is_sea_route: row.is_sea_route,
            })
            .collect::<Vec<_>>();

        Self {
            graph,
            settlements,
            routes,
            army_markers: vec![
                MovingMapMarker {
                    label: "Army A7".to_string(),
                    origin: SettlementId(1),
                    destination: SettlementId(3),
                    progress: 0.22,
                    speed: 0.08,
                },
                MovingMapMarker {
                    label: "Army A8".to_string(),
                    origin: SettlementId(2),
                    destination: SettlementId(4),
                    progress: 0.61,
                    speed: 0.05,
                },
            ],
            caravan_markers: vec![
                MovingMapMarker {
                    label: "Caravan C12".to_string(),
                    origin: SettlementId(3),
                    destination: SettlementId(5),
                    progress: 0.4,
                    speed: 0.04,
                },
                MovingMapMarker {
                    label: "Caravan C19".to_string(),
                    origin: SettlementId(1),
                    destination: SettlementId(6),
                    progress: 0.75,
                    speed: 0.03,
                },
            ],
            zoom: 1.0,
        }
    }

    fn settlement_position(&self, settlement_id: SettlementId) -> Option<Vec2> {
        self.graph
            .settlement(settlement_id)
            .map(|row| Vec2::new(row.map_x as f32 * MAP_SCALE, row.map_y as f32 * MAP_SCALE))
    }
}

enum BackendRequest {
    Login {
        email: String,
        password: String,
        otp_code: Option<String>,
    },
    FetchCharacters {
        access_token: String,
    },
    FetchBootstrap {
        access_token: String,
        character_id: u64,
    },
}

enum BackendResponse {
    Login(Result<SessionContext, String>),
    Characters(Result<Vec<CharacterSummary>, String>),
    Bootstrap(Result<CampaignBootstrapSummary, String>),
}

#[derive(Deserialize)]
struct LoginResponsePayload {
    access_token: String,
    #[serde(default)]
    refresh_token: String,
    session_id: String,
    user_id: u64,
    #[serde(default)]
    display_name: String,
}

#[derive(Deserialize)]
struct CharacterPayload {
    id: u64,
    name: String,
    #[serde(default)]
    level: i32,
    #[serde(default)]
    is_selected: bool,
}

#[derive(Deserialize)]
struct BootstrapResponsePayload {
    character: BootstrapCharacterPayload,
    level: BootstrapLevelPayload,
    spawn: BootstrapSpawnPayload,
    instance: BootstrapInstancePayload,
    runtime: BootstrapRuntimePayload,
}

#[derive(Deserialize)]
struct BootstrapCharacterPayload {
    id: u64,
    name: String,
}

#[derive(Deserialize)]
struct BootstrapLevelPayload {
    #[serde(default)]
    name: String,
    #[serde(default)]
    descriptive_name: String,
}

#[derive(Deserialize)]
struct BootstrapSpawnPayload {
    #[serde(default)]
    world_x: i32,
    #[serde(default)]
    world_y: i32,
    #[serde(default)]
    world_z: f32,
    #[serde(default)]
    yaw_deg: f32,
}

#[derive(Deserialize)]
struct BootstrapInstancePayload {
    #[serde(default)]
    id: String,
    #[serde(default)]
    kind: String,
}

#[derive(Deserialize)]
struct BootstrapRuntimePayload {
    #[serde(default)]
    camera_profile_key: String,
}

pub fn run() {
    let config = BackendConfig::from_env();
    let bridge = spawn_backend_bridge(config.clone());

    App::new()
        .insert_resource(config)
        .insert_resource(bridge)
        .insert_resource(ShellState::from_env_handoff())
        .insert_resource(CampaignScene::default())
        .insert_resource(CampaignMapSurface::sample())
        .insert_resource(ClearColor(Color::srgb(0.05, 0.07, 0.08)))
        .add_plugins(DefaultPlugins)
        .add_plugins(EguiPlugin::default())
        .add_systems(Startup, (setup_scene, startup_handoff_fetch))
        .add_systems(
            Update,
            (
                poll_backend_responses,
                animate_campaign_markers,
                draw_campaign_map_gizmos,
                sync_campaign_scene,
                draw_shell_ui,
            ),
        )
        .run();
}

fn spawn_backend_bridge(config: BackendConfig) -> BackendBridge {
    let (request_tx, request_rx) = mpsc::channel::<BackendRequest>();
    let (response_tx, response_rx) = mpsc::channel::<BackendResponse>();

    thread::spawn(move || backend_worker_loop(config, request_rx, response_tx));

    BackendBridge {
        request_tx,
        response_rx: Mutex::new(response_rx),
    }
}

fn backend_worker_loop(
    config: BackendConfig,
    request_rx: Receiver<BackendRequest>,
    response_tx: Sender<BackendResponse>,
) {
    let client = match Client::builder().timeout(Duration::from_secs(10)).build() {
        Ok(client) => client,
        Err(error) => {
            let _ = response_tx.send(BackendResponse::Login(Err(format!(
                "Failed building HTTP client: {error}"
            ))));
            return;
        }
    };

    while let Ok(command) = request_rx.recv() {
        match command {
            BackendRequest::Login {
                email,
                password,
                otp_code,
            } => {
                let result = execute_login(&client, &config, &email, &password, otp_code.as_deref());
                let _ = response_tx.send(BackendResponse::Login(result));
            }
            BackendRequest::FetchCharacters { access_token } => {
                let result = execute_fetch_characters(&client, &config, &access_token);
                let _ = response_tx.send(BackendResponse::Characters(result));
            }
            BackendRequest::FetchBootstrap {
                access_token,
                character_id,
            } => {
                let result = execute_fetch_bootstrap(&client, &config, &access_token, character_id);
                let _ = response_tx.send(BackendResponse::Bootstrap(result));
            }
        }
    }
}

fn execute_login(
    client: &Client,
    config: &BackendConfig,
    email: &str,
    password: &str,
    otp_code: Option<&str>,
) -> Result<SessionContext, String> {
    let url = format!("{}/auth/login", config.base_url);
    let mut payload = serde_json::json!({
        "email": email,
        "password": password,
        "client_version": config.client_version,
        "client_content_version_key": config.client_content_version_key,
    });
    if let Some(code) = otp_code.and_then(|value| trimmed_nonempty(value.to_string())) {
        payload["otp_code"] = serde_json::Value::String(code);
    }

    let response = client
        .post(url)
        .header(CONTENT_TYPE, "application/json")
        .header("x-client-version", &config.client_version)
        .header("x-client-content-version", &config.client_content_version_key)
        .body(payload.to_string())
        .send()
        .map_err(|error| format!("Login request failed: {error}"))?;

    let payload: LoginResponsePayload = decode_api_response(response)?;
    Ok(SessionContext {
        access_token: payload.access_token,
        refresh_token: payload.refresh_token,
        session_id: payload.session_id,
        user_id: payload.user_id,
        display_name: payload.display_name,
    })
}

fn execute_fetch_characters(
    client: &Client,
    config: &BackendConfig,
    access_token: &str,
) -> Result<Vec<CharacterSummary>, String> {
    let url = format!("{}/characters", config.base_url);
    let response = client
        .get(url)
        .header(AUTHORIZATION, format!("Bearer {access_token}"))
        .header("x-client-version", &config.client_version)
        .header("x-client-content-version", &config.client_content_version_key)
        .send()
        .map_err(|error| format!("Character list request failed: {error}"))?;

    let payload: Vec<CharacterPayload> = decode_api_response(response)?;
    let mut rows = payload
        .into_iter()
        .map(|row| CharacterSummary {
            id: row.id,
            name: row.name,
            level: row.level,
            is_selected: row.is_selected,
        })
        .collect::<Vec<_>>();
    rows.sort_by(|left, right| left.name.cmp(&right.name));
    Ok(rows)
}

fn execute_fetch_bootstrap(
    client: &Client,
    config: &BackendConfig,
    access_token: &str,
    character_id: u64,
) -> Result<CampaignBootstrapSummary, String> {
    let url = format!("{}/characters/{character_id}/world-bootstrap", config.base_url);
    let response = client
        .post(url)
        .header(AUTHORIZATION, format!("Bearer {access_token}"))
        .header(CONTENT_TYPE, "application/json")
        .header("x-client-version", &config.client_version)
        .header("x-client-content-version", &config.client_content_version_key)
        .body("{\"override_level_id\":null}")
        .send()
        .map_err(|error| format!("World bootstrap request failed: {error}"))?;

    let payload: BootstrapResponsePayload = decode_api_response(response)?;
    Ok(CampaignBootstrapSummary {
        character_id: payload.character.id,
        character_name: payload.character.name,
        level_name: payload.level.name,
        level_description: payload.level.descriptive_name,
        instance_id: payload.instance.id,
        instance_kind: payload.instance.kind,
        spawn_world_x: payload.spawn.world_x,
        spawn_world_y: payload.spawn.world_y,
        spawn_world_z: payload.spawn.world_z,
        yaw_deg: payload.spawn.yaw_deg,
        camera_profile_key: payload.runtime.camera_profile_key,
    })
}

fn decode_api_response<T: DeserializeOwned>(response: reqwest::blocking::Response) -> Result<T, String> {
    let status = response.status();
    let body = response
        .text()
        .map_err(|error| format!("Failed reading backend response: {error}"))?;

    if !status.is_success() {
        let message = extract_error_message(&body);
        return Err(format!("HTTP {}: {message}", status.as_u16()));
    }

    serde_json::from_str::<T>(&body).map_err(|error| format!("Failed decoding backend response: {error}"))
}

fn extract_error_message(body: &str) -> String {
    if let Ok(value) = serde_json::from_str::<serde_json::Value>(body) {
        if let Some(message) = value
            .get("error")
            .and_then(|error| error.get("message"))
            .and_then(|message| message.as_str())
        {
            let trimmed = message.trim();
            if !trimmed.is_empty() {
                return trimmed.to_string();
            }
        }

        if let Some(detail_message) = value
            .get("detail")
            .and_then(|detail| detail.get("message"))
            .and_then(|message| message.as_str())
        {
            let trimmed = detail_message.trim();
            if !trimmed.is_empty() {
                return trimmed.to_string();
            }
        }

        if let Some(detail_text) = value.get("detail").and_then(|detail| detail.as_str()) {
            let trimmed = detail_text.trim();
            if !trimmed.is_empty() {
                return trimmed.to_string();
            }
        }
    }

    let fallback = body.trim();
    if fallback.is_empty() {
        return "Unknown backend error".to_string();
    }
    fallback.chars().take(180).collect()
}

fn setup_scene(mut commands: Commands) {
    commands.spawn(Camera2d);
}

fn startup_handoff_fetch(mut shell: ResMut<ShellState>, bridge: Res<BackendBridge>) {
    let Some(session) = shell.session.as_ref() else {
        return;
    };

    if bridge
        .request_tx
        .send(BackendRequest::FetchCharacters {
            access_token: session.access_token.clone(),
        })
        .is_ok()
    {
        shell.request_in_flight = true;
        shell.status_line = "Loaded launcher handoff. Fetching character roster...".to_string();
    } else {
        shell.phase = ShellPhase::Login;
        shell.session = None;
        shell.status_line = "Failed to initialize backend worker from handoff session.".to_string();
    }
}

fn poll_backend_responses(mut shell: ResMut<ShellState>, bridge: Res<BackendBridge>) {
    let mut messages = Vec::new();
    {
        let Ok(receiver) = bridge.response_rx.lock() else {
            shell.request_in_flight = false;
            shell.status_line = "Backend response channel lock failed.".to_string();
            return;
        };

        loop {
            match receiver.try_recv() {
                Ok(message) => messages.push(message),
                Err(TryRecvError::Empty) => break,
                Err(TryRecvError::Disconnected) => {
                    shell.request_in_flight = false;
                    shell.status_line = "Backend worker disconnected.".to_string();
                    break;
                }
            }
        }
    }

    for message in messages {
        handle_backend_response(&mut shell, &bridge.request_tx, message);
    }
}

fn handle_backend_response(shell: &mut ShellState, request_tx: &Sender<BackendRequest>, message: BackendResponse) {
    match message {
        BackendResponse::Login(Ok(session)) => {
            shell.session = Some(session.clone());
            shell.phase = ShellPhase::CharacterSelect;
            shell.status_line = "Login successful. Fetching character roster...".to_string();
            shell.request_in_flight = request_tx
                .send(BackendRequest::FetchCharacters {
                    access_token: session.access_token,
                })
                .is_ok();
            if !shell.request_in_flight {
                shell.status_line = "Login succeeded but character fetch dispatch failed.".to_string();
            }
        }
        BackendResponse::Login(Err(error)) => {
            shell.phase = ShellPhase::Login;
            shell.request_in_flight = false;
            shell.status_line = format!("Login failed: {error}");
        }
        BackendResponse::Characters(Ok(characters)) => {
            shell.characters = characters;
            shell.selected_character_id = resolve_selected_character_id(&shell.characters, shell.selected_character_id);
            shell.phase = ShellPhase::CharacterSelect;
            shell.request_in_flight = false;
            if shell.characters.is_empty() {
                shell.status_line = "No characters were returned by backend.".to_string();
            } else {
                shell.status_line = format!("Loaded {} character(s).", shell.characters.len());
            }
        }
        BackendResponse::Characters(Err(error)) => {
            shell.phase = ShellPhase::CharacterSelect;
            shell.request_in_flight = false;
            shell.status_line = format!("Character fetch failed: {error}");
        }
        BackendResponse::Bootstrap(Ok(bootstrap)) => {
            shell.campaign_bootstrap = Some(bootstrap.clone());
            shell.phase = ShellPhase::CampaignReady;
            shell.request_in_flight = false;
            shell.status_line = format!(
                "Entered campaign scene for {} in {}.",
                bootstrap.character_name, bootstrap.level_description
            );
        }
        BackendResponse::Bootstrap(Err(error)) => {
            shell.phase = ShellPhase::CharacterSelect;
            shell.request_in_flight = false;
            shell.status_line = format!("World bootstrap failed: {error}");
        }
    }
}

fn animate_campaign_markers(time: Res<Time>, shell: Res<ShellState>, mut map: ResMut<CampaignMapSurface>) {
    if shell.phase != ShellPhase::CampaignReady {
        return;
    }

    let delta = time.delta_secs().clamp(0.0, 0.2);
    for marker in &mut map.army_markers {
        advance_marker(marker, delta);
    }
    for marker in &mut map.caravan_markers {
        advance_marker(marker, delta);
    }
}

fn advance_marker(marker: &mut MovingMapMarker, delta_seconds: f32) {
    marker.progress += marker.speed * delta_seconds;
    if marker.progress >= 1.0 {
        marker.progress = 0.0;
        std::mem::swap(&mut marker.origin, &mut marker.destination);
    }
}

fn draw_campaign_map_gizmos(mut gizmos: Gizmos, shell: Res<ShellState>, map: Res<CampaignMapSurface>) {
    if shell.phase != ShellPhase::CampaignReady {
        return;
    }

    for route in &map.routes {
        let Some(origin) = map.settlement_position(route.origin) else {
            continue;
        };
        let Some(destination) = map.settlement_position(route.destination) else {
            continue;
        };
        let color = if route.is_sea_route {
            Color::srgb(0.21, 0.49, 0.66)
        } else {
            Color::srgb(0.46, 0.37, 0.28)
        };
        gizmos.line_2d(origin * map.zoom, destination * map.zoom, color);
    }

    for settlement in &map.settlements {
        let pos = Vec2::new(settlement.map_x * MAP_SCALE, settlement.map_y * MAP_SCALE) * map.zoom;
        let color = match settlement.fog {
            FogVisibility::Visible => Color::srgb(0.82, 0.76, 0.43),
            FogVisibility::Shrouded => Color::srgb(0.46, 0.5, 0.55),
            FogVisibility::Obscured => Color::srgb(0.2, 0.24, 0.28),
        };
        gizmos.circle_2d(pos, 5.0 * map.zoom.clamp(0.6, 2.2), color);
    }

    for marker in &map.army_markers {
        if let Some(pos) = marker_world_position(&map, marker) {
            gizmos.circle_2d(
                pos * map.zoom,
                4.0 * map.zoom.clamp(0.6, 2.2),
                Color::srgb(0.87, 0.33, 0.24),
            );
        }
    }

    for marker in &map.caravan_markers {
        if let Some(pos) = marker_world_position(&map, marker) {
            gizmos.circle_2d(
                pos * map.zoom,
                3.5 * map.zoom.clamp(0.6, 2.2),
                Color::srgb(0.25, 0.72, 0.64),
            );
        }
    }
}

fn marker_world_position(map: &CampaignMapSurface, marker: &MovingMapMarker) -> Option<Vec2> {
    let origin = map.settlement_position(marker.origin)?;
    let destination = map.settlement_position(marker.destination)?;
    Some(origin.lerp(destination, marker.progress.clamp(0.0, 1.0)))
}

fn draw_shell_ui(
    mut egui_contexts: EguiContexts,
    mut shell: ResMut<ShellState>,
    config: Res<BackendConfig>,
    bridge: Res<BackendBridge>,
    mut map: ResMut<CampaignMapSurface>,
) {
    let Ok(ctx) = egui_contexts.ctx_mut() else {
        return;
    };

    egui::Window::new("Ambitions of Peace - Client Bootstrap Shell")
        .anchor(egui::Align2::LEFT_TOP, [12.0, 12.0])
        .resizable(true)
        .show(ctx, |ui| {
            ui.label(format!("Backend: {}", config.base_url));
            ui.label(format!("Phase: {}", shell.phase.label()));
            ui.label(format!("Status: {}", shell.status_line));
            ui.separator();

            if let Some(session) = shell.session.as_ref() {
                ui.label(format!("Session: {}", session.session_id));
                ui.label(format!("User: {} ({})", session.display_name, session.user_id));
                if !session.refresh_token.is_empty() {
                    ui.label("Refresh token present.");
                }
                ui.separator();
            }

            match shell.phase {
                ShellPhase::Login | ShellPhase::Authenticating => {
                    render_login_controls(ui, &mut shell, &config, &bridge);
                }
                ShellPhase::CharacterSelect | ShellPhase::Bootstrapping => {
                    render_character_controls(ui, &mut shell, &config, &bridge);
                }
                ShellPhase::CampaignReady => {
                    render_campaign_summary(ui, &mut shell, &config, &bridge, &mut map);
                }
            }
        });
}

fn render_login_controls(ui: &mut egui::Ui, shell: &mut ShellState, config: &BackendConfig, bridge: &BackendBridge) {
    ui.heading("Login");
    ui.horizontal(|ui| {
        ui.label("Email");
        ui.text_edit_singleline(&mut shell.email);
    });
    ui.horizontal(|ui| {
        ui.label("Password");
        ui.add(egui::TextEdit::singleline(&mut shell.password).password(true));
    });
    ui.horizontal(|ui| {
        ui.label("MFA OTP");
        ui.add(egui::TextEdit::singleline(&mut shell.otp_code));
    });

    let login_clicked = ui
        .add_enabled(
            !shell.request_in_flight,
            egui::Button::new("Login and Fetch Characters"),
        )
        .clicked();
    if login_clicked {
        let email = shell.email.trim().to_string();
        let password = shell.password.trim().to_string();
        if email.is_empty() || password.is_empty() {
            shell.status_line = "Email and password are required.".to_string();
            return;
        }

        let otp_code = trimmed_nonempty(shell.otp_code.clone());
        if bridge
            .request_tx
            .send(BackendRequest::Login {
                email,
                password,
                otp_code,
            })
            .is_ok()
        {
            shell.phase = ShellPhase::Authenticating;
            shell.request_in_flight = true;
            shell.status_line = format!("Authenticating against {}...", config.base_url);
        } else {
            shell.status_line = "Failed to dispatch login request.".to_string();
        }
    }

    ui.separator();
    ui.label("Optional launcher handoff env vars:");
    ui.label("AOP_HANDOFF_ACCESS_TOKEN, AOP_HANDOFF_SESSION_ID, AOP_HANDOFF_USER_ID, AOP_HANDOFF_DISPLAY_NAME");
}

fn render_character_controls(
    ui: &mut egui::Ui,
    shell: &mut ShellState,
    config: &BackendConfig,
    bridge: &BackendBridge,
) {
    ui.heading("Character Selection");

    if shell.characters.is_empty() {
        ui.label("No characters loaded.");
    } else {
        for character in &shell.characters {
            let selected = shell.selected_character_id == Some(character.id);
            let suffix = if character.is_selected {
                " [server-selected]"
            } else {
                ""
            };
            let label = format!("{} (Lv.{}){}", character.name, character.level, suffix);
            if ui.selectable_label(selected, label).clicked() {
                shell.selected_character_id = Some(character.id);
            }
        }
    }

    ui.separator();
    let enter_clicked = ui
        .add_enabled(
            !shell.request_in_flight && shell.selected_character_id.is_some() && shell.session.is_some(),
            egui::Button::new("Fetch Session Bootstrap and Enter Campaign"),
        )
        .clicked();

    if enter_clicked {
        let Some(character_id) = shell.selected_character_id else {
            shell.status_line = "Select a character first.".to_string();
            return;
        };
        let Some(session) = shell.session.as_ref() else {
            shell.phase = ShellPhase::Login;
            shell.status_line = "Session missing. Log in again.".to_string();
            return;
        };

        if bridge
            .request_tx
            .send(BackendRequest::FetchBootstrap {
                access_token: session.access_token.clone(),
                character_id,
            })
            .is_ok()
        {
            shell.phase = ShellPhase::Bootstrapping;
            shell.request_in_flight = true;
            shell.status_line = format!("Requesting world bootstrap for character #{character_id}...");
        } else {
            shell.status_line = "Failed to dispatch world bootstrap request.".to_string();
        }
    }

    let refresh_clicked = ui
        .add_enabled(
            !shell.request_in_flight && shell.session.is_some(),
            egui::Button::new("Refresh Characters"),
        )
        .clicked();

    if refresh_clicked && let Some(session) = shell.session.as_ref() {
        if bridge
            .request_tx
            .send(BackendRequest::FetchCharacters {
                access_token: session.access_token.clone(),
            })
            .is_ok()
        {
            shell.request_in_flight = true;
            shell.status_line = format!("Refreshing character roster from {}...", config.base_url);
        } else {
            shell.status_line = "Failed to dispatch character refresh request.".to_string();
        }
    }

    if ui.button("Clear Session and Return to Login").clicked() {
        shell.session = None;
        shell.characters.clear();
        shell.selected_character_id = None;
        shell.campaign_bootstrap = None;
        shell.phase = ShellPhase::Login;
        shell.request_in_flight = false;
        shell.status_line = "Session cleared. Enter credentials to continue.".to_string();
    }
}

fn render_campaign_summary(
    ui: &mut egui::Ui,
    shell: &mut ShellState,
    config: &BackendConfig,
    bridge: &BackendBridge,
    map: &mut CampaignMapSurface,
) {
    ui.heading("Campaign Entry Scene");
    if let Some(bootstrap) = shell.campaign_bootstrap.as_ref() {
        ui.label(format!(
            "Character: {} (#{}).",
            bootstrap.character_name, bootstrap.character_id
        ));
        ui.label(format!(
            "Level: {} ({})",
            bootstrap.level_name, bootstrap.level_description
        ));
        ui.label(format!(
            "Instance: {} [{}]",
            bootstrap.instance_id, bootstrap.instance_kind
        ));
        ui.label(format!(
            "Spawn: ({}, {}, {:.2}) yaw {:.1}",
            bootstrap.spawn_world_x, bootstrap.spawn_world_y, bootstrap.spawn_world_z, bootstrap.yaw_deg
        ));
        ui.label(format!("Camera profile: {}", bootstrap.camera_profile_key));
    } else {
        ui.label("No campaign bootstrap payload loaded yet.");
    }

    ui.separator();
    ui.heading("Campaign Map Rendering MVP");
    ui.label("Rendered in-scene: settlement nodes, route lines, army markers, caravan markers, fog visibility.");
    ui.add(egui::Slider::new(&mut map.zoom, 0.6..=2.2).text("Map zoom"));
    ui.horizontal(|ui| {
        ui.colored_label(egui::Color32::from_rgb(209, 195, 110), "Visible");
        ui.colored_label(egui::Color32::from_rgb(120, 130, 140), "Shrouded");
        ui.colored_label(egui::Color32::from_rgb(52, 62, 72), "Obscured");
    });
    ui.label(format!(
        "Settlements: {} | Routes: {} | Armies: {} | Caravans: {}",
        map.settlements.len(),
        map.routes.len(),
        map.army_markers.len(),
        map.caravan_markers.len()
    ));
    if let Some(settlement) = map
        .settlements
        .iter()
        .find(|row| Some(row.id) == shell.selected_character_id.map(SettlementId))
        .or_else(|| map.settlements.first())
    {
        ui.label(format!("Map focus sample: {} (#{})", settlement.name, settlement.id.0));
    }
    if !map.army_markers.is_empty() {
        let labels = map
            .army_markers
            .iter()
            .map(|row| row.label.as_str())
            .collect::<Vec<_>>()
            .join(", ");
        ui.label(format!("Army markers: {labels}"));
    }
    if !map.caravan_markers.is_empty() {
        let labels = map
            .caravan_markers
            .iter()
            .map(|row| row.label.as_str())
            .collect::<Vec<_>>()
            .join(", ");
        ui.label(format!("Caravan markers: {labels}"));
    }

    ui.separator();
    if ui.button("Back to Character Selection").clicked() {
        shell.phase = ShellPhase::CharacterSelect;
        shell.status_line = format!("Returned to character selection for {}.", config.base_url);
    }

    let refresh_clicked = ui
        .add_enabled(
            !shell.request_in_flight && shell.session.is_some(),
            egui::Button::new("Refresh Characters"),
        )
        .clicked();
    if refresh_clicked && let Some(session) = shell.session.as_ref() {
        if bridge
            .request_tx
            .send(BackendRequest::FetchCharacters {
                access_token: session.access_token.clone(),
            })
            .is_ok()
        {
            shell.phase = ShellPhase::CharacterSelect;
            shell.request_in_flight = true;
            shell.status_line = "Refreshing roster after campaign entry.".to_string();
        } else {
            shell.status_line = "Failed to dispatch character refresh request.".to_string();
        }
    }
}

fn sync_campaign_scene(mut commands: Commands, mut scene: ResMut<CampaignScene>, shell: Res<ShellState>) {
    let Some(bootstrap) = shell.campaign_bootstrap.as_ref() else {
        if let Some(marker) = scene.marker_entity.take() {
            commands.entity(marker).despawn();
        }
        scene.active_character_id = None;
        return;
    };

    if shell.phase != ShellPhase::CampaignReady {
        if let Some(marker) = scene.marker_entity.take() {
            commands.entity(marker).despawn();
        }
        scene.active_character_id = None;
        return;
    }

    if scene.active_character_id == Some(bootstrap.character_id) {
        return;
    }

    if let Some(marker) = scene.marker_entity.take() {
        commands.entity(marker).despawn();
    }

    let marker = commands
        .spawn((
            Sprite::from_color(Color::srgb(0.88, 0.74, 0.3), Vec2::new(20.0, 20.0)),
            Transform::from_xyz(
                bootstrap.spawn_world_x as f32 * 0.2,
                bootstrap.spawn_world_y as f32 * 0.2,
                5.0,
            ),
        ))
        .id();

    scene.marker_entity = Some(marker);
    scene.active_character_id = Some(bootstrap.character_id);
}

fn resolve_selected_character_id(characters: &[CharacterSummary], current: Option<u64>) -> Option<u64> {
    if let Some(current_id) = current
        && characters.iter().any(|row| row.id == current_id)
    {
        return Some(current_id);
    }

    characters
        .iter()
        .find(|row| row.is_selected)
        .map(|row| row.id)
        .or_else(|| characters.first().map(|row| row.id))
}

fn trimmed_nonempty(value: String) -> Option<String> {
    let trimmed = value.trim();
    if trimmed.is_empty() {
        None
    } else {
        Some(trimmed.to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::{CharacterSummary, extract_error_message, resolve_selected_character_id};

    #[test]
    fn extracts_error_message_from_backend_shapes() {
        let wrapped = r#"{"error":{"message":"validation failed"}}"#;
        assert_eq!(extract_error_message(wrapped), "validation failed");

        let detailed = r#"{"detail":{"message":"invalid_credentials"}}"#;
        assert_eq!(extract_error_message(detailed), "invalid_credentials");

        let plain = "backend unavailable";
        assert_eq!(extract_error_message(plain), "backend unavailable");
    }

    #[test]
    fn resolves_selected_character_preferring_server_selected_then_first() {
        let rows = vec![
            CharacterSummary {
                id: 10,
                name: "A".to_string(),
                level: 1,
                is_selected: false,
            },
            CharacterSummary {
                id: 11,
                name: "B".to_string(),
                level: 2,
                is_selected: true,
            },
        ];

        assert_eq!(resolve_selected_character_id(&rows, None), Some(11));
        assert_eq!(resolve_selected_character_id(&rows, Some(10)), Some(10));
        assert_eq!(resolve_selected_character_id(&rows, Some(999)), Some(11));

        let none_rows: Vec<CharacterSummary> = Vec::new();
        assert_eq!(resolve_selected_character_id(&none_rows, Some(10)), None);
    }
}
