from datetime import datetime, timedelta, timezone
import json
import secrets
import jwt
import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import ActivityLog, StudentProfile, User, now_utc

router = APIRouter(prefix="/auth", tags=["auth"])

def issue_token(user_id: int) -> str:
    payload = {"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(days=7)}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")

def get_current_user(cod2ship_session: str | None = Cookie(default=None), db: Session = Depends(get_db)) -> User:
    if not cod2ship_session:
        raise HTTPException(401, "Authentication required")
    try:
        payload = jwt.decode(cod2ship_session, settings.secret_key, algorithms=["HS256"])
        user = db.get(User, int(payload["sub"]))
    except (jwt.InvalidTokenError, KeyError, ValueError):
        user = None
    if not user or user.status != "active":
        raise HTTPException(401, "Invalid or inactive account")
    user.last_active = now_utc()
    db.commit()
    return user

@router.get("/google/login")
def google_login():
    if not settings.google_client_id or not settings.google_client_secret:
        if settings.is_production:
            raise HTTPException(503, "Google OAuth is not configured")
        return RedirectResponse(settings.frontend_url + "/dashboard")
    state = secrets.token_urlsafe(32)
    params = httpx.QueryParams({
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    })
    response = RedirectResponse("https://accounts.google.com/o/oauth2/v2/auth?" + str(params))
    response.set_cookie("oauth_state", state, httponly=True, secure=settings.cookie_secure, samesite="lax", max_age=600, path="/")
    return response

@router.get("/google/callback")
async def google_callback(code: str, state: str, oauth_state: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if not oauth_state or not secrets.compare_digest(state, oauth_state):
        raise HTTPException(400, "Invalid OAuth state")
    async with httpx.AsyncClient(timeout=15) as client:
        token_response = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code, "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        })
        token_response.raise_for_status()
        access_token = token_response.json()["access_token"]
        profile_response = await client.get("https://openidconnect.googleapis.com/v1/userinfo", headers={"Authorization": "Bearer " + access_token})
        profile_response.raise_for_status()
        profile = profile_response.json()

    google_id = profile["sub"]
    email = profile["email"].lower()
    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = User(
            google_id=google_id, name=profile.get("name") or email.split("@")[0],
            email=email, profile_image=profile.get("picture"),
            role="admin" if email in settings.admin_email_set else "student",
        )
        db.add(user)
        db.flush()
        if user.role == "student":
            db.add(StudentProfile(user_id=user.id))
        db.add(ActivityLog(user_id=user.id, event="google_login", metadata_json=json.dumps({"source": "google"})))
    else:
        user.name = profile.get("name") or user.name
        user.profile_image = profile.get("picture") or user.profile_image
        user.last_login = now_utc()
        user.last_active = now_utc()
        user.visits += 1
        db.add(ActivityLog(user_id=user.id, event="google_login"))
    db.commit()

    redirect = RedirectResponse(settings.frontend_url + "/dashboard")
    redirect.set_cookie("cod2ship_session", issue_token(user.id), httponly=True, secure=settings.cookie_secure, samesite=settings.cookie_samesite, max_age=604800, path="/")
    redirect.delete_cookie("oauth_state", path="/")
    return redirect

@router.get("/me")
def me(user: User = Depends(get_current_user)):
    profile = user.student_profile
    return {"id": user.id, "name": user.name, "email": user.email, "profile_image": user.profile_image,
            "role": user.role, "status": user.status,
            "registration_status": profile.registration_status if profile else "approved"}

@router.post("/logout")
def logout():
    response = Response(status_code=204)
    response.delete_cookie("cod2ship_session", path="/")
    return response
