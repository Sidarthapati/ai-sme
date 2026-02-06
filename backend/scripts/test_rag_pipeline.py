"""
Test script for RAG pipeline.
Tests query answering with the vector database.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag import RAGPipeline, create_rag_pipeline
from src.utils import log


def test_basic_query():
    """Test a basic query."""
    print("\n" + "="*70)
    print("TEST 1: Basic Query")
    print("="*70 + "\n")
    
    pipeline = create_rag_pipeline()
    
    question = "How does Kafka handle replication?"
    
    print(f"Question: {question}\n")
    print("Processing...")
    
    result = pipeline.query(question)
    
    print(f"\n✅ Answer ({len(result['answer'])} characters):")
    print("-" * 70)
    print(result['answer'])
    print("-" * 70)
    
    print(f"\nSources ({len(result['sources'])}):")
    for i, source in enumerate(result['sources'][:3], 1):
        print(f"  {i}. {source['title'][:60]}...")
        print(f"     URL: {source['url'][:80]}...")
    
    return True


def test_code_query():
    """Test a code-specific query."""
    print("\n" + "="*70)
    print("TEST 2: Code Query")
    print("="*70 + "\n")
    
    pipeline = create_rag_pipeline()
    
    question = "Show me how to create a Kafka producer"
    
    print(f"Question: {question}\n")
    
    result = pipeline.query(question, source_type='github')
    
    print(f"✅ Answer ({len(result['answer'])} characters):")
    print("-" * 70)
    print(result['answer'][:500] + "..." if len(result['answer']) > 500 else result['answer'])
    print("-" * 70)
    
    return True


def test_documentation_query():
    """Test a documentation query."""
    print("\n" + "="*70)
    print("TEST 3: Documentation Query")
    print("="*70 + "\n")
    
    pipeline = create_rag_pipeline()
    
    question = "What are the deployment requirements for Kafka?"
    
    print(f"Question: {question}\n")
    
    result = pipeline.query(question, source_type='confluence')
    
    print(f"✅ Answer ({len(result['answer'])} characters):")
    print("-" * 70)
    print(result['answer'][:500] + "..." if len(result['answer']) > 500 else result['answer'])
    print("-" * 70)
    
    return True


def test_pipeline_stats():
    """Test getting pipeline statistics."""
    print("\n" + "="*70)
    print("TEST 4: Pipeline Statistics")
    print("="*70 + "\n")
    
    pipeline = create_rag_pipeline()
    stats = pipeline.get_stats()
    
    print("Pipeline Statistics:")
    print(f"  • Vector DB documents: {stats['vector_store']['total_documents']}")
    print(f"  • Retrieval top_k: {stats['retrieval_top_k']}")
    print(f"  • Generator model: {stats['generator_model']}")
    
    return True


def main():
    """Run all tests."""
    print("\n🚀 RAG PIPELINE TEST SUITE 🚀\n")
    
    results = []
    
    try:
        results.append(("Basic Query", test_basic_query()))
    except Exception as e:
        log.error(f"Test 1 failed: {e}")
        results.append(("Basic Query", False))
    
    try:
        results.append(("Code Query", test_code_query()))
    except Exception as e:
        log.error(f"Test 2 failed: {e}")
        results.append(("Code Query", False))
    
    try:
        results.append(("Documentation Query", test_documentation_query()))
    except Exception as e:
        log.error(f"Test 3 failed: {e}")
        results.append(("Documentation Query", False))
    
    try:
        results.append(("Pipeline Stats", test_pipeline_stats()))
    except Exception as e:
        log.error(f"Test 4 failed: {e}")
        results.append(("Pipeline Stats", False))
    
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
        print("\n🎉 All tests passed! RAG pipeline is working! 🎉\n")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
