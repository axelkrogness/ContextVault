from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
    database_url:str
    jwt_secret:str
    cors_origins:str="http://localhost:3000"
    embedding_api_url: str | None = None
    embedding_api_key: str | None = None
    embedding_dimensions: int = 64
    rate_limit_per_minute:int=60
    model_config=SettingsConfigDict(env_file=".env",extra="ignore")
settings=Settings()
