use std::net::SocketAddr;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AppConfig {
    pub bind_addr: String,
    pub service_name: String,
    pub log_level: String,
}

impl AppConfig {
    pub fn from_env() -> Self {
        Self {
            bind_addr: std::env::var("WORLD_SERVICE_BIND_ADDR").unwrap_or_else(|_| "0.0.0.0:8088".to_string()),
            service_name: std::env::var("WORLD_SERVICE_NAME").unwrap_or_else(|_| "world-service".to_string()),
            log_level: std::env::var("WORLD_SERVICE_LOG_LEVEL").unwrap_or_else(|_| "info".to_string()),
        }
    }

    pub fn socket_addr(&self) -> Result<SocketAddr, std::net::AddrParseError> {
        self.bind_addr.parse()
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
}
