from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    RATE_LIMITING_ENABLE: bool = False
    RATE_LIMITING_FREQUENCY: str = "2/3seconds"

    # Credentials for the proxy pool. PROXY_POOL is a comma-separated
    # "ip:port" list supplied by the caller; empty means request directly.
    PROXY_USERNAME: str = ""
    PROXY_PASSWORD: str = ""
    PROXY_POOL: str = ""


settings = Settings()
