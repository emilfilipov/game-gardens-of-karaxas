from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    jwt_secret: str
    jwt_issuer: str = "karaxas"
    jwt_audience: str = "karaxas-client"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 30

    ops_api_token: str
    version_grace_minutes_default: int = 5

    db_host: str
    db_port: int = 5432
    db_name: str = "karaxas"
    db_user: str
    db_password: str
    db_sslmode: str = "disable"
    db_connect_timeout: int = 5

    @property
    def database_url(self) -> str:
        if self.db_host.startswith("/cloudsql/"):
            return (
                f"postgresql+psycopg://{self.db_user}:{self.db_password}"
                f"@/{self.db_name}?host={self.db_host}&connect_timeout={self.db_connect_timeout}"
            )
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?connect_timeout={self.db_connect_timeout}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
