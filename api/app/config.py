from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    cors_origins: str = "http://localhost:3000"
    embedding_provider: str = "local"
    openai_api_key: str | None = None
    embedding_model: str = "text-embedding-3-small"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
settings=Settings()
