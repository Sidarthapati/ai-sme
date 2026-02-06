# Quick Reference Guide

Fast reference for common commands and information.

## 🚀 Starting the Application

### Backend
```bash
cd backend
source venv/bin/activate  # Activate virtual environment
python main.py            # Start server
```
**URL:** http://localhost:8000
**API Docs:** http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm run dev              # Start dev server
```
**URL:** http://localhost:3000

### Docker (Both)
```bash
docker-compose up -d     # Start all services
docker-compose logs -f   # View logs
docker-compose down      # Stop all services
```

## 📁 Important Files

### Configuration
- `backend/.env` - Backend environment variables (API keys, etc.)
- `frontend/.env.local` - Frontend environment variables
- `backend/src/config/settings.py` - Configuration management

### Entry Points
- `backend/main.py` - Backend application
- `frontend/app/page.tsx` - Frontend home page

### Data Storage
- `data/raw/` - Raw scraped data
- `data/processed/` - Processed documents
- `chroma_db/` - Vector database (auto-created)

## 🔑 Environment Variables

### Backend (.env)
```env
# Required
OPENAI_API_KEY=sk-...

# Optional (has defaults)
OPENAI_MODEL=gpt-4-turbo-preview
CHUNK_SIZE=800
RETRIEVAL_TOP_K=5
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🛠️ Common Commands

### Backend

```bash
# Install/Update dependencies
cd "/Users/sidarthapati/Desktop/Projects/AI SME/backend"
source venv/bin/activate
python main.py
pip install -r requirements.txt

# Create new migration
# (Add when we have database)

# Run tests
pytest

# Check code style
black .
flake8 .

# View logs
tail -f logs/app.log
```

### Frontend

```bash
# Install/Update dependencies
npm install

# Build for production
npm run build

# Run production build
npm start

# Type check
npm run type-check

# Lint
npm run lint
```

## 🐛 Troubleshooting

### Backend not starting
```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Check .env file exists
ls -la backend/.env
```

### Frontend not starting
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install

# Check Node version
node --version  # Should be 18+
```

### API key issues
```bash
# Verify .env file has the key
cat backend/.env | grep OPENAI_API_KEY

# Test API key
python -c "import openai; openai.api_key='YOUR_KEY'; print('Key valid')"
```

## 📊 Project Structure Quick View

```
AI SME/
├── backend/              # Python FastAPI backend
│   ├── src/
│   │   ├── api/         # API endpoints
│   │   ├── config/      # Configuration
│   │   ├── indexers/    # Document processing
│   │   ├── rag/         # RAG pipeline
│   │   ├── scrapers/    # Data collection
│   │   └── utils/       # Utilities
│   ├── main.py          # Entry point
│   └── requirements.txt # Dependencies
│
├── frontend/            # React/Next.js frontend
│   ├── app/            # Pages
│   ├── components/     # React components
│   └── lib/            # Utilities
│
├── data/               # Data storage
│   ├── raw/           # Scraped data
│   └── processed/     # Processed data
│
└── docs/              # Documentation (to be added)
```

## 🎯 Current Status

- ✅ Project structure created
- ✅ Configuration management set up
- ✅ Backend scaffolding ready
- ✅ Frontend scaffolding ready
- ✅ Docker setup prepared
- ⏳ Waiting: OpenAI API key
- ⏳ Next: Day 1 - Confluence scraper

## 📝 Week 1 Goals

**By end of Week 1, you should have:**
- Working Confluence scraper
- GitHub code indexer
- Vector database populated
- RAG pipeline functional
- API endpoints working
- Can ask questions and get answers

## 🔗 Useful Links

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [LlamaIndex Docs](https://docs.llamaindex.ai/)
- [OpenAI API](https://platform.openai.com/docs)

### Data Sources (POC)
- [Apache Kafka Confluence](https://cwiki.apache.org/confluence/display/KAFKA)
- [Apache Kafka GitHub](https://github.com/apache/kafka)

### Tools
- [OpenAI Playground](https://platform.openai.com/playground)
- [ChromaDB Docs](https://docs.trychroma.com/)

## 💡 Tips

1. **Keep terminals open** - Run backend and frontend in separate terminals
2. **Check logs** - Backend logs are in `backend/logs/`
3. **Use Swagger UI** - Access at http://localhost:8000/docs
4. **Hot reload works** - Changes auto-reload in both backend and frontend
5. **Git commit often** - Commit after each working feature

## 🆘 Getting Help

1. Check error logs in `backend/logs/`
2. Review `.env` files for missing keys
3. Verify all dependencies installed
4. Check if services are running on correct ports
5. Refer to `SETUP.md` for detailed setup

## 📦 Installing Additional Packages

### Backend
```bash
cd backend
source venv/bin/activate
pip install package-name
pip freeze > requirements.txt  # Update requirements
```

### Frontend
```bash
cd frontend
npm install package-name
# package.json automatically updates
```

## 🎨 Code Style

### Python (Backend)
- Use type hints
- Follow PEP 8
- Docstrings for all functions
- Max line length: 100

### TypeScript (Frontend)
- Use TypeScript types
- Functional components
- Use hooks (useState, useEffect, etc.)
- Follow React best practices

---

**Remember:** You're building a POC, so focus on functionality first, then polish! 🚀
