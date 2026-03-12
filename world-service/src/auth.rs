use std::collections::{HashMap, HashSet};
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};

use axum::Json;
use axum::body::{Body, to_bytes};
use axum::extract::{Request, State};
use axum::http::{HeaderMap, StatusCode};
use axum::middleware::Next;
use axum::response::{IntoResponse, Response};
use hmac::{Hmac, Mac};
use serde::Serialize;
use sha2::{Digest, Sha256};
use tracing::{info, warn};

type HmacSha256 = Hmac<Sha256>;

pub const HEADER_SERVICE_ID: &str = "x-aop-service-id";
pub const HEADER_SCOPE: &str = "x-aop-scope";
pub const HEADER_TIMESTAMP: &str = "x-aop-timestamp";
pub const HEADER_NONCE: &str = "x-aop-nonce";
pub const HEADER_BODY_SHA256: &str = "x-aop-body-sha256";
pub const HEADER_SIGNATURE: &str = "x-aop-signature";

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ServiceAuthConfig {
    pub enabled: bool,
    pub shared_secret: String,
    pub expected_service_id: String,
    pub allowed_scopes: Vec<String>,
    pub required_scope: String,
    pub max_clock_skew_seconds: u64,
    pub replay_window_seconds: u64,
    pub max_body_bytes: usize,
}

