# Threat model

## Scope

This document covers the FastAPI service, document ingestion, tenant-scoped retrieval, structured-data tools, session state, model generation, ADK agents, and the MCP contract service.

The current repository is a portfolio implementation. It demonstrates controls and testable boundaries, but it is not a substitute for an organization-specific security review.

## Trust boundaries

```text
Untrusted caller
  -> authenticated edge / identity proxy
  -> FastAPI application
  -> tenant authorization mapping
  -> retrieval, session, and structured-data stores
  -> Vertex AI / agent tools
```

`X-Tenant-ID` is a namespace input in the local implementation. A production system must derive or validate it from an authenticated identity and an authorization policy. The header alone is not authentication.

## Threats and mitigations

| Threat | Example | Implemented mitigation | Residual risk / production follow-up |
|---|---|---|---|
| Cross-tenant retrieval | Tenant A receives Tenant B policy text | Tenant filter is applied before scoring in memory retrieval and as a mandatory Chroma metadata filter | Bind tenant to verified identity; add authorization integration tests against the production store |
| Cross-tenant session leakage | Same session ID reused by two tenants | Session primary key and all reads include both tenant and session | Encrypt durable storage and enforce retention/deletion policy |
| Tool tenant spoofing | Model passes a different tenant to an MCP tool | MCP and ADK examples bind tenant through trusted runtime configuration, not a tool argument | Replace static binding with workload identity and per-request signed context |
| Prompt injection | User requests system prompt or instruction override | Deterministic screening, safety route, regression cases, reviewer agent | Add document-level injection detection, model safety evaluation, and human review for high-risk actions |
| Sensitive data in traces | Prompt or retrieved evidence written to telemetry | Current spans store counts, route, and tenant identifier rather than document text | Hash or tokenize identifiers; apply log exclusions and organization retention rules |
| Untrusted file upload | Malformed or oversized PDF | MIME validation, size limit, parse failure handling, extractable-text check | Malware scanning, content disarm, asynchronous sandboxed ingestion |
| Excessive agent autonomy | Agent invokes unsafe tools or makes irreversible changes | Current tools are read-only; reviewer agent is separated; no write tools are exposed | Add tool allowlists, approvals, idempotency keys, and action-level audit records before write tools |
| Unsupported answer | Model invents policy or contract data | Evidence-only instruction, source return, abstention path, evaluation suite | Add production groundedness evaluation and sampled human review |
| Credential leakage | API keys committed or returned to user | Vertex uses Application Default Credentials; no model key is stored in source | Secret Manager for any non-Google credentials; automated secret scanning |
| Denial of service / cost abuse | Large files or repeated expensive requests | Upload size limit, bounded retrieval, bounded output tokens, Cloud Run scaling limit | Identity-aware rate limits, quotas, budgets, and anomaly alerts |

## Security invariants

1. Tenant filtering happens before context reaches the model.
2. Tenant identity is never selected by model output.
3. Read-only tools remain the default.
4. Conversation state is keyed by tenant and session.
5. Prompts, credentials, and full evidence are not attached to trace attributes.
6. Unknown or insufficient evidence results in abstention rather than invention.

## Verification

Automated tests cover tenant retrieval isolation, structured-data isolation, session isolation, deletion, prompt-injection blocking, and bounded history. Evaluation cases are executed for every pull request and published as a CI artifact.
