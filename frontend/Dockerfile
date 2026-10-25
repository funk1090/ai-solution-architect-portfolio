# syntax=docker/dockerfile:1
# Frontend image (Feature 0010). Build context = repository root:
#   docker build -f frontend/Dockerfile .
# No torch here: the frontend is a pure client of the API (Feature 0008).
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/frontend/.venv/bin:$PATH" \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

RUN useradd --create-home --uid 1000 app

WORKDIR /app/frontend
COPY frontend ./
RUN uv sync --frozen --no-dev && chown -R app:app /app/frontend

USER app
EXPOSE 8501

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)"

CMD ["streamlit", "run", "src/portfolio_frontend/app.py", \
     "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
