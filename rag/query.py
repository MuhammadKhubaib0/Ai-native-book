#!/usr/bin/env python3
"""
Standalone script for querying the RAG system
This script can be used to test the RAG functionality with textbook content
"""

import os
import sys
from pathlib import Path
import argparse
import logging

# Add the backend to the path so we can import our RAG modules
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from backend.rag.document_processor import DocumentProcessor
from backend.rag.retriever import Retriever

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def query_rag_system(query_text: str, top_k: int = 5):
    """
    Query the RAG system and return results
    """
    logger.info(f"Processing query: {query_text}")
    
    # Initialize document processor and retriever
    # In a real implementation, we would load the pre-built index
    # For this test script, we'll create a new one
    processor = DocumentProcessor()
    retriever = Retriever(processor)
    
    # Build index (in a real scenario, this would be loaded from storage)
    retriever.build_index()
    
    # Perform the query
    results = retriever.retrieve(query_text, top_k=top_k)
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Query the RAG system with textbook content")
    parser.add_argument("--query", type=str, required=True,
                        help="Query text to search for in the textbook content")
    parser.add_argument("--top-k", type=int, default=5,
                        help="Number of top results to return (default: 5)")
    
    args = parser.parse_args()
    
    try:
        # Perform query
        results = query_rag_system(args.query, args.top_k)
        
        # Print results
        print(f"\nQuery: {args.query}\n")
        print(f"Found {len(results)} relevant results:\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result['score']:.4f}")
            print(f"   Source: {result['source']}")
            print(f"   Content: {result['content'][:200]}...")
            print()
        
    except Exception as e:
        logger.error(f"Error during query: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()