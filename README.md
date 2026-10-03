# Cod2Ship

**Learn • Code • Build**

Cod2Ship is a hands-on learning platform for students from Class 6 to college.

## Stack

- Frontend: React + Vite + JavaScript
- Backend: FastAPI + Python
- Database: PostgreSQL
- Authentication: Google OAuth
- Frontend deployment: Vercel
- Backend deployment: Render

## Project structure

```
Code2Ship/
├── frontend/        # React + Vite app
├── backend/         # FastAPI API
└── render.yaml      # Render API + PostgreSQL Blueprint
```

## Local development

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Copy `backend/.env.example` to `backend/.env`, fill the values, then run:

```bash
uvicorn app.main:app --reload
```

## Deploy backend to Render

This repository includes `render.yaml`. Render Blueprints can create the web service and PostgreSQL database from the repository configuration. Render documents FastAPI deployment with a Python web service, Uvicorn start command, and health checks. citeturn0search0turn0search2

1. Open Render and sign in with GitHub.
2. Choose **New → Blueprint**.
3. Select `Hrsht02/Code2Ship` and branch `main`.
4. Select `render.yaml`.
5. Enter the secret/environment values requested by Render:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI`
   - `GOOGLE_FORM_URL` (optional)
   - `FRONTEND_URL`
   - `SECRET_KEY`
   - `ADMIN_EMAILS`
6. Deploy the Blueprint.
7. Test:
   - `https://<your-render-service>.onrender.com/health`
   - `https://<your-render-service>.onrender.com/docs`

Render's free web services can be used for testing but spin down after inactivity. Render's current free Postgres plan expires after 30 days, so upgrade the database if you need persistent production data. citeturn0search6

## Deploy frontend to Vercel

1. Open Vercel and choose **Add New → Project**.
2. Import `Hrsht02/Code2Ship` from GitHub.
3. Set **Root Directory** to `frontend`.
4. Framework: **Vite**.
5. Add the environment variable:

```
VITE_API_URL=https://<your-render-service>.onrender.com
```

6. Deploy.
7. Copy the Vercel production URL.

Vite/React applications are supported directly on Vercel. citeturn0search7

## Google OAuth production configuration

After both deployments exist, update these values:

### Render

```
FRONTEND_URL=https://<your-vercel-domain>
GOOGLE_REDIRECT_URI=https://<your-render-service>.onrender.com/auth/google/callback
COOKIE_SECURE=true
COOKIE_SAMESITE=none
ENVIRONMENT=production
```

### Google Cloud Console

Add the Render callback URL to the OAuth client's **Authorized redirect URIs**:

```
https://<your-render-service>.onrender.com/auth/google/callback
```

The frontend URL is used as the post-login destination.

## Security notes

- Keep `GOOGLE_CLIENT_SECRET` and `SECRET_KEY` only in Render environment variables.
- Never commit `.env` files.
- Production cookies use HTTPS and cross-site-compatible settings for the Vercel → Render architecture.
- Backend authorization is server-side; the frontend is not treated as a security boundary.

## MVP status

Current implementation includes:
- Public landing page
- Google OAuth session flow
- Student/admin role foundation
- Student registration status
- Registration form redirect
- Admin user listing endpoint
- PostgreSQL-ready SQLAlchemy models
- Render Blueprint
- Vercel SPA deployment configuration
- Production CORS and cookie configuration

The larger LMS specification still requires the remaining course, batch, teacher, class, assignment, submission, notes, announcements, attendance, analytics, and full admin UI modules before calling the product feature-complete.
