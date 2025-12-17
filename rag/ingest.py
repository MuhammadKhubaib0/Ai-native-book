#!/usr/bin/env python3
"""
Standalone script for document ingestion for RAG implementation
This script can be used to process and ingest textbook content into the RAG system
"""

import os
import sys
from pathlib import Path
import argparse
import logging

# Add the backend to the path so we can import our RAG modules
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from backend.rag.document_processor import DocumentProcessor
from backend.rag.embedding import generate_embeddings
from backend.rag.retriever import Retriever
from backend.db.models import Document as DBDocument
from backend.db import SessionLocal, engine

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ingest_documents_from_directory(content_dir: str, db_session):
    """
    Process and ingest documents from a content directory
    """
    logger.info(f"Starting ingestion from directory: {content_dir}")
    
    # Initialize document processor
    processor = DocumentProcessor(content_dir)
    documents = processor.load_documents()
    
    # Process each document
    for doc in documents:
        logger.info(f"Processing document: {doc['title']}")
        
        # Create document chunks
        chunks = processor.chunk_document(doc["content"])
        
        # Save document to database
        db_doc = DBDocument(
            title=doc["title"],
            module=doc["module"],
            chapter=doc["chapter"],
            content=doc["content"],
            url=doc["source"]
        )
        
        db_session.add(db_doc)
        db_session.commit()
        
        logger.info(f"Saved document {doc['title']} to database")
    
    logger.info(f"Completed ingestion of {len(documents)} documents")


def main():
    parser = argparse.ArgumentParser(description="Ingest documents for RAG implementation")
    parser.add_argument("--content-dir", type=str, required=True, 
                        help="Directory containing textbook content to ingest")
    parser.add_argument("--db-url", type=str, default=None,
                        help="Database URL (defaults to environment variable)")
    
    args = parser.parse_args()
    
    # Initialize database session
    db_session = SessionLocal()
    
    try:
        # Perform ingestion
        ingest_documents_from_directory(args.content_dir, db_session)
        
        # Build embedding index (placeholder for now)
        logger.info("Building embedding index...")
        processor = DocumentProcessor(args.content_dir)
        retriever = Retriever(processor)
        retriever.build_index()
        logger.info("Embedding index built successfully")
        
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        sys.exit(1)
    finally:
        db_session.close()


if __name__ == "__main__":
    main()