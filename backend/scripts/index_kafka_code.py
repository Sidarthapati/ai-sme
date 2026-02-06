"""
Production script to index Apache Kafka code repository.
Run this to collect code samples for the POC.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.github_indexer import index_kafka_repository
from src.utils import log


def main():
    """Index Apache Kafka code repository."""
    
    repo_path = "/Users/sidarthapati/Desktop/Projects/kafka"
    max_files = 150
    output_dir = "/Users/sidarthapati/Desktop/Projects/AI SME/data/raw/github"
    target_dirs = ["clients/src/main", "core/src/main", "connect/api/src/main", "streams/src/main"]
    
    print(f"\n💻 Indexing {max_files} code files...")
    
    try:
        documents = index_kafka_repository(
            repo_path=repo_path,
            max_files=max_files,
            output_dir=output_dir,
            target_dirs=target_dirs
        )
        
        files_indexed = len(set(doc.file_path for doc in documents))
        total_chars = sum(len(doc.content) for doc in documents)
        
        print(f"✅ Indexed {files_indexed} files into {len(documents)} chunks ({total_chars:,} characters)")
        print(f"   Saved to: {Path(output_dir).absolute()}\n")
        
        return 0
        
    except Exception as e:
        log.error(f"Indexing failed: {e}")
        print(f"❌ Error: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
