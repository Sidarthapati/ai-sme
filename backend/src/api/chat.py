"""
Chat endpoints for querying the AI assistant.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Optional
from ..rag import RAGPipeline, create_rag_pipeline
import json
import uuid
from datetime import datetime

from ..api.models import ChatRequest, ChatResponse, ChatStreamChunk, Source
from ..utils import log

router = APIRouter(prefix="/chat", tags=["chat"])

# In-memory conversation storage (replace with Redis/DB in production)
conversations: Dict[str, list] = {}
_pipeline: Optional[RAGPipeline] = None

def get_pipeline() -> RAGPipeline:
    """Lazy initialize pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = create_rag_pipeline()
    return _pipeline


def get_conversation_history(conversation_id: str) -> list:
    """Get conversation history."""
    return conversations.get(conversation_id, [])


def add_to_conversation(conversation_id: str, role: str, content: str):
    """Add message to conversation."""
    if conversation_id not in conversations:
        conversations[conversation_id] = []
    
    conversations[conversation_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a chat message and get a response.
    """
    try:
        # Get or create conversation ID
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Get conversation history
        history = get_conversation_history(conversation_id)
        
        # Query the pipeline
        result = get_pipeline().query(
            question=request.message,
            source_type=request.source_type,
            conversation_history=history if history else None,
            stream=False
        )
        
        # Add to conversation history
        add_to_conversation(conversation_id, "user", request.message)
        add_to_conversation(conversation_id, "assistant", result["answer"])
        
        # Format sources
        sources = [
            Source(
                title=s.get("title", "Untitled"),
                url=s.get("url", ""),
                source_type=s.get("source_type", "unknown"),
                similarity_score=s.get("similarity_score")
            )
            for s in result.get("sources", [])
        ]
        
        return ChatResponse(
            answer=result["answer"],
            sources=sources,
            context_used=result.get("context_used", 0),
            conversation_id=conversation_id
        )
        
    except Exception as e:
        log.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response for real-time display.
    """
    async def generate():
        try:
            conversation_id = request.conversation_id or str(uuid.uuid4())
            history = get_conversation_history(conversation_id)
            
            answer_parts = []
            
            for chunk_data in get_pipeline().query_stream(
                question=request.message,
                source_type=request.source_type,
                conversation_history=history if history else None
            ):
                if chunk_data["type"] == "chunk":
                    answer_parts.append(chunk_data["content"])
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk_data['content']})}\n\n"
                
                elif chunk_data["type"] == "complete":
                    full_answer = chunk_data.get("answer", "".join(answer_parts))
                    
                    # Add to conversation
                    add_to_conversation(conversation_id, "user", request.message)
                    add_to_conversation(conversation_id, "assistant", full_answer)
                    
                    # Format sources
                    sources = [
                        {
                            "title": s.get("title", "Untitled"),
                            "url": s.get("url", ""),
                            "source_type": s.get("source_type", "unknown"),
                            "similarity_score": s.get("similarity_score")
                        }
                        for s in chunk_data.get("sources", [])
                    ]
                    
                    complete_data = {
                        'type': 'complete',
                        'answer': full_answer,
                        'sources': sources,
                        'context_used': chunk_data.get('context_used', 0),
                        'conversation_id': conversation_id
                    }
                    yield f"data: {json.dumps(complete_data)}\n\n"
                
                elif chunk_data["type"] == "error":
                    yield f"data: {json.dumps({'type': 'error', 'content': chunk_data.get('content', 'Unknown error')})}\n\n"
            
        except Exception as e:
            log.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history."""
    history = get_conversation_history(conversation_id)
    
    if not history:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation_id,
        "messages": history,
        "message_count": len(history)
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    if conversation_id in conversations:
        del conversations[conversation_id]
        return {"success": True, "message": "Conversation deleted"}
    else:
        raise HTTPException(status_code=404, detail="Conversation not found")
