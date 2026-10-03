from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from .config import settings

app = FastAPI(title="Cod2Ship API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "service": "cod2ship-api"}

@app.get("/config/registration-form")
def registration_form():
    if settings.google_form_url:
        return RedirectResponse(settings.google_form_url)
    return {"configured": False, "message": "Registration form is not configured yet."}

@app.get("/auth/google/login")
def google_login():
    # OAuth wiring is intentionally configuration-driven. Add the Google OAuth
    # provider once GOOGLE_CLIENT_ID/SECRET are configured in deployment.
    if not settings.google_client_id:
        return RedirectResponse(f"{settings.frontend_url}/dashboard")
    from urllib.parse import urlencode
    params = urlencode({
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    })
    return RedirectResponse("https://accounts.google.com/o/oauth2/v2/auth?" + params)

@app.get("/auth/google/callback")
def google_callback(code: str):
    # Token exchange/user creation is the next auth implementation step.
    # Never accept a role from the browser; roles will be server controlled.
    return RedirectResponse(f"{settings.frontend_url}/dashboard")
