from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from the environment / .env (see .env.example)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "rex-api"
    database_url: str = "postgresql+asyncpg://rex:rex@localhost:5432/rex"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = ["http://localhost:3000"]

    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""
    livekit_token_ttl_s: int = 3600
    livekit_agent_name: str = "rex"

    # DEV_AUTH=1 enables the unauthenticated dev user and returns magic-link tokens in the response.
    dev_auth: bool = False
    session_secret: str = ""
    token_enc_key: str = "0" * 64
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_s: int = 900
    magic_link_ttl_s: int = 900
