"""
Production script to build the complete vector database.
Processes all documents and creates the searchable index.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.indexers import DocumentProcessor
from src.rag import VectorStore
from src.utils import log


def main():
    """Build the complete vector database."""
    
    confluence_dir = "/Users/sidarthapati/Desktop/Projects/AI SME/data/raw/confluence"
    github_dir = "/Users/sidarthapati/Desktop/Projects/AI SME/data/raw/github"
    vector_db_dir = "./chroma_db"
    collection_name = "ai_sme_documents"
    
    print(f"\n🔨 Building vector database...")
    
    try:
        processor = DocumentProcessor(chunk_size=800, chunk_overlap=100)
        vector_store = VectorStore(persist_directory=vector_db_dir, collection_name=collection_name)
        
        print("Processing documents and generating embeddings...")
        processed_chunks = processor.process_from_directories(
            confluence_dir=confluence_dir,
            github_dir=github_dir,
            generate_embeddings=True
        )
        
        all_chunks = []
        for source_type, chunks in processed_chunks.items():
            all_chunks.extend(chunks)
        
        print(f"Indexing {len(all_chunks)} chunks into vector database...")
        added_count = vector_store.add_documents(all_chunks)
        
        stats = vector_store.get_stats()
        
        print(f"\n✅ Vector database built successfully")
        print(f"   Total documents: {stats['total_documents']}")
        print(f"   Location: {stats['persist_directory']}\n")
        
        return 0
        
    except Exception as e:
        log.error(f"Build failed: {e}")
        print(f"❌ Error: {e}")
        print("   Check: 1) OPENAI_API_KEY in .env, 2) scraped documents exist, 3) API credits\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
