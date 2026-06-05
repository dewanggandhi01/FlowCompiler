# Deployment Guide

## Option 1: Docker Compose (Recommended for Development)

### Prerequisites
- Docker Desktop installed
- `.env` file configured with `OPENAI_API_KEY`

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/dewanggandhi01/FlowCompiler.git
cd FlowCompiler

# 2. Create .env from template
cp .env.example .env
# Edit .env: Add your OPENAI_API_KEY

# 3. Build and run all services
docker-compose up --build

# 4. Access the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# PostgreSQL: localhost:5432
```

### Stopping
```bash
docker-compose down          # Stop containers
docker-compose down -v       # Stop + remove data volumes
```

---

## Option 2: Vercel (Frontend) + Render (Backend)

### Deploy Backend to Render

1. **Push code to GitHub:**
   ```bash
   git remote add origin https://github.com/dewanggandhi01/FlowCompiler.git
   git push -u origin main
   ```

2. **Create Render account** at https://render.com

3. **New Web Service:**
   - Connect your GitHub repo
   - Render will auto-detect `render.yaml`
   - Add environment variables:
     - `OPENAI_API_KEY` = your key
     - `FRONTEND_URL` = your Vercel URL (after deploying frontend)

4. **Note your Render URL** (e.g., `https://flowcompiler-api.onrender.com`)

### Deploy Frontend to Vercel

1. **Create Vercel account** at https://vercel.com

2. **Import project:**
   - Connect GitHub repo
   - Set **Root Directory** to `frontend`
   - Add environment variable:
     - `NEXT_PUBLIC_API_URL` = your Render backend URL

3. **Deploy** — Vercel will auto-build and deploy

4. **Update Render** `FRONTEND_URL` with your Vercel URL for CORS

---

## Option 3: Manual VPS Deployment

### Backend (Ubuntu/Debian)

```bash
# Install Python 3.12
sudo apt update && sudo apt install python3.12 python3.12-venv python3-pip

# Clone and setup
git clone https://github.com/dewanggandhi01/FlowCompiler.git
cd FlowCompiler
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Add your keys

# Install PostgreSQL
sudo apt install postgresql
sudo -u postgres createdb flowcompiler

# Run with Gunicorn
pip install gunicorn
gunicorn src.app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# (Optional) Use systemd for auto-restart
# Create /etc/systemd/system/flowcompiler.service
```

### Frontend (Same or separate server)

```bash
# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs

cd FlowCompiler/frontend
npm install
npm run build
npm start  # or use pm2: pm2 start npm --name flowcompiler-ui -- start
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key |
| `OPENAI_MODEL` | ❌ | Model name (default: `gpt-4o`) |
| `DATABASE_URL` | ❌ | PostgreSQL connection string |
| `SUPABASE_URL` | ❌ | Supabase project URL |
| `SUPABASE_KEY` | ❌ | Supabase anon key |
| `FRONTEND_URL` | ❌ | Frontend URL for CORS |
| `APP_ENV` | ❌ | `development`, `staging`, `production` |
