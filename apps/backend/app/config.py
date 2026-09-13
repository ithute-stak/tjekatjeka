from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    database_url: str = Field(
        default="postgresql+psycopg://tjekatjeka:change-me@db:5432/tjekatjeka",
        validation_alias="TJEKATJEKA_DATABASE_URL",
    )
    redis_url: str = Field(default="redis://redis:6379/0", validation_alias="TJEKATJEKA_REDIS_URL")
    auth_issuer: str = Field(default="https://auth.ithute.co.ls", validation_alias="TJEKATJEKA_AUTH_ISSUER")
    auth_audience: str = Field(default="tjekatjeka", validation_alias="TJEKATJEKA_AUTH_AUDIENCE")
    bootstrap_admin_email: str = Field(default="", validation_alias="TJEKATJEKA_BOOTSTRAP_ADMIN_EMAIL")
    dev_auth_bypass: bool = Field(default=False, validation_alias="TJEKATJEKA_DEV_AUTH_BYPASS")
    document_storage_path: str = Field(default="/data/documents", validation_alias="TJEKATJEKA_DOCUMENT_STORAGE_PATH")


settings = Settings()
