from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .auth import router as auth_router, get_current_user
from .config import settings
from .database import Base, engine, get_db
from .models import User

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Cod2Ship API", version="0.3.0")

allowed_origins = [origin.strip().rstrip("/") for origin in settings.frontend_url.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(auth_router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "cod2ship-api", "environment": settings.environment}

@app.get("/config/registration-form")
def registration_form():
    if settings.google_form_url:
        return RedirectResponse(settings.google_form_url)
    return {"configured": False, "message": "Registration form is not configured yet."}

@app.get("/admin/users")
def admin_users(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "admin":
        raise HTTPException(403, "Admin access required")
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [{"id": u.id, "name": u.name, "email": u.email, "role": u.role, "status": u.status,
             "registration_status": u.student_profile.registration_status if u.student_profile else "approved"} for u in users]