impl ServiceAuthConfig {
    pub fn validate(&self) -> Result<(), String> {
        if !self.enabled {
            return Ok(());
        }
        if self.shared_secret.trim().is_empty() {
            return Err("WORLD_SERVICE_INTERNAL_AUTH_SECRET must not be empty when auth is enabled".to_string());
        }
        if self.expected_service_id.trim().is_empty() {
            return Err("WORLD_SERVICE_ALLOWED_CALLER_ID must not be empty when auth is enabled".to_string());
        }
        if self.required_scope.trim().is_empty() {
            return Err("WORLD_SERVICE_REQUIRED_SCOPE must not be empty when auth is enabled".to_string());
        }
        if self.allowed_scopes.is_empty() {
            return Err(
                "WORLD_SERVICE_ALLOWED_SCOPES must include at least one scope when auth is enabled".to_string(),
            );
        }
        if self.max_clock_skew_seconds == 0 {
            return Err("WORLD_SERVICE_MAX_CLOCK_SKEW_SECONDS must be greater than zero".to_string());
        }
        if self.replay_window_seconds == 0 {
            return Err("WORLD_SERVICE_REPLAY_WINDOW_SECONDS must be greater than zero".to_string());
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AuthenticatedServiceCall {
    pub service_id: String,
    pub scope: String,
    pub timestamp_unix: u64,
    pub nonce: String,
}

#[derive(Clone)]
pub struct ServiceAuthState {
    enabled: bool,
    shared_secret: Arc<str>,
    expected_service_id: Arc<str>,
    allowed_scopes: Arc<HashSet<String>>,
    required_scope: Arc<str>,
    max_clock_skew_seconds: u64,
    replay_window_seconds: u64,
    max_body_bytes: usize,
    replay_cache: ReplayCache,
}

impl ServiceAuthState {
    pub fn new(config: ServiceAuthConfig) -> Result<Self, String> {
        config.validate()?;
        let mut normalized_scopes = HashSet::new();
        for scope in config.allowed_scopes {
            let trimmed = scope.trim();
            if !trimmed.is_empty() {
                normalized_scopes.insert(trimmed.to_string());
            }
        }
        if config.enabled && normalized_scopes.is_empty() {
            return Err("WORLD_SERVICE_ALLOWED_SCOPES resolved to zero non-empty scopes".to_string());
        }

        Ok(Self {
            enabled: config.enabled,
            shared_secret: Arc::from(config.shared_secret),
            expected_service_id: Arc::from(config.expected_service_id),
            allowed_scopes: Arc::new(normalized_scopes),
            required_scope: Arc::from(config.required_scope),
            max_clock_skew_seconds: config.max_clock_skew_seconds,
            replay_window_seconds: config.replay_window_seconds,
            max_body_bytes: config.max_body_bytes,
            replay_cache: ReplayCache::new(),
        })
    }
}

#[derive(Clone, Default)]
struct ReplayCache {
    // key format: "{service_id}:{nonce}", value: expiration unix second
    entries: Arc<Mutex<HashMap<String, u64>>>,
}

impl ReplayCache {
    fn new() -> Self {
        Self::default()
    }

    fn mark_if_fresh(&self, service_id: &str, nonce: &str, now_unix: u64, replay_window_seconds: u64) -> bool {
        let mut guard = self.entries.lock().expect("replay cache poisoned");
        guard.retain(|_, expires_at| *expires_at > now_unix);

        let key = format!("{service_id}:{nonce}");
        if guard.contains_key(&key) {
            return false;
        }

        guard.insert(key, now_unix + replay_window_seconds);
        true
    }
}

#[derive(Debug)]
struct Reject {
    status: StatusCode,
    code: &'static str,
    message: &'static str,
}

#[derive(Serialize)]
struct RejectEnvelope<'a> {
    error: RejectBody<'a>,
}

#[derive(Serialize)]
struct RejectBody<'a> {
    code: &'a str,
    message: &'a str,
}

impl Reject {
    fn into_response(self) -> Response {
        (
            self.status,
            Json(RejectEnvelope {
                error: RejectBody {
                    code: self.code,
                    message: self.message,
                },
            }),
        )
            .into_response()
    }
}

pub async fn require_internal_service_auth(
    State(state): State<ServiceAuthState>,
    request: Request,
    next: Next,
) -> Response {
    if !state.enabled {
        return next.run(request).await;
    }

    let (parts, body) = request.into_parts();
    let method = parts.method.as_str().to_ascii_uppercase();
    let path_and_query = parts
        .uri
        .path_and_query()
        .map(|value| value.as_str().to_string())
        .unwrap_or_else(|| parts.uri.path().to_string());

    let body_bytes = match to_bytes(body, state.max_body_bytes).await {
        Ok(bytes) => bytes,
        Err(_) => {
            warn!(path = %path_and_query, "internal auth rejected: body too large");
            return Reject {
                status: StatusCode::PAYLOAD_TOO_LARGE,
                code: "payload_too_large",
                message: "request body exceeds allowed size",
            }
            .into_response();
        }
    };

    let verification = verify_request(&state, &parts.headers, &method, &path_and_query, body_bytes.as_ref());

    let claims = match verification {
        Ok(value) => value,
        Err(reject) => {
            warn!(
                path = %path_and_query,
                code = reject.code,
                "internal auth rejected"
            );
            return reject.into_response();
        }
    };

    let now_unix = now_unix_seconds();
    if !state
        .replay_cache
        .mark_if_fresh(&claims.service_id, &claims.nonce, now_unix, state.replay_window_seconds)
    {
        warn!(
            path = %path_and_query,
            service_id = %claims.service_id,
            nonce = %claims.nonce,
            "internal auth rejected: replay detected"
        );
        return Reject {
            status: StatusCode::CONFLICT,
            code: "replay_detected",
            message: "nonce has already been used",
        }
        .into_response();
    }

    info!(
        path = %path_and_query,
        service_id = %claims.service_id,
        scope = %claims.scope,
        nonce = %claims.nonce,
        timestamp_unix = claims.timestamp_unix,
        "internal privileged call authorized"
    );

    let mut request = Request::from_parts(parts, Body::from(body_bytes));
    request.extensions_mut().insert(claims);
    next.run(request).await
}

fn verify_request(
    state: &ServiceAuthState,
    headers: &HeaderMap,
    method: &str,
    path_and_query: &str,
    body: &[u8],
) -> Result<AuthenticatedServiceCall, Reject> {
    let service_id = header_string(headers, HEADER_SERVICE_ID)?;
    if service_id != state.expected_service_id.as_ref() {
        return Err(Reject {
            status: StatusCode::UNAUTHORIZED,
            code: "invalid_service_id",
            message: "service id is not authorized",
        });
    }

    let scope = header_string(headers, HEADER_SCOPE)?;
    if !state.allowed_scopes.contains(scope.as_str()) {
        return Err(Reject {
            status: StatusCode::FORBIDDEN,
            code: "scope_not_allowed",
            message: "service scope is not allowed",
        });
    }
    if scope != state.required_scope.as_ref() {
        return Err(Reject {
            status: StatusCode::FORBIDDEN,
            code: "insufficient_scope",
            message: "service scope does not satisfy endpoint requirement",
        });
    }

    let timestamp_raw = header_string(headers, HEADER_TIMESTAMP)?;
    let timestamp_unix = timestamp_raw.parse::<u64>().map_err(|_| Reject {
        status: StatusCode::UNAUTHORIZED,
        code: "invalid_timestamp",
        message: "timestamp must be unix seconds",
    })?;

    let now_unix = now_unix_seconds();
    if now_unix.abs_diff(timestamp_unix) > state.max_clock_skew_seconds {
        return Err(Reject {
            status: StatusCode::UNAUTHORIZED,
            code: "stale_timestamp",
            message: "timestamp outside accepted clock skew",
        });
    }

    let nonce = header_string(headers, HEADER_NONCE)?;
    let body_hash = header_string(headers, HEADER_BODY_SHA256)?;
    let computed_hash = sha256_hex(body);
    if body_hash != computed_hash {
        return Err(Reject {
            status: StatusCode::UNAUTHORIZED,
            code: "body_hash_mismatch",
            message: "body hash does not match request payload",
        });
    }

    let signature = header_string(headers, HEADER_SIGNATURE)?;
    let canonical = canonical_payload(
        method,
        path_and_query,
        &service_id,
        &scope,
        timestamp_unix,
        &nonce,
        &body_hash,
    );

    if !verify_signature(state.shared_secret.as_ref(), &canonical, &signature) {
        return Err(Reject {
            status: StatusCode::UNAUTHORIZED,
            code: "invalid_signature",
            message: "request signature is invalid",
        });
    }

    Ok(AuthenticatedServiceCall {
        service_id,
        scope,
        timestamp_unix,
        nonce,
    })
}

fn header_string(headers: &HeaderMap, name: &str) -> Result<String, Reject> {
    let value = headers.get(name).ok_or(Reject {
        status: StatusCode::UNAUTHORIZED,
        code: "missing_header",
        message: "required service auth header is missing",
    })?;

    let value = value.to_str().map_err(|_| Reject {
        status: StatusCode::UNAUTHORIZED,
        code: "invalid_header",
        message: "service auth header must be valid utf-8",
    })?;

    let trimmed = value.trim();
    if trimmed.is_empty() {
        return Err(Reject {
            status: StatusCode::UNAUTHORIZED,
            code: "empty_header",
            message: "service auth header must not be empty",
        });
    }

    Ok(trimmed.to_string())
}

fn now_unix_seconds() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("current time should be after unix epoch")
        .as_secs()
}

