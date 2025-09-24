from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    config_path: str = "./config/main"
    gitea_token: str = ""
    competitors_compose_path: str = "./competitors.yml"
    webhook_secret: str = "secret"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
