
import argparse
import os
from typing import Optional

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.streamable_http import TransportSecuritySettings

API_KEY = os.environ.get("PATHGUARD_API_KEY", "")
API_BASE = os.environ.get("PATHGUARD_API_BASE", "https://pathguard-v2.up.railway.app")

server = MCPServer("pathguard", version="0.1.0")


async def _call_api(method: str, path: str, json_body: Optional[dict] = None) -> dict:
    if not API_KEY:
        return {"error": "PATHGUARD_API_KEY is not set. Get a free key at pathguard.cieltech.org/docs.html"}

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.request(
            method,
            f"{API_BASE}{path}",
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
async def check_transaction(address: str, chain: str = "EVM", amount: Optional[float] = None) -> dict:
   
    return await _call_api("POST", "/v1/check", {"address": address, "chain": chain, "amount": amount})


@server.tool()
async def check_transactions_batch(items: list[dict]) -> dict:
   
    return await _call_api("POST", "/v1/check-batch", {"items": items})


@server.tool()
async def report_scam_address(address: str, chain: str = "EVM", reason: Optional[str] = None) -> dict:
    
    return await _call_api("POST", "/v1/report", {"address": address, "chain": chain, "reason": reason})


@server.tool()
async def get_usage_status() -> dict:
    """Check your current PathGuard plan, monthly scan quota, and how much you've used this month."""
    return await _call_api("GET", "/v1/billing/status")


def main():
    parser = argparse.ArgumentParser(description="PathGuard MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="stdio for local MCP clients (Claude Desktop, etc), streamable-http for a public HTTPS endpoint",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (streamable-http only)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (streamable-http only)")
    parser.add_argument(
        "--allowed-host",
        action="append",
        default=[],
        help="Hostname allowed to reach this server (streamable-http only, DNS-rebinding protection). Repeatable.",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        server.run(transport="stdio")
        return

    security = None
    if args.allowed_host:
        security = TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=args.allowed_host,
        )

    server.run(
        transport="streamable-http",
        host=args.host,
        port=args.port,
        transport_security=security,
    )


if __name__ == "__main__":
    main()