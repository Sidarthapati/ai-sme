# Railway ChromaDB Setup Guide

## Problem
ChromaDB is empty in production (0 documents). Need to populate it and persist it.

## Solution 1: Copy Local ChromaDB to Railway (Fastest)

### Prerequisites
- Railway CLI installed: `npm i -g @railway/cli`
- Local `chroma_db` directory with data (should have ~970 documents)

### Steps

1. **Add Railway Volume** (if not done):
   - Railway → Backend Service → Settings → Volumes
   - Add Volume: `/app/chroma_db`, 1GB

2. **Login to Railway CLI**:
   ```bash
   railway login
   ```

3. **Link to your project**:
   ```bash
   cd backend
   railway link
   ```

4. **Copy local chroma_db to Railway**:
   ```bash
   # From your local backend directory
   railway run --service ai-sme --command "rm -rf /app/chroma_db/*" || true
   
   # Copy files (if Railway CLI supports file copy)
   # OR use Railway's file upload feature if available
   ```

**Note**: Railway CLI might not support direct file copy. Use Option B instead.

---

## Solution 2: Rebuild Vector DB in Production (Recommended)

### Step 1: Upload Data Files to Railway

You need to get your `data/raw/confluence` and `data/raw/github` files to Railway.

**Option 2A: Use Railway's File Upload** (if available)
- Railway → Backend Service → Files/Storage
- Upload your `data/raw` directory

**Option 2B: Add Data Files to Git** (temporary, then remove)
1. Copy data files to backend:
   ```bash
   cp -r data backend/data
   ```
2. Commit and push (temporary)
3. Rebuild vector DB in Railway
4. Remove from git (add to .gitignore)

**Option 2C: Create a One-Time Build Script**

Create a script that downloads/scrapes data in production, then builds the vector DB.

### Step 2: Create Production Build Script

Create `backend/scripts/build_vector_db_production.py`:

```python
"""
Production script to build vector database in Railway.
Uses environment variables for paths.
"""
import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.indexers import DocumentProcessor
from src.rag import VectorStore
from src.utils import log
from src.config import settings

def main():
    """Build vector database using environment-configured paths."""
    
    # Use environment variables or defaults
    confluence_dir = os.getenv('DATA_CONFLUENCE_DIR', '/app/data/raw/confluence')
    github_dir = os.getenv('DATA_GITHUB_DIR', '/app/data/raw/github')
    vector_db_dir = settings.chroma_persist_directory
    collection_name = "ai_sme_documents"
    
    log.info(f"🔨 Building vector database...")
    log.info(f"Confluence dir: {confluence_dir}")
    log.info(f"GitHub dir: {github_dir}")
    log.info(f"Vector DB dir: {vector_db_dir}")
    
    try:
        processor = DocumentProcessor(chunk_size=800, chunk_overlap=100)
        vector_store = VectorStore(persist_directory=vector_db_dir, collection_name=collection_name)
        
        # Check if data directories exist
        if not Path(confluence_dir).exists() and not Path(github_dir).exists():
            log.error("❌ Data directories not found!")
            log.error("Please ensure data/raw/confluence and data/raw/github exist")
            return 1
        
        log.info("Processing documents and generating embeddings...")
        processed_chunks = processor.process_from_directories(
            confluence_dir=confluence_dir if Path(confluence_dir).exists() else None,
            github_dir=github_dir if Path(github_dir).exists() else None,
            generate_embeddings=True
        )
        
        all_chunks = []
        for source_type, chunks in processed_chunks.items():
            all_chunks.extend(chunks)
        
        if not all_chunks:
            log.error("❌ No chunks processed! Check data directories.")
            return 1
        
        log.info(f"Indexing {len(all_chunks)} chunks into vector database...")
        added_count = vector_store.add_documents(all_chunks)
        
        stats = vector_store.get_stats()
        
        log.info(f"✅ Vector database built successfully")
        log.info(f"   Total documents: {stats['total_documents']}")
        log.info(f"   Location: {stats['persist_directory']}")
        
        return 0
        
    except Exception as e:
        log.error(f"Build failed: {e}")
        import traceback
        log.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### Step 3: Run Build Script in Railway

**Via Railway CLI**:
```bash
railway run --service ai-sme python scripts/build_vector_db_production.py
```

**Via Railway Dashboard**:
- Railway → Backend Service → Deployments → Latest
- Open shell/terminal (if available)
- Run: `python scripts/build_vector_db_production.py`

---

## Solution 3: Auto-Rebuild on Startup (Advanced)

Modify `backend/main.py` to check if ChromaDB is empty and rebuild automatically.

---

## Quick Fix: Copy Local ChromaDB via Railway Volume

If you have Railway CLI and your local chroma_db is ready:

1. **Add Volume** (as above)
2. **Use Railway Shell**:
   ```bash
   railway shell --service ai-sme
   ```
3. **In the shell, check volume**:
   ```bash
   ls -la /app/chroma_db
   ```
4. **Copy files** (you'll need to upload them somehow)

**Easiest**: Use Option 2B - temporarily commit data files, rebuild, then remove.

---

## Verification

After building, check logs:
```
Collection: ai_sme_documents (970 documents)  ← Should show ~970, not 0
```

Then test a query - it should find documents!
