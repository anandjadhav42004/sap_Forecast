# Deployment - SAP Prognos

The application uses a decoupled architecture for deployment.

## 1. Backend (FastAPI on Render)
The Python backend is deployed to [Render.com](https://render.com).

**Render Configuration:**
- **Build Command**: `pip install -r forecast-api/requirements.txt`
- **Start Command**: `uvicorn forecast-api.main:app --host 0.0.0.0 --port 10000`
- **Root Directory**: `.` (Root)
- **Environment Variables**:
  - `ALLOWED_ORIGINS`: `https://sap-forecast.vercel.app`
  - `PYTHON_VERSION`: `3.9.0`

## 2. Frontend (SAPUI5 on Vercel)
The UI is deployed statically to [Vercel](https://vercel.com).

**Vercel Configuration:**
- **Framework Preset**: Other
- **Root Directory**: `frontend-ui5`
- **Build Command**: `None`
- **Output Directory**: `.`
- **Routing**: Handled by SAPUI5 Hash Routing. Vercel is configured via `index.html` redirects to serve `webapp/index.html` from the root.

## 3. Local Development
```bash
# Terminal 1: Backend
cd forecast-api
source venv/bin/activate
uvicorn main:app --reload

# Terminal 2: Frontend
cd frontend-ui5
npx serve .
```
