use bevy::prelude::*;
use bevy_egui::{EguiContexts, EguiPlugin, egui};
use reqwest::blocking::Client;
use reqwest::header::{AUTHORIZATION, CONTENT_TYPE};
use serde::Deserialize;
use serde::Serialize;
use serde::de::DeserializeOwned;
use sim_core::{SettlementId, SettlementTier, TravelGraph, classify_route_risk, sample_levant_travel_graph};
use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::path::PathBuf;
use std::sync::Mutex;
use std::sync::mpsc::{self, Receiver, Sender, TryRecvError};
use std::thread;
use std::time::Duration;
use std::time::{SystemTime, UNIX_EPOCH};

const DEFAULT_API_BASE_URL: &str = "http://127.0.0.1:8000";
const DEFAULT_CLIENT_VERSION: &str = "dev-0.1.0";
const DEFAULT_CONTENT_VERSION_KEY: &str = "runtime_gameplay_v1";
const DEFAULT_PANEL_LAYOUT_PATH: &str = "client-app/runtime/panel_layout.json";
const DEFAULT_AUTHORED_MAP_PATH: &str = "client-app/runtime/authored_map.json";
const DEFAULT_PROVINCE_PACK_PATH: &str = "assets/content/provinces/acre/acre_poc_v1.json";
const MAP_SCALE: f32 = 2.3;
const SETTLEMENT_KIND_OPTIONS: [&str; 5] = ["camp", "village", "town", "city", "fortress"];

const HANDOFF_SCHEMA_VERSION: u32 = 1;

#[derive(Debug, Clone, Default)]
struct StartupOptions {
    handoff_file: Option<PathBuf>,
    handoff_json: Option<String>,
}

impl StartupOptions {
    fn from_args() -> Self {
        parse_startup_options(env::args().skip(1))
    }
}

#[derive(Debug, Clone)]
struct ResolvedStartupHandoff {
    source: String,
    email: Option<String>,
    selected_character_id: Option<u64>,
    session: SessionContext,
    base_url: Option<String>,
    client_version: Option<String>,
    client_content_version_key: Option<String>,
}

#[derive(Debug, Deserialize)]
struct StructuredHandoffPayload {
    #[serde(default)]
    schema_version: u32,
    #[serde(default)]
    email: String,
    #[serde(default)]
    access_token: String,
    #[serde(default)]
    refresh_token: String,
    #[serde(default)]
    session_id: String,
    #[serde(default)]
    user_id: Option<u64>,
    #[serde(default)]
    display_name: String,
    #[serde(default)]
    character_id: Option<u64>,
    #[serde(default)]
    api_base_url: String,
    #[serde(default)]
    client_version: String,
    #[serde(default)]
    client_content_version_key: String,
    #[serde(default)]
    expires_unix_ms: Option<u64>,
}

fn default_settlement_kind() -> String {
    "town".to_string()
}

fn settlement_tier_from_kind(raw: &str) -> SettlementTier {
    match raw.trim().to_lowercase().as_str() {
        "camp" => SettlementTier::Camp,
        "village" => SettlementTier::Village,
        "city" => SettlementTier::City,
        "fortress" => SettlementTier::Fortress,
        _ => SettlementTier::Town,
    }
}

