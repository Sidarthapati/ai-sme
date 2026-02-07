# Railway Deployment Plan - AI SME Assistant

Complete step-by-step guide for deploying the AI SME Assistant to Railway.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Railway Setup](#railway-setup)
3. [Backend Deployment](#backend-deployment)
4. [Frontend Deployment](#frontend-deployment)
5. [Database Configuration](#database-configuration)
6. [Google OAuth Setup](#google-oauth-setup)
7. [CORS Configuration](#cors-configuration)
8. [ChromaDB Persistence](#chromadb-persistence)
9. [Environment Variables Checklist](#environment-variables-checklist)
10. [Post-Deployment Verification](#post-deployment-verification)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- [x] Railway account created
- [x] PostgreSQL database already provisioned on Railway
- [x] Google Cloud Project with OAuth credentials
- [x] OpenAI API key
- [x] GitHub repository connected to Railway (or ready to deploy)

---

## Railway Setup

### 1. Create Railway Project
1. Go to [Railway Dashboard](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo" (recommended) or "Empty Project"
4. Connect your GitHub repository

### 2. Add Services
You'll need **3 services**:
- **Backend Service** (FastAPI)
- **Frontend Service** (Next.js)
- **PostgreSQL Database** (already exists)

---

## Backend Deployment

### Step 1: Prepare Backend for Production

#### Update Dockerfile (if needed)
The existing `backend/Dockerfile` should work, but ensure it's production-ready:

```dockerfile
# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/raw data/processed chroma_db logs

# Expose port
EXPOSE 8000

# Run the application (production mode)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Note**: Railway will automatically detect the Dockerfile and use it.

### Step 2: Create Railway Service for Backend

1. In Railway project, click "New Service"
2. Select "GitHub Repo" → Choose your repository
3. Railway will auto-detect the Dockerfile
4. **Set Root Directory**: `backend` (important!)
5. Railway will build and deploy automatically

### Step 3: Configure Backend Environment Variables

In Railway backend service → **Variables** tab, add:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_production_openai_key
OPENAI_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-large

# Vector Database (ChromaDB - local)
VECTOR_DB_TYPE=chroma
VECTOR_DB_PATH=/app/chroma_db
CHROMA_PERSIST_DIRECTORY=/app/chroma_db

# Application Settings
APP_NAME=AI SME Assistant
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# CORS Configuration (UPDATE WITH YOUR FRONTEND URL)
# Format: comma-separated URLs
CORS_ORIGINS=https://your-frontend-app.railway.app,https://your-custom-domain.com

# Database (PostgreSQL - Railway Internal URL)
# Railway will auto-inject this, but you can also set manually:
# DATABASE_URL=postgresql+asyncpg://postgres:password@postgres.railway.internal:5432/railway
# OR use Railway's provided DATABASE_URL variable (recommended)

# Google OAuth (Production)
GOOGLE_CLIENT_ID=your_production_google_client_id.apps.googleusercontent.com

# JWT Secret Key (GENERATE A STRONG RANDOM STRING)
JWT_SECRET_KEY=generate-a-very-long-random-string-here-min-32-chars

# RAG Configuration
CHUNK_SIZE=800
CHUNK_OVERLAP=100
RETRIEVAL_TOP_K=5
LLM_TEMPERATURE=0.3
MAX_RESPONSE_TOKENS=1000

# Document Upload
MAX_UPLOAD_SIZE_MB=10
ALLOWED_FILE_TYPES=.txt,.md,.pdf,.docx,.doc
```

**Important Notes**:
- `DATABASE_URL`: Railway will auto-inject this. Use the **internal** URL format: `postgresql+asyncpg://postgres:password@postgres.railway.internal:5432/railway`
- `CORS_ORIGINS`: Update this **after** you deploy frontend and get its URL
- `JWT_SECRET_KEY`: Generate a strong random string (use: `openssl rand -hex 32`)

### Step 4: Link PostgreSQL Database

1. In Railway backend service → **Variables** tab
2. Click "Add Variable" → "Reference"
3. Select your PostgreSQL service
4. Choose `DATABASE_URL` variable
5. Railway will auto-inject the connection string

**OR** manually set:
- Use Railway's internal database URL: `postgres.railway.internal`
- Format: `postgresql+asyncpg://postgres:password@postgres.railway.internal:5432/railway`

### Step 5: Configure Port

Railway auto-assigns `PORT` environment variable. Update your backend to use it:

The backend already uses `settings.api_port` which reads from `API_PORT` env var. Railway will set `PORT`, so you may need to update `main.py` to prefer `PORT` over `API_PORT`, OR set `API_PORT=$PORT` in Railway variables.

**Recommended**: Add to Railway variables:
```bash
API_PORT=${{PORT}}
```

---

## Frontend Deployment

### Step 1: Update Frontend Dockerfile for Production

Update `frontend/Dockerfile`:

```dockerfile
# Frontend Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Expose port
EXPOSE 3000

# Run the application
CMD ["node", "server.js"]
```

**Note**: If using Next.js standalone output, update `next.config.js`:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // ... other config
}
```

**Alternative simpler Dockerfile** (if standalone doesn't work):

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Build for production
RUN npm run build

EXPOSE 3000

# Start production server
CMD ["npm", "start"]
```

### Step 2: Create Railway Service for Frontend

1. In Railway project, click "New Service"
2. Select "GitHub Repo" → Choose your repository
3. Set **Root Directory**: `frontend`
4. Railway will build and deploy

### Step 3: Configure Frontend Environment Variables

In Railway frontend service → **Variables** tab:

```bash
# Backend API URL (UPDATE AFTER BACKEND DEPLOYMENT)
NEXT_PUBLIC_API_URL=https://your-backend-app.railway.app

# Google OAuth (Production)
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_production_google_client_id.apps.googleusercontent.com

# Application
NEXT_PUBLIC_APP_NAME=AI SME Assistant
NEXT_PUBLIC_APP_VERSION=1.0.0

# Feature Flags
NEXT_PUBLIC_ENABLE_FILE_UPLOAD=true
NEXT_PUBLIC_ENABLE_FEEDBACK=true
NEXT_PUBLIC_ENABLE_DARK_MODE=true
```

**Important**: 
- `NEXT_PUBLIC_API_URL`: Set this **after** backend is deployed and you have its Railway URL
- All `NEXT_PUBLIC_*` variables are exposed to the browser

---

## Database Configuration

### Step 1: Verify Database Connection

Your PostgreSQL database is already on Railway. Verify:

1. Go to PostgreSQL service → **Variables** tab
2. Note the `DATABASE_URL` (internal format)
3. Backend should auto-connect via Railway's variable reference

### Step 2: Database Initialization

The backend's `init_db()` function will automatically:
- Create tables (`users`, `conversations`, `messages`)
- Run on first startup

**No manual migration needed** - SQLAlchemy handles it.

### Step 3: Verify Database Tables

After first deployment, check logs for:
```
✅ Database initialized
```

If you see errors, check:
- `DATABASE_URL` format is correct
- Database service is running
- Connection string uses `postgresql+asyncpg://` prefix

---

## Google OAuth Setup

### Step 1: Update Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **APIs & Services** → **Credentials**
3. Select your OAuth 2.0 Client ID
4. Click **Edit**

### Step 2: Add Authorized JavaScript Origins

Add your production frontend URL:
```
https://your-frontend-app.railway.app
```

If you have a custom domain:
```
https://your-custom-domain.com
```

### Step 3: Add Authorized Redirect URIs

Add your production frontend URL:
```
https://your-frontend-app.railway.app
```

**Note**: For `@react-oauth/google`, redirect URIs may not be needed, but add them to be safe.

### Step 4: Update Environment Variables

- **Backend**: `GOOGLE_CLIENT_ID` = Production Client ID
- **Frontend**: `NEXT_PUBLIC_GOOGLE_CLIENT_ID` = Production Client ID

**Important**: Use the **same** Client ID in both backend and frontend.

---

## CORS Configuration

### Location
CORS is configured in `backend/main.py` (lines 58-64) and reads from `CORS_ORIGINS` environment variable.

### Configuration Format

In Railway backend service → **Variables**:

```bash
CORS_ORIGINS=https://your-frontend-app.railway.app,https://your-custom-domain.com
```

**Format**: Comma-separated list of URLs (no spaces, or spaces are trimmed automatically)

### Step-by-Step

1. **Deploy backend first** → Get backend URL
2. **Deploy frontend** → Get frontend URL
3. **Update backend CORS**:
   - Go to backend service → Variables
   - Set `CORS_ORIGINS` = `https://your-frontend-url.railway.app`
   - Railway will auto-redeploy

### Example

```bash
# Single origin
CORS_ORIGINS=https://ai-sme-frontend.railway.app

# Multiple origins (comma-separated)
CORS_ORIGINS=https://ai-sme-frontend.railway.app,https://ai-sme.example.com
```

**Important**: 
- Use `https://` (not `http://`)
- No trailing slashes
- Include the full domain

---

## ChromaDB Persistence

### Current Setup
ChromaDB is configured to use local storage at `./chroma_db` (or `/app/chroma_db` in Docker).

### Railway Persistent Storage

Railway provides **ephemeral storage** by default. For ChromaDB to persist:

#### Option 1: Use Railway Volumes (Recommended)

1. In Railway backend service → **Settings** tab
2. Scroll to **Volumes** section
3. Click **Add Volume**
4. Set:
   - **Mount Path**: `/app/chroma_db`
   - **Size**: 1GB (or more, depending on your data)
5. Railway will persist this directory across deployments

#### Option 2: Use Environment Variable

Ensure `CHROMA_PERSIST_DIRECTORY` points to the volume:

```bash
CHROMA_PERSIST_DIRECTORY=/app/chroma_db
```

#### Option 3: Rebuild Vector DB After Deployment

If volumes don't work initially:
1. SSH into Railway container (if possible) OR
2. Add a one-time script to rebuild vector DB:
   ```bash
   python scripts/build_vector_database.py
   ```

### Verify Persistence

After deployment:
1. Check logs for: `Initialized vector store: /app/chroma_db`
2. Check document count: `Collection: ai_sme_documents (970 documents)`
3. Restart service → Data should persist

---

## Environment Variables Checklist

### Backend Service Variables

```bash
# ✅ Required
OPENAI_API_KEY=sk-...
DATABASE_URL=${{Postgres.DATABASE_URL}}  # Reference from Postgres service
CORS_ORIGINS=https://your-frontend.railway.app
GOOGLE_CLIENT_ID=...apps.googleusercontent.com
JWT_SECRET_KEY=<generate-random-32-chars>

# ✅ Recommended
DEBUG=false
LOG_LEVEL=INFO
VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIRECTORY=/app/chroma_db
API_PORT=${{PORT}}  # Use Railway's PORT variable

# ✅ Optional (with defaults)
OPENAI_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-large
CHUNK_SIZE=800
RETRIEVAL_TOP_K=5
```

### Frontend Service Variables

```bash
# ✅ Required
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_GOOGLE_CLIENT_ID=...apps.googleusercontent.com

# ✅ Optional
NEXT_PUBLIC_ENABLE_FILE_UPLOAD=true
NEXT_PUBLIC_ENABLE_DARK_MODE=true
```

### PostgreSQL Service Variables

Railway auto-manages these. You only need to **reference** `DATABASE_URL` in backend.

---

## Post-Deployment Verification

### 1. Backend Health Check

```bash
curl https://your-backend.railway.app/
```

Expected response:
```json
{
  "name": "AI SME Assistant",
  "version": "1.0.0",
  "status": "running",
  "message": "AI SME API is operational"
}
```

### 2. Frontend Accessibility

1. Open `https://your-frontend.railway.app`
2. Should see login page
3. Check browser console for errors

### 3. Google OAuth Flow

1. Click "Sign in with Google"
2. Complete OAuth flow
3. Should redirect back to chat page
4. Check backend logs for user creation

### 4. Database Connection

Check backend logs for:
```
✅ Database initialized
```

### 5. Vector DB Initialization

Check backend logs for:
```
Initialized vector store: /app/chroma_db
Collection: ai_sme_documents (970 documents)
```

### 6. Chat Functionality

1. Send a test message
2. Verify response
3. Check conversation persists (refresh page)

### 7. File Upload

1. Go to Upload page
2. Upload a test file
3. Verify it appears in document list

---

## Troubleshooting

### Backend Issues

#### Database Connection Failed
- **Check**: `DATABASE_URL` format (should be `postgresql+asyncpg://...`)
- **Check**: Using Railway's internal URL (`postgres.railway.internal`)
- **Check**: Database service is running

#### CORS Errors
- **Check**: `CORS_ORIGINS` includes frontend URL (exact match, including `https://`)
- **Check**: No trailing slashes in URLs
- **Check**: Frontend is using correct backend URL

#### ChromaDB Not Found
- **Check**: `CHROMA_PERSIST_DIRECTORY` is set correctly
- **Check**: Volume is mounted (if using volumes)
- **Solution**: Rebuild vector DB after deployment

### Frontend Issues

#### API Connection Failed
- **Check**: `NEXT_PUBLIC_API_URL` is correct
- **Check**: Backend is running and accessible
- **Check**: CORS is configured correctly

#### Google OAuth Not Working
- **Check**: `NEXT_PUBLIC_GOOGLE_CLIENT_ID` matches backend `GOOGLE_CLIENT_ID`
- **Check**: Authorized origins in Google Console include frontend URL
- **Check**: Using `https://` (not `http://`)

#### Build Fails
- **Check**: All `NEXT_PUBLIC_*` variables are set
- **Check**: Node version matches (18+)
- **Check**: Build logs for specific errors

### General Issues

#### Services Not Communicating
- **Check**: Both services are in same Railway project
- **Check**: Using Railway-generated URLs (or custom domains)
- **Check**: Network policies allow communication

#### Environment Variables Not Loading
- **Check**: Variables are set in correct service
- **Check**: `NEXT_PUBLIC_*` prefix for frontend variables
- **Check**: No typos in variable names
- **Solution**: Redeploy after changing variables

---

## Deployment Order

1. ✅ **PostgreSQL Database** (already exists)
2. ✅ **Backend Service**
   - Deploy backend
   - Set environment variables
   - Link database
   - Get backend URL
3. ✅ **Frontend Service**
   - Deploy frontend
   - Set `NEXT_PUBLIC_API_URL` = backend URL
   - Get frontend URL
4. ✅ **Update Backend CORS**
   - Set `CORS_ORIGINS` = frontend URL
5. ✅ **Update Google OAuth**
   - Add frontend URL to authorized origins
6. ✅ **Verify Everything**
   - Test OAuth login
   - Test chat
   - Test file upload

---

## Custom Domain Setup (Optional)

### Backend Custom Domain

1. In Railway backend service → **Settings** → **Networking**
2. Click **Generate Domain** or **Add Custom Domain**
3. Update `CORS_ORIGINS` to include custom domain

### Frontend Custom Domain

1. In Railway frontend service → **Settings** → **Networking**
2. Click **Generate Domain** or **Add Custom Domain**
3. Update Google OAuth authorized origins
4. Update backend `CORS_ORIGINS`

---

## Monitoring & Logs

### View Logs

1. Railway Dashboard → Select service → **Deployments** tab
2. Click on latest deployment → **View Logs**
3. Or use Railway CLI: `railway logs`

### Key Logs to Monitor

- Backend startup: `✅ Database initialized`
- Vector DB: `Collection: ai_sme_documents (X documents)`
- API requests: `INFO: ... "POST /api/chat/stream HTTP/1.1" 200 OK`
- Errors: `ERROR: ...`

---

## Cost Optimization

### Railway Pricing

- **Hobby Plan**: $5/month (includes $5 credit)
- **Pro Plan**: $20/month (includes $20 credit)

### Tips

1. Use Railway's free tier for POC
2. Monitor usage in Railway dashboard
3. Set up usage alerts
4. Consider pausing services when not in use

---

## Security Checklist

- [ ] `DEBUG=false` in production
- [ ] Strong `JWT_SECRET_KEY` (32+ random characters)
- [ ] `OPENAI_API_KEY` is secure (not exposed)
- [ ] CORS only allows your frontend domain
- [ ] Google OAuth uses production credentials
- [ ] Database uses Railway's internal network
- [ ] No hardcoded secrets in code
- [ ] Environment variables are set in Railway (not in code)

---

## Next Steps After Deployment

1. ✅ Test all functionality
2. ✅ Set up monitoring (optional)
3. ✅ Configure custom domains (optional)
4. ✅ Set up backups for database
5. ✅ Document your deployment process
6. ✅ Share access with team

---

## Quick Reference

### Railway URLs Format
- Backend: `https://your-backend-name.up.railway.app`
- Frontend: `https://your-frontend-name.up.railway.app`

### Important Files
- `backend/Dockerfile` - Backend container config
- `frontend/Dockerfile` - Frontend container config
- `backend/.env.example` - Backend env template
- `frontend/.env.example` - Frontend env template
- `backend/main.py` - CORS configuration (line 58-64)

### Key Commands (if using Railway CLI)

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link project
railway link

# View logs
railway logs

# Open shell
railway shell
```

---

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Railway Status: https://status.railway.app

---

**Last Updated**: February 2026
**Version**: 1.0.0
