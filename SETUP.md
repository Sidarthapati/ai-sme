# Setup Guide for AI SME Assistant

Complete setup instructions for local development.

## Prerequisites

### Required Software
- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Git** - [Download](https://git-scm.com/)

### Required API Keys
- **OpenAI API Key** - [Get it here](https://platform.openai.com/api-keys)
  - Or **Azure OpenAI** credentials (for production at Wells Fargo)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
cd ~/Desktop/Projects
cd "AI SME"
```

### 2. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your OpenAI API key
# nano .env  (or use any text editor)
```

**Required in .env:**
```env
OPENAI_API_KEY=your_actual_api_key_here
```

### 3. Frontend Setup

```bash
# Open new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env.local
```

### 4. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python main.py
```

Backend will run on: http://localhost:8000

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Frontend will run on: http://localhost:3000

### 5. Verify Installation

1. Open browser: http://localhost:8000
   - Should see: `{"name": "AI SME Assistant", "status": "running"}`

2. Open browser: http://localhost:3000
   - Should see the frontend landing page

## 📦 Alternative: Docker Setup

If you prefer using Docker:

```bash
# Make sure Docker Desktop is running

# Create .env file in root with your API key
cp backend/.env.example .env
# Edit .env with your OPENAI_API_KEY

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔧 Troubleshooting

### Backend Issues

**Problem: `ModuleNotFoundError`**
```bash
# Make sure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

**Problem: `pydantic_core._pydantic_core.ValidationError`**
- Check that `.env` file exists and has `OPENAI_API_KEY`
- Verify API key is valid

### Frontend Issues

**Problem: `Module not found` errors**
```bash
rm -rf node_modules package-lock.json
npm install
```

**Problem: Port 3000 already in use**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
# Or use different port
PORT=3001 npm run dev
```

## 📝 Development Workflow

### Day 1-7 (Week 1): Backend Development
Focus on backend directory:
- Implement scrapers
- Set up vector database
- Build RAG pipeline
- Create API endpoints

### Day 8-14 (Week 2): Frontend Development
Focus on frontend directory:
- Build chat interface
- Add document upload
- Connect to backend API

### Day 15-21 (Week 3): Integration & Polish
- End-to-end testing
- Performance optimization
- Documentation
- Deployment preparation

## 🎯 Next Steps

1. **Verify setup works** - Run both backend and frontend
2. **Check API keys** - Make sure OpenAI key is valid
3. **Read Week 1 Plan** - Start with Day 1 tasks (Confluence scraper)

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [LlamaIndex Documentation](https://docs.llamaindex.ai/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

## 💡 Tips

- Keep both terminals open during development
- Backend changes auto-reload with `--reload` flag
- Frontend has hot-reload by default
- Check `logs/` directory for error logs
- Use `http://localhost:8000/docs` for API documentation (Swagger UI)

## 🆘 Need Help?

If you encounter issues:
1. Check the logs in `backend/logs/`
2. Verify all environment variables are set
3. Make sure all dependencies are installed
4. Try restarting both services

---

Happy coding! 🚀
