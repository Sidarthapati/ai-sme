# Day 3-4 Setup Instructions

Complete guide for setting up embeddings and vector database.

## ✅ Files Created

### Indexers Module (3 files):
1. `backend/src/indexers/chunker.py` - Document chunking with token counting
2. `backend/src/indexers/embeddings.py` - OpenAI embedding generation
3. `backend/src/indexers/document_processor.py` - Complete processing pipeline

### RAG Module (1 file):
4. `backend/src/rag/vector_store.py` - ChromaDB vector database interface

### Scripts (2 files):
5. `backend/scripts/test_indexing_pipeline.py` - Test suite
6. `backend/scripts/build_vector_database.py` - Production indexing script

---

## 🔧 Setup Steps

### Step 1: Get OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

### Step 2: Add API Key to .env

Edit `backend/.env` and add your key:

```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

### Step 3: Install Required Dependencies

Run this command:

```bash
cd "/Users/sidarthapati/Desktop/Projects/AI SME/backend"
source venv/bin/activate
pip install tiktoken chromadb openai tenacity
```

**What these do:**
- `tiktoken` - Token counting for chunking
- `chromadb` - Vector database
- `openai` - OpenAI API client
- `tenacity` - Retry logic for API calls

---

## 🧪 Testing

### Test 1: Run the Test Suite (Recommended First)

This tests each component separately:

```bash
cd "/Users/sidarthapati/Desktop/Projects/AI SME/backend"
source venv/bin/activate
python scripts/test_indexing_pipeline.py
```

**What it tests:**
1. ✅ Document chunking (no API needed)
2. ✅ Embedding generation (needs API key)
3. ✅ Vector store operations (no API needed)
4. ✅ Full pipeline (needs API key, uses 2 docs)

**Expected output:** All 4 tests should pass

---

## 🚀 Building the Vector Database

### Option A: Build Full Database (Recommended)

Process all your scraped documents:

```bash
cd "/Users/sidarthapati/Desktop/Projects/AI SME/backend"
source venv/bin/activate
python scripts/build_vector_database.py
```

**This will:**
1. Load all Confluence and GitHub documents
2. Chunk them into ~800 token pieces
3. Generate embeddings using OpenAI
4. Store in ChromaDB at `backend/chroma_db/`

**Time:** ~2-5 minutes depending on document count
**Cost:** ~$0.01-0.05 (OpenAI embeddings are cheap)

### Option B: Test with Small Sample First

If you want to test with fewer documents first, you can modify the script or just run the test suite.

---

## 📊 What Happens

### Document Processing Flow:

```
Raw JSON files (data/raw/)
    ↓
Load documents
    ↓
Chunk into 800-token pieces with 100-token overlap
    ↓
Generate embeddings (3072 dimensions)
    ↓
Store in ChromaDB (chroma_db/)
    ↓
Ready for semantic search!
```

### Example:
- **Input:** 49 Confluence pages + 50 code files
- **After chunking:** ~300-500 chunks
- **After embedding:** Each chunk has 3072-dim vector
- **Storage:** ~50-100MB in ChromaDB

---

## 🔍 Verifying It Works

After building the database, you can check:

```python
from src.rag import VectorStore

# Connect to database
vector_store = VectorStore()

# Get stats
stats = vector_store.get_stats()
print(f"Total documents: {stats['total_documents']}")

# Test search
results = vector_store.search_by_text(
    "How does Kafka handle replication?",
    n_results=3
)
print(f"Found {len(results['documents'])} results")
```

---

## ⚠️ Troubleshooting

### Error: "Field required: openai_api_key"
**Fix:** Add `OPENAI_API_KEY` to `backend/.env`

### Error: "No module named 'tiktoken'"
**Fix:** Run `pip install tiktoken chromadb openai tenacity`

### Error: "Rate limit exceeded"
**Fix:** You're hitting OpenAI rate limits. Wait a minute or reduce batch size.

### Error: "No documents found"
**Fix:** Run the scrapers first:
```bash
python scripts/scrape_kafka_docs.py
python scripts/index_kafka_code.py
```

### Error: "Insufficient credits"
**Fix:** Add credits to your OpenAI account at https://platform.openai.com/account/billing

---

## 💰 Cost Estimate

**OpenAI Embedding Costs:**
- Model: text-embedding-3-large
- Price: $0.00013 per 1K tokens
- For ~500 chunks of 800 tokens each: ~$0.05

**Very cheap!** The entire POC should cost less than $1 in embeddings.

---

## 📁 Output

After building, you'll have:

```
backend/
├── chroma_db/              # Vector database (created)
│   └── [ChromaDB files]
└── data/
    └── raw/
        ├── confluence/     # Your scraped docs
        └── github/         # Your indexed code
```

---

## ✅ Success Criteria

You'll know it worked when:

1. ✅ Test script passes all 4 tests
2. ✅ `chroma_db/` directory is created
3. ✅ Vector store shows correct document count
4. ✅ Can search and get relevant results

---

## 🎯 Next Steps (Day 5)

Once vector database is built:
1. Build RAG pipeline (retriever + generator)
2. Create API endpoints for chat
3. Test end-to-end queries

---

## 📝 Quick Commands Reference

```bash
# Activate environment
cd "/Users/sidarthapati/Desktop/Projects/AI SME/backend"
source venv/bin/activate

# Install dependencies
pip install tiktoken chromadb openai tenacity

# Test pipeline
python scripts/test_indexing_pipeline.py

# Build vector database
python scripts/build_vector_database.py

# Check if it worked
python -c "from src.rag import VectorStore; vs = VectorStore(); print(f'Documents: {vs.count()}')"
```

---

## 🆘 Need Help?

If you get stuck:
1. Check `backend/logs/app.log` for detailed errors
2. Verify API key is correct in `.env`
3. Make sure you have scraped documents first
4. Check OpenAI account has credits

---

**Ready to proceed?** Run the test script first to make sure everything works!
