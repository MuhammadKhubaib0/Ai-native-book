# Backend API for RAG Implementation

This is the backend service for the Retrieval Augmented Generation (RAG) functionality related to the textbook content. It provides a FastAPI-based API for document management and querying.

## Features

- Document ingestion and management
- RAG-based querying of textbook content
- Health check endpoints
- Modular API structure ready for expansion

## Prerequisites

- Python 3.8+
- pip

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env to match your configuration
   ```

4. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

## API Endpoints

- `GET /health` - Check the health status of the backend service
- `GET /api/v1/documents` - Retrieve a list of available textbook documents
- `POST /api/v1/documents` - Ingest a new document into the system
- `POST /api/v1/query` - Query the textbook content using RAG

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── api/                # API routes
│   ├── __init__.py
│   ├── documents.py    # Document management endpoints
│   └── query.py        # Query endpoints
├── db/                 # Database models and setup
│   ├── __init__.py
│   └── models.py
└── rag/                # RAG-specific logic
    ├── __init__.py
    ├── embedding.py
    ├── document_processor.py
    └── retriever.py
```

## Environment Variables

- `PORT` - Port number for the server (default: 8000)
- `DATABASE_URL` - Database connection string (default: sqlite:///./rag_textbook.db)

## Development

To run with auto-reload during development:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

API documentation is automatically available at `http://localhost:8000/docs`.