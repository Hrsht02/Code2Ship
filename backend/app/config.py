from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"
    google_form_url: str = ""
    frontend_url: str = "http://localhost:5173"
    secret_key: str = "change-me"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

settings = Settings()
