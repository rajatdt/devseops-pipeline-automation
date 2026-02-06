from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BOND_")

    app_name: str = "Bond Price Tracker"
    ecb_base_url: str = "https://data-api.ecb.europa.eu/service/data"
    cache_ttl_seconds: int = 300  # 5 minutes


settings = Settings()
