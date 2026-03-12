mod auth;
mod config;
mod tick_runner;

use std::io;
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};

use axum::extract::{Path, State};
use axum::http::{HeaderName, StatusCode};
use axum::middleware;
use axum::routing::{get, post};
use axum::{Extension, Json, Router};
use serde::{Deserialize, Serialize};
use sim_core::SIM_SCHEMA_VERSION;
use sim_core::{
    RiskModifiers, RouteEdge, SettlementId, SettlementNode, Tick, TravelEstimate, TravelGraph, TravelPreference,
    sample_levant_travel_graph,
};
use tower_http::request_id::{MakeRequestUuid, PropagateRequestIdLayer, SetRequestIdLayer};
use tower_http::trace::TraceLayer;
use tracing::{info, warn};
use tracing_subscriber::EnvFilter;

use crate::auth::{AuthenticatedServiceCall, ServiceAuthConfig, ServiceAuthState};
use crate::config::AppConfig;
use crate::tick_runner::{
    LogisticsStateSnapshot, TickAdvanceResult, TickMetrics, TickRunner, TickRunnerConfig, TickSnapshot,
    build_move_army_command, build_set_stance_command, build_supply_transfer_command,
};

#[derive(Clone)]
struct AppState {
    config: Arc<AppConfig>,
    started_at_unix: u64,
    tick_runner: Arc<Mutex<TickRunner>>,
    travel_graph: Arc<TravelGraph>,
}

#[derive(Serialize)]
struct HealthResponse {
    status: &'static str,
    service: String,
    version: String,
    sim_schema_version: u32,
}

#[derive(Serialize)]
struct ReadyResponse {
    status: &'static str,
    started_at_unix: u64,
}

#[derive(Serialize)]
struct ConfigResponse {
    bind_addr: String,
    service_name: String,
    log_level: String,
    internal_auth_enabled: bool,
    allowed_caller_id: String,
    required_scope: String,
    max_clock_skew_seconds: u64,
    replay_window_seconds: u64,
    tick_interval_ms: u64,
    snapshot_interval_ticks: u64,
    max_snapshots_kept: usize,
}

#[derive(Debug, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
enum ControlCommandKind {
    IssueMoveArmy {
        army_id: u64,
        origin: u64,
        destination: u64,
    },
    SetFactionStance {
        actor_faction: u64,
        target_faction: u64,
        relation_delta: i32,
    },
    QueueSupplyTransfer {
        from_army: u64,
        to_army: u64,
        food: u32,
        horses: u32,
        materiel: u32,
    },
}

#[derive(Debug, Deserialize)]
struct ControlCommandRequest {
    trace_id: String,
    command: ControlCommandKind,
}

#[derive(Debug, Serialize)]
struct ControlCommandResponse {
    status: &'static str,
    accepted: bool,
    trace_id: String,
    queued_command_type: &'static str,
    queue_depth: usize,
    current_tick: u64,
    caller_service_id: String,
    caller_scope: String,
}

#[derive(Debug, Deserialize)]
struct TickAdvanceRequest {
    now_ms: u64,
}

#[derive(Debug, Serialize)]
struct TickAdvanceResponse {
    status: &'static str,
    ticks_executed: usize,
    current_tick: u64,
    queue_depth: usize,
    metrics: TickMetrics,
    latest_snapshot: Option<TickSnapshot>,
    caller_service_id: String,
    caller_scope: String,
}

#[derive(Debug, Serialize)]
struct TravelMapResponse {
    settlements: Vec<SettlementNode>,
    routes: Vec<RouteEdge>,
    choke_points: Vec<u64>,
}

#[derive(Debug, Serialize)]
struct TravelAdjacencyResponse {
    settlement_id: u64,
    adjacent_settlement_ids: Vec<u64>,
}

#[derive(Debug, Deserialize)]
struct TravelPlanRequest {
    origin_settlement_id: u64,
    destination_settlement_id: u64,
    #[serde(default = "default_travel_preference")]
    preference: TravelPreference,
    #[serde(default)]
    risk_modifiers: Option<RiskModifiers>,
    departure_tick: u64,
    #[serde(default = "default_ticks_per_hour")]
    ticks_per_hour: u32,
}

#[derive(Debug, Serialize)]
struct TravelPlanResponse {
    status: &'static str,
    plan: sim_core::TravelPlan,
    estimate: TravelEstimate,
}

#[derive(Debug, Serialize)]
struct LogisticsStateResponse {
    status: &'static str,
    current_tick: u64,
    state: LogisticsStateSnapshot,
}

fn default_travel_preference() -> TravelPreference {
    TravelPreference::Fastest
}

fn default_ticks_per_hour() -> u32 {
    4
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let config = AppConfig::from_env();
    init_tracing(&config.log_level);

    let addr = config.socket_addr()?;
    let auth_state = build_auth_state(&config)?;
    let tick_runner = TickRunner::new(TickRunnerConfig::new(
        config.tick_interval_ms,
        config.snapshot_interval_ticks,
        config.max_snapshots_kept,
    ));
    let state = AppState {
        config: Arc::new(config),
        started_at_unix: SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs(),
        tick_runner: Arc::new(Mutex::new(tick_runner)),
        travel_graph: Arc::new(sample_levant_travel_graph()),
    };

    let request_id_header = HeaderName::from_static("x-request-id");
    let app = build_router(state, auth_state, request_id_header.clone());

    let listener = tokio::net::TcpListener::bind(addr).await?;
    info!(bind_addr = %addr, "world-service listening");
    axum::serve(listener, app).await?;
    Ok(())
}

fn build_auth_state(config: &AppConfig) -> Result<ServiceAuthState, io::Error> {
    if config.internal_auth_enabled && config.internal_auth_secret == "dev-only-change-me" {
        warn!("WORLD_SERVICE_INTERNAL_AUTH_SECRET is using the default development value; set a strong shared secret");
    }

    ServiceAuthState::new(ServiceAuthConfig {
        enabled: config.internal_auth_enabled,
        shared_secret: config.internal_auth_secret.clone(),
        expected_service_id: config.allowed_caller_id.clone(),
        allowed_scopes: config.allowed_scope_list(),
        required_scope: config.required_scope.clone(),
        max_clock_skew_seconds: config.max_clock_skew_seconds,
        replay_window_seconds: config.replay_window_seconds,
        max_body_bytes: config.internal_max_body_bytes,
    })
    .map_err(io::Error::other)
}

fn build_router(state: AppState, auth_state: ServiceAuthState, request_id_header: HeaderName) -> Router {
    let internal_control_routes = Router::new()
        .route("/internal/control/commands", post(control_command))
        .route("/internal/control/tick", post(advance_ticks))
        .route_layer(middleware::from_fn_with_state(
            auth_state,
            auth::require_internal_service_auth,
        ));

    Router::new()
        .route("/healthz", get(healthz))
        .route("/readyz", get(readyz))
        .route("/config", get(config_endpoint))
        .route("/travel/map", get(travel_map))
        .route("/travel/adjacency/{settlement_id}", get(travel_adjacency))
        .route("/travel/plan", post(travel_plan))
        .route("/logistics/state", get(logistics_state))
        .merge(internal_control_routes)
        .with_state(state)
        .layer(PropagateRequestIdLayer::new(request_id_header.clone()))
        .layer(SetRequestIdLayer::new(request_id_header, MakeRequestUuid))
        .layer(TraceLayer::new_for_http())
}

async fn healthz(State(state): State<AppState>) -> (StatusCode, Json<HealthResponse>) {
    (
        StatusCode::OK,
        Json(HealthResponse {
            status: "ok",
            service: state.config.service_name.clone(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            sim_schema_version: SIM_SCHEMA_VERSION,
        }),
    )
}

async fn readyz(State(state): State<AppState>) -> (StatusCode, Json<ReadyResponse>) {
    (
        StatusCode::OK,
        Json(ReadyResponse {
            status: "ready",
            started_at_unix: state.started_at_unix,
        }),
    )
}

async fn config_endpoint(State(state): State<AppState>) -> (StatusCode, Json<ConfigResponse>) {
    (
        StatusCode::OK,
        Json(ConfigResponse {
            bind_addr: state.config.bind_addr.clone(),
            service_name: state.config.service_name.clone(),
            log_level: state.config.log_level.clone(),
            internal_auth_enabled: state.config.internal_auth_enabled,
            allowed_caller_id: state.config.allowed_caller_id.clone(),
            required_scope: state.config.required_scope.clone(),
            max_clock_skew_seconds: state.config.max_clock_skew_seconds,
            replay_window_seconds: state.config.replay_window_seconds,
            tick_interval_ms: state.config.tick_interval_ms,
            snapshot_interval_ticks: state.config.snapshot_interval_ticks,
            max_snapshots_kept: state.config.max_snapshots_kept,
        }),
    )
}

async fn control_command(
    State(state): State<AppState>,
    Extension(caller): Extension<AuthenticatedServiceCall>,
    Json(payload): Json<ControlCommandRequest>,
) -> (StatusCode, Json<ControlCommandResponse>) {
    let mut runner = state
        .tick_runner
        .lock()
        .expect("tick runner lock should not be poisoned");

    let (queued_command_type, envelope) = match payload.command {
        ControlCommandKind::IssueMoveArmy {
            army_id,
            origin,
            destination,
        } => (
            "issue_move_army",
            build_move_army_command(&payload.trace_id, army_id, origin, destination),
        ),
        ControlCommandKind::SetFactionStance {
            actor_faction,
            target_faction,
            relation_delta,
        } => (
            "set_faction_stance",
            build_set_stance_command(&payload.trace_id, actor_faction, target_faction, relation_delta),
        ),
        ControlCommandKind::QueueSupplyTransfer {
            from_army,
            to_army,
            food,
            horses,
            materiel,
        } => (
            "queue_supply_transfer",
            build_supply_transfer_command(&payload.trace_id, from_army, to_army, food, horses, materiel),
        ),
    };

    runner.queue_command(envelope);
    let queue_depth = runner.queue_depth();
    let current_tick = runner.current_tick().0;

    info!(
        caller_service_id = %caller.service_id,
        caller_scope = %caller.scope,
        trace_id = %payload.trace_id,
        queued_command_type,
        queue_depth,
        current_tick,
        "internal control command queued"
    );

    (
        StatusCode::ACCEPTED,
        Json(ControlCommandResponse {
            status: "accepted",
            accepted: true,
            trace_id: payload.trace_id,
            queued_command_type,
            queue_depth,
            current_tick,
            caller_service_id: caller.service_id,
            caller_scope: caller.scope,
        }),
    )
}

async fn advance_ticks(
    State(state): State<AppState>,
    Extension(caller): Extension<AuthenticatedServiceCall>,
    Json(payload): Json<TickAdvanceRequest>,
) -> (StatusCode, Json<TickAdvanceResponse>) {
    let mut runner = state
        .tick_runner
        .lock()
        .expect("tick runner lock should not be poisoned");
    let TickAdvanceResult {
        ticks_executed,
        current_tick,
        queue_depth,
        metrics,
        latest_snapshot,
    } = runner.run_due_ticks(payload.now_ms);

    info!(
        caller_service_id = %caller.service_id,
        caller_scope = %caller.scope,
        ticks_executed,
        current_tick = current_tick.0,
        queue_depth,
        "internal tick advance executed"
    );

    (
        StatusCode::ACCEPTED,
        Json(TickAdvanceResponse {
            status: "accepted",
            ticks_executed,
            current_tick: current_tick.0,
            queue_depth,
            metrics,
            latest_snapshot,
            caller_service_id: caller.service_id,
            caller_scope: caller.scope,
        }),
    )
}

async fn travel_map(State(state): State<AppState>) -> (StatusCode, Json<TravelMapResponse>) {
    let settlements = state.travel_graph.settlements().cloned().collect();
    let routes = state.travel_graph.routes().cloned().collect();
    let choke_points = state.travel_graph.choke_points().into_iter().map(|row| row.0).collect();

    (
        StatusCode::OK,
        Json(TravelMapResponse {
            settlements,
            routes,
            choke_points,
        }),
    )
}

async fn travel_adjacency(
    State(state): State<AppState>,
    Path(settlement_id): Path<u64>,
) -> (StatusCode, Json<TravelAdjacencyResponse>) {
    let adjacent = state
        .travel_graph
        .adjacent_settlements(SettlementId(settlement_id))
        .into_iter()
        .map(|row| row.0)
        .collect();

    (
        StatusCode::OK,
        Json(TravelAdjacencyResponse {
            settlement_id,
            adjacent_settlement_ids: adjacent,
        }),
    )
}

async fn travel_plan(
    State(state): State<AppState>,
    Json(payload): Json<TravelPlanRequest>,
) -> (StatusCode, Json<TravelPlanResponse>) {
    let origin = SettlementId(payload.origin_settlement_id);
    let destination = SettlementId(payload.destination_settlement_id);
    let modifiers = payload.risk_modifiers.unwrap_or_else(RiskModifiers::neutral);

    let Some(plan) = state
        .travel_graph
        .plan_route(origin, destination, payload.preference, modifiers)
    else {
        return (
            StatusCode::NOT_FOUND,
            Json(TravelPlanResponse {
                status: "route_not_found",
                plan: sim_core::TravelPlan {
                    settlements: Vec::new(),
                    route_ids: Vec::new(),
                    total_travel_hours: 0,
                    total_risk: 0,
                },
                estimate: TravelEstimate {
                    departure_tick: Tick(payload.departure_tick),
                    arrival_tick: Tick(payload.departure_tick),
                    total_travel_hours: 0,
                    total_risk: 0,
                },
            }),
        );
    };

    let estimate = state
        .travel_graph
        .estimate_arrival(Tick(payload.departure_tick), &plan, payload.ticks_per_hour);

    (
        StatusCode::OK,
        Json(TravelPlanResponse {
            status: "ok",
            plan,
            estimate,
        }),
    )
}

async fn logistics_state(State(state): State<AppState>) -> (StatusCode, Json<LogisticsStateResponse>) {
    let runner = state
        .tick_runner
        .lock()
        .expect("tick runner lock should not be poisoned");

    (
        StatusCode::OK,
        Json(LogisticsStateResponse {
            status: "ok",
            current_tick: runner.current_tick().0,
            state: runner.logistics_state(),
        }),
    )
}

fn init_tracing(log_level: &str) {
    let filter = EnvFilter::try_new(log_level)
        .or_else(|_| EnvFilter::try_new("info"))
        .expect("fallback log filter should always parse");

    tracing_subscriber::fmt()
        .with_env_filter(filter)
        .json()
        .with_current_span(true)
        .with_span_list(true)
        .init();
}

#[cfg(test)]
mod tests {
    use std::sync::Arc;
    use std::time::{SystemTime, UNIX_EPOCH};

    use axum::body::{Body, to_bytes};
    use axum::http::{HeaderName, Request, StatusCode};
    use tower::ServiceExt;

    use crate::auth::{
        HEADER_BODY_SHA256, HEADER_NONCE, HEADER_SCOPE, HEADER_SERVICE_ID, HEADER_SIGNATURE, HEADER_TIMESTAMP,
        SigningContract, sign_request,
    };
    use crate::config::AppConfig;
    use crate::tick_runner::{TickRunner, TickRunnerConfig};
    use crate::{AppState, build_auth_state, build_router};

    fn test_config() -> AppConfig {
        AppConfig {
            bind_addr: "127.0.0.1:8088".to_string(),
            service_name: "world-service".to_string(),
            log_level: "info".to_string(),
            internal_auth_enabled: true,
            internal_auth_secret: "integration-secret".to_string(),
            allowed_caller_id: "fastapi-control-plane".to_string(),
            allowed_scopes: "world.control.mutate".to_string(),
            required_scope: "world.control.mutate".to_string(),
            max_clock_skew_seconds: 120,
            replay_window_seconds: 600,
            internal_max_body_bytes: 64 * 1024,
            tick_interval_ms: 100,
            snapshot_interval_ticks: 2,
            max_snapshots_kept: 16,
        }
    }

    fn test_app() -> axum::Router {
        let config = test_config();
        let auth_state = build_auth_state(&config).expect("auth state should build");
        let tick_runner = TickRunner::new(TickRunnerConfig::new(
            config.tick_interval_ms,
            config.snapshot_interval_ticks,
            config.max_snapshots_kept,
        ));
        let state = AppState {
            config: Arc::new(config),
            started_at_unix: 1_700_000_000,
            tick_runner: Arc::new(std::sync::Mutex::new(tick_runner)),
            travel_graph: Arc::new(sim_core::sample_levant_travel_graph()),
        };
        build_router(state, auth_state, HeaderName::from_static("x-request-id"))
    }

    fn signed_json_request(path: &str, nonce: &str, body: &str) -> Request<Body> {
        let method = "POST";
        let now_unix = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("time should be valid")
            .as_secs();

        let (body_hash, signature) = sign_request(
            &SigningContract {
                secret: "integration-secret",
                method,
                path_and_query: path,
                service_id: "fastapi-control-plane",
                scope: "world.control.mutate",
                timestamp_unix: now_unix,
                nonce,
            },
            body.as_bytes(),
        );

        Request::builder()
            .method(method)
            .uri(path)
            .header("content-type", "application/json")
            .header(HEADER_SERVICE_ID, "fastapi-control-plane")
            .header(HEADER_SCOPE, "world.control.mutate")
            .header(HEADER_TIMESTAMP, now_unix.to_string())
            .header(HEADER_NONCE, nonce)
            .header(HEADER_BODY_SHA256, body_hash)
            .header(HEADER_SIGNATURE, signature)
            .body(Body::from(body.to_string()))
            .expect("request should build")
    }

    #[tokio::test]
    async fn internal_control_endpoint_rejects_unsigned_requests() {
        let app = test_app();

        let response = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/internal/control/commands")
                    .header("content-type", "application/json")
                    .body(Body::from(
                        r#"{"trace_id":"trace-a","command":{"type":"set_faction_stance","actor_faction":1,"target_faction":2,"relation_delta":3}}"#,
                    ))
                    .expect("request should build"),
            )
            .await
            .expect("response should resolve");

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn internal_control_endpoint_accepts_signed_requests() {
        let app = test_app();
        let body = r#"{"trace_id":"trace-a","command":{"type":"set_faction_stance","actor_faction":1,"target_faction":2,"relation_delta":3}}"#;
        let response = app
            .oneshot(signed_json_request("/internal/control/commands", "nonce-accept", body))
            .await
            .expect("response should resolve");

        assert_eq!(response.status(), StatusCode::ACCEPTED);
    }

    #[tokio::test]
    async fn internal_control_endpoint_blocks_replay_nonce() {
        let app = test_app();
        let body = r#"{"trace_id":"trace-a","command":{"type":"set_faction_stance","actor_faction":1,"target_faction":2,"relation_delta":3}}"#;

        let first = app
            .clone()
            .oneshot(signed_json_request("/internal/control/commands", "nonce-replay", body))
            .await
            .expect("first response should resolve");
        assert_eq!(first.status(), StatusCode::ACCEPTED);

        let replay = app
            .oneshot(signed_json_request("/internal/control/commands", "nonce-replay", body))
            .await
            .expect("replay response should resolve");
        assert_eq!(replay.status(), StatusCode::CONFLICT);
    }

    #[tokio::test]
    async fn internal_tick_endpoint_advances_runner() {
        let app = test_app();

        let command_body =
            r#"{"trace_id":"trace-b","command":{"type":"issue_move_army","army_id":7,"origin":1,"destination":2}}"#;
        let queued = app
            .clone()
            .oneshot(signed_json_request(
                "/internal/control/commands",
                "nonce-queue",
                command_body,
            ))
            .await
            .expect("queue response should resolve");
        assert_eq!(queued.status(), StatusCode::ACCEPTED);

        let tick_response = app
            .oneshot(signed_json_request(
                "/internal/control/tick",
                "nonce-tick",
                r#"{"now_ms":0}"#,
            ))
            .await
            .expect("tick response should resolve");
        assert_eq!(tick_response.status(), StatusCode::ACCEPTED);

        let bytes = to_bytes(tick_response.into_body(), usize::MAX)
            .await
            .expect("response body should decode");
        let payload: serde_json::Value = serde_json::from_slice(&bytes).expect("valid json body");

        assert_eq!(payload["ticks_executed"], 1);
        assert_eq!(payload["current_tick"], 1);
    }

    #[tokio::test]
    async fn travel_plan_endpoint_returns_deterministic_route() {
        let app = test_app();

        let response = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/travel/plan")
                    .header("content-type", "application/json")
                    .body(Body::from(
                        r#"{"origin_settlement_id":1,"destination_settlement_id":5,"preference":"fastest","departure_tick":100,"ticks_per_hour":4}"#,
                    ))
                    .expect("request should build"),
            )
            .await
            .expect("response should resolve");

        assert_eq!(response.status(), StatusCode::OK);

        let bytes = to_bytes(response.into_body(), usize::MAX)
            .await
            .expect("response body should decode");
        let payload: serde_json::Value = serde_json::from_slice(&bytes).expect("valid json body");

        assert_eq!(payload["status"], "ok");
        assert_eq!(payload["plan"]["settlements"], serde_json::json!([1, 2, 3, 4, 5]));
        assert_eq!(payload["estimate"]["arrival_tick"], 240);
    }

    #[tokio::test]
    async fn logistics_state_reflects_transfer_after_tick() {
        let app = test_app();

        let queue_transfer_body = r#"{"trace_id":"trace-logistics","command":{"type":"queue_supply_transfer","from_army":7,"to_army":8,"food":12,"horses":0,"materiel":0}}"#;
        let queued = app
            .clone()
            .oneshot(signed_json_request(
                "/internal/control/commands",
                "nonce-logistics-queue",
                queue_transfer_body,
            ))
            .await
            .expect("queue response should resolve");
        assert_eq!(queued.status(), StatusCode::ACCEPTED);

        let ticked = app
            .clone()
            .oneshot(signed_json_request(
                "/internal/control/tick",
                "nonce-logistics-tick",
                r#"{"now_ms":0}"#,
            ))
            .await
            .expect("tick response should resolve");
        assert_eq!(ticked.status(), StatusCode::ACCEPTED);

        let state_response = app
            .oneshot(
                Request::builder()
                    .method("GET")
                    .uri("/logistics/state")
                    .body(Body::empty())
                    .expect("request should build"),
            )
            .await
            .expect("state response should resolve");
        assert_eq!(state_response.status(), StatusCode::OK);

        let bytes = to_bytes(state_response.into_body(), usize::MAX)
            .await
            .expect("response body should decode");
        let payload: serde_json::Value = serde_json::from_slice(&bytes).expect("valid json body");

        let army8 = payload["state"]["armies"]
            .as_array()
            .expect("armies should be array")
            .iter()
            .find(|row| row["army_id"] == 8)
            .expect("army 8 should exist");

        assert!(army8["stock"]["food"].as_u64().unwrap_or(0) >= 15);
    }
}
