use std::net::SocketAddr;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AppConfig {
    pub bind_addr: String,
    pub service_name: String,
    pub log_level: String,
    pub internal_auth_enabled: bool,
    pub internal_auth_secret: String,
    pub allowed_caller_id: String,
    pub allowed_scopes: String,
    pub required_scope: String,
    pub max_clock_skew_seconds: u64,
    pub replay_window_seconds: u64,
    pub internal_max_body_bytes: usize,
    pub tick_interval_ms: u64,
    pub snapshot_interval_ticks: u64,
    pub max_snapshots_kept: usize,
}

impl AppConfig {
    pub fn from_env() -> Self {
        Self {
            bind_addr: std::env::var("WORLD_SERVICE_BIND_ADDR").unwrap_or_else(|_| "0.0.0.0:8088".to_string()),
            service_name: std::env::var("WORLD_SERVICE_NAME").unwrap_or_else(|_| "world-service".to_string()),
            log_level: std::env::var("WORLD_SERVICE_LOG_LEVEL").unwrap_or_else(|_| "info".to_string()),
            internal_auth_enabled: std::env::var("WORLD_SERVICE_INTERNAL_AUTH_ENABLED")
                .map(|value| value.trim().eq_ignore_ascii_case("true"))
                .unwrap_or(true),
            internal_auth_secret: std::env::var("WORLD_SERVICE_INTERNAL_AUTH_SECRET")
                .unwrap_or_else(|_| "dev-only-change-me".to_string()),
            allowed_caller_id: std::env::var("WORLD_SERVICE_ALLOWED_CALLER_ID")
                .unwrap_or_else(|_| "fastapi-control-plane".to_string()),
            allowed_scopes: std::env::var("WORLD_SERVICE_ALLOWED_SCOPES")
                .unwrap_or_else(|_| "world.control.mutate".to_string()),
            required_scope: std::env::var("WORLD_SERVICE_REQUIRED_SCOPE")
                .unwrap_or_else(|_| "world.control.mutate".to_string()),
            max_clock_skew_seconds: std::env::var("WORLD_SERVICE_MAX_CLOCK_SKEW_SECONDS")
                .ok()
                .and_then(|value| value.parse::<u64>().ok())
                .unwrap_or(90),
            replay_window_seconds: std::env::var("WORLD_SERVICE_REPLAY_WINDOW_SECONDS")
                .ok()
                .and_then(|value| value.parse::<u64>().ok())
                .unwrap_or(300),
            internal_max_body_bytes: std::env::var("WORLD_SERVICE_INTERNAL_MAX_BODY_BYTES")
                .ok()
                .and_then(|value| value.parse::<usize>().ok())
                .unwrap_or(1_048_576),
            tick_interval_ms: std::env::var("WORLD_SERVICE_TICK_INTERVAL_MS")
                .ok()
                .and_then(|value| value.parse::<u64>().ok())
                .unwrap_or(200),
            snapshot_interval_ticks: std::env::var("WORLD_SERVICE_SNAPSHOT_INTERVAL_TICKS")
                .ok()
                .and_then(|value| value.parse::<u64>().ok())
                .unwrap_or(10),
            max_snapshots_kept: std::env::var("WORLD_SERVICE_MAX_SNAPSHOTS_KEPT")
                .ok()
                .and_then(|value| value.parse::<usize>().ok())
                .unwrap_or(64),
        }
    }

    pub fn socket_addr(&self) -> Result<SocketAddr, std::net::AddrParseError> {
        self.bind_addr.parse()
    }

    pub fn allowed_scope_list(&self) -> Vec<String> {
        self.allowed_scopes
            .split(',')
            .map(str::trim)
            .filter(|entry| !entry.is_empty())
            .map(ToString::to_string)
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::AppConfig;

    #[test]
    fn default_bind_address_is_set() {
        let cfg = AppConfig::from_env();
        assert!(!cfg.bind_addr.is_empty());
    }

    #[test]
    fn default_auth_scope_list_is_non_empty() {
        let cfg = AppConfig::from_env();
        assert!(!cfg.allowed_scope_list().is_empty());
    }

    #[test]
    fn default_tick_settings_are_positive() {
        let cfg = AppConfig::from_env();
        assert!(cfg.tick_interval_ms > 0);
        assert!(cfg.snapshot_interval_ticks > 0);
        assert!(cfg.max_snapshots_kept > 0);
    }
}
