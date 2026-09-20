"""FastAPI application unifying Phases 1-6 behind a single API (FR1)."""
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from portfolio_api.routers import assistant, classifier, documents, ingestion

app = FastAPI(
    title="AI Solution Architect Portfolio API",
    description="Unified API over document generation, ingestion, classification, and RAG.",
    version="0.7.0",
)

app.include_router(documents.router)
app.include_router(ingestion.router)
app.include_router(classifier.router)
app.include_router(assistant.router)

# FR3: /metrics, excluded from the OpenAPI schema (it's an
# infrastructure endpoint, not part of the product's own API surface).
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """No authentication required -- this is what a load balancer or
    uptime monitor would poll."""
    return {"status": "ok"}
