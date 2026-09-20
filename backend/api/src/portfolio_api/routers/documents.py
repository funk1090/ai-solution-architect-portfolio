"""Wraps document_generator (Phase 1). Reuses its Factory/repository
exactly as the CLI does -- no business logic reimplemented (NFR1).
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from portfolio_api.auth import verify_api_key

router = APIRouter(prefix="/documents", tags=["documents"], dependencies=[Depends(verify_api_key)])


class GenerateRequest(BaseModel):
    document_type: str
    count: int = 1


class GenerateResponse(BaseModel):
    generated: int
    output_dir: str


@router.post("/generate", response_model=GenerateResponse)
def generate_documents(request: GenerateRequest) -> GenerateResponse:
    from document_generator.config import Settings
    from document_generator.factory import GeneratorFactory
    from document_generator.models import DocumentType
    from document_generator.providers import EnterpriseFakerProvider
    from document_generator.repository import PostgresDocumentMetadataRepository

    settings = Settings()
    doc_type = DocumentType(request.document_type)

    provider = EnterpriseFakerProvider(seed=settings.generation_seed)
    repository = PostgresDocumentMetadataRepository(settings.database_url)
    repository.create_tables()
    factory = GeneratorFactory(provider=provider, repository=repository)

    output_dir = settings.document_output_dir / doc_type.value
    generator = factory.create(doc_type, output_dir=output_dir, seed=settings.generation_seed)
    results = generator.generate(request.count)

    return GenerateResponse(generated=len(results), output_dir=str(output_dir))
