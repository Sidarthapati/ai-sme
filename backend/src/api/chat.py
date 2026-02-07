"""
Chat endpoints for querying the AI assistant.
Now uses database for conversation persistence.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import Dict, Optional, List
from ..rag import RAGPipeline, create_rag_pipeline
from ..database import get_db, User, Conversation, Message
from ..auth.jwt import get_current_user
import json
import uuid
from datetime import datetime

from ..api.models import ChatRequest, ChatResponse, ChatStreamChunk, Source
from ..utils import log

router = APIRouter(prefix="/chat", tags=["chat"])

# RAG Pipeline (lazy initialization)
_pipeline: Optional[RAGPipeline] = None

def get_pipeline() -> RAGPipeline:
    """Lazy initialize pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = create_rag_pipeline()
    return _pipeline


async def get_conversation_history(conversation_id: str, db: AsyncSession) -> List[Dict]:
    """Get conversation history from database."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    
    return [
        {
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.created_at.isoformat() if msg.created_at else None,
        }
        for msg in messages
    ]


async def ensure_max_conversations(user_id: str, db: AsyncSession, max_count: int = 50):
    """
    Ensure user has at most max_count conversations.
    Delete oldest conversations if limit exceeded.
    """
    # Count conversations
    count_result = await db.execute(
        select(func.count(Conversation.id))
        .where(Conversation.user_id == user_id)
    )
    count = count_result.scalar() or 0
    
    if count >= max_count:
        # Get oldest conversation IDs
        oldest_result = await db.execute(
            select(Conversation.id)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.asc())
            .limit(count - max_count + 1)  # Delete enough to get under limit
        )
        oldest_ids = [row[0] for row in oldest_result.fetchall()]
        
        # Delete oldest conversations (cascade will delete messages)
        if oldest_ids:
            await db.execute(
                delete(Conversation).where(Conversation.id.in_(oldest_ids))
            )
            await db.commit()
            log.info(f"Deleted {len(oldest_ids)} oldest conversations for user {user_id}")


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a chat message and get a response.
    Requires authentication.
    """
    try:
        # Get or create conversation
        conversation_id = request.conversation_id
        conversation = None
        
        if conversation_id:
            # Try to find existing conversation
            result = await db.execute(
                select(Conversation)
                .where(Conversation.id == conversation_id)
                .where(Conversation.user_id == user.id)
            )
            conversation = result.scalar_one_or_none()
            
            if conversation is None:
                # Conversation not found - create new one with the provided ID
                await ensure_max_conversations(user.id, db)
                
                conversation = Conversation(
                    id=conversation_id,  # Use the provided ID
                    user_id=user.id,
                    title=None,
                )
                db.add(conversation)
                await db.commit()
                await db.refresh(conversation)
                log.info(f"Created new conversation with provided ID: {conversation_id}")
        else:
            # Create new conversation
            # Ensure max conversations limit
            await ensure_max_conversations(user.id, db)
            
            conversation = Conversation(
                user_id=user.id,
                title=None,  # Will be set from first message
            )
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)
            conversation_id = conversation.id
        
        # Get conversation history
        history = await get_conversation_history(conversation_id, db)
        
        # Query the pipeline
        result = get_pipeline().query(
            question=request.message,
            source_type=request.source_type,
            conversation_history=history if history else None,
            stream=False
        )
        
        # Save user message
        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
        )
        db.add(user_message)
        
        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=result["answer"],
            sources=json.dumps([
                {
                    "title": s.get("title", "Untitled"),
                    "url": s.get("url", ""),
                    "source_type": s.get("source_type", "unknown"),
                    "similarity_score": s.get("similarity_score"),
                }
                for s in result.get("sources", [])
            ]) if result.get("sources") else None,
        )
        db.add(assistant_message)
        
        # Update conversation title if it's the first message
        if conversation.title is None:
            # Use first 50 chars of first user message as title
            conversation.title = request.message[:50] + ("..." if len(request.message) > 50 else "")
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        
        await db.commit()
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Chat error: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    user: User = Depends(get_current_user),
):
    """
    Stream chat response for real-time display.
    Requires authentication.
    """
    async def generate():
        log.info("=" * 80)
        log.info("🎬 GENERATOR FUNCTION CALLED - Starting stream")
        log.info(f"User ID: {user.id}, Message: {request.message[:50]}...")
        log.info("=" * 80)
        
        # Create a new database session for the entire streaming duration
        from ..database.connection import AsyncSessionLocal
        
        db = None
        try:
            log.info(f"🚀 Creating database session...")
            # Create a new session using the sessionmaker
            db = AsyncSessionLocal()
            log.info("✅ Database session created successfully")
            
            # Get or create conversation
            conversation_id = request.conversation_id
            conversation = None
            log.info(f"📝 Processing message: {request.message[:50]}...")
            log.info(f"📝 Conversation ID: {conversation_id or 'None (will create new)'}")
            
            if conversation_id:
                # Try to find existing conversation
                result = await db.execute(
                    select(Conversation)
                    .where(Conversation.id == conversation_id)
                    .where(Conversation.user_id == user.id)
                )
                conversation = result.scalar_one_or_none()
                
                if conversation is None:
                    # Conversation not found - create new one with the provided ID
                    log.info(f"📝 Conversation {conversation_id} not found, creating new one with this ID")
                    await ensure_max_conversations(user.id, db)
                    
                    conversation = Conversation(
                        id=conversation_id,  # Use the provided ID
                        user_id=user.id,
                        title=None,
                    )
                    db.add(conversation)
                    await db.commit()
                    await db.refresh(conversation)
                    log.info(f"✅ Created new conversation with ID: {conversation_id}")
            else:
                # No conversation_id provided - create new conversation
                log.info("📝 No conversation ID provided, creating new conversation")
                await ensure_max_conversations(user.id, db)
                
                conversation = Conversation(
                    user_id=user.id,
                    title=None,
                )
                db.add(conversation)
                await db.commit()
                await db.refresh(conversation)
                conversation_id = conversation.id
                log.info(f"✅ Created new conversation with ID: {conversation_id}")
            
            # Get conversation history
            history = await get_conversation_history(conversation_id, db)
            log.info(f"Retrieved {len(history)} messages from conversation history")
            
            # Save user message
            user_message = Message(
                conversation_id=conversation_id,
                role="user",
                content=request.message,
            )
            db.add(user_message)
            await db.commit()
            
            answer_parts = []
            full_answer = ""
            sources_data = []
            
            # Stream response
            log.info(f"🔍 Calling RAG pipeline for query: {request.message[:50]}...")
            pipeline = get_pipeline()
            log.info(f"✅ Pipeline initialized, starting query_stream...")
            
            try:
                log.info(f"🔄 Starting to iterate over pipeline.query_stream...")
                stream_iter = pipeline.query_stream(
                    question=request.message,
                    source_type=request.source_type,
                    conversation_history=history if history else None
                )
                log.info(f"✅ Got stream iterator, starting to yield chunks...")
                
                chunk_count = 0
                for chunk_data in stream_iter:
                    chunk_count += 1
                    log.debug(f"📦 Received chunk #{chunk_count}, type: {chunk_data.get('type')}")
                    if chunk_data["type"] == "chunk":
                        answer_parts.append(chunk_data["content"])
                        full_answer += chunk_data["content"]
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk_data['content']})}\n\n"
                    
                    elif chunk_data["type"] == "complete":
                        full_answer = chunk_data.get("answer", full_answer)
                        sources_data = chunk_data.get("sources", [])
                        
                        # Save assistant message
                        assistant_message = Message(
                            conversation_id=conversation_id,
                            role="assistant",
                            content=full_answer,
                            sources=json.dumps([
                                {
                                    "title": s.get("title", "Untitled"),
                                    "url": s.get("url", ""),
                                    "source_type": s.get("source_type", "unknown"),
                                    "similarity_score": s.get("similarity_score"),
                                }
                                for s in sources_data
                            ]) if sources_data else None,
                        )
                        db.add(assistant_message)
                        
                        # Update conversation title if first message
                        if conversation.title is None:
                            conversation.title = request.message[:50] + ("..." if len(request.message) > 50 else "")
                        
                        conversation.updated_at = datetime.utcnow()
                        await db.commit()
                        
                        # Format sources
                        sources = [
                            {
                                "title": s.get("title", "Untitled"),
                                "url": s.get("url", ""),
                                "source_type": s.get("source_type", "unknown"),
                                "similarity_score": s.get("similarity_score")
                            }
                            for s in sources_data
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
                        log.error(f"❌ Pipeline returned error chunk: {chunk_data.get('content', 'Unknown error')}")
                        yield f"data: {json.dumps({'type': 'error', 'error': chunk_data.get('content', 'Unknown error')})}\n\n"
                
                log.info(f"✅ Finished streaming {chunk_count} chunks")
                
            except Exception as pipeline_error:
                import traceback
                log.error(f"❌ RAG pipeline error: {pipeline_error}")
                log.error(f"❌ Traceback: {traceback.format_exc()}")
                yield f"data: {json.dumps({'type': 'error', 'error': f'Pipeline error: {str(pipeline_error)}'})}\n\n"
            
        except Exception as e:
            import traceback
            log.error("=" * 80)
            log.error(f"❌❌❌ STREAM GENERATOR ERROR: {type(e).__name__}: {e}")
            log.error(f"❌❌❌ Full traceback:")
            log.error(traceback.format_exc())
            log.error("=" * 80)
            if db:
                try:
                    await db.rollback()
                    log.info("✅ Database rolled back")
                except Exception as rollback_error:
                    log.error(f"❌ Error during rollback: {rollback_error}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        finally:
            # Always close the database session
            log.info("🧹 Cleaning up database session...")
            if db:
                try:
                    await db.close()
                    log.info("✅ Database session closed successfully")
                except Exception as close_error:
                    log.error(f"❌ Error closing database session: {close_error}")
            log.info("=" * 80)
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/conversations")
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all conversations for the current user.
    Returns most recent first, max 50.
    """
    # Use subquery to count messages to avoid lazy loading issues
    message_count_subquery = (
        select(func.count(Message.id))
        .where(Message.conversation_id == Conversation.id)
        .scalar_subquery()
    )
    
    result = await db.execute(
        select(
            Conversation,
            message_count_subquery.label("message_count")
        )
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(50)
    )
    rows = result.all()
    
    return {
        "conversations": [
            {
                "id": conv.id,
                "title": conv.title or "New Conversation",
                "created_at": conv.created_at.isoformat() if conv.created_at else None,
                "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
                "message_count": msg_count or 0,
            }
            for conv, msg_count in rows
        ],
        "total": len(rows)
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation with all messages."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == user.id)
    )
    conversation = result.scalar_one_or_none()
    
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Load messages
    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = messages_result.scalars().all()
    
    # Parse sources from JSON
    messages_data = []
    for msg in messages:
        sources = None
        if msg.sources:
            try:
                sources = json.loads(msg.sources) if isinstance(msg.sources, str) else msg.sources
            except:
                sources = None
        
        messages_data.append({
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "sources": sources,
            "timestamp": msg.created_at.isoformat() if msg.created_at else None,
        })
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
        "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
        "messages": messages_data,
        "message_count": len(messages_data)
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a conversation."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == user.id)
    )
    conversation = result.scalar_one_or_none()
    
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await db.delete(conversation)
    await db.commit()
    
    return {"success": True, "message": "Conversation deleted"}
