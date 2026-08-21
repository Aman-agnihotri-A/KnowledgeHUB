from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    app_name: str = "KnowledgeHub"
    app_env: str = "development"
    debug: bool = True
    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    document_storage_path: str = "storage/documents"

    answer_generation_provider: str = (
        "deterministic"
    )

    openai_api_key: str | None = None

    openai_model: str = "gpt-5.6-luna"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()