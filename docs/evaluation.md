# Evaluation methodology

## Goals

The evaluation suite is designed to catch regressions in the system boundaries that matter before model quality is measured in a live cloud environment:

- grounded retrieval
- correct abstention
- tenant isolation
- prompt-injection handling
- structured-data routing
- session-state isolation
- Korean query matching

## Current deterministic suite

The repository includes 12 JSONL cases in `evaluation/cases.jsonl`. Each case builds an isolated in-memory environment, runs the agent, and validates applicable properties such as:

- required answer content
- forbidden cross-tenant content
- expected route
- expected safety flag
- expected source title
- structured-data call count
- bounded history count

The runner writes `evaluation/report.json` with an overall result, category-level pass rates, checks, routes, source titles, safety flags, and local request metrics. GitHub Actions publishes this file as the `evaluation-report` artifact.

## Running locally

```bash
python -m evaluation.run
```

A failed check exits with a non-zero status so it blocks the pull request.

## What the current suite proves

- The local deterministic retrieval and routing implementation behaves consistently.
- Cross-tenant data is excluded in the tested retrieval, structured-data, and session scenarios.
- Known prompt-injection phrases enter the safety path.
- Unsupported questions cause the local provider to abstain.
- The agent exposes route, source, latency, token, and configured cost fields through one response contract.

## What it does not prove

- Real-world answer quality from Vertex AI Gemini.
- Semantic retrieval quality on a large production corpus.
- Robustness against novel or encoded prompt injections.
- p95 latency, throughput, availability, or cost under realistic load.
- Human trust, adoption, or business ROI.

Those claims require a deployed environment, representative customer data, current model pricing, and measured traffic. They are intentionally not fabricated in this portfolio.

## Production evaluation plan

### Retrieval

- Recall@K
- Precision@K
- mean reciprocal rank
- correct policy-version selection
- citation coverage and citation correctness

### Agent trajectory

- correct specialist selection
- required tool-call completion
- unnecessary tool-call rate
- tool argument validity
- reviewer rejection and revision rate

### Answer quality

- groundedness
- factual consistency
- answer relevance
- safe abstention
- authorization correctness

### Operations

- p50 and p95 end-to-end latency
- model and tool latency by span
- input/output tokens
- tokens per second
- estimated and billed cost per request
- error and timeout rate
- cache hit rate

### Human evaluation

A domain reviewer should grade a stratified sample and adjudicate failures. Automated model-based grading may be added as a signal, but it should not be the only judge for policy or compliance use cases.

## Dataset governance

A production golden dataset should include source version, expected evidence, reviewer identity, approval timestamp, risk category, and change history. Regression cases should be added whenever an incident or user correction reveals a new failure mode.
