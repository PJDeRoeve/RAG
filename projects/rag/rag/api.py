import fastapi
from rag.settings import settings
from rag.document.view import router as document_router

api_router = fastapi.APIRouter(
    prefix=f"/api/{settings.API_VERSION}",
)

api_router.include_router(router=document_router, tags=["documents"])
