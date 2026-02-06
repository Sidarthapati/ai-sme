"""
Complete RAG pipeline orchestration.
Combines retrieval and generation for end-to-end question answering.
"""

from typing import List, Dict, Optional
from .retriever import Retriever
from .generator import Generator
from .vector_store import VectorStore
from ..utils import log


class RAGPipeline:
    """
    Complete RAG pipeline: retrieve relevant documents and generate answers.
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        retriever: Optional[Retriever] = None,
        generator: Optional[Generator] = None,
        retrieval_top_k: int = 5
    ):
        """
        Initialize the RAG pipeline.
        
        Args:
            vector_store: VectorStore instance
            retriever: Retriever instance (creates new if None)
            generator: Generator instance (creates new if None)
            retrieval_top_k: Number of documents to retrieve
        """
        self.vector_store = vector_store or VectorStore()
        self.retriever = retriever or Retriever(
            vector_store=self.vector_store,
            top_k=retrieval_top_k
        )
        self.generator = generator or Generator()
        
        log.info("Initialized RAG pipeline")
    
    def query(
        self,
        question: str,
        source_type: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Dict:
        """
        Answer a question using RAG pipeline.
        
        Args:
            question: User's question
            source_type: Optional filter by source type ('confluence' or 'github')
            conversation_history: Optional previous messages for context
            stream: Whether to stream the response
        
        Returns:
            Dictionary with answer, sources, and metadata
        """
        log.info(f"Processing query: {question[:50]}...")
        
        # Step 1: Retrieve relevant documents
        retrieved_docs = self.retriever.retrieve(
            query=question,
            source_type=source_type
        )
        
        if not retrieved_docs:
            return {
                'answer': "I couldn't find any relevant documentation to answer your question. Please try rephrasing or check if the information exists in our knowledge base.",
                'sources': [],
                'context_used': 0,
                'retrieval_success': False
            }
        
        # Step 2: Generate answer
        if stream:
            # For streaming, we'll return a generator
            from .prompts import format_context_for_prompt
            context = format_context_for_prompt(retrieved_docs)
            
            return {
                'answer_stream': self.generator.generate_stream(
                    query=question,
                    context=context,
                    conversation_history=conversation_history
                ),
                'sources': self.retriever.format_sources(retrieved_docs),
                'context_used': len(retrieved_docs),
                'retrieval_success': True
            }
        else:
            # Standard generation
            result = self.generator.generate_with_sources(
                query=question,
                retrieved_docs=retrieved_docs,
                conversation_history=conversation_history
            )
            
            result['retrieval_success'] = True
            return result
    
    def query_stream(
        self,
        question: str,
        source_type: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ):
        """
        Stream response for real-time display.
        
        Args:
            question: User's question
            source_type: Optional filter by source type
            conversation_history: Optional previous messages
        
        Yields:
            Response chunks and final sources
        """
        # Retrieve documents
        retrieved_docs = self.retriever.retrieve(
            query=question,
            source_type=source_type
        )
        
        if not retrieved_docs:
            yield {
                'type': 'error',
                'content': "I couldn't find any relevant documentation."
            }
            return
        
        # Format sources
        sources = self.retriever.format_sources(retrieved_docs)
        
        # Stream answer
        from .prompts import format_context_for_prompt
        context = format_context_for_prompt(retrieved_docs)
        
        answer_chunks = []
        for chunk in self.generator.generate_stream(
            query=question,
            context=context,
            conversation_history=conversation_history
        ):
            answer_chunks.append(chunk)
            yield {
                'type': 'chunk',
                'content': chunk
            }
        
        # Yield final result
        yield {
            'type': 'complete',
            'answer': ''.join(answer_chunks),
            'sources': sources,
            'context_used': len(retrieved_docs)
        }
    
    def get_stats(self) -> Dict:
        """
        Get pipeline statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'vector_store': self.vector_store.get_stats(),
            'retrieval_top_k': self.retriever.top_k,
            'generator_model': self.generator.model
        }


# Convenience function
def create_rag_pipeline(
    vector_db_path: Optional[str] = None,
    retrieval_top_k: int = 5
) -> RAGPipeline:
    """
    Quick function to create a RAG pipeline.
    
    Args:
        vector_db_path: Path to vector database
        retrieval_top_k: Number of documents to retrieve
    
    Returns:
        RAGPipeline instance
    """
    vector_store = VectorStore(persist_directory=vector_db_path) if vector_db_path else VectorStore()
    return RAGPipeline(vector_store=vector_store, retrieval_top_k=retrieval_top_k)
