# Cod2Ship

Learn • Code • Build

Cod2Ship is a hands-on learning platform for students from Class 6 to college.

## Stack

- Frontend: React + Vite + JavaScript
- Backend: FastAPI + Python
- Database: PostgreSQL
- Authentication: Google OAuth (production configuration)
- Frontend deployment: Vercel
- Backend deployment: Render

## Local development

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Copy `frontend/.env.example` to `.env` and `backend/.env.example` to `.env`.

## MVP

Phase 1 covers the public landing page, Google-login entry point, student registration state, admin registration review, and role-aware dashboard foundations.
