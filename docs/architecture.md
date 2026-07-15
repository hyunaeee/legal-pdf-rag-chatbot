# Architecture

## Goal

Evolve the original single-process Streamlit PDF chatbot into an enterprise-oriented AI system that demonstrates the full path from a local prototype to a deployable Google Cloud application.

The design prioritizes replaceable interfaces, tenant isolation before generation, deterministic CI, read-only tools, measurable agent stages, and honest separation between implemented code and claims that require a live deployment.

## System context

```text
User or enterprise application
        |
        v
Identity-aware edge
        |
        v
FastAPI on Cloud Run
        |
        +--> tenant authorization
        +--> PDF ingestion
        +--> orchestration
        +--> session deletion
        +--> operational metrics
        |
        v
Evidence and tool layer
        +--> unstructured policy retrieval
        +--> structured contract repository
        +--> MCP read-only contract tool
        |
        v
Model and agent layer
        +--> local deterministic provider
        +--> Vertex AI Gemini provider
        +--> Google ADK multi-agent team
        |
        v
OpenTelemetry collector / cloud observability backend
```

## Implemented components

### FastAPI boundary

`app/main.py` owns the HTTP contract:

- `GET /health`
- `POST /v1/documents`
- `POST /v1/chat`
- `DELETE /v1/sessions/{session_id}`
- `GET /metrics`

PDF ingestion validates MIME type, size, parseability, and extractable text before indexing.

### Orchestration

`app/agent.py` exposes explicit stages:

1. safety screening
2. route selection
3. conversation-context lookup
4. tenant-scoped retrieval
5. optional structured-data lookup
6. model generation
7. state persistence
8. metric aggregation

Each major stage has a dedicated OpenTelemetry span. This makes latency and failures attributable to a specific part of the workflow rather than one opaque request.

### Google ADK team

`agents/enterprise_policy/agent.py` defines a standalone multi-agent application:

```text
enterprise_policy_coordinator
    +--> policy_retrieval_agent
    +--> contract_workflow_agent
    +--> compliance_reviewer_agent
```

The specialists have narrow descriptions, instructions, and read-only tools. The coordinator is responsible for delegation and final synthesis.

The FastAPI deterministic coordinator and the ADK team are intentionally separate execution paths. The first provides credential-free regression behavior; the second demonstrates the production agent framework and delegation structure.

### Model providers

`ModelProvider` separates orchestration from model access.

| Provider | Use |
|---|---|
| `LocalExtractiveProvider` | Deterministic CI and local demonstrations |
| `VertexGeminiProvider` | Managed generation through Vertex AI and Google Gen AI SDK |

The Vertex provider uses Application Default Credentials and returns token metadata when supplied by the API.

### Retrieval

`Retriever` allows storage and ranking to change without modifying the API or agent.

| Backend | Characteristics |
|---|---|
| `InMemoryRetriever` | Deterministic lexical and Korean n-gram retrieval for tests |
| `PersistentChromaRetriever` | Persistent vector search with mandatory tenant metadata filter |

`EmbeddingProvider` similarly supports local deterministic hash embeddings and Vertex AI embeddings.

Tenant filtering is applied before evidence is returned to orchestration. Prompt instructions are not used as the primary authorization mechanism.

### Structured data

`SQLiteContractRepository` demonstrates access to contract workflow fields:

- contract ID
- owner
- status
- renewal date
- risk level

Every query includes the tenant key. The interface is intended to be replaced by Cloud SQL, AlloyDB, or an enterprise API in a real deployment.

### MCP

`mcp_server/server.py` exposes read-only contract status lookup. The tenant is bound by trusted server configuration instead of being accepted as a model-generated tool argument.

This prevents the model from selecting another tenant namespace, while still leaving a clear seam for per-request workload identity in a production MCP deployment.

### Session state

`SQLiteSessionStore` persists turns under the composite key:

```text
tenant_id + session_id + sequence
```

Only a bounded number of recent turns are supplied as conversational context. The API also exposes tenant-scoped deletion.

A production replacement should add encryption, retention jobs, durable managed storage, concurrency controls, and data-subject deletion workflows.

### Observability