fn sha256_hex(body: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(body);
    hex::encode(hasher.finalize())
}

fn canonical_payload(
    method: &str,
    path_and_query: &str,
    service_id: &str,
    scope: &str,
    timestamp_unix: u64,
    nonce: &str,
    body_hash: &str,
) -> String {
    format!("{method}\n{path_and_query}\n{service_id}\n{scope}\n{timestamp_unix}\n{nonce}\n{body_hash}")
}

fn verify_signature(secret: &str, payload: &str, provided_signature: &str) -> bool {
    let provided = match hex::decode(provided_signature) {
        Ok(value) => value,
        Err(_) => return false,
    };

    let mut mac =
        HmacSha256::new_from_slice(secret.as_bytes()).expect("hmac can be initialized with arbitrary key length");
    mac.update(payload.as_bytes());
    mac.verify_slice(&provided).is_ok()
}

#[cfg(test)]
pub struct SigningContract<'a> {
    pub secret: &'a str,
    pub method: &'a str,
    pub path_and_query: &'a str,
    pub service_id: &'a str,
    pub scope: &'a str,
    pub timestamp_unix: u64,
    pub nonce: &'a str,
}

#[cfg(test)]
pub fn sign_request(contract: &SigningContract<'_>, body: &[u8]) -> (String, String) {
    let body_hash = sha256_hex(body);
    let canonical = canonical_payload(
        contract.method,
        contract.path_and_query,
        contract.service_id,
        contract.scope,
        contract.timestamp_unix,
        contract.nonce,
        &body_hash,
    );

    let mut mac = HmacSha256::new_from_slice(contract.secret.as_bytes())
        .expect("hmac can be initialized with arbitrary key length");
    mac.update(canonical.as_bytes());
    let signature = hex::encode(mac.finalize().into_bytes());

    (body_hash, signature)
}

