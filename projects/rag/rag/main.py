import fastapi
import uvicorn

from rag.api import api_router

app = fastapi.FastAPI(
    title="RAG api",
    description="REST API to interact with take home project",
    version="0.1.0",
)


# Health check route (public, unprotected)
@app.get("/healthcheck", include_in_schema=True)
async def healthcheck():
    """Health check endpoint."""
    return {"status": "ok"}


app.include_router(
    api_router,
)

if __name__ == "__main__":
    uvicorn.run("rag.main:app", port=8005, host="127.0.0.1", reload=True)
