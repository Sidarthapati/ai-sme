# Google OAuth Setup Guide

This guide will help you set up Google OAuth for the AI SME Assistant.

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name it "AI SME Assistant" (or your preferred name)
4. Click "Create"

## Step 2: Enable Google+ API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Google+ API" or "Google Identity Services"
3. Click on it and click "Enable"

## Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure OAuth consent screen:
   - User Type: External (for POC)
   - App name: "AI SME Assistant"
   - User support email: Your email
   - Developer contact: Your email
   - Click "Save and Continue"
   - Scopes: Add `email`, `profile`, `openid`
   - Click "Save and Continue"
   - Test users: Add your email (for testing)
   - Click "Save and Continue"
4. Application type: "Web application"
5. Name: "AI SME Web Client"
6. Authorized JavaScript origins:
   - **For local development:** `http://localhost:3000`
   - **For production (add later when you deploy):**
     - If using Railway: `https://your-app-name.railway.app` (replace with your actual Railway URL)
     - If using Render: `https://your-app-name.onrender.com` (replace with your actual Render URL)
     - If using Vercel: `https://your-app-name.vercel.app` (replace with your actual Vercel URL)
     - If using custom domain: `https://yourdomain.com` (your actual domain)
   
   **Note:** You can add multiple origins. Start with just `http://localhost:3000` for now, and add production URLs later when you deploy.

7. Authorized redirect URIs:
   - **For local development:** `http://localhost:3000`
   - **For production (add later when you deploy):** Same URLs as above
   
   **Important:** These must match exactly (including `http://` vs `https://` and no trailing slash)
   
8. Click "Create"
9. **Copy the Client ID** - you'll need this!

## Step 4: Configure Environment Variables (For Local Development)

**Right now, you only need to set up for local development.** You'll add production URLs later when you deploy.

### Backend (.env)
```bash
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
JWT_SECRET_KEY=generate-a-random-secret-key-here-minimum-32-characters
```

### Frontend (.env.local)
**Create this file** in the `frontend/` directory (it doesn't exist by default because it's gitignored):

```bash
# In frontend/.env.local
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Steps:**
1. Go to `frontend/` directory
2. Create a new file named `.env.local` (note the dot at the beginning)
3. Copy the content from `frontend/.env.example` or use the template above
4. Replace `your-client-id-here.apps.googleusercontent.com` with your actual Client ID

**Note:** 
- The Client ID is the same for both frontend and backend
- `.env.local` is gitignored (won't be committed to git) - this is correct!
- Next.js automatically loads `.env.local` when you run `npm run dev`

## Step 5: Generate JWT Secret Key

Generate a random secret key for JWT tokens:

```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or using OpenSSL
openssl rand -base64 32

# Or use an online generator
# https://randomkeygen.com/
```

Copy the generated key to `JWT_SECRET_KEY` in backend `.env`.

## Step 6: Test Locally

1. Start backend:
   ```bash
   cd backend
   source venv/bin/activate
   python main.py
   ```

2. Start frontend:
   ```bash
   cd frontend
   npm install  # Install new dependencies
   npm run dev
   ```

3. Open `http://localhost:3000`
4. Click "Sign in with Google"
5. Select your Google account
6. You should be authenticated!

## Troubleshooting

### "Error 400: redirect_uri_mismatch"
- Make sure your redirect URI in Google Console matches exactly:
  - `http://localhost:3000` (not `http://localhost:3000/`)
  - Check for trailing slashes

### "Invalid token"
- Make sure `GOOGLE_CLIENT_ID` matches in both frontend and backend
- Check that the Client ID is correct (no extra spaces)

### "Email not verified"
- Make sure you're using a Google account with verified email
- Check OAuth consent screen scopes include `email`

## Production Deployment

When deploying to Railway/Render:

1. **Deploy your frontend first** to get the actual URL:
   - Railway: Your frontend will get a URL like `https://ai-sme-frontend-production.up.railway.app`
   - Render: Your frontend will get a URL like `https://ai-sme-frontend.onrender.com`
   - Vercel: Your frontend will get a URL like `https://ai-sme-frontend.vercel.app`

2. **Go back to Google Cloud Console** → Your OAuth Client → Edit:
   - Add the production URL to "Authorized JavaScript origins"
   - Add the production URL to "Authorized redirect URIs"
   - Example: `https://ai-sme-frontend-production.up.railway.app`
   - **Important:** Use the exact URL from your deployment platform

3. Update environment variables in Railway/Render dashboard:
   - Backend: `GOOGLE_CLIENT_ID`, `JWT_SECRET_KEY`
   - Frontend: `NEXT_PUBLIC_GOOGLE_CLIENT_ID`

4. Make sure CORS origins include your frontend URL in backend settings:
   - Backend `.env`: `CORS_ORIGINS=http://localhost:3000,https://your-actual-frontend-url.com`

## Security Notes

- **Never commit** `.env` files to git
- Use different `JWT_SECRET_KEY` for production
- Keep your Google Client Secret secure (we don't use it in this setup, but good practice)
- Consider restricting OAuth to specific email domains for production
