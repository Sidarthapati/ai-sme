"""
Test script for the complete indexing pipeline.
Tests chunking, embedding, and vector store operations.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.indexers import DocumentProcessor
from src.rag import VectorStore
from src.utils import log


def test_chunking():
    """Test document chunking."""
    print("\n" + "="*70)
    print("TEST 1: Document Chunking")
    print("="*70 + "\n")
    
    # Load a few documents
    confluence_dir = Path("/Users/sidarthapati/Desktop/Projects/AI SME/data/raw/confluence")
    github_dir = Path("/Users/sidarthapati/Desktop/Projects/AI SME/data/raw/github")
    
    processor = DocumentProcessor(chunk_size=800, chunk_overlap=100)
    
    # Load documents
    documents = processor.load_all_documents(
        confluence_dir=confluence_dir,
        github_dir=github_dir
    )
    
    total_docs = len(documents['confluence']) + len(documents['github'])
    print(f"Loaded {total_docs} documents")
    print(f"  • Confluence: {len(documents['confluence'])}")
    print(f"  • GitHub: {len(documents['github'])}")
    
    # Chunk without embeddings (faster for testing)
    if documents['confluence']:
        chunks = processor.process_documents(
            documents['confluence'][:3],  # Just 3 docs for testing
            generate_embeddings=False
        )
        
        print(f"\n✅ Chunked 3 Confluence documents into {len(chunks)} chunks")
        print(f"\nSample chunk:")
        print(f"  • ID: {chunks[0]['chunk_id']}")
        print(f"  • Tokens: {chunks[0]['token_count']}")
        print(f"  • Content preview: {chunks[0]['content'][:200]}...")
        return True
    else:
        print("❌ No Confluence documents found")
        return False


def test_embeddings():
    """Test embedding generation."""
    print("\n" + "="*70)
    print("TEST 2: Embedding Generation")
    print("="*70 + "\n")
    
    from src.indexers import EmbeddingService
    
    try:
        service = EmbeddingService()
        
        # Test single embedding
        test_text = "Apache Kafka is a distributed streaming platform."
        embedding = service.embed_text(test_text)
        
        print(f"✅ Generated embedding for test text")
        print(f"  • Embedding dimensions: {len(embedding)}")
        print(f"  • First 5 values: {embedding[:5]}")
        return True
        
    except Exception as e:
        print(f"❌ Embedding failed: {e}")
        print("\nMake sure OPENAI_API_KEY is set in backend/.env")
        return False


def test_vector_store():
    """Test vector store operations."""
    print("\n" + "="*70)
    print("TEST 3: Vector Store Operations")
    print("="*70 + "\n")
    
    # Create test vector store
    vector_store = VectorStore(
        persist_directory="./test_chroma_db",
        collection_name="test_collection"
    )
    
    # Reset for clean test
    vector_store.reset()
    
    # Create test documents with embeddings
    test_docs = [
        {
            'id': 'test_1',
            'content': 'Apache Kafka is a distributed streaming platform',
            'embedding': [0.1] * 3072,  # Dummy embedding
            'source_type': 'test'
        },
        {
            'id': 'test_2',
            'content': 'Kafka handles real-time data feeds',
            'embedding': [0.2] * 3072,
            'source_type': 'test'
        }
    ]
    
    # Add documents
    added = vector_store.add_documents(test_docs)
    print(f"✅ Added {added} test documents to vector store")
    
    # Get stats
    stats = vector_store.get_stats()
    print(f"\nVector store stats:")
    print(f"  • Total documents: {stats['total_documents']}")
    print(f"  • Collection: {stats['collection_name']}")
    
    # Test retrieval
    doc = vector_store.get_by_id('test_1')
    if doc:
        print(f"\n✅ Retrieved document by ID")
        print(f"  • Content: {doc['content'][:50]}...")
    
    # Cleanup
    import shutil
    shutil.rmtree("./test_chroma_db", ignore_errors=True)
    
    return True


def test_full_pipeline():
    """Test the complete pipeline with real data."""
    print("\n" + "="*70)
    print("TEST 4: Full Pipeline (Small Sample)")
    print("="*70 + "\n")
    
    confluence_dir = "data/raw/confluence"
    github_dir = "data/raw/github"
    
    processor = DocumentProcessor(chunk_size=800, chunk_overlap=100)
    
    # Load documents
    documents = processor.load_all_documents(
        confluence_dir=Path(confluence_dir),
        github_dir=Path(github_dir)
    )
    
    total = len(documents['confluence']) + len(documents['github'])
    
    if total == 0:
        print("❌ No documents found. Run scrapers first!")
        return False
    
    print(f"Loaded {total} documents")
    
    # Process just 2 documents (to save API calls)
    sample_docs = (documents['confluence'][:1] + documents['github'][:1])
    
    print(f"\nProcessing {len(sample_docs)} sample documents...")
    print("(This will use OpenAI API - make sure you have credits)")
    
    try:
        chunks = processor.process_documents(
            sample_docs,
            generate_embeddings=True
        )
        
        print(f"\n✅ Pipeline complete!")
        print(f"  • Documents processed: {len(sample_docs)}")
        print(f"  • Chunks created: {len(chunks)}")
        print(f"  • Chunks with embeddings: {sum(1 for c in chunks if c.get('embedding'))}")
        
        # Show sample
        if chunks:
            chunk = chunks[0]
            print(f"\nSample chunk:")
            print(f"  • ID: {chunk['chunk_id']}")
            print(f"  • Tokens: {chunk['token_count']}")
            print(f"  • Has embedding: {bool(chunk.get('embedding'))}")
            print(f"  • Embedding dims: {len(chunk.get('embedding', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "🚀 " + "="*66 + " 🚀")
    print("   INDEXING PIPELINE TEST SUITE")
    print("   Testing chunking, embeddings, and vector store")
    print("🚀 " + "="*66 + " 🚀\n")
    
    results = []
    
    # Test 1: Chunking (no API needed)
    try:
        results.append(("Document Chunking", test_chunking()))
    except Exception as e:
        log.error(f"Test 1 failed: {e}")
        results.append(("Document Chunking", False))
    
    # Test 2: Embeddings (needs API key)
    try:
        results.append(("Embedding Generation", test_embeddings()))
    except Exception as e:
        log.error(f"Test 2 failed: {e}")
        results.append(("Embedding Generation", False))
    
    # Test 3: Vector store (no API needed)
    try:
        results.append(("Vector Store", test_vector_store()))
    except Exception as e:
        log.error(f"Test 3 failed: {e}")
        results.append(("Vector Store", False))
    
    # Test 4: Full pipeline (needs API key)
    try:
        results.append(("Full Pipeline", test_full_pipeline()))
    except Exception as e:
        log.error(f"Test 4 failed: {e}")
        results.append(("Full Pipeline", False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70 + "\n")
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Indexing pipeline is ready! 🎉\n")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
