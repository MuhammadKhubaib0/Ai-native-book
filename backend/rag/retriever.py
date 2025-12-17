"""
Retriever class for RAG implementation
"""
import logging
from typing import List, Dict, Any
from .embedding import generate_embeddings, query_embeddings
from .document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

class Retriever:
    """
    Class to handle document retrieval for RAG implementation
    """
    
    def __init__(self, doc_processor: DocumentProcessor):
        self.doc_processor = doc_processor
        self.embeddings_db = []
    
    def build_index(self):
        """
        Build an index of document embeddings
        """
        logger.info("Building document embedding index...")
        documents = self.doc_processor.load_documents()
        
        for doc in documents:
            # Chunk the document content
            chunks = self.doc_processor.chunk_document(doc["content"])
            
            for i, chunk in enumerate(chunks):
                # Generate embedding for the chunk
                embedding = generate_embeddings(chunk)
                
                # Store in our embedding database
                self.embeddings_db.append({
                    "id": f"{doc['id']}_chunk_{i}",
                    "content": chunk,
                    "source": doc["source"],
                    "title": doc["title"],
                    "embedding": embedding
                })
        
        logger.info(f"Built index with {len(self.embeddings_db)} chunks")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant documents for the given query
        """
        if not self.embeddings_db:
            logger.warning("Embedding database is empty. Call build_index() first.")
            return []
        
        # Query the embeddings database
        results = query_embeddings(query, self.embeddings_db, top_k)
        
        logger.info(f"Retrieved {len(results)} documents for query: '{query}'")
        return results