import argparse
import os
from typing import Optional, Literal
from pydantic import BaseModel, Field

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.streamable_http import TransportSecuritySettings

class TransferDetails(BaseModel):
    token: str = Field(min_length=1,max_length=64)
    token_kind: Literal['native','token'] = 'token'
    network: Literal['ETHEREUM','BASE','ARBITRUM','OPTIMISM','BSC','POLYGON','BITCOIN','SOLANA','TRON','XRPL','STELLAR']
    destination_type: Literal['personal_wallet','exchange']
    exchange: str | None = Field(default=None,max_length=80)
    token_contract: str | None = Field(default=None,max_length=128)
    memo: str | None = Field(default=None,max_length=256)
    memo_required: bool | None = None
    recipient_network: str | None = Field(default=None,max_length=32)


class BatchItem(BaseModel):
    address: str
    chain: str = "EVM"
    amount: float | None = None
    raw_amount_input: str | None = None
    transfer: TransferDetails | None = None


API_KEY = os.environ.get("PATHGUARD_API_KEY", "")
API_BASE = os.environ.get("PATHGUARD_API_BASE", "https://api.pathguard.cieltech.org")

server = MCPServer("pathguard", version="0.2.0")


async def _call_api(method: str, path: str, json_body: Optional[dict] = None) -> dict:
    if not API_KEY:
        return {
            "error": (
                "PATHGUARD_API_KEY is not set. "
                "Get a free key at pathguard.cieltech.org/docs.html"
            )
        }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.request(
            method,
            f"{API_BASE.rstrip('/')}{path}",
            headers={"x-api-key": API_KEY},
            json=json_body,
        )

    try:
        data = resp.json()
    except Exception:
        return {"error": f"Unexpected response from PathGuard API (status {resp.status_code})"}

    if not resp.is_success:
        return {"error": data.get("detail", f"PathGuard API returned {resp.status_code}")}
    return data


@server.tool()
async def check_transaction(
    address: str,
    chain: str = "EVM",
    amount: Optional[float] = None,
    transfer: TransferDetails | None = None,
) -> dict:
    """Analyze one transaction. Optional transfer details check token/network/deposit requirements. Unknown does not mean safe. Never sends funds."""
    return await _call_api(
        "POST",
        "/v1/check",
        {"address": address, "chain": chain, "amount": amount, "transfer": transfer.model_dump() if transfer else None},
    )


@server.tool()
async def check_transactions_batch(items: list[BatchItem]) -> dict:
    """Check up to 1,000 crypto transactions. Each item accepts optional transfer details; unknown means confirm with the recipient."""
    return await _call_api("POST", "/v1/check-batch", {"items": [item.model_dump() for item in items]})


@server.tool()
async def report_scam_address(
    address: str,
    chain: str = "EVM",
    reason: Optional[str] = None,
) -> dict:
    """Report a suspected scam address to PathGuard's community reporting system."""
    return await _call_api(
        "POST",
        "/v1/report",
        {"address": address, "chain": chain, "reason": reason},
    )


@server.tool()
async def get_usage_status() -> dict:
    """Check your current PathGuard plan, monthly scan quota, and usage."""
    return await _call_api("GET", "/v1/billing/status")


def _env_list(name: str) -> list[str]:
    value = os.environ.get(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


def main():
    parser = argparse.ArgumentParser(description="PathGuard MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default=os.environ.get("PATHGUARD_MCP_TRANSPORT", "stdio"),
        help="stdio for local MCP clients; streamable-http for remote MCP deployments",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("PATHGUARD_MCP_HOST", "127.0.0.1"),
        help="Host to bind to (streamable-http only)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PATHGUARD_MCP_PORT", os.environ.get("PORT", "8000"))),
        help="Port to bind to (streamable-http only)",
    )
    parser.add_argument(
        "--allowed-host",
        action="append",
        default=None,
        help="Allowed hostname (repeatable). Overrides PATHGUARD_MCP_ALLOWED_HOSTS.",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        server.run(transport="stdio")
        return

    allowed_hosts = args.allowed_host or _env_list("PATHGUARD_MCP_ALLOWED_HOSTS")

    security = None
    if allowed_hosts:
        security = TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=allowed_hosts,
        )

    server.run(
        transport="streamable-http",
        host=args.host,
        port=args.port,
        transport_security=security,
    )


if __name__ == "__main__":
    main()
