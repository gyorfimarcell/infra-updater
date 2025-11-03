from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    config_path: str = "./config/main"
    competitors_compose_path: str = "./competitors.yml"
    traefik_config_path: str = "./routes.yaml"
    webhook_secret: str = "secret"
    docker_project_name: str = "infra"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
