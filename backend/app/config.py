from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./cod2ship.db"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"
    google_form_url: str = ""
    frontend_url: str = "http://localhost:5173"
    secret_key: str = "change-me"
    admin_emails: str = ""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def admin_email_set(self) -> set[str]:
        return {email.strip().lower() for email in self.admin_emails.split(",") if email.strip()}

settings = Settings()
