from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    jwt_secret: str
    jwt_issuer: str = "children-of-ikphelion"
    jwt_audience: str = "children-of-ikphelion-client"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 30
    jwt_refresh_ttl_days_admin: int = 7

    ops_api_token: str
    version_grace_minutes_default: int = 5
    publish_drain_enabled: bool = True
    publish_drain_max_concurrent: int = 1
    content_feature_phase: str = "drain_enforced"
    security_feature_phase: str = "hardened"
    request_rate_limit_enabled: bool = True
    cors_allowed_origins: str = ""
    max_request_body_bytes: int = 1048576
    auth_rate_limit_window_seconds: int = 60
    auth_rate_limit_max_attempts_per_ip: int = 12
    auth_rate_limit_max_attempts_per_account: int = 8
    auth_rate_limit_lockout_seconds: int = 300
    chat_write_rate_limit_window_seconds: int = 10
    chat_write_rate_limit_max_per_ip: int = 40
    chat_write_rate_limit_max_per_account: int = 30
    chat_write_rate_limit_lockout_seconds: int = 30
    runtime_gameplay_config_path: str = "/app/runtime/gameplay_config.json"
    runtime_gameplay_staged_config_path: str = "/app/runtime/gameplay_config.staged.json"
    runtime_gameplay_backup_config_path: str = "/app/runtime/gameplay_config.backup.json"
    runtime_gameplay_signature_pin: str = ""
    github_publish_enabled: bool = False
    github_repo_owner: str = ""
    github_repo_name: str = ""
    github_default_branch: str = "main"
    github_token: str = ""
    github_release_workflow: str = "release.yml"
    github_backend_workflow: str = "deploy-backend.yml"
    world_service_base_url: str = "http://127.0.0.1:8088"
    world_service_caller_id: str = "fastapi-control-plane"
    world_service_scope: str = "world.control.mutate"
    world_service_auth_secret: str = "dev-only-change-me"
    world_service_request_timeout_seconds: float = 5.0

    db_host: str
    db_port: int = 5432
    db_name: str = "karaxas"
    db_user: str
    db_password: str
    db_sslmode: str = "require"
    db_connect_timeout: int = 5

    @property
    def database_url(self) -> str:
        sslmode = (self.db_sslmode or "").strip().lower()
        if sslmode not in {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}:
            sslmode = "require"
        if self.db_host.startswith("/cloudsql/"):
            return (
                f"postgresql+psycopg://{self.db_user}:{self.db_password}"
                f"@/{self.db_name}?host={self.db_host}&connect_timeout={self.db_connect_timeout}&sslmode={sslmode}"
            )
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?connect_timeout={self.db_connect_timeout}&sslmode={sslmode}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
