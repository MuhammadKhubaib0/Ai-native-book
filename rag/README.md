# Standalone RAG Scripts

This directory contains standalone scripts for the RAG (Retrieval Augmented Generation) functionality related to the textbook content.

## Overview

These scripts provide standalone functionality for:
- Document ingestion into the RAG system
- Querying the RAG system with test queries

## Prerequisites

- Python 3.8+
- The backend service dependencies (install via requirements.txt)

## Setup

1. Ensure the backend dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Document Ingestion

To ingest textbook content into the RAG system:

```bash
python ingest.py --content-dir "/path/to/textbook/content"
```

### Query Testing

To query the RAG system:

```bash
python query.py --query "What is ROS 2?"
```

## Scripts

- `ingest.py`: Processes and ingests textbook content into the RAG system
- `query.py`: Allows querying the RAG system with test queries
- `requirements.txt`: Python dependencies for the scripts

## Notes

- These scripts are designed to work with the backend service for RAG implementation
- The scripts use the same core RAG modules as the backend service
- For production use, consider using the backend API instead of these standalone scripts