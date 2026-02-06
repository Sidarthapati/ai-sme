"""
Document upload and management endpoints.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
import json
from pathlib import Path
from datetime import datetime
import hashlib

from ..api.models import (
    DocumentUploadResponse,
    DocumentInfo,
    DocumentListResponse,
    DocumentDeleteResponse
)
from ..indexers import DocumentProcessor
from ..rag import VectorStore
from ..config import settings
from ..utils import log

router = APIRouter(prefix="/documents", tags=["documents"])

# Initialize components
processor = DocumentProcessor()
vector_store = VectorStore()


def extract_text_from_file(file_path: Path, file_type: str) -> str:
    """Extract text from different file types."""
    if file_type in ['.txt', '.md']:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    elif file_type == '.pdf':
        import PyPDF2
        text = []
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text())
        return '\n\n'.join(text)
    
    elif file_type in ['.docx', '.doc']:
        from docx import Document as DocxDocument
        doc = DocxDocument(file_path)
        return '\n'.join([para.text for para in doc.paragraphs])
    
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    tags: Optional[str] = None
):
    """
    Upload and index a new document.
    """
    try:
        # Validate file type
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.allowed_file_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not allowed. Allowed: {settings.allowed_file_types}"
            )
        
        # Validate file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset
        
        if file_size > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.max_upload_size_mb}MB"
            )
        
        # Save temporarily
        temp_dir = Path("/tmp/ai_sme_uploads")
        temp_dir.mkdir(exist_ok=True)
        temp_path = temp_dir / file.filename
        
        with open(temp_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Extract text
        try:
            text_content = extract_text_from_file(temp_path, file_ext)
        except Exception as e:
            temp_path.unlink()
            raise HTTPException(status_code=400, detail=f"Error extracting text: {e}")
        
        # Create document
        file_hash = hashlib.md5(text_content.encode()).hexdigest()
        doc_id = f"uploaded_{file_hash}"
        
        document = {
            'id': doc_id,
            'title': title or file.filename,
            'content': text_content,
            'filename': file.filename,
            'file_type': file_ext,
            'source_type': 'uploaded_document',
            'uploaded_at': datetime.now().isoformat(),
            'tags': tags.split(',') if tags else []
        }
        
        # Process and index
        chunks = processor.process_documents([document], generate_embeddings=True)
        
        if chunks:
            added_count = vector_store.add_documents(chunks)
            
            # Cleanup temp file
            temp_path.unlink()
            
            return DocumentUploadResponse(
                success=True,
                document_id=doc_id,
                chunks_created=len(chunks),
                filename=file.filename,
                message=f"Document indexed successfully"
            )
        else:
            temp_path.unlink()
            raise HTTPException(status_code=500, detail="Failed to process document")
    
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=DocumentListResponse)
async def list_documents(source_type: Optional[str] = None):
    """
    List all indexed documents.
    """
    try:
        # Get stats from vector store
        stats = vector_store.get_stats()
        
        # Note: This is simplified - in production, you'd query metadata
        # For now, return basic info
        return DocumentListResponse(
            documents=[],
            total=stats.get('total_documents', 0)
        )
    
    except Exception as e:
        log.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(document_id: str):
    """
    Delete a document from the index.
    """
    try:
        success = vector_store.delete_by_id(document_id)
        
        if success:
            return DocumentDeleteResponse(
                success=True,
                message=f"Document {document_id} deleted"
            )
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
