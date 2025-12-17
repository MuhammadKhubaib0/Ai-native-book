from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid

router = APIRouter()

# Data models
class Document(BaseModel):
    id: str
    title: str
    module: str
    chapter: int
    url: str

class DocumentRequest(BaseModel):
    content: str
    title: str
    module: str
    chapter: int

class DocumentResponse(BaseModel):
    id: str
    message: str

# Mock data store
documents_db = []

@router.get("/", response_model=List[Document])
async def get_documents():
    """
    Retrieve a list of available textbook documents
    """
    # Return mock data for now - this would come from a real database in production
    mock_docs = [
        Document(
            id=str(uuid.uuid4()),
            title="Introduction to ROS 2",
            module="module1-ros2",
            chapter=1,
            url="/docs/module1-ros2/intro"
        ),
        Document(
            id=str(uuid.uuid4()),
            title="Python Agents Bridging ROS 2",
            module="module1-ros2",
            chapter=2,
            url="/docs/module1-ros2/python-agents"
        ),
        Document(
            id=str(uuid.uuid4()),
            title="Humanoid Robot Description with URDF",
            module="module1-ros2",
            chapter=3,
            url="/docs/module1-ros2/urdf-humanoids"
        )
    ]
    return mock_docs


@router.post("/", response_model=DocumentResponse)
async def create_document(doc_request: DocumentRequest):
    """
    Ingest a new document into the system
    """
    # Generate a new ID for the document
    doc_id = str(uuid.uuid4())
    
    # In a real implementation, we would store the document in a database
    # For now, we'll just return a success response
    documents_db.append({
        "id": doc_id,
        "content": doc_request.content,
        "title": doc_request.title,
        "module": doc_request.module,
        "chapter": doc_request.chapter
    })
    
    return DocumentResponse(
        id=doc_id,
        message=f"Document '{doc_request.title}' successfully ingested"
    )