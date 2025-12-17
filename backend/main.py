from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

app = FastAPI(
    title="Backend API for RAG Implementation",
    description="API for the RAG (Retrieval Augmented Generation) functionality related to the textbook content",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """
    Check the health status of the backend service
    """
    return {"status": "healthy", "timestamp": "2025-12-15T10:00:00Z"}

# Include API routes
from api import router as api_router
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)