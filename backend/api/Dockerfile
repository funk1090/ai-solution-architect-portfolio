# syntax=docker/dockerfile:1
# API image (Feature 0010). Build context = repository root:
#   docker build -f backend/api/Dockerfile .
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/opt/hf \
    PATH="/opt/venv/bin:$PATH"

RUN useradd --create-home --uid 1000 app \
 && mkdir -p /data/generated /opt/hf \
 && chown -R app:app /data /opt/hf

# Same layout as the repository: the API depends on sibling packages
# through relative path sources (ADR-0003).
WORKDIR /app
COPY backend ./backend

WORKDIR /app/backend/api
# Install the *locked* dependencies, but without the CUDA wheels that
# PyPI's torch pulls in on Linux: embeddings of short texts run fine on
# CPU, and the GPU is reserved for the LLM. `--torch-backend cpu` swaps
# in the CPU build of the same torch version.
RUN uv export --frozen --no-dev --no-hashes --no-emit-project -o requirements.txt \
 && grep -v -E '^(nvidia-|triton)' requirements.txt > requirements.cpu.txt \
 && uv venv /opt/venv \
 && uv pip install --python /opt/venv/bin/python --torch-backend cpu -r requirements.cpu.txt \
 && uv pip install --python /opt/venv/bin/python --no-deps -e .

# Bake the embedding model into the image so the first request does not
# depend on the network (NFR4).
ARG EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${EMBEDDING_MODEL_NAME}')" \
 && chown -R app:app /opt/hf

ENV DOCUMENT_OUTPUT_DIR=/data/generated
USER app
WORKDIR /app/backend
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["uvicorn", "portfolio_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
