# Simulated incident report: stale policy selected

> This is a deliberately constructed portfolio scenario, not a real customer incident.

## Summary

A policy assistant returned a 2024 travel-expense limit even though a 2026 policy had superseded it. The answer was grounded in a retrieved document, but the retrieval layer had no effective-date or superseded-document metadata and therefore treated both documents as equally valid.

## User impact

- An employee could submit an expense using an outdated limit.
- A reviewer could incorrectly reject or approve a claim.
- The answer looked trustworthy because it contained a citation.

This illustrates why citation presence alone is not a sufficient quality metric.

## Detection

The issue would be detected through:

1. A regression query with two conflicting policy versions.
2. A trace showing both versions in the candidate set.
3. A reviewer check comparing the answer date with document metadata.
4. A user feedback event marking the citation as outdated.

## Root cause

- Document ingestion preserved page and title but did not require `effective_from`, `effective_to`, or `supersedes` metadata.
- Retrieval ranking optimized textual similarity only.
- The generation prompt had no instruction to prefer the currently effective version.
- The evaluation set did not contain conflicting-version questions.

## Corrective actions

### Immediate

- Add document lifecycle metadata during ingestion.
- Filter out documents that are not effective at the request timestamp.
- Display policy version and effective date beside each citation.
- Add a regression case containing both old and current versions.

### Structural

- Introduce a metadata schema with validation before indexing.
- Record ingestion source, checksum, version, and status.
- Add a policy-version resolver before vector scoring.
- Require the compliance reviewer to reject answers based on expired evidence.

## Verification plan

| Check | Success criterion |
|---|---|
| Version conflict regression | Current policy selected in 100% of deterministic cases |
| Citation metadata | Every returned source includes version and effective date |
| Stale-evidence reviewer | Expired-only evidence causes abstention |
| Trace inspection | Candidate versions and filtering decision are observable without logging full document content |

## Trade-offs

Metadata filtering can reduce recall when source metadata is incomplete. The safer production behavior is to quarantine incomplete documents or return an explicit uncertainty message rather than silently including them.

## Lesson

A production RAG system must evaluate **evidence validity**, not only retrieval similarity and answer fluency. The incident becomes a reusable engineering pattern: version-aware ingestion, metadata authorization, regression evaluation, and observable filtering decisions.
