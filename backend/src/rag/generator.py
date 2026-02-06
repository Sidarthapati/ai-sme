"""
Response generator for RAG pipeline.
Uses LLM to generate answers based on retrieved context.
"""

from typing import List, Dict, Optional
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings
from ..utils import log
from .prompts import SYSTEM_PROMPT, build_user_prompt, build_chat_prompt


class Generator:
    """
    Generates responses using LLM based on retrieved context.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.3,
        max_tokens: int = 1000
    ):
        """
        Initialize the generator.
        
        Args:
            api_key: OpenAI API key (uses settings if None)
            model: LLM model to use
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in .env")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        
        log.info(f"Initialized generator: model={model}, temperature={temperature}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _generate(
        self,
        messages: List[Dict],
        stream: bool = False
    ):
        """
        Generate response with retry logic.
        
        Args:
            messages: List of message dictionaries
            stream: Whether to stream the response
        
        Returns:
            Response from OpenAI API
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=stream
            )
            return response
        except Exception as e:
            log.error(f"Error generating response: {e}")
            raise
    
    def generate(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate a response to a query given context.
        
        Args:
            query: User's question
            context: Retrieved context from documents
            conversation_history: Optional previous messages
        
        Returns:
            Generated response text
        """
        # Build prompt
        if conversation_history:
            user_prompt = build_chat_prompt(query, context, conversation_history)
        else:
            user_prompt = build_user_prompt(query, context)
        
        # Build messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        # Generate response
        response = self._generate(messages)
        
        answer = response.choices[0].message.content
        
        log.info(f"Generated response ({len(answer)} characters)")
        return answer
    
    def generate_stream(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None
    ):
        """
        Generate a streaming response (for real-time display).
        
        Args:
            query: User's question
            context: Retrieved context
            conversation_history: Optional previous messages
        
        Yields:
            Response chunks as they're generated
        """
        if conversation_history:
            user_prompt = build_chat_prompt(query, context, conversation_history)
        else:
            user_prompt = build_user_prompt(query, context)
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self._generate(messages, stream=True)
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def generate_with_sources(
        self,
        query: str,
        retrieved_docs: List[Dict],
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Generate response with source citations.
        
        Args:
            query: User's question
            retrieved_docs: Retrieved documents
            conversation_history: Optional previous messages
        
        Returns:
            Dictionary with answer and sources
        """
        # Format context from retrieved docs
        from .prompts import format_context_for_prompt
        context = format_context_for_prompt(retrieved_docs)
        
        # Generate answer
        answer = self.generate(query, context, conversation_history)
        
        # Extract sources
        sources = [
            {
                'title': doc.get('title', 'Untitled'),
                'url': doc.get('url', ''),
                'source_type': doc.get('source_type', 'unknown'),
                'similarity_score': doc.get('similarity_score', 0)
            }
            for doc in retrieved_docs
        ]
        
        return {
            'answer': answer,
            'sources': sources,
            'context_used': len(retrieved_docs)
        }
