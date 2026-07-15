from __future__ import annotations

import os

from google.adk import Agent

from agents.enterprise_policy.tools import (
    get_contract_status,
    review_response,
    search_policy_documents,
)


MODEL = os.getenv("EPA_ADK_MODEL", "gemini-2.5-flash")

policy_retrieval_agent = Agent(
    name="policy_retrieval_agent",
    model=MODEL,
    mode="single_turn",
    description=(
        "Searches authorized policy documents and returns grounded excerpts "
        "with source titles."
    ),
    instruction=(
        "Use search_policy_documents for policy questions. Answer only from the "
        "returned evidence. If no evidence is found, abstain."
    ),
    tools=[search_policy_documents],
)

contract_workflow_agent = Agent(
    name="contract_workflow_agent",
    model=MODEL,
    mode="single_turn",
    description=(
        "Retrieves structured contract owner, status, renewal date, and risk data."
    ),
    instruction=(
        "Use get_contract_status for contract workflow questions. Never invent "
        "records and never request or select a tenant identifier."
    ),
    tools=[get_contract_status],
)

compliance_reviewer_agent = Agent(
    name="compliance_reviewer_agent",
    model=MODEL,
    mode="single_turn",
    description=(
        "Reviews candidate answers for unsupported claims, sensitive data, "
        "and unsafe certainty."
    ),
    instruction=(
        "Use review_response before approving an answer. When checks fail, "
        "return the flags and require revision or abstention."
    ),
    tools=[review_response],
)

root_agent = Agent(
    name="enterprise_policy_coordinator",
    model=MODEL,
    description=(
        "Coordinates policy retrieval, structured contract lookup, and final "
        "compliance review."
    ),
    instruction=(
        "Delegate policy questions to policy_retrieval_agent. Delegate contract "
        "workflow questions to contract_workflow_agent. For requests that need "
        "both sources, call both specialists. Before returning a substantive "
        "answer, delegate the draft and evidence to compliance_reviewer_agent. "
        "Return citations and abstain when evidence is insufficient."
    ),
    sub_agents=[
        policy_retrieval_agent,
        contract_workflow_agent,
        compliance_reviewer_agent,
    ],
)
