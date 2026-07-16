# Enterprise Policy Agent

An individual, end-to-end Generative AI engineering portfolio that evolves a Streamlit legal-PDF RAG prototype into a tenant-aware enterprise policy and contract assistant.

The repository is designed around the responsibilities of a Forward Deployed Engineer: discover a business workflow, connect structured and unstructured data, build the application and cloud integration layers, add safety and observability, and leave behind testable deployment artifacts.

## Current status

The project runs without cloud credentials in deterministic local mode and includes production adapters for Google Cloud. The code does **not** claim a live customer deployment or publish fabricated cloud latency, quality, cost, or ROI numbers. Those measurements require a configured GCP project, representative data, and real traffic.

## Implemented capabilities

| Area | Implementation |
|---|---|
| API | FastAPI health, PDF ingestion, chat, metrics, and session-deletion endpoints |
| Unstructured data | PDF parsing, chunking, Korean n-gram retrieval, citations, and abstention |
| Vector storage | In-memory deterministic backend and persistent Chroma adapter |
| Embeddings | Local deterministic hash embeddings and Vertex AI embedding adapter |
| Generation | Local extractive provider and Vertex AI Gemini provider via Google Gen AI SDK |
| Agentic workflow | Google ADK coordinator with policy, contract, and compliance-review sub-agents |
| Structured data | Tenant-scoped SQLite contract repository |
| MCP | Read-only contract-status MCP server with runtime-bound tenant context |
| State | Tenant/session-scoped conversation persistence, bounded context, and deletion |
| Security | Pre-generation tenant filtering, upload validation, prompt-injection route, read-only tools |
| Observability | FastAPI OpenTelemetry instrumentation and granular agent spans |
| LLM metrics | Latency, input/output tokens, tokens per second, and configurable cost estimate |
| Evaluation | 12 deterministic regression cases with category-level JSON report |
| Delivery | Docker, GitHub Actions, Terraform, Artifact Registry, private Cloud Run, least-privilege runtime account |

## Architecture

```text
Authenticated client
        |
        v
FastAPI service on Cloud Run
        |
        +--> tenant authorization boundary
        |
        +--> coordinator
        |      +--> policy retrieval
        |      |      +--> memory or persistent Chroma
        |      |      +--> local hash or Vertex embeddings
        |      |
        |      +--> structured contract lookup
        |      |      +--> SQLite demo adapter / managed DB replacement seam
        |      |
        |      +--> compliance and safety review
        |
        +--> local extractive model or Vertex AI Gemini
        |
        +--> tenant/session-scoped state
        |
        +--> OpenTelemetry traces, logs, and metrics
```

A standalone Google ADK implementation is available in `agents/enterprise_policy`. It contains:

- `enterprise_policy_coordinator`
- `policy_retrieval_agent`
- `contract_workflow_agent`
- `compliance_reviewer_agent`

See [`docs/architecture.md`](docs/architecture.md) for component boundaries and trade-offs.

## Request lifecycle

1. The API validates the tenant namespace and request shape.
2. The safety stage blocks known instruction-override and system-prompt requests.
3. The coordinator selects policy retrieval or structured-data-plus-retrieval.
4. Retrieval filters by tenant before evidence reaches a model.
5. Structured contract records are queried through a tenant-scoped repository.
6. Bounded conversation context is loaded using the tenant and session composite key.
7. The configured model provider generates an evidence-constrained answer.
8. Sources, route, safety flags, token metrics, throughput, and optional cost estimate are returned.
9. User and assistant turns are stored for the active tenant/session.
10. OpenTelemetry spans record stage timing without attaching full document text.

## API

| Endpoint | Purpose |
|---|---|
| `GET /health` | Runtime health and model backend |
| `POST /v1/documents` | Validate and ingest a tenant-scoped PDF |
| `POST /v1/chat` | Route, retrieve, generate, and return cited evidence |
| `DELETE /v1/sessions/{session_id}` | Delete conversation turns for one tenant/session |
| `GET /metrics` | Request, failure, latency, retrieval, token, and estimated-cost counters |

Except for `/health`, the local API requires `X-Tenant-ID`. This demonstrates namespace isolation, but the header is not authentication. A production edge must map an authenticated principal to an allowed tenant.

## Local setup

