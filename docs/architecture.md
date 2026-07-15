# Architecture

## Goal

Evolve the original single-process Streamlit RAG demo into a tenant-aware enterprise AI service that can be deployed on Google Cloud and extended with Google ADK agents.

## Current implementation

- FastAPI HTTP boundary
- Tenant header enforcement and retrieval isolation
- PDF MIME type, size, and parse validation
- Deterministic local retrieval backend for repeatable tests
- Explicit coordinator, retrieval, and safety-review stages
- Prompt-injection screening
- Request latency and retrieval counters
- Automated API, security, and tenant-isolation tests
- Evaluation regression suite in GitHub Actions

## Production target on Google Cloud

```text
Web client
  -> Cloud Load Balancing / IAP
  -> Cloud Run FastAPI service
  -> Google ADK coordinator
       -> policy retrieval agent
       -> structured-data agent
       -> compliance reviewer agent
  -> Vertex AI Gemini
  -> Vertex AI Vector Search or AlloyDB
  -> Cloud Storage / BigQuery

Telemetry: OpenTelemetry -> Cloud Trace, Logging, Monitoring
Secrets: Secret Manager
Identity: dedicated service accounts and tenant-scoped authorization
```

## Key decisions

### Local deterministic fallback

The repository must run and test without cloud credentials. The in-memory retriever and extractive response path provide deterministic CI behavior. Google Cloud adapters should implement the same interfaces.

### Tenant isolation before generation

Retrieval candidates are filtered by tenant before scoring. This prevents cross-tenant context from reaching the model and makes authorization testable independently from prompt behavior.

### Explicit agent stages

Routing, retrieval, and review are separated even in local mode. This creates clear seams for Google ADK sub-agents and enables trajectory-level evaluation later.

### Honest metrics

The current metrics are local latency and request counters only. Token usage, cost-per-request, model latency, and distributed traces require a configured Vertex AI deployment and are intentionally not fabricated.

## Next adapters

1. Vertex AI Gemini response generator
2. Google ADK coordinator and sub-agents
3. MCP server for structured contract-status data
4. Persistent vector backend with metadata filtering
5. OpenTelemetry exporter for Google Cloud
6. Terraform and Cloud Run deployment workflow