#[cfg(test)]
mod tests {
    use std::time::{SystemTime, UNIX_EPOCH};

    use super::{
        HEADER_BODY_SHA256, HEADER_NONCE, HEADER_SCOPE, HEADER_SERVICE_ID, HEADER_SIGNATURE, HEADER_TIMESTAMP,
    };
    use super::{ServiceAuthConfig, ServiceAuthState, SigningContract, sign_request, verify_request};
    use axum::http::HeaderMap;

    fn test_state() -> ServiceAuthState {
        ServiceAuthState::new(ServiceAuthConfig {
            enabled: true,
            shared_secret: "integration-secret".to_string(),
            expected_service_id: "fastapi-control-plane".to_string(),
            allowed_scopes: vec!["world.control.mutate".to_string()],
            required_scope: "world.control.mutate".to_string(),
            max_clock_skew_seconds: 90,
            replay_window_seconds: 300,
            max_body_bytes: 1024 * 1024,
        })
        .expect("state should build")
    }

    #[test]
    fn signature_verification_accepts_valid_contract() {
        let state = test_state();
        let method = "POST";
        let path = "/internal/control/commands";
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("time should be valid")
            .as_secs();
        let nonce = "nonce-1";
        let body = br#"{"command":"tick"}"#;

        let (body_hash, signature) = sign_request(
            &SigningContract {
                secret: "integration-secret",
                method,
                path_and_query: path,
                service_id: "fastapi-control-plane",
                scope: "world.control.mutate",
                timestamp_unix: timestamp,
                nonce,
            },
            body,
        );

        let mut headers = HeaderMap::new();
        headers.insert(HEADER_SERVICE_ID, "fastapi-control-plane".parse().unwrap());
        headers.insert(HEADER_SCOPE, "world.control.mutate".parse().unwrap());
        headers.insert(HEADER_TIMESTAMP, timestamp.to_string().parse().unwrap());
        headers.insert(HEADER_NONCE, nonce.parse().unwrap());
        headers.insert(HEADER_BODY_SHA256, body_hash.parse().unwrap());
        headers.insert(HEADER_SIGNATURE, signature.parse().unwrap());

        let result = verify_request(&state, &headers, method, path, body).expect("request should verify");
        assert_eq!(result.service_id, "fastapi-control-plane");
        assert_eq!(result.scope, "world.control.mutate");
    }

    #[test]
    fn signature_verification_rejects_tampered_body() {
        let state = test_state();
        let method = "POST";
        let path = "/internal/control/commands";
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("time should be valid")
            .as_secs();
        let nonce = "nonce-2";
        let body = br#"{"command":"tick"}"#;
        let tampered = br#"{"command":"tick-now"}"#;

        let (body_hash, signature) = sign_request(
            &SigningContract {
                secret: "integration-secret",
                method,
                path_and_query: path,
                service_id: "fastapi-control-plane",
                scope: "world.control.mutate",
                timestamp_unix: timestamp,
                nonce,
            },
            body,
        );

        let mut headers = HeaderMap::new();
        headers.insert(HEADER_SERVICE_ID, "fastapi-control-plane".parse().unwrap());
        headers.insert(HEADER_SCOPE, "world.control.mutate".parse().unwrap());
        headers.insert(HEADER_TIMESTAMP, timestamp.to_string().parse().unwrap());
        headers.insert(HEADER_NONCE, nonce.parse().unwrap());
        headers.insert(HEADER_BODY_SHA256, body_hash.parse().unwrap());
        headers.insert(HEADER_SIGNATURE, signature.parse().unwrap());

        let reject = verify_request(&state, &headers, method, path, tampered).expect_err("tampered body must fail");
        assert_eq!(reject.code, "body_hash_mismatch");
    }
}
