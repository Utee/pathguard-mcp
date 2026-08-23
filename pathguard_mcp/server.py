"""
PathGuard MCP server. Wraps the PathGuard REST API as MCP tools, so any
MCP-compatible AI agent (Claude Desktop, Claude Code, etc.) can check
crypto transactions for scams and mistakes directly in conversation.

Available to any plan, since this just calls the same authenticated API
endpoints as everything else — your API key's plan/quota already applies.

Configure with two environment variables:
    PATHGUARD_API_KEY  - your PathGuard API key (starts with 'pg_')
    PATHGUARD_API_BASE - your PathGuard backend URL (defaults to the
                          production one, override for local testing)
"""
import argparse
import os
from typing import Optional

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

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
    """
    Scan a single crypto transaction for scam addresses, clipboard-hijack
    patterns, and typo/decimal mistakes before sending. Returns a risk
    score (0-100), a list of flags, and whether it should be blocked.

    Args:
        address: The destination address being sent to
        chain: EVM, BTC, SOL, or TRON. Defaults to EVM.
        amount: The amount being sent, used for precision-mistake checks
    """
    return await _call_api("POST", "/v1/check", {"address": address, "chain": chain, "amount": amount})


@server.tool()
async def check_transactions_batch(items: list[dict]) -> dict:
    """
    Scan up to 100 transactions in one call, useful for reviewing a batch
    of transfers at once.

    Args:
        items: List of transactions, each a dict with 'address' (required),
               'chain' (optional, defaults to EVM), and 'amount' (optional)
    """
    return await _call_api("POST", "/v1/check-batch", {"items": items})


@server.tool()
async def report_scam_address(address: str, chain: str = "EVM", reason: Optional[str] = None) -> dict:
    """
    Flag an address as a scam. Once 3 distinct accounts report the same
    address, it's treated as confirmed and blocked for everyone.

    Args:
        address: The suspected scam address
        chain: EVM, BTC, SOL, or TRON. Defaults to EVM.
        reason: Why this address looks like a scam
    """
    return await _call_api("POST", "/v1/report", {"address": address, "chain": chain, "reason": reason})


@server.tool()
async def get_usage_status() -> dict:
    """Check your current PathGuard plan, monthly scan quota, and how much you've used this month."""
    return await _call_api("GET", "/v1/billing/status")


def main():
    """Start PathGuard over local stdio or Streamable HTTP.

    Stdio is intended for local MCP clients such as Claude Desktop, Gemini
    CLI, and Grok CLI. Streamable HTTP is intended for a deployed server that
    remote clients, such as ChatGPT and Grok on the web, can reach.
    """
    parser = argparse.ArgumentParser(description="Run the PathGuard MCP server")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default=os.environ.get("PATHGUARD_MCP_TRANSPORT", "stdio"),
        help="MCP transport to serve (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("PATHGUARD_MCP_HOST", "127.0.0.1"),
        help="HTTP bind host; used only with --transport streamable-http",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PATHGUARD_MCP_PORT", os.environ.get("PORT", "8000"))),
        help="HTTP port; used only with --transport streamable-http",
    )
    parser.add_argument(
        "--allowed-host",
        action="append",
        default=[],
        metavar="HOST",
        help=(
            "Public hostname allowed to call the HTTP server; repeat for each "
            "hostname. Also accepts PATHGUARD_MCP_ALLOWED_HOSTS as a comma-separated list."
        ),
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        server.run(transport="stdio")
        return

    # A public HTTP server must explicitly allow its public Host header. This
    # retains the MCP SDK's DNS-rebinding protection while working behind a
    # tunnel, reverse proxy, or deployed custom domain.
    configured_hosts = [
        host.strip()
        for host in os.environ.get("PATHGUARD_MCP_ALLOWED_HOSTS", "").split(",")
        if host.strip()
    ]
    configured_hosts.extend(args.allowed_host)
    allowed_hosts = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
    for host in configured_hosts:
        allowed_hosts.extend((host, f"{host}:*"))

    # Stateless Streamable HTTP is appropriate here: every tool call is
    # independently authenticated with the configured PathGuard API key.
    server.run(
        transport="streamable-http",
        host=args.host,
        port=args.port,
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(allowed_hosts=allowed_hosts),
    )


if __name__ == "__main__":
    main()
