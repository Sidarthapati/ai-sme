# Database Setup Guide (PostgreSQL)

This guide will help you set up PostgreSQL for the AI SME Assistant.

## Option 1: Local PostgreSQL (Development)

### Install PostgreSQL

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download from [PostgreSQL website](https://www.postgresql.org/download/windows/)

### Create Database

```bash
# Connect to PostgreSQL
psql postgres

# Create database
CREATE DATABASE ai_sme;

# Create user (optional)
CREATE USER ai_sme_user WITH PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE ai_sme TO ai_sme_user;

# Exit
\q
```

### Configure Backend

Update `backend/.env`:
```bash
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/ai_sme
# OR using individual components:
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_sme
```

## Option 2: Railway PostgreSQL (Recommended for POC)

1. Go to [Railway](https://railway.app/)
2. Sign up/login
3. Click "New Project"
4. Click "Add Database" → "PostgreSQL"
5. Railway will automatically create a PostgreSQL database
6. Click on the database → "Variables" tab
7. Copy the `DATABASE_URL` (it looks like: `postgresql://postgres:password@host:port/railway`)
8. Add to your backend `.env`:
   ```bash
   DATABASE_URL=postgresql+asyncpg://postgres:password@host:port/railway
   ```
   **Note:** Change `postgresql://` to `postgresql+asyncpg://` for async support

## Option 3: Render PostgreSQL

1. Go to [Render](https://render.com/)
2. Sign up/login
3. Click "New" → "PostgreSQL"
4. Name it "ai-sme-db"
5. Select free tier
6. Click "Create Database"
7. Copy the "Internal Database URL" or "External Database URL"
8. Add to backend `.env`:
   ```bash
   DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname
   ```

## Initialize Database Tables

The database tables will be created automatically when you start the backend:

```bash
cd backend
source venv/bin/activate
python main.py
```

You should see:
```
✅ Database initialized
```

## Verify Database

Connect to your database and check tables:

```bash
psql your_database_url

# List tables
\dt

# Check users table
SELECT * FROM users;

# Check conversations table
SELECT * FROM conversations;

# Check messages table
SELECT * FROM messages;
```

## Database Schema

The application creates these tables automatically:

- **users**: Stores user information (email, name, Google ID)
- **conversations**: Stores conversation metadata (user_id, title, timestamps)
- **messages**: Stores individual messages (conversation_id, role, content, sources)

## Troubleshooting

### "Connection refused"
- Make sure PostgreSQL is running
- Check host/port in DATABASE_URL
- Verify firewall settings

### "Database does not exist"
- Create the database first (see above)
- Check database name in DATABASE_URL

### "Authentication failed"
- Verify username/password in DATABASE_URL
- Check PostgreSQL user permissions

### "Module 'asyncpg' not found"
- Install dependencies: `pip install -r requirements.txt`
- Make sure you're in the virtual environment

## Production Notes

- Use managed PostgreSQL (Railway/Render) for production
- Enable backups
- Monitor database size
- Set up connection pooling if needed
- Use environment variables, never hardcode credentials
