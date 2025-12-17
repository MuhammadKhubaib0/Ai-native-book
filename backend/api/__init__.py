from fastapi import APIRouter
from .documents import router as documents_router
from .query import router as query_router

# Main API router
router = APIRouter()
router.include_router(documents_router)
router.include_router(query_router)