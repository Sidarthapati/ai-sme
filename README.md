# Currently Hosted at : https://ami-sme-frontend-production.up.railway.app/chat 

# AI SME - Intelligent Documentation Assistant

An AI-powered assistant trained on Confluence documentation and GitHub codebases to answer team questions and provide instant access to documentation and code references.

## 🎯 Project Overview

This POC demonstrates an enterprise-grade RAG (Retrieval Augmented Generation) system that:
- Indexes Confluence documentation and GitHub repositories
- Answers questions with source citations
- Supports uploading additional documents (PDF, DOCX, TXT)
- Provides a modern chat interface for developers

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│     React Frontend (Next.js)        │
│  - Chat UI                          │
│  - Document Upload                  │
│  - Source Display                   │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│     FastAPI Backend                 │
│  - RAG Pipeline                     │
│  - Document Processing              │
│  - API Endpoints                    │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│     ChromaDB Vector Store           │
│  - Embeddings                       │
│  - Semantic Search                  │
└─────────────────────────────────────┘
```

## 📁 Project Structure

```
AI SME/
├── backend/              # Python backend service
│   ├── src/
│   │   ├── scrapers/    # Confluence & GitHub scrapers
│   │   ├── indexers/    # Document indexing logic
│   │   ├── rag/         # RAG pipeline implementation
│   │   ├── api/         # FastAPI endpoints
│   │   ├── config/      # Configuration management
│   │   └── utils/       # Helper utilities
│   ├── tests/           # Backend tests
│   ├── requirements.txt # Python dependencies
│   ├── .env.example     # Environment template
│   └── main.py          # Application entry point
├── frontend/            # React frontend
│   ├── app/            # Next.js app directory
│   ├── components/     # React components
│   ├── lib/            # Utilities & API client
│   └── package.json    # Node dependencies
├── data/               # Data storage
│   ├── raw/           # Raw scraped data
│   └── processed/     # Processed documents
├── docs/              # Documentation
└── docker-compose.yml # Container orchestration
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key (or Azure OpenAI)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python main.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## 🔧 Configuration

Create a `.env` file in the backend directory:

```env
OPENAI_API_KEY=your_key_here
VECTOR_DB_PATH=./chroma_db
CONFLUENCE_BASE_URL=https://your-confluence.atlassian.net
GITHUB_TOKEN=your_github_token
```

## 📊 Current Status

### ✅ Week 1 Progress (Backend Foundation)
- [ ] Project structure setup
- [ ] Confluence scraper
- [ ] GitHub indexer
- [ ] Vector database setup
- [ ] RAG pipeline
- [ ] API endpoints
- [ ] Document upload processing

### 🔜 Week 2 (Frontend Development)
- [ ] Next.js setup
- [ ] Chat interface
- [ ] Source citations display
- [ ] File upload UI
- [ ] Advanced features

### 🔜 Week 3 (Polish & Demo)
- [ ] Quality improvements
- [ ] Admin panel
- [ ] Documentation
- [ ] Deployment setup

## 🎓 POC Data Source

Currently using **Apache Kafka** project for POC:
- **Confluence**: https://cwiki.apache.org/confluence/display/KAFKA
- **GitHub**: https://github.com/apache/kafka

This demonstrates the system with real-world, production-quality documentation and code.

## 📝 License

Internal use only - Wells Fargo

## 👥 Contact

For questions or support, contact the development team.
