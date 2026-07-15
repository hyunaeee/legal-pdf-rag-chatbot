# Fictional customer discovery case study

> The organization, users, volumes, and success targets below are fictional. This document demonstrates a Forward Deployed Engineering discovery process and does not claim real customer deployment.

## Customer context

A 1,500-person technology company manages internal policies as PDFs and contract workflow data in a legacy database. Employees ask repetitive questions through chat, while Legal and Procurement manually verify the current policy and contract status.

## Discovery questions

### Users and decisions

- Who asks policy questions, and which decisions depend on the answer?
- Which questions require a human legal or compliance reviewer?
- What evidence must be shown for users to trust an answer?
- Which actions are read-only, and which could change business data?

### Data

- Where are policy documents stored?
- How are versions, effective dates, departments, and confidentiality recorded?
- Which contract fields are safe to expose to each user group?
- How quickly must changes appear in the index?

### Security and operations

- How is identity mapped to a tenant, department, and role?
- What data may be sent to a managed model service?
- What are the retention and deletion requirements?
- What latency, availability, and incident-response targets apply?

## Proposed first deployment

### In scope

- Read-only answers over approved policy PDFs.
- Read-only contract owner, workflow status, renewal date, and risk lookup.
- Source citations and explicit abstention.
- Tenant and role authorization before retrieval.
- Request traces, failure metrics, token usage, and configurable cost estimates.
- A reviewer step for unsupported claims and sensitive output.

### Out of scope

- Legal advice.
- Contract approval or modification.
- Automatic policy publication.
- Cross-tenant analytics.
- Unreviewed high-impact actions.

## Success criteria

| Outcome | Measurement plan |
|---|---|
| Task completion | Representative users complete policy and contract-status tasks without manual search |
| Groundedness | Answers are supported by authorized evidence and correct citations |
| Safe abstention | Unsupported and unauthorized requests are refused correctly |
| Adoption | Weekly active users and repeated use after the pilot |
| Efficiency | Median manual handling time compared with assisted task time |
| Reliability | Error rate, p95 latency, tool failure rate, and recovery behavior |
| Cost | Input/output tokens and estimated cost per completed task |

Targets should be agreed with the customer after a baseline study rather than invented before measurement.

## Pilot plan

1. Select two departments and a limited approved document collection.
2. Build a golden dataset from historical questions and reviewer-approved answers.
3. Run the service in read-only mode with human feedback.
4. Review failed traces and authorization events weekly.
5. Compare completion time, quality, and cost with the baseline workflow.
6. Expand only when safety, reliability, and user-adoption gates are met.

## ROI model

The ROI calculation should use measured values:

```text
monthly benefit
= (baseline handling minutes - assisted handling minutes)
  × monthly task volume
  × fully loaded labor cost per minute

monthly net value
= monthly benefit
  - model cost
  - infrastructure cost
  - review and support cost
```

The portfolio intentionally does not publish a fabricated ROI percentage. The implementation exposes the operational inputs needed to calculate it after a real pilot.

## Adoption risks

- Users may distrust answers without recognizable citations.
- Incorrect document ownership may create authorization gaps.
- A slower multi-agent path may reduce adoption for simple questions.
- Review teams may be overwhelmed if escalation thresholds are too broad.

The rollout should therefore start with high-frequency, low-risk, read-only tasks and use measured feedback to decide where additional agent autonomy is justified.
