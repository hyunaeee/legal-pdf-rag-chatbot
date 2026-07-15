from __future__ import annotations

import os
from dataclasses import asdict

from mcp.server.fastmcp import FastMCP

from app.structured_data import SQLiteContractRepository

mcp = FastMCP("enterprise-contract-tools")
repository = SQLiteContractRepository(
    os.getenv("EPA_STRUCTURED_DATA_PATH", "data/contracts.db")
)
bound_tenant_id = os.getenv("EPA_MCP_TENANT_ID")


@mcp.tool()
def get_contract_status(contract_id: str) -> dict[str, str]:
    """Return one contract record for the server-bound tenant.

    The tenant is supplied by the trusted server environment, not by model output.
    This prevents a tool call from selecting another tenant's namespace.
    """
    if not bound_tenant_id:
        raise RuntimeError("EPA_MCP_TENANT_ID must be configured.")

    record = repository.get(
        tenant_id=bound_tenant_id,
        contract_id=contract_id,
    )
    if record is None:
        return {
            "status": "not_found",
            "contract_id": contract_id,
        }
    return {key: str(value) for key, value in asdict(record).items()}


if __name__ == "__main__":
    mcp.run(transport="stdio")
