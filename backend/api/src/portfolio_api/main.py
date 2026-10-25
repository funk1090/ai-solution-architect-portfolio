"""FastAPI application unifying Phases 1-6 behind a single API (FR1)."""
from fastapi import Depends, FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from portfolio_api.rate_limit import limit_default
from portfolio_api.routers import assistant, classifier, compliance, corpus, documents, ingestion

# Rate limiting (Feature 0010): the default tier covers every protected
# router; /health and /metrics stay outside it. Expensive routes add the
# stricter `limit_expensive` dependency at the route level.
app = FastAPI(
    title="AI Solution Architect Portfolio API",
    description="Unified API over document generation, ingestion, classification, and RAG.",
    version="0.9.0",
)

app.include_router(documents.router, dependencies=[Depends(limit_default)])
app.include_router(ingestion.router, dependencies=[Depends(limit_default)])
app.include_router(classifier.router, dependencies=[Depends(limit_default)])
app.include_router(assistant.router, dependencies=[Depends(limit_default)])
app.include_router(corpus.router, dependencies=[Depends(limit_default)])
app.include_router(compliance.router, dependencies=[Depends(limit_default)])

# FR3: /metrics, excluded from the OpenAPI schema (it's an
# infrastructure endpoint, not part of the product's own API surface).
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """No authentication required -- this is what a load balancer or
    uptime monitor would poll."""
    return {"status": "ok"}
