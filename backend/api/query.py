from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

# Data models
class QueryRequest(BaseModel):
    query: str
    max_results: int = 5

class QueryResult(BaseModel):
    content: str
    source: str
    score: float

class QueryResponse(BaseModel):
    results: List[QueryResult]

@router.post("/", response_model=QueryResponse)
async def query_documents(query_request: QueryRequest):
    """
    Query the textbook content using RAG
    """
    # For now, return mock results - this would be replaced with actual RAG implementation
    mock_results = [
        QueryResult(
            content=f"Mock response to query: {query_request.query}",
            source="module1-ros2/intro",
            score=0.95
        ),
        QueryResult(
            content="Another mock response related to the query",
            source="module2-gazebo-unity/physics-simulation",
            score=0.87
        )
    ]
    
    # Limit results to max_results if specified
    if query_request.max_results:
        mock_results = mock_results[:query_request.max_results]
    
    return QueryResponse(results=mock_results)