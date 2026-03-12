mod config;

use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};

use axum::extract::State;
use axum::http::{HeaderName, StatusCode};
use axum::routing::get;
use axum::{Json, Router};
use serde::Serialize;
use sim_core::SIM_SCHEMA_VERSION;
use tower_http::request_id::{MakeRequestUuid, PropagateRequestIdLayer, SetRequestIdLayer};
use tower_http::trace::TraceLayer;
use tracing::info;
use tracing_subscriber::EnvFilter;

use crate::config::AppConfig;

#[derive(Clone)]
struct AppState {
    config: Arc<AppConfig>,
    started_at_unix: u64,
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
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let config = AppConfig::from_env();
    init_tracing(&config.log_level);

    let addr = config.socket_addr()?;
    let state = AppState {
        config: Arc::new(config),
        started_at_unix: SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs(),
    };

    let request_id_header = HeaderName::from_static("x-request-id");

    let app = Router::new()
        .route("/healthz", get(healthz))
        .route("/readyz", get(readyz))
        .route("/config", get(config_endpoint))
        .with_state(state)
        .layer(PropagateRequestIdLayer::new(request_id_header.clone()))
        .layer(SetRequestIdLayer::new(request_id_header, MakeRequestUuid))
        .layer(TraceLayer::new_for_http());

    let listener = tokio::net::TcpListener::bind(addr).await?;
    info!(bind_addr = %addr, "world-service listening");
    axum::serve(listener, app).await?;
    Ok(())
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