fn risk_band_label(total_risk: u32) -> &'static str {
    match classify_route_risk(total_risk) {
        sim_core::RouteRiskBand::Low => "low",
        sim_core::RouteRiskBand::Guarded => "guarded",
        sim_core::RouteRiskBand::High => "high",
        sim_core::RouteRiskBand::Severe => "severe",
    }
}

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

    fn apply_handoff_overrides(
        &mut self,
        base_url: Option<String>,
        client_version: Option<String>,
        client_content_version_key: Option<String>,
    ) {
        if let Some(value) = base_url.and_then(trimmed_nonempty) {
            self.base_url = value.trim_end_matches('/').to_string();
        }
        if let Some(value) = client_version.and_then(trimmed_nonempty) {
            self.client_version = value;
        }
        if let Some(value) = client_content_version_key.and_then(trimmed_nonempty) {
            self.client_content_version_key = value;
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
    handoff_session_active: bool,
    email: String,
    password: String,
    otp_code: String,
    session: Option<SessionContext>,
    characters: Vec<CharacterSummary>,
    selected_character_id: Option<u64>,
    campaign_bootstrap: Option<CampaignBootstrapSummary>,
}

impl ShellState {
    fn from_startup_handoff(config: &mut BackendConfig, options: &StartupOptions) -> Self {
        let mut state = Self {
            phase: ShellPhase::Login,
            status_line: "Ready. Enter account credentials to continue.".to_string(),
            email: env::var("AOP_HANDOFF_EMAIL").unwrap_or_default(),
            password: String::new(),
            ..Self::default()
        };

        match resolve_startup_handoff(options) {
            Ok(Some(handoff)) => {
                let ResolvedStartupHandoff {
                    source,
                    email,
                    selected_character_id,
                    session,
                    base_url,
                    client_version,
                    client_content_version_key,
                } = handoff;
                config.apply_handoff_overrides(base_url, client_version, client_content_version_key);
                if let Some(email) = email {
                    state.email = email;
                }
                state.selected_character_id = selected_character_id;
                state.session = Some(session);
                state.handoff_session_active = true;
                state.phase = ShellPhase::CharacterSelect;
                state.status_line = format!("External handoff loaded from {}. Fetching characters...", source);
            }
            Ok(None) => {}
            Err(error) => {
                state.status_line = format!("External handoff rejected: {error}. Enter credentials to continue.");
            }
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
    tier: SettlementTier,
    fog: FogVisibility,
}

#[derive(Clone, Debug)]
struct RouteRenderEdge {
    origin: SettlementId,
    destination: SettlementId,
    is_sea_route: bool,
}

#[derive(Clone, Debug, Deserialize)]
struct ProvincePackSettlement {
    id: u64,
    name: String,
    map_x: i32,
    map_y: i32,
    #[serde(default)]
    kind: Option<String>,
}

#[derive(Clone, Debug, Deserialize)]
struct ProvincePackRoute {
    id: u64,
    origin: u64,
    destination: u64,
    travel_hours: u32,
    base_risk: u32,
    is_sea_route: bool,
}

#[derive(Clone, Debug, Deserialize)]
struct ProvincePackData {
    settlements: Vec<ProvincePackSettlement>,
    routes: Vec<ProvincePackRoute>,
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
        let graph = load_default_campaign_graph().unwrap_or_else(sample_levant_travel_graph);
        let settlements = graph
            .settlements()
            .enumerate()
            .map(|(index, row)| {
                let fog = if index < 2 {
                    FogVisibility::Visible
                } else if index < 5 {
                    FogVisibility::Shrouded
                } else {
                    FogVisibility::Obscured
                };
                SettlementRenderNode {
                    id: row.id,
                    name: row.name.clone(),
                    map_x: row.map_x as f32,
                    map_y: row.map_y as f32,
                    tier: row.tier,
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

        let first_route = routes.first().cloned();
        let second_route = routes.get(1).cloned().or_else(|| first_route.clone());

        Self {
            graph,
            settlements,
            routes,
            army_markers: [
                marker_from_route(first_route.clone(), "Army A7", 0.22, 0.08),
                marker_from_route(second_route.clone(), "Army A8", 0.61, 0.05),
            ]
            .into_iter()
            .flatten()
            .collect(),
            caravan_markers: [
                marker_from_route(second_route, "Caravan C12", 0.4, 0.04),
                marker_from_route(first_route, "Caravan C19", 0.75, 0.03),
            ]
            .into_iter()
            .flatten()
            .collect(),
            zoom: 1.0,
        }
    }

    fn settlement_position(&self, settlement_id: SettlementId) -> Option<Vec2> {
        self.graph
            .settlement(settlement_id)
            .map(|row| Vec2::new(row.map_x as f32 * MAP_SCALE, row.map_y as f32 * MAP_SCALE))
    }
}

fn marker_from_route(
    route: Option<RouteRenderEdge>,
    label: &str,
    progress: f32,
    speed: f32,
) -> Option<MovingMapMarker> {
    route.map(|route| MovingMapMarker {
        label: label.to_string(),
        origin: route.origin,
        destination: route.destination,
        progress,
        speed,
    })
}

fn load_default_campaign_graph() -> Option<TravelGraph> {
    let pack_path = env::var("AOP_PROVINCE_PACK_PATH")
        .ok()
        .map(|raw| raw.trim().to_string())
        .filter(|value| !value.is_empty())
        .unwrap_or_else(|| DEFAULT_PROVINCE_PACK_PATH.to_string());
    let payload = fs::read_to_string(pack_path).ok()?;
    let parsed = serde_json::from_str::<ProvincePackData>(&payload).ok()?;
    build_graph_from_pack(&parsed).ok()
}

fn build_graph_from_pack(pack: &ProvincePackData) -> Result<TravelGraph, String> {
    let mut graph = TravelGraph::default();
    for settlement in &pack.settlements {
        if settlement.name.trim().is_empty() {
            return Err(format!("Settlement {} has empty name", settlement.id));
        }
        graph.insert_settlement(sim_core::SettlementNode {
            id: SettlementId(settlement.id),
            name: settlement.name.trim().to_string(),
            map_x: settlement.map_x,
            map_y: settlement.map_y,
            tier: settlement
                .kind
                .as_deref()
                .map(settlement_tier_from_kind)
                .unwrap_or_default(),
        });
    }

    for route in &pack.routes {
        graph
            .insert_route(sim_core::RouteEdge {
                id: sim_core::RouteId(route.id),
                origin: SettlementId(route.origin),
                destination: SettlementId(route.destination),
                travel_hours: route.travel_hours,
                base_risk: route.base_risk,
                is_sea_route: route.is_sea_route,
            })
            .map_err(|error| format!("Route {} invalid: {}", route.id, error))?;
    }

    if graph.settlements().next().is_none() {
        return Err("Province pack has no settlements".to_string());
    }
    if graph.routes().next().is_none() {
        return Err("Province pack has no routes".to_string());
    }
    Ok(graph)
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum LayoutPreset {
    Strategist,
    Operations,
}

impl LayoutPreset {
    fn as_str(self) -> &'static str {
        match self {
            Self::Strategist => "strategist",
            Self::Operations => "operations",
        }
    }

    fn from_str(value: &str) -> Self {
        match value.trim().to_lowercase().as_str() {
            "operations" => Self::Operations,
            _ => Self::Strategist,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum DomainPanel {
    Character,
    Household,
    Logistics,
    Trade,
    Espionage,
    Diplomacy,
    Notifications,
}

impl DomainPanel {
    fn key(self) -> &'static str {
        match self {
            Self::Character => "character",
            Self::Household => "household",
            Self::Logistics => "logistics",
            Self::Trade => "trade",
            Self::Espionage => "espionage",
            Self::Diplomacy => "diplomacy",
            Self::Notifications => "notifications",
        }
    }

    fn title(self) -> &'static str {
        match self {
            Self::Character => "Character",
            Self::Household => "Household",
            Self::Logistics => "Logistics",
            Self::Trade => "Trade",
            Self::Espionage => "Espionage",
            Self::Diplomacy => "Diplomacy",
            Self::Notifications => "Notifications",
        }
    }

    fn hotkey(self) -> KeyCode {
        match self {
            Self::Character => KeyCode::F1,
            Self::Household => KeyCode::F2,
            Self::Logistics => KeyCode::F3,
            Self::Trade => KeyCode::F4,
            Self::Espionage => KeyCode::F5,
            Self::Diplomacy => KeyCode::F6,
            Self::Notifications => KeyCode::F7,
        }
    }
}

const DOMAIN_PANELS: [DomainPanel; 7] = [
    DomainPanel::Character,
    DomainPanel::Household,
    DomainPanel::Logistics,
    DomainPanel::Trade,
    DomainPanel::Espionage,
    DomainPanel::Diplomacy,
    DomainPanel::Notifications,
];

#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
struct PanelRect {
    x: f32,
    y: f32,
    width: f32,
    height: f32,
}

impl PanelRect {
    fn from_points(pos: [f32; 2], size: [f32; 2]) -> Self {
        Self {
            x: pos[0],
            y: pos[1],
            width: size[0],
            height: size[1],
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct PanelLayoutSnapshot {
    preset: String,
    open: BTreeMap<String, bool>,
    rects: BTreeMap<String, PanelRect>,
}

#[derive(Resource)]
struct PanelUiState {
    storage_path: PathBuf,
    snapshot: PanelLayoutSnapshot,
    last_io_status: String,
}

impl PanelUiState {
    fn from_env() -> Self {
        let storage_path = env::var("AOP_PANEL_LAYOUT_PATH")
            .ok()
            .and_then(trimmed_nonempty)
            .map(PathBuf::from)
            .unwrap_or_else(|| PathBuf::from(DEFAULT_PANEL_LAYOUT_PATH));

        let mut state = Self {
            storage_path,
            snapshot: default_layout_snapshot(LayoutPreset::Strategist),
            last_io_status: "Layout preset loaded: strategist".to_string(),
        };
        state.load_from_disk();
        state
    }

    fn current_preset(&self) -> LayoutPreset {
        LayoutPreset::from_str(&self.snapshot.preset)
    }

    fn apply_preset(&mut self, preset: LayoutPreset) {
        self.snapshot = default_layout_snapshot(preset);
        self.last_io_status = format!("Applied layout preset: {}", preset.as_str());
    }

    fn save_to_disk(&mut self) {
        if let Some(parent) = self.storage_path.parent()
            && let Err(error) = fs::create_dir_all(parent)
        {
            self.last_io_status = format!("Layout save failed: {error}");
            return;
        }
        match serde_json::to_string_pretty(&self.snapshot) {
            Ok(payload) => match fs::write(&self.storage_path, payload) {
                Ok(()) => {
                    self.last_io_status = format!("Layout saved to {}", self.storage_path.display());
                }
                Err(error) => {
                    self.last_io_status = format!("Layout save failed: {error}");
                }
            },
            Err(error) => {
                self.last_io_status = format!("Layout save failed: {error}");
            }
        }
    }

    fn load_from_disk(&mut self) {
        let raw = match fs::read_to_string(&self.storage_path) {
            Ok(raw) => raw,
            Err(_) => return,
        };
        match serde_json::from_str::<PanelLayoutSnapshot>(&raw) {
            Ok(snapshot) => {
                self.snapshot = snapshot;
                self.last_io_status = format!("Layout loaded from {}", self.storage_path.display());
            }
            Err(error) => {
                self.last_io_status = format!("Layout load failed: {error}");
            }
        }
    }

    fn is_open(&self, panel: DomainPanel) -> bool {
        self.snapshot.open.get(panel.key()).copied().unwrap_or(true)
    }

    fn set_open(&mut self, panel: DomainPanel, open: bool) {
        self.snapshot.open.insert(panel.key().to_string(), open);
    }

    fn panel_rect(&self, panel: DomainPanel) -> PanelRect {
        self.snapshot.rects.get(panel.key()).copied().unwrap_or_else(|| {
            let fallback = default_layout_snapshot(self.current_preset());
            fallback
                .rects
                .get(panel.key())
                .copied()
                .unwrap_or_else(|| PanelRect::from_points([24.0, 320.0], [320.0, 220.0]))
        })
    }

    fn set_panel_rect_from_egui(&mut self, panel: DomainPanel, rect: egui::Rect) {
        self.snapshot.rects.insert(
            panel.key().to_string(),
            PanelRect::from_points([rect.min.x, rect.min.y], [rect.width(), rect.height()]),
        );
    }
}

fn default_layout_snapshot(preset: LayoutPreset) -> PanelLayoutSnapshot {
    let mut open = BTreeMap::new();
    for panel in DOMAIN_PANELS {
        open.insert(panel.key().to_string(), true);
    }

    let mut rects = BTreeMap::new();
    match preset {
        LayoutPreset::Strategist => {
            rects.insert(
                DomainPanel::Character.key().to_string(),
                PanelRect::from_points([22.0, 320.0], [300.0, 220.0]),
            );
            rects.insert(
                DomainPanel::Household.key().to_string(),
                PanelRect::from_points([336.0, 320.0], [300.0, 220.0]),
            );
            rects.insert(
                DomainPanel::Logistics.key().to_string(),
                PanelRect::from_points([650.0, 320.0], [300.0, 220.0]),
            );
            rects.insert(
                DomainPanel::Trade.key().to_string(),
                PanelRect::from_points([964.0, 320.0], [300.0, 220.0]),
            );
            rects.insert(
                DomainPanel::Espionage.key().to_string(),
                PanelRect::from_points([22.0, 552.0], [408.0, 220.0]),
            );
            rects.insert(
                DomainPanel::Diplomacy.key().to_string(),
                PanelRect::from_points([444.0, 552.0], [408.0, 220.0]),
            );
            rects.insert(
                DomainPanel::Notifications.key().to_string(),
                PanelRect::from_points([866.0, 552.0], [398.0, 220.0]),
            );
        }
        LayoutPreset::Operations => {
            rects.insert(
                DomainPanel::Character.key().to_string(),
                PanelRect::from_points([22.0, 320.0], [420.0, 190.0]),
            );
            rects.insert(
                DomainPanel::Household.key().to_string(),
                PanelRect::from_points([22.0, 520.0], [420.0, 190.0]),
            );
            rects.insert(
                DomainPanel::Logistics.key().to_string(),
                PanelRect::from_points([456.0, 320.0], [420.0, 190.0]),
            );
            rects.insert(
                DomainPanel::Trade.key().to_string(),
                PanelRect::from_points([456.0, 520.0], [420.0, 190.0]),
            );
            rects.insert(
                DomainPanel::Espionage.key().to_string(),
                PanelRect::from_points([890.0, 320.0], [380.0, 190.0]),
            );
            rects.insert(
                DomainPanel::Diplomacy.key().to_string(),
                PanelRect::from_points([890.0, 520.0], [380.0, 190.0]),
            );
            rects.insert(
                DomainPanel::Notifications.key().to_string(),
                PanelRect::from_points([890.0, 120.0], [380.0, 190.0]),
            );
        }
    }

    PanelLayoutSnapshot {
        preset: preset.as_str().to_string(),
        open,
        rects,
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct AuthoredSettlement {
    id: u64,
    name: String,
    map_x: i32,
    map_y: i32,
    #[serde(default = "default_settlement_kind")]
    kind: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct AuthoredRoute {
    id: u64,
    origin: u64,
    destination: u64,
    travel_hours: u32,
    base_risk: u32,
    is_sea_route: bool,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct AuthoredMapData {
    settlements: Vec<AuthoredSettlement>,
    routes: Vec<AuthoredRoute>,
}

#[derive(Resource)]
struct MapToolsState {
    tools_enabled: bool,
    storage_path: PathBuf,
    data: AuthoredMapData,
    selected_settlement_index: usize,
    draft_route_origin_index: usize,
    draft_route_destination_index: usize,
    draft_route_travel_hours: u32,
    draft_route_base_risk: u32,
    draft_route_is_sea: bool,
    last_status: String,
    validation_errors: Vec<String>,
}

impl MapToolsState {
    fn from_env() -> Self {
        let storage_path = env::var("AOP_TOOLS_MAP_PATH")
            .ok()
            .and_then(trimmed_nonempty)
            .map(PathBuf::from)
            .unwrap_or_else(|| PathBuf::from(DEFAULT_AUTHORED_MAP_PATH));
        let tools_enabled = env::var("AOP_TOOLS_ENABLED")
            .ok()
            .map(|raw| raw.trim().eq_ignore_ascii_case("true"))
            .unwrap_or(false)
            || env::var("AOP_TOOLS_ROLE")
                .ok()
                .map(|raw| {
                    let normalized = raw.trim().to_lowercase();
                    matches!(normalized.as_str(), "designer" | "admin")
                })
                .unwrap_or(false);

        let mut state = Self {
            tools_enabled,
            storage_path,
            data: sample_authored_map_data(),
            selected_settlement_index: 0,
            draft_route_origin_index: 0,
            draft_route_destination_index: 0,
            draft_route_travel_hours: 24,
            draft_route_base_risk: 800,
            draft_route_is_sea: false,
            last_status: "Tools mode inactive".to_string(),
            validation_errors: Vec::new(),
        };
        if state.tools_enabled {
            state.last_status = "Tools mode active".to_string();
            state.load_from_disk();
        }
        state
    }

    fn load_from_disk(&mut self) {
        let raw = match fs::read_to_string(&self.storage_path) {
            Ok(raw) => raw,
            Err(_) => return,
        };
        match serde_json::from_str::<AuthoredMapData>(&raw) {
            Ok(mut data) => {
                normalize_authored_map(&mut data);
                self.data = data;
                self.selected_settlement_index = 0;
                self.last_status = format!("Loaded authored map from {}", self.storage_path.display());
            }
            Err(error) => {
                self.last_status = format!("Failed loading authored map: {error}");
            }
        }
    }

    fn save_to_disk(&mut self) {
        let mut data = self.data.clone();
        normalize_authored_map(&mut data);
        if let Some(parent) = self.storage_path.parent()
            && let Err(error) = fs::create_dir_all(parent)
        {
            self.last_status = format!("Save failed: {error}");
            return;
        }
        match serde_json::to_string_pretty(&data) {
            Ok(payload) => match fs::write(&self.storage_path, payload) {
                Ok(()) => {
                    self.data = data;
                    self.last_status = format!("Saved authored map to {}", self.storage_path.display());
                }
                Err(error) => {
                    self.last_status = format!("Save failed: {error}");
                }
            },
            Err(error) => {
                self.last_status = format!("Save failed: {error}");
            }
        }
    }
}

fn sample_authored_map_data() -> AuthoredMapData {
    let graph = load_default_campaign_graph().unwrap_or_else(sample_levant_travel_graph);
    let settlements = graph
        .settlements()
        .map(|row| AuthoredSettlement {
            id: row.id.0,
            name: row.name.clone(),
            map_x: row.map_x,
            map_y: row.map_y,
            kind: format!("{:?}", row.tier).to_lowercase(),
        })
        .collect::<Vec<_>>();
    let routes = graph
        .routes()
        .map(|row| AuthoredRoute {
            id: row.id.0,
            origin: row.origin.0,
            destination: row.destination.0,
            travel_hours: row.travel_hours,
            base_risk: row.base_risk,
            is_sea_route: row.is_sea_route,
        })
        .collect::<Vec<_>>();
    AuthoredMapData { settlements, routes }
}

fn normalize_authored_map(data: &mut AuthoredMapData) {
    data.settlements.sort_by_key(|row| row.id);
    data.routes.sort_by_key(|row| row.id);
}

fn validate_and_build_graph(data: &AuthoredMapData) -> Result<TravelGraph, Vec<String>> {
    let mut errors = Vec::new();
    let mut graph = TravelGraph::default();
    let mut settlement_ids = BTreeMap::new();

    for settlement in &data.settlements {
        let name = settlement.name.trim();
        if name.is_empty() {
            errors.push(format!("Settlement {} has empty name", settlement.id));
            continue;
        }
        if !SETTLEMENT_KIND_OPTIONS.contains(&settlement.kind.as_str()) {
            errors.push(format!(
                "Settlement {} has invalid kind '{}'",
                settlement.id, settlement.kind
            ));
            continue;
        }
        if settlement_ids.insert(settlement.id, true).is_some() {
            errors.push(format!("Duplicate settlement id {}", settlement.id));
            continue;
        }
        graph.insert_settlement(sim_core::SettlementNode {
            id: SettlementId(settlement.id),
            name: name.to_string(),
            map_x: settlement.map_x,
            map_y: settlement.map_y,
            tier: settlement_tier_from_kind(&settlement.kind),
        });
    }

    let mut route_ids = BTreeMap::new();
    for route in &data.routes {
        if route_ids.insert(route.id, true).is_some() {
            errors.push(format!("Duplicate route id {}", route.id));
            continue;
        }
        if !settlement_ids.contains_key(&route.origin) {
            errors.push(format!(
                "Route {} origin settlement {} does not exist",
                route.id, route.origin
            ));
            continue;
        }
        if !settlement_ids.contains_key(&route.destination) {
            errors.push(format!(
                "Route {} destination settlement {} does not exist",
                route.id, route.destination
            ));
            continue;
        }

        if let Err(error) = graph.insert_route(sim_core::RouteEdge {
            id: sim_core::RouteId(route.id),
            origin: SettlementId(route.origin),
            destination: SettlementId(route.destination),
            travel_hours: route.travel_hours,
            base_risk: route.base_risk,
            is_sea_route: route.is_sea_route,
        }) {
            errors.push(format!("Route {} invalid: {}", route.id, error));
        }
    }

    if errors.is_empty() { Ok(graph) } else { Err(errors) }
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
    let startup_options = StartupOptions::from_args();
    let mut config = BackendConfig::from_env();
    let shell_state = ShellState::from_startup_handoff(&mut config, &startup_options);
    let bridge = spawn_backend_bridge(config.clone());

    App::new()
        .insert_resource(config)
        .insert_resource(bridge)
        .insert_resource(shell_state)
        .insert_resource(CampaignScene::default())
        .insert_resource(CampaignMapSurface::sample())
        .insert_resource(PanelUiState::from_env())
        .insert_resource(MapToolsState::from_env())
        .insert_resource(ClearColor(Color::srgb(0.05, 0.07, 0.08)))
        .add_plugins(DefaultPlugins)
        .add_plugins(EguiPlugin::default())
        .add_systems(
            Startup,
            (setup_scene, startup_handoff_fetch, startup_apply_authored_map),
        )
        .add_systems(
            Update,
            (
                poll_backend_responses,
                animate_campaign_markers,
                draw_campaign_map_gizmos,
                sync_campaign_scene,
                panel_hotkeys,
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

fn parse_startup_options<I>(args: I) -> StartupOptions
where
    I: IntoIterator<Item = String>,
{
    let mut options = StartupOptions::default();
    let mut iter = args.into_iter();

    while let Some(arg) = iter.next() {
        if let Some(value) = arg.strip_prefix("--handoff-file=") {
            options.handoff_file = trimmed_nonempty(value.to_string()).map(PathBuf::from);
            continue;
        }
        if arg == "--handoff-file" {
            options.handoff_file = iter.next().and_then(trimmed_nonempty).map(PathBuf::from);
            continue;
        }
        if let Some(value) = arg.strip_prefix("--handoff-json=") {
            options.handoff_json = trimmed_nonempty(value.to_string());
            continue;
        }
        if arg == "--handoff-json" {
            options.handoff_json = iter.next().and_then(trimmed_nonempty);
            continue;
        }
    }

    options
}

fn unix_now_millis() -> u64 {
    match SystemTime::now().duration_since(UNIX_EPOCH) {
        Ok(duration) => u64::try_from(duration.as_millis()).unwrap_or(u64::MAX),
        Err(_) => 0,
    }
}

fn resolve_startup_handoff(options: &StartupOptions) -> Result<Option<ResolvedStartupHandoff>, String> {
    if let Some(raw) = options.handoff_json.clone() {
        let handoff = parse_structured_handoff_payload(&raw, "cli:--handoff-json", unix_now_millis())?;
        return Ok(Some(handoff));
    }

    if let Some(path) = options.handoff_file.as_ref() {
        let raw = fs::read_to_string(path)
            .map_err(|error| format!("failed reading handoff file {}: {error}", path.display()))?;
        let handoff = parse_structured_handoff_payload(&raw, &format!("cli:{}", path.display()), unix_now_millis())?;
        return Ok(Some(handoff));
    }

    if let Some(raw) = env::var("AOP_HANDOFF_JSON").ok().and_then(trimmed_nonempty) {
        let handoff = parse_structured_handoff_payload(&raw, "env:AOP_HANDOFF_JSON", unix_now_millis())?;
        return Ok(Some(handoff));
    }

    if let Some(path_text) = env::var("AOP_HANDOFF_PATH").ok().and_then(trimmed_nonempty) {
        let path = PathBuf::from(path_text);
        let raw = fs::read_to_string(&path)
            .map_err(|error| format!("failed reading handoff file {}: {error}", path.display()))?;
        let handoff = parse_structured_handoff_payload(&raw, &format!("env:{}", path.display()), unix_now_millis())?;
        return Ok(Some(handoff));
    }

    resolve_legacy_env_handoff()
}

fn parse_structured_handoff_payload(
    raw: &str,
    source: &str,
    now_unix_ms: u64,
) -> Result<ResolvedStartupHandoff, String> {
    let payload: StructuredHandoffPayload =
        serde_json::from_str(raw).map_err(|error| format!("invalid handoff JSON from {source}: {error}"))?;

    if payload.schema_version != 0 && payload.schema_version != HANDOFF_SCHEMA_VERSION {
        return Err(format!(
            "unsupported handoff schema_version={} from {}",
            payload.schema_version, source
        ));
    }

    if let Some(expires_unix_ms) = payload.expires_unix_ms
        && now_unix_ms > expires_unix_ms
    {
        return Err(format!(
            "handoff payload from {} is expired (expires_unix_ms={expires_unix_ms})",
            source
        ));
    }

    let access_token = trimmed_nonempty(payload.access_token)
        .ok_or_else(|| format!("handoff payload from {} is missing access_token", source))?;
    let session_id = trimmed_nonempty(payload.session_id)
        .ok_or_else(|| format!("handoff payload from {} is missing session_id", source))?;

    let selected_character_id = payload.character_id.filter(|value| *value > 0);
    let session = SessionContext {
        access_token,
        refresh_token: trimmed_nonempty(payload.refresh_token).unwrap_or_default(),
        session_id,
        user_id: payload.user_id.unwrap_or(0),
        display_name: trimmed_nonempty(payload.display_name).unwrap_or_else(|| "Handoff User".to_string()),
    };

    Ok(ResolvedStartupHandoff {
        source: source.to_string(),
        email: trimmed_nonempty(payload.email),
        selected_character_id,
        session,
        base_url: trimmed_nonempty(payload.api_base_url),
        client_version: trimmed_nonempty(payload.client_version),
        client_content_version_key: trimmed_nonempty(payload.client_content_version_key),
    })
}

fn resolve_legacy_env_handoff() -> Result<Option<ResolvedStartupHandoff>, String> {
    let access_token = env::var("AOP_HANDOFF_ACCESS_TOKEN").ok().and_then(trimmed_nonempty);
    let session_id = env::var("AOP_HANDOFF_SESSION_ID").ok().and_then(trimmed_nonempty);

    if access_token.is_none() && session_id.is_none() {
        return Ok(None);
    }

    let access_token = access_token.ok_or_else(|| {
        "legacy handoff missing AOP_HANDOFF_ACCESS_TOKEN while AOP_HANDOFF_SESSION_ID is set".to_string()
    })?;
    let session_id = session_id.ok_or_else(|| {
        "legacy handoff missing AOP_HANDOFF_SESSION_ID while AOP_HANDOFF_ACCESS_TOKEN is set".to_string()
    })?;

    let expires_unix_ms = env::var("AOP_HANDOFF_EXPIRES_UNIX_MS")
        .ok()
        .and_then(trimmed_nonempty)
        .map(|value| {
            value
                .parse::<u64>()
                .map_err(|_| "AOP_HANDOFF_EXPIRES_UNIX_MS must be an unsigned integer (unix milliseconds)".to_string())
        })
        .transpose()?;

    if let Some(expires) = expires_unix_ms
        && unix_now_millis() > expires
    {
        return Err(format!(
            "legacy handoff payload is expired (AOP_HANDOFF_EXPIRES_UNIX_MS={expires})"
        ));
    }

    let user_id = env::var("AOP_HANDOFF_USER_ID")
        .ok()
        .and_then(trimmed_nonempty)
        .map(|value| {
            value
                .parse::<u64>()
                .map_err(|_| "AOP_HANDOFF_USER_ID must be an unsigned integer".to_string())
        })
        .transpose()?
        .unwrap_or(0);

    let selected_character_id = env::var("AOP_HANDOFF_CHARACTER_ID")
        .ok()
        .and_then(trimmed_nonempty)
        .map(|value| {
            value
                .parse::<u64>()
                .map_err(|_| "AOP_HANDOFF_CHARACTER_ID must be an unsigned integer".to_string())
        })
        .transpose()?
        .filter(|value| *value > 0);

    let session = SessionContext {
        access_token,
        refresh_token: env::var("AOP_HANDOFF_REFRESH_TOKEN")
            .ok()
            .and_then(trimmed_nonempty)
            .unwrap_or_default(),
        session_id,
        user_id,
        display_name: env::var("AOP_HANDOFF_DISPLAY_NAME")
            .ok()
            .and_then(trimmed_nonempty)
            .unwrap_or_else(|| "Handoff User".to_string()),
    };

    Ok(Some(ResolvedStartupHandoff {
        source: "legacy-env".to_string(),
        email: env::var("AOP_HANDOFF_EMAIL").ok().and_then(trimmed_nonempty),
        selected_character_id,
        session,
        base_url: env::var("AOP_HANDOFF_API_BASE_URL").ok().and_then(trimmed_nonempty),
        client_version: env::var("AOP_HANDOFF_CLIENT_VERSION").ok().and_then(trimmed_nonempty),
        client_content_version_key: env::var("AOP_HANDOFF_CLIENT_CONTENT_VERSION_KEY")
            .ok()
            .and_then(trimmed_nonempty),
    }))
}

fn is_auth_http_error(error: &str) -> bool {
    error.contains("HTTP 401") || error.contains("HTTP 403")
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
        shell.status_line = "Loaded external handoff session. Fetching character roster...".to_string();
    } else {
        shell.phase = ShellPhase::Login;
        shell.session = None;
        shell.status_line = "Failed to initialize backend worker from handoff session.".to_string();
    }
}

fn startup_apply_authored_map(mut map: ResMut<CampaignMapSurface>, mut tools: ResMut<MapToolsState>) {
    if !tools.tools_enabled {
        return;
    }
    match validate_and_build_graph(&tools.data) {
        Ok(graph) => {
            apply_graph_to_surface(&mut map, graph);
            tools.validation_errors.clear();
            tools.last_status = "Tools map loaded and validated.".to_string();
        }
        Err(errors) => {
            tools.validation_errors = errors;
            tools.last_status = "Tools map validation failed on startup; using fallback map.".to_string();
        }
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

fn panel_hotkeys(keys: Res<ButtonInput<KeyCode>>, shell: Res<ShellState>, mut panels: ResMut<PanelUiState>) {
    if shell.phase != ShellPhase::CampaignReady {
        return;
    }

    for panel in DOMAIN_PANELS {
        if keys.just_pressed(panel.hotkey()) {
            let currently_open = panels.is_open(panel);
            panels.set_open(panel, !currently_open);
            panels.last_io_status = format!(
                "{} panel {} via {:?}",
                panel.title(),
                if currently_open { "hidden" } else { "opened" },
                panel.hotkey()
            );
        }
    }
}

fn handle_backend_response(shell: &mut ShellState, request_tx: &Sender<BackendRequest>, message: BackendResponse) {
    match message {
        BackendResponse::Login(Ok(session)) => {
            shell.session = Some(session.clone());
            shell.handoff_session_active = false;
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
            if shell.handoff_session_active && is_auth_http_error(&error) {
                shell.phase = ShellPhase::Login;
                shell.request_in_flight = false;
                shell.session = None;
                shell.characters.clear();
                shell.selected_character_id = None;
                shell.handoff_session_active = false;
                shell.status_line = format!("External handoff session was rejected ({error}). Please log in again.");
                return;
            }
            shell.phase = ShellPhase::CharacterSelect;
            shell.request_in_flight = false;
            shell.status_line = format!("Character fetch failed: {error}");
        }
        BackendResponse::Bootstrap(Ok(bootstrap)) => {
            shell.campaign_bootstrap = Some(bootstrap.clone());
            shell.handoff_session_active = false;
            shell.phase = ShellPhase::CampaignReady;
            shell.request_in_flight = false;
            shell.status_line = format!(
                "Entered campaign scene for {} in {}.",
                bootstrap.character_name, bootstrap.level_description
            );
        }
        BackendResponse::Bootstrap(Err(error)) => {
            if shell.handoff_session_active && is_auth_http_error(&error) {
                shell.phase = ShellPhase::Login;
                shell.request_in_flight = false;
                shell.session = None;
                shell.characters.clear();
                shell.selected_character_id = None;
                shell.handoff_session_active = false;
                shell.status_line = format!("External handoff session was rejected ({error}). Please log in again.");
                return;
            }
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
        let size_factor = match settlement.tier {
            SettlementTier::Camp => 0.65,
            SettlementTier::Village => 0.85,
            SettlementTier::Town => 1.0,
            SettlementTier::City => 1.3,
            SettlementTier::Fortress => 1.4,
        };
        gizmos.circle_2d(pos, 5.0 * size_factor * map.zoom.clamp(0.6, 2.2), color);
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

fn apply_graph_to_surface(map: &mut CampaignMapSurface, graph: TravelGraph) {
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
                tier: row.tier,
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

    map.graph = graph;
    map.settlements = settlements;
    map.routes = routes;
}

fn draw_shell_ui(
    mut egui_contexts: EguiContexts,
    mut shell: ResMut<ShellState>,
    config: Res<BackendConfig>,
    bridge: Res<BackendBridge>,
    mut map: ResMut<CampaignMapSurface>,
    mut panels: ResMut<PanelUiState>,
    mut tools: ResMut<MapToolsState>,
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
                    render_campaign_summary(ui, &mut shell, &config, &bridge, &mut map, &mut panels);
                }
            }
        });

    if shell.phase == ShellPhase::CampaignReady {
        render_domain_panels(ctx, &shell, &map, &mut panels);
        render_tools_window(ctx, &mut map, &mut tools);
    }
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
    ui.label("Optional external handoff:");
    ui.label("Preferred: --handoff-file <path> or AOP_HANDOFF_PATH (JSON contract, schema_version=1).");
    ui.label("Fallback: legacy env vars AOP_HANDOFF_ACCESS_TOKEN + AOP_HANDOFF_SESSION_ID.");
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
        shell.handoff_session_active = false;
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
    panels: &mut PanelUiState,
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
    ui.heading("Panel Controls");
    ui.label(
        "Hotkeys: F1 Character, F2 Household, F3 Logistics, F4 Trade, F5 Espionage, F6 Diplomacy, F7 Notifications.",
    );
    ui.horizontal(|ui| {
        if ui.button("Strategist Preset").clicked() {
            panels.apply_preset(LayoutPreset::Strategist);
        }
        if ui.button("Operations Preset").clicked() {
            panels.apply_preset(LayoutPreset::Operations);
        }
        if ui.button("Save Layout").clicked() {
            panels.save_to_disk();
        }
        if ui.button("Load Layout").clicked() {
            panels.load_from_disk();
        }
    });
    ui.label(format!("Layout state: {}", panels.last_io_status));

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

fn render_domain_panels(ctx: &egui::Context, shell: &ShellState, map: &CampaignMapSurface, panels: &mut PanelUiState) {
    render_panel_window(ctx, panels, DomainPanel::Character, |ui| {
        if let Some(bootstrap) = shell.campaign_bootstrap.as_ref() {
            ui.label(format!("Name: {}", bootstrap.character_name));
            ui.label(format!("Character ID: {}", bootstrap.character_id));
            ui.label(format!("Level Surface: {}", bootstrap.level_description));
            ui.label(format!(
                "Spawn: ({}, {})",
                bootstrap.spawn_world_x, bootstrap.spawn_world_y
            ));
        } else {
            ui.label("No active character bootstrap payload.");
        }
    });

    render_panel_window(ctx, panels, DomainPanel::Household, |ui| {
        let visible = map
            .settlements
            .iter()
            .filter(|row| row.fog == FogVisibility::Visible)
            .count();
        let shrouded = map
            .settlements
            .iter()
            .filter(|row| row.fog == FogVisibility::Shrouded)
            .count();
        ui.label("Household dashboard (code-first panel shell).");
        ui.label(format!("Visible holdings: {visible}"));
        ui.label(format!("Peripheral holdings: {shrouded}"));
        if let Some(node) = map.settlements.first() {
            ui.label(format!("Primary seat candidate: {}", node.name));
        }
    });

    render_panel_window(ctx, panels, DomainPanel::Logistics, |ui| {
        ui.label("Army movement status");
        for marker in &map.army_markers {
            ui.label(format!(
                "{}: S{} -> S{} | progress {:.0}%",
                marker.label,
                marker.origin.0,
                marker.destination.0,
                marker.progress * 100.0
            ));
        }
    });

    render_panel_window(ctx, panels, DomainPanel::Trade, |ui| {
        ui.label("Caravan lane status");
        for marker in &map.caravan_markers {
            ui.label(format!(
                "{}: S{} -> S{} | progress {:.0}%",
                marker.label,
                marker.origin.0,
                marker.destination.0,
                marker.progress * 100.0
            ));
        }
        let sea_routes = map.routes.iter().filter(|row| row.is_sea_route).count();
        ui.label(format!("Sea routes monitored: {sea_routes}"));
    });

    render_panel_window(ctx, panels, DomainPanel::Espionage, |ui| {
        let visible = map
            .settlements
            .iter()
            .filter(|row| row.fog == FogVisibility::Visible)
            .count();
        let shrouded = map
            .settlements
            .iter()
            .filter(|row| row.fog == FogVisibility::Shrouded)
            .count();
        let obscured = map
            .settlements
            .iter()
            .filter(|row| row.fog == FogVisibility::Obscured)
            .count();
        ui.label("Fog intelligence posture");
        ui.label(format!("Visible: {visible}"));
        ui.label(format!("Shrouded: {shrouded}"));
        ui.label(format!("Obscured: {obscured}"));
    });

    render_panel_window(ctx, panels, DomainPanel::Diplomacy, |ui| {
        ui.label("Diplomatic route pressure snapshot");
        let land_routes = map.routes.iter().filter(|row| !row.is_sea_route).count();
        let sea_routes = map.routes.iter().filter(|row| row.is_sea_route).count();
        ui.label(format!("Land corridors: {land_routes}"));
        ui.label(format!("Sea corridors: {sea_routes}"));
        if let Some(bootstrap) = shell.campaign_bootstrap.as_ref() {
            ui.label(format!(
                "Current theater: {} ({})",
                bootstrap.level_name, bootstrap.instance_kind
            ));
        }
    });

    let layout_status = panels.last_io_status.clone();
    render_panel_window(ctx, panels, DomainPanel::Notifications, |ui| {
        ui.label("Latest status");
        ui.label(shell.status_line.as_str());
        ui.separator();
        ui.label("Panel layout");
        ui.label(layout_status.as_str());
    });
}

fn render_panel_window<F>(ctx: &egui::Context, panels: &mut PanelUiState, panel: DomainPanel, add_contents: F)
where
    F: FnOnce(&mut egui::Ui),
{
    let mut open = panels.is_open(panel);
    let rect = panels.panel_rect(panel);

    let response = egui::Window::new(panel.title())
        .open(&mut open)
        .default_pos([rect.x, rect.y])
        .default_size([rect.width, rect.height])
        .resizable(true)
        .show(ctx, add_contents);

    panels.set_open(panel, open);
    if let Some(response) = response {
        panels.set_panel_rect_from_egui(panel, response.response.rect);
    }
}

fn render_tools_window(ctx: &egui::Context, map: &mut CampaignMapSurface, tools: &mut MapToolsState) {
    if !tools.tools_enabled {
        return;
    }

    egui::Window::new("Tools Mode - Map Authoring")
        .anchor(egui::Align2::RIGHT_TOP, [-16.0, 16.0])
        .default_size([460.0, 620.0])
        .resizable(true)
        .show(ctx, |ui| {
            ui.label("Role-gated tools mode is active.");
            ui.label("Edit settlements/routes, validate schema, then save authored map JSON.");
            ui.label(format!("Storage: {}", tools.storage_path.display()));
            ui.label(format!("Status: {}", tools.last_status));

            ui.separator();
            ui.heading("Settlement Editor");
            if tools.data.settlements.is_empty() {
                ui.label("No settlements available.");
            } else {
                tools.selected_settlement_index = tools
                    .selected_settlement_index
                    .min(tools.data.settlements.len().saturating_sub(1));
                let selected_label = tools
                    .data
                    .settlements
                    .get(tools.selected_settlement_index)
                    .map(|row| format!("#{} {}", row.id, row.name))
                    .unwrap_or_else(|| "None".to_string());
                egui::ComboBox::from_label("Selected Settlement")
                    .selected_text(selected_label)
                    .show_ui(ui, |ui| {
                        for (index, settlement) in tools.data.settlements.iter().enumerate() {
                            ui.selectable_value(
                                &mut tools.selected_settlement_index,
                                index,
                                format!("#{} {}", settlement.id, settlement.name),
                            );
                        }
                    });

                if let Some(selected) = tools.data.settlements.get_mut(tools.selected_settlement_index) {
                    ui.horizontal(|ui| {
                        ui.label("Name");
                        ui.text_edit_singleline(&mut selected.name);
                    });
                    ui.horizontal(|ui| {
                        ui.label("Kind");
                        egui::ComboBox::from_id_salt("tools-settlement-kind")
                            .selected_text(selected.kind.clone())
                            .show_ui(ui, |ui| {
                                for kind in SETTLEMENT_KIND_OPTIONS {
                                    ui.selectable_value(&mut selected.kind, kind.to_string(), kind);
                                }
                            });
                    });
                    ui.horizontal(|ui| {
                        ui.label("Map X");
                        ui.add(egui::DragValue::new(&mut selected.map_x).range(-200..=200));
                        ui.label("Map Y");
                        ui.add(egui::DragValue::new(&mut selected.map_y).range(-200..=200));
                    });
                }

                ui.horizontal(|ui| {
                    if ui.button("Add Settlement").clicked() {
                        let next_id = tools
                            .data
                            .settlements
                            .iter()
                            .map(|row| row.id)
                            .max()
                            .unwrap_or(0)
                            .saturating_add(1);
                        tools.data.settlements.push(AuthoredSettlement {
                            id: next_id,
                            name: format!("New Settlement {next_id}"),
                            map_x: 0,
                            map_y: 0,
                            kind: default_settlement_kind(),
                        });
                        normalize_authored_map(&mut tools.data);
                        tools.selected_settlement_index = tools
                            .data
                            .settlements
                            .iter()
                            .position(|row| row.id == next_id)
                            .unwrap_or(0);
                        tools.last_status = format!("Added settlement {next_id}");
                    }
                    if ui.button("Delete Selected").clicked() && !tools.data.settlements.is_empty() {
                        let removed = tools.data.settlements.remove(tools.selected_settlement_index);
                        tools.selected_settlement_index = tools
                            .selected_settlement_index
                            .min(tools.data.settlements.len().saturating_sub(1));
                        tools.last_status = format!("Deleted settlement {}", removed.id);
                        tools
                            .data
                            .routes
                            .retain(|row| row.origin != removed.id && row.destination != removed.id);
                    }
                });
            }

            ui.separator();
            ui.heading("Route Editor");
            if tools.data.settlements.len() < 2 {
                ui.label("Need at least two settlements to define routes.");
            } else {
                tools.draft_route_origin_index = tools
                    .draft_route_origin_index
                    .min(tools.data.settlements.len().saturating_sub(1));
                tools.draft_route_destination_index = tools
                    .draft_route_destination_index
                    .min(tools.data.settlements.len().saturating_sub(1));

                egui::ComboBox::from_label("Origin")
                    .selected_text(tools.data.settlements[tools.draft_route_origin_index].name.clone())
                    .show_ui(ui, |ui| {
                        for (index, settlement) in tools.data.settlements.iter().enumerate() {
                            ui.selectable_value(
                                &mut tools.draft_route_origin_index,
                                index,
                                format!("#{} {}", settlement.id, settlement.name),
                            );
                        }
                    });
                egui::ComboBox::from_label("Destination")
                    .selected_text(tools.data.settlements[tools.draft_route_destination_index].name.clone())
                    .show_ui(ui, |ui| {
                        for (index, settlement) in tools.data.settlements.iter().enumerate() {
                            ui.selectable_value(
                                &mut tools.draft_route_destination_index,
                                index,
                                format!("#{} {}", settlement.id, settlement.name),
                            );
                        }
                    });
                ui.horizontal(|ui| {
                    ui.label("Travel Hours");
                    ui.add(egui::DragValue::new(&mut tools.draft_route_travel_hours).range(1..=480));
                    ui.label("Base Risk");
                    ui.add(egui::DragValue::new(&mut tools.draft_route_base_risk).range(0..=10_000));
                });
                ui.checkbox(&mut tools.draft_route_is_sea, "Sea route");
                if ui.button("Add Route").clicked() {
                    if tools.draft_route_origin_index == tools.draft_route_destination_index {
                        tools.last_status = "Cannot create route to same settlement.".to_string();
                    } else {
                        let origin_id = tools.data.settlements[tools.draft_route_origin_index].id;
                        let destination_id = tools.data.settlements[tools.draft_route_destination_index].id;
                        let next_id = tools
                            .data
                            .routes
                            .iter()
                            .map(|row| row.id)
                            .max()
                            .unwrap_or(0)
                            .saturating_add(1);
                        tools.data.routes.push(AuthoredRoute {
                            id: next_id,
                            origin: origin_id,
                            destination: destination_id,
                            travel_hours: tools.draft_route_travel_hours.max(1),
                            base_risk: tools.draft_route_base_risk,
                            is_sea_route: tools.draft_route_is_sea,
                        });
                        normalize_authored_map(&mut tools.data);
                        tools.last_status = format!("Added route {next_id}");
                    }
                }
                ui.collapsing("Current Routes", |ui| {
                    for route in tools.data.routes.iter().take(12) {
                        ui.label(format!(
                            "#{} S{} -> S{} | {}h | risk {} ({}) | sea {}",
                            route.id,
                            route.origin,
                            route.destination,
                            route.travel_hours,
                            route.base_risk,
                            risk_band_label(route.base_risk),
                            route.is_sea_route
                        ));
                    }
                });
            }

            ui.separator();
            ui.heading("Validation and Persistence");
            ui.horizontal(|ui| {
                if ui.button("Validate").clicked() {
                    match validate_and_build_graph(&tools.data) {
                        Ok(graph) => {
                            tools.validation_errors.clear();
                            apply_graph_to_surface(map, graph);
                            tools.last_status = "Validation passed and map applied.".to_string();
                        }
                        Err(errors) => {
                            tools.validation_errors = errors;
                            tools.last_status = "Validation failed.".to_string();
                        }
                    }
                }
                if ui.button("Save").clicked() {
                    match validate_and_build_graph(&tools.data) {
                        Ok(graph) => {
                            tools.validation_errors.clear();
                            apply_graph_to_surface(map, graph);
                            tools.save_to_disk();
                        }
                        Err(errors) => {
                            tools.validation_errors = errors;
                            tools.last_status = "Save blocked by validation errors.".to_string();
                        }
                    }
                }
                if ui.button("Load").clicked() {
                    tools.load_from_disk();
                    match validate_and_build_graph(&tools.data) {
                        Ok(graph) => {
                            tools.validation_errors.clear();
                            apply_graph_to_surface(map, graph);
                            tools.last_status = "Loaded authored map and applied.".to_string();
                        }
                        Err(errors) => {
                            tools.validation_errors = errors;
                            tools.last_status = "Loaded authored map but validation failed.".to_string();
                        }
                    }
                }
            });

            if tools.validation_errors.is_empty() {
                ui.label("Validation: OK");
            } else {
                ui.colored_label(egui::Color32::from_rgb(236, 111, 99), "Validation errors:");
                for row in tools.validation_errors.iter().take(12) {
                    ui.label(format!("- {row}"));
                }
            }
        });
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
    use std::fs;
    use std::path::PathBuf;

    use super::{
        AuthoredMapData, AuthoredRoute, AuthoredSettlement, CharacterSummary, DOMAIN_PANELS, LayoutPreset,
        ProvincePackData, build_graph_from_pack, default_layout_snapshot, extract_error_message, is_auth_http_error,
        parse_startup_options, parse_structured_handoff_payload, resolve_selected_character_id,
        sample_authored_map_data, validate_and_build_graph,
    };

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

    #[test]
    fn layout_snapshot_contains_all_domain_panels() {
        let snapshot = default_layout_snapshot(LayoutPreset::Strategist);
        for panel in DOMAIN_PANELS {
            assert!(snapshot.open.contains_key(panel.key()));
            assert!(snapshot.rects.contains_key(panel.key()));
        }
    }

    #[test]
    fn authored_map_validation_rejects_missing_route_settlement() {
        let invalid = AuthoredMapData {
            settlements: vec![AuthoredSettlement {
                id: 1,
                name: "A".to_string(),
                map_x: 0,
                map_y: 0,
                kind: "village".to_string(),
            }],
            routes: vec![AuthoredRoute {
                id: 7,
                origin: 1,
                destination: 2,
                travel_hours: 12,
                base_risk: 500,
                is_sea_route: false,
            }],
        };

        let errors = validate_and_build_graph(&invalid).expect_err("Expected validation to fail");
        assert!(!errors.is_empty());
    }

    #[test]
    fn authored_map_validation_rejects_invalid_settlement_kind() {
        let invalid = AuthoredMapData {
            settlements: vec![AuthoredSettlement {
                id: 1,
                name: "A".to_string(),
                map_x: 0,
                map_y: 0,
                kind: "metropolis".to_string(),
            }],
            routes: vec![AuthoredRoute {
                id: 7,
                origin: 1,
                destination: 1,
                travel_hours: 12,
                base_risk: 500,
                is_sea_route: false,
            }],
        };
        let errors = validate_and_build_graph(&invalid).expect_err("Expected validation to fail");
        assert!(errors.iter().any(|row| row.contains("invalid kind")));
    }

    #[test]
    fn sample_authored_map_validates_to_graph() {
        let sample = sample_authored_map_data();
        let graph = validate_and_build_graph(&sample).expect("Sample authored map should validate");
        assert!(graph.settlements().count() > 0);
        assert!(graph.routes().count() > 0);
    }

    #[test]
    fn acre_province_pack_builds_graph() {
        let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("..")
            .join("assets/content/provinces/acre/acre_poc_v1.json");
        let payload = fs::read_to_string(path).expect("acre province pack should exist");
        let parsed = serde_json::from_str::<ProvincePackData>(&payload).expect("province pack should parse");
        let graph = build_graph_from_pack(&parsed).expect("province pack graph should validate");
        assert_eq!(graph.settlements().count(), 2);
        assert_eq!(graph.routes().count(), 4);
    }

    #[test]
    fn startup_options_parse_handoff_flags() {
        let options = parse_startup_options(vec![
            "--handoff-file".to_string(),
            "C:/tmp/handoff.json".to_string(),
            "--handoff-json={\"schema_version\":1}".to_string(),
        ]);

        assert_eq!(
            options
                .handoff_file
                .expect("handoff file should be parsed")
                .to_string_lossy(),
            "C:/tmp/handoff.json"
        );
        assert_eq!(
            options.handoff_json.expect("handoff json should be parsed"),
            "{\"schema_version\":1}"
        );
    }

    #[test]
    fn structured_handoff_payload_parses_and_validates() {
        let payload = r#"{
            "schema_version": 1,
            "email": "designer@test.com",
            "access_token": "token-abc",
            "refresh_token": "refresh-xyz",
            "session_id": "session-123",
            "user_id": 77,
            "display_name": "Designer",
            "character_id": 42,
            "api_base_url": "https://example.test/api",
            "client_version": "1.2.3",
            "client_content_version_key": "runtime_v2",
            "expires_unix_ms": 32503680000000
        }"#;

        let handoff = parse_structured_handoff_payload(payload, "test", 1).expect("handoff should parse");
        assert_eq!(handoff.session.session_id, "session-123");
        assert_eq!(handoff.session.user_id, 77);
        assert_eq!(handoff.selected_character_id, Some(42));
        assert_eq!(handoff.base_url.as_deref(), Some("https://example.test/api"));
        assert_eq!(handoff.client_version.as_deref(), Some("1.2.3"));
        assert_eq!(handoff.client_content_version_key.as_deref(), Some("runtime_v2"));
    }

    #[test]
    fn structured_handoff_payload_rejects_missing_required_fields_and_expired_payloads() {
        let missing_session_id = r#"{
            "schema_version": 1,
            "access_token": "token-abc"
        }"#;
        let error = parse_structured_handoff_payload(missing_session_id, "test", 10)
            .expect_err("missing session_id should fail");
        assert!(error.contains("session_id"));

        let expired = r#"{
            "schema_version": 1,
            "access_token": "token-abc",
            "session_id": "session-123",
            "expires_unix_ms": 9
        }"#;
        let error = parse_structured_handoff_payload(expired, "test", 10).expect_err("expired payload should fail");
        assert!(error.contains("expired"));
    }

    #[test]
    fn auth_http_error_detection_catches_401_and_403() {
        assert!(is_auth_http_error("HTTP 401: invalid token"));
        assert!(is_auth_http_error("HTTP 403: forbidden"));
        assert!(!is_auth_http_error("HTTP 502: upstream failed"));
    }
}