OpenTelemetry is optional and no-op by default. When enabled, the application instruments FastAPI and creates granular spans for:

- retrieval
- structured-data lookup
- model generation
- state persistence

Metrics returned by the service include:

- request and failure counts
- average local latency
- retrieval and structured-data calls
- input and output tokens
- tokens per second
- configured estimated cost per request

Model pricing is injected through configuration rather than hardcoded.

## Deployment architecture

```text
Artifact Registry
        |
        v
Private Cloud Run v2 service
        |
        +--> dedicated runtime service account
        +--> Vertex AI model and embedding APIs
        +--> OTLP collector / observability backend
        +--> durable policy, vector, contract, and session stores
```

Terraform provisions the current minimum cloud resources:

- required service APIs
- Artifact Registry repository
- dedicated service account
- Vertex AI and telemetry IAM roles
- private Cloud Run service
- startup and liveness probes
- bounded minimum and maximum instances
- optional unauthenticated invocation only when explicitly enabled

## Security boundaries

### Tenant identity

The local API requires `X-Tenant-ID` to make isolation testable. It is not a production identity control. At the enterprise edge, an authenticated principal must be mapped to an allowed tenant and roles before the request reaches application logic.

### Evidence isolation

Document, structured-data, and session lookups all include tenant scope before data is exposed to a model.

### Tool safety

Current tools are read-only. Any future write action should require explicit authorization, confirmation, idempotency, and an audit record.

### Telemetry minimization

Span attributes contain stage, route, identifiers, and counts. Full prompts, document contents, credentials, and generated answers are not attached by the custom tracing layer.

See [`threat-model.md`](threat-model.md) for the complete threat analysis.

## Key decisions and trade-offs

### Deterministic local fallback

**Decision:** Maintain credential-free local implementations.

**Why:** Pull-request checks must not require cloud credentials, external availability, or nondeterministic model output.

**Trade-off:** Passing local tests does not prove Vertex model quality or production retrieval accuracy.

### Interfaces before infrastructure coupling

**Decision:** Define providers and repositories for models, embeddings, retrieval, structured data, and sessions.

**Why:** Customer environments differ; a Forward Deployed Engineer must integrate with existing systems without rewriting all orchestration logic.

**Trade-off:** More modules and configuration than a small demo requires.

### Tenant filtering before generation

**Decision:** Filter evidence in the data layer.

**Why:** Model instructions cannot reliably enforce authorization after unauthorized context has already been retrieved.

**Trade-off:** Authorization metadata must be correct and consistently populated.

### Read-only first deployment

**Decision:** Agent and MCP examples expose lookup tools only.

**Why:** Read-only workflows reduce operational risk while evaluation, adoption, and authorization are established.

**Trade-off:** The initial system cannot automate approval or update workflows.

### Configurable price inputs

**Decision:** Calculate cost from token counts only when current price rates are supplied.

**Why:** Model prices and billing contexts change; hardcoded values quickly become misleading.

**Trade-off:** Cost remains `null` until the deployment configuration includes rates.

### Separate deterministic and ADK paths

**Decision:** Keep a simple local coordinator and a standalone ADK agent application.

**Why:** The local path provides stable regression tests, while the ADK path demonstrates delegation and framework-specific integration.

**Trade-off:** Production convergence requires choosing one primary runtime and expanding its end-to-end integration tests.

## Failure behavior

- Unsupported question: abstain.
- Missing tenant header: reject request.
- Invalid or oversized PDF: reject ingestion.
- Prompt-injection pattern: return safety response before retrieval.
- Missing Vertex configuration: fail at startup rather than silently use another model.
- Missing optional dependency: return an explicit installation error.
- Missing structured record: continue with available evidence or abstain.

## Remaining production decisions

The repository intentionally leaves the following dependent on a real customer and GCP environment:

- identity provider and role mapping
- managed vector and relational storage choice
- document version and effective-date authority
- data residency and retention policy
- live model selection and current pricing
- service-level objectives and autoscaling limits
- human-review thresholds
- load, chaos, and disaster-recovery testing

These decisions should be made through customer discovery and measured pilots rather than assumed in a generic portfolio.
