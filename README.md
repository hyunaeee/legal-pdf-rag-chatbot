# Enterprise Policy Agent

A production-oriented evolution of the original Legal PDF RAG Chatbot, designed to demonstrate enterprise GenAI engineering skills relevant to Forward Deployed Engineering roles.

## What this project demonstrates

- Tenant-aware document retrieval and isolation
- FastAPI service boundaries instead of a UI-only prototype
- PDF validation and controlled ingestion
- Explicit coordinator, retrieval, and safety-review stages
- Prompt-injection blocking
- Automated API, security, and regression tests
- Evaluation cases executed in GitHub Actions
- Containerized deployment path for Cloud Run
- Architecture seams for Google ADK, Vertex AI, MCP, and OpenTelemetry

> The current branch includes a deterministic local backend so tests can run without cloud credentials. Vertex AI and Google ADK are documented as the next production adapters; no cloud performance or cost numbers are claimed until they are measured.

## Architecture

```text
Client
  -> FastAPI
  -> Coordinator
       -> tenant-aware retrieval
       -> safety reviewer
  -> cited response

Target deployment:
Cloud Run -> Google ADK -> Vertex AI Gemini
          -> Vector Search / AlloyDB
          -> MCP structured-data service
          -> Cloud Trace / Logging / Monitoring
```

See [`docs/architecture.md`](docs/architecture.md) for decisions and the Google Cloud target design.

## API

| Endpoint | Purpose |
|---|---|
| `GET /health` | Runtime health and backend mode |
| `POST /v1/documents` | Validate and ingest a tenant-scoped PDF |
| `POST /v1/chat` | Route, retrieve, review, and answer |
| `GET /metrics` | Local request, failure, latency, and retrieval counters |

Except for `/health`, requests use the `X-Tenant-ID` header to enforce tenant isolation.

## Local setup

```bash
git clone https://github.com/hyunaeee/legal-pdf-rag-chatbot.git
cd legal-pdf-rag-chatbot
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Open the API documentation at `http://localhost:8000/docs`.

## Docker

```bash
docker build -t enterprise-policy-agent .
docker run --rm -p 8080:8080 enterprise-policy-agent
```

## Tests and evaluation

```bash
pytest --cov=app
python -m evaluation.run
```

The initial evaluation set covers:

- grounded answer retrieval
- abstention when evidence is unavailable
- prompt-injection blocking
- cross-tenant data isolation

The CI workflow runs linting, tests, coverage, and the evaluation regression suite for every pull request.

## Original prototype

The repository began as a Streamlit legal PDF RAG chatbot using LangChain, Chroma, Upstage Solar, and PyPDF. The original files remain available for comparison, showing the progression from a learning prototype to a service-oriented architecture.

## Roadmap

- [x] FastAPI service and typed configuration
- [x] Tenant-aware retrieval isolation
- [x] PDF input validation
- [x] Coordinator/retrieval/reviewer separation
- [x] Prompt-injection regression test
- [x] Evaluation dataset and CI gate
- [x] Docker image
- [ ] Vertex AI Gemini adapter
- [ ] Google ADK multi-agent implementation
- [ ] MCP structured-data server
- [ ] Persistent vector backend and metadata filters
- [ ] OpenTelemetry export to Google Cloud
- [ ] Terraform and Cloud Run deployment workflow
- [ ] Measured latency, token, cost, and quality report

## Safety

This project is an engineering portfolio and does not provide legal advice. Production use requires organization-specific authorization, retention, privacy, and human-review policies.