```bash
git clone https://github.com/hyunaeee/legal-pdf-rag-chatbot.git
cd legal-pdf-rag-chatbot
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e '.[dev]'
cp .env.example .env
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for the generated API documentation.

### Local deterministic mode

The default configuration needs no model credentials:

```dotenv
EPA_MODEL_BACKEND=local
EPA_RETRIEVAL_BACKEND=memory
EPA_EMBEDDING_BACKEND=hash
EPA_SESSION_STORE_PATH=:memory:
EPA_STRUCTURED_DATA_PATH=:memory:
```

This mode is used by CI so regression behavior is repeatable.

## Vertex AI mode

Install the AI integrations and authenticate with Application Default Credentials:

```bash
pip install -e '.[ai]'
gcloud auth application-default login
```

```dotenv
EPA_MODEL_BACKEND=vertex
EPA_GOOGLE_CLOUD_PROJECT=your-project-id
EPA_GOOGLE_CLOUD_LOCATION=asia-northeast3
EPA_VERTEX_MODEL=gemini-2.5-flash
```

The provider records model-reported input/output token counts when available.

## Persistent vector mode

```dotenv
EPA_RETRIEVAL_BACKEND=chroma
EPA_VECTOR_STORE_PATH=data/chroma
EPA_EMBEDDING_BACKEND=hash
```

To use Vertex embeddings:

```dotenv
EPA_EMBEDDING_BACKEND=vertex
EPA_VERTEX_EMBEDDING_MODEL=gemini-embedding-001
EPA_GOOGLE_CLOUD_PROJECT=your-project-id
```

Every Chroma query includes a tenant metadata filter before results are returned.

## Google ADK multi-agent application

```bash
pip install -e '.[ai]'
export EPA_ADK_TENANT_ID=demo
export EPA_POLICY_DIRECTORY=data/policies
adk web agents
```

The runtime supplies the tenant binding. Tenant selection is intentionally not exposed as a model tool argument.

## MCP contract tool

```bash
pip install -e '.[ai]'
export EPA_MCP_TENANT_ID=demo
export EPA_STRUCTURED_DATA_PATH=data/contracts.db
python -m mcp_server.server
```

The MCP server exposes a read-only `get_contract_status` tool. Write operations are intentionally excluded.

## OpenTelemetry

```bash
pip install -e '.[observability]'
```

```dotenv
EPA_OTEL_ENABLED=true
EPA_OTEL_SERVICE_NAME=enterprise-policy-agent
EPA_OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

Instrumented stages include:

- FastAPI request handling
- retrieval
- structured-data lookup
- model generation
- state persistence

Trace attributes contain routing and count information rather than full prompts or retrieved documents.

## Token throughput and cost metrics

The application reports token counts from the model provider and calculates `tokens_per_second` when output-token metadata is available.

Current model prices are deliberately not hardcoded. Supply the rates that apply to the selected model and billing context:

```dotenv
EPA_INPUT_COST_PER_MILLION_USD=0
EPA_OUTPUT_COST_PER_MILLION_USD=0
```

When both values remain zero, `estimated_cost_usd` is returned as `null` rather than presenting a misleading estimate.

## Tests and evaluation

```bash
ruff check app agents mcp_server tests evaluation
pytest --cov=app --cov-report=term-missing
python -m evaluation.run
```

The deterministic suite covers:

- grounded policy answers
- Korean retrieval variants
- abstention when evidence is unavailable
- English and Korean prompt injection
- document, structured-data, and session tenant isolation
- structured-data routing
- bounded conversation history

The runner writes `evaluation/report.json`. GitHub Actions publishes it as the `evaluation-report` artifact and fails the pull request when a case regresses.

See [`docs/evaluation.md`](docs/evaluation.md) for the production evaluation plan, including retrieval, trajectory, answer-quality, latency, token, cost, and human-review metrics.

## Docker

The production image installs the Vertex, ADK, MCP, Chroma, and OpenTelemetry integrations and runs as a non-root user.

```bash
docker build -t enterprise-policy-agent .
docker run --rm -p 8080:8080 enterprise-policy-agent
```

## Google Cloud deployment

Terraform provisions:

- required Google Cloud APIs
- Artifact Registry
- a dedicated runtime service account
- Vertex AI and telemetry IAM roles
- a private Cloud Run v2 service
- health probes and bounded autoscaling
- optional public invocation only when explicitly enabled

See [`infrastructure/terraform/README.md`](infrastructure/terraform/README.md).

## Engineering documents

- [`docs/architecture.md`](docs/architecture.md): system boundaries and trade-offs
- [`docs/evaluation.md`](docs/evaluation.md): deterministic and production evaluation strategy
- [`docs/threat-model.md`](docs/threat-model.md): threats, controls, and residual risks
- [`docs/incident-report.md`](docs/incident-report.md): simulated stale-policy retrieval incident
- [`docs/customer-discovery.md`](docs/customer-discovery.md): fictional FDE discovery and ROI measurement plan

## Individual ownership

This repository is structured as an individual portfolio project. Its evidence of ownership includes application code, cloud adapters, agent and tool design, tests, evaluation cases, threat modeling, infrastructure-as-code, CI, incident analysis, and customer-discovery documentation in one repository.

The implementation keeps interfaces replaceable so each design choice can be explained independently:

- model provider
- embedding provider
- retriever
- structured-data repository
- session store
- observability exporter

## Original prototype

The repository began as a Streamlit PDF chatbot using LangChain, Chroma, Upstage Solar, and PyPDF. The original files remain for comparison, showing the progression from a learning prototype to a service-oriented enterprise architecture.

## Remaining production work

- Deploy into an authorized GCP project and publish measured p50/p95 latency, quality, token, and billed-cost results.
- Replace caller-supplied tenant headers with identity-derived authorization.
- Replace local SQLite state and contract storage with a managed durable service.
- Add policy version/effective-date metadata and stale-document regression cases.
- Run load, failure-injection, and recovery tests.
- Conduct domain-expert evaluation and a real user-adoption pilot.

## Safety

This project is an engineering portfolio and does not provide legal advice. Production use requires organization-specific identity, authorization, privacy, retention, data-residency, incident-response, and human-review policies.
