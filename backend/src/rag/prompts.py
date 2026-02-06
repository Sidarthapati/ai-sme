"""
Prompt templates for the RAG pipeline.
Defines system prompts and query formatting for the AI assistant.
"""

from typing import List, Dict


SYSTEM_PROMPT = """You are an AI assistant for a development team. You have access to team documentation from Confluence and code from GitHub repositories.

Your role:
- Answer questions about services, APIs, and processes accurately
- Provide links to relevant documentation and code when available
- Help developers with onboarding and troubleshooting
- Be concise but thorough
- If you don't know something, say so - don't make up information

Guidelines:
- Always cite sources with URLs when provided
- For code questions, reference specific files and line numbers
- For process questions, reference the documentation
- Use clear, developer-friendly language
- Format code blocks properly when showing examples
"""


def format_context_for_prompt(retrieved_docs: List[Dict]) -> str:
    """
    Format retrieved documents as context for the LLM.
    
    Args:
        retrieved_docs: List of document dictionaries with content and metadata
        
    Returns:
        Formatted context string
    """
    if not retrieved_docs:
        return "No relevant documentation found."
    
    context_parts = []
    
    for i, doc in enumerate(retrieved_docs, 1):
        source_type = doc.get('source_type', 'unknown')
        title = doc.get('title', 'Untitled')
        content = doc.get('content', doc.get('documents', [''])[0] if isinstance(doc.get('documents'), list) else '')
        url = doc.get('url', '')
        
        context_parts.append(f"[Source {i}]")
        context_parts.append(f"Type: {source_type}")
        context_parts.append(f"Title: {title}")
        if url:
            context_parts.append(f"URL: {url}")
        context_parts.append(f"Content:\n{content}")
        context_parts.append("")  # Empty line between sources
    
    return "\n".join(context_parts)


def build_user_prompt(query: str, context: str) -> str:
    """
    Build the user prompt with query and context.
    
    Args:
        query: User's question
        context: Formatted context from retrieved documents
        
    Returns:
        Complete user prompt
    """
    return f"""Based on the following context from our documentation and codebase:

{context}

Question: {query}

Provide a helpful answer and include relevant links from the sources above."""


def build_chat_prompt(query: str, context: str, conversation_history: List[Dict] = None) -> str:
    """
    Build prompt with conversation history for multi-turn conversations.
    
    Args:
        query: Current user question
        context: Retrieved context
        conversation_history: Previous messages in the conversation
        
    Returns:
        Complete prompt with history
    """
    if not conversation_history:
        return build_user_prompt(query, context)
    
    # Build history context
    history_text = "\n".join([
        f"{msg['role']}: {msg['content']}"
        for msg in conversation_history[-5:]  # Last 5 messages
    ])
    
    return f"""Previous conversation:
{history_text}

Current context from documentation:
{context}

Current question: {query}

Provide a helpful answer based on the conversation history and documentation above."""
