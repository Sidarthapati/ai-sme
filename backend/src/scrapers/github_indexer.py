"""
GitHub code indexer for extracting and indexing code from local repositories.
Designed to work with the Apache Kafka repository for POC.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Set
import json
from dataclasses import dataclass, asdict
import fnmatch

from ..utils import log


@dataclass
class CodeDocument:
    """Data class for an indexed code document."""
    id: str
    title: str
    content: str
    url: str
    file_path: str
    repo_name: str
    language: str
    start_line: int
    end_line: int
    last_modified: Optional[str]
    source_type: str = "github"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class LocalGitHubIndexer:
    """
    Indexer for local Git repositories.
    Walks through files and creates searchable code chunks.
    """
    
    def __init__(
        self,
        repo_path: str,
        repo_name: str,
        github_url: Optional[str] = None
    ):
        """
        Initialize the indexer.
        
        Args:
            repo_path: Path to the local Git repository
            repo_name: Name of the repository (e.g., 'kafka')
            github_url: Optional GitHub URL for generating links
        """
        self.repo_path = Path(repo_path)
        self.repo_name = repo_name
        self.github_url = github_url or f"https://github.com/apache/{repo_name}"
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        log.info(f"Initialized indexer for {repo_name} at {repo_path}")
    
    def should_index_file(self, file_path: Path) -> bool:
        """
        Determine if a file should be indexed.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file should be indexed
        """
        # Get relative path for pattern matching
        try:
            rel_path = file_path.relative_to(self.repo_path)
            rel_path_str = str(rel_path)
        except ValueError:
            return False
        
        # Exclude patterns
        exclude_patterns = [
            '*/test/*', '*/tests/*', '*Test.java', '*Test.scala',
            '*/target/*', '*/build/*', '*/dist/*', '*/out/*',
            '*/node_modules/*', '*/.git/*', '*/.gradle/*',
            '*/generated/*', '*/generated-src/*',
            '*/.idea/*', '*/.vscode/*',
            '*/checkstyle/*', '*/jmh-benchmarks/*',
        ]
        
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(rel_path_str, pattern):
                return False
        
        # Include only code files
        include_extensions = {
            '.java', '.scala', '.py', '.js', '.ts',
            '.md', '.rst', '.txt',
            '.yaml', '.yml', '.properties', '.conf',
            '.sh', '.gradle', '.xml'
        }
        
        return file_path.suffix.lower() in include_extensions
    
    def detect_language(self, file_path: Path) -> str:
        """
        Detect programming language from file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language identifier
        """
        ext_map = {
            '.java': 'java',
            '.scala': 'scala',
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.md': 'markdown',
            '.rst': 'restructuredtext',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.properties': 'properties',
            '.conf': 'config',
            '.sh': 'bash',
            '.gradle': 'gradle',
            '.xml': 'xml',
            '.txt': 'text',
        }
        
        return ext_map.get(file_path.suffix.lower(), 'plaintext')
    
    def chunk_code(
        self,
        content: str,
        file_path: Path,
        chunk_size: int = 150,
        overlap: int = 20
    ) -> List[Dict]:
        """
        Split code into chunks with overlap.
        
        Args:
            content: File content
            file_path: Path to the file
            chunk_size: Number of lines per chunk
            overlap: Number of overlapping lines between chunks
            
        Returns:
            List of chunk dictionaries
        """
        lines = content.split('\n')
        chunks = []
        
        # For small files, keep as single chunk
        if len(lines) <= chunk_size:
            return [{
                'content': content,
                'start_line': 1,
                'end_line': len(lines)
            }]
        
        # For large files, create overlapping chunks
        i = 0
        while i < len(lines):
            end = min(i + chunk_size, len(lines))
            chunk_lines = lines[i:end]
            
            chunks.append({
                'content': '\n'.join(chunk_lines),
                'start_line': i + 1,
                'end_line': end
            })
            
            # Move forward with overlap
            i += chunk_size - overlap
            
            # Avoid tiny last chunks
            if i < len(lines) and len(lines) - i < overlap:
                break
        
        return chunks
    
    def generate_github_url(
        self,
        file_path: Path,
        start_line: int,
        end_line: int
    ) -> str:
        """
        Generate GitHub URL for a code chunk.
        
        Args:
            file_path: Path to the file
            start_line: Starting line number
            end_line: Ending line number
            
        Returns:
            GitHub URL with line numbers
        """
        rel_path = file_path.relative_to(self.repo_path)
        
        # Use 'trunk' or 'main' as default branch
        url = f"{self.github_url}/blob/trunk/{rel_path}"
        
        if start_line == end_line:
            url += f"#L{start_line}"
        else:
            url += f"#L{start_line}-L{end_line}"
        
        return url
    
    def get_last_modified(self, file_path: Path) -> Optional[str]:
        """
        Get last modified timestamp for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            ISO format timestamp or None
        """
        try:
            from datetime import datetime
            mtime = file_path.stat().st_mtime
            dt = datetime.fromtimestamp(mtime)
            return dt.isoformat()
        except Exception as e:
            log.warning(f"Could not get mtime for {file_path}: {e}")
            return None
    
    def index_file(self, file_path: Path) -> List[CodeDocument]:
        """
        Index a single file.
        
        Args:
            file_path: Path to the file to index
            
        Returns:
            List of CodeDocument objects (one per chunk)
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Skip empty files
            if not content.strip():
                return []
            
            # Get metadata
            rel_path = file_path.relative_to(self.repo_path)
            language = self.detect_language(file_path)
            last_modified = self.get_last_modified(file_path)
            
            # Chunk the content
            chunks = self.chunk_code(content, file_path)
            
            # Create documents
            documents = []
            for chunk in chunks:
                doc_id = f"{self.repo_name}_{rel_path}_{chunk['start_line']}"
                doc_id = doc_id.replace('/', '_').replace(' ', '_')
                
                url = self.generate_github_url(
                    file_path,
                    chunk['start_line'],
                    chunk['end_line']
                )
                
                doc = CodeDocument(
                    id=doc_id,
                    title=f"{self.repo_name}/{rel_path}",
                    content=chunk['content'],
                    url=url,
                    file_path=str(rel_path),
                    repo_name=self.repo_name,
                    language=language,
                    start_line=chunk['start_line'],
                    end_line=chunk['end_line'],
                    last_modified=last_modified,
                    source_type="github"
                )
                
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            log.error(f"Error indexing {file_path}: {e}")
            return []
    
    def index_repository(
        self,
        max_files: Optional[int] = None,
        target_dirs: Optional[List[str]] = None,
        output_dir: Optional[Path] = None
    ) -> List[CodeDocument]:
        """
        Index all files in the repository.
        
        Args:
            max_files: Maximum number of files to index (None = all)
            target_dirs: Specific directories to index (None = all)
            output_dir: Optional directory to save JSON files
            
        Returns:
            List of all CodeDocument objects
        """
        log.info(f"Starting repository indexing: {self.repo_name}")
        
        # Determine which directories to scan
        if target_dirs:
            search_paths = [self.repo_path / d for d in target_dirs]
        else:
            search_paths = [self.repo_path]
        
        # Collect all files to index
        files_to_index = []
        for search_path in search_paths:
            if not search_path.exists():
                log.warning(f"Directory does not exist: {search_path}")
                continue
            
            for root, dirs, files in os.walk(search_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    file_path = Path(root) / file
                    
                    if self.should_index_file(file_path):
                        files_to_index.append(file_path)
                        
                        if max_files and len(files_to_index) >= max_files:
                            break
                
                if max_files and len(files_to_index) >= max_files:
                    break
        
        log.info(f"Found {len(files_to_index)} files to index")
        
        # Index each file
        all_documents = []
        for i, file_path in enumerate(files_to_index, 1):
            if i % 10 == 0:
                log.info(f"Progress: {i}/{len(files_to_index)} files")
            
            documents = self.index_file(file_path)
            all_documents.extend(documents)
            
            # Save to output directory if specified
            if output_dir and documents:
                output_dir.mkdir(parents=True, exist_ok=True)
                
                for doc in documents:
                    filename = f"github_{doc.id}.json"
                    filepath = output_dir / filename
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(doc.to_dict(), f, indent=2, ensure_ascii=False)
        
        log.info(f"Indexing complete! Created {len(all_documents)} code chunks from {len(files_to_index)} files")
        
        return all_documents


# Convenience function for Kafka repository
def index_kafka_repository(
    repo_path: str = "/Users/sidarthapati/Desktop/Projects/kafka",
    max_files: int = 50,
    output_dir: Optional[str] = None,
    target_dirs: Optional[List[str]] = None
) -> List[CodeDocument]:
    """
    Quick function to index Apache Kafka repository.
    
    Args:
        repo_path: Path to the Kafka repository
        max_files: Maximum number of files to index
        output_dir: Optional directory to save JSON files
        target_dirs: Specific directories to index (e.g., ['core', 'clients'])
        
    Returns:
        List of indexed documents
    """
    indexer = LocalGitHubIndexer(
        repo_path=repo_path,
        repo_name="kafka",
        github_url="https://github.com/apache/kafka"
    )
    
    output_path = Path(output_dir) if output_dir else None
    
    return indexer.index_repository(
        max_files=max_files,
        target_dirs=target_dirs,
        output_dir=output_path
    )
