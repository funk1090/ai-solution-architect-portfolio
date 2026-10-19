# portfolio-frontend

Streamlit web interface for the AI Solution Architect Portfolio (Feature 0008).
A pure client of the Phase 7 API: it contains no business logic and the API key
never leaves the Streamlit server process.

## Run

```bash
cp .env.example .env      # set API_KEY to match backend/api/.env
uv sync
uv run streamlit run src/portfolio_frontend/app.py
```

The API must be running (default `http://localhost:8000`).

## Test

```bash
uv run pytest -v
```

## Pages
Corpus (status + counts), Pipeline (generate / ingest / index), Ask (grounded Q&A with sources), Classify (requirement classification + model comparison).
