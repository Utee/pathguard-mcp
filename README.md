# pathguard-mcp

PathGuard MCP lets MCP-compatible AI agents check crypto transactions for scams and mistakes directly in conversation. It supports local MCP clients such as Claude Desktop, Claude Code, Gemini CLI, Grok CLI, Cursor, and Codex, plus remote Streamable HTTP deployments.

[![MCP Registry](https://img.shields.io/badge/MCP%20Registry-org.cieltech.pathguard%2Fpathguard-blue)](https://registry.modelcontextprotocol.io/v0.1/servers?search=org.cieltech.pathguard/pathguard)

> Listed on the official MCP Registry as `org.cieltech.pathguard/pathguard`.

The production MCP server is a thin, authenticated interface to PathGuard's transaction-safety API. PathGuard analyzes transactions before a send; it does **not** sign, broadcast, or transfer funds.

## Production MCP

Remote Streamable HTTP endpoint:

```
https://api.pathguard.cieltech.org/mcp/
```

Remote clients use OAuth to connect an existing PathGuard account. During authorization, PathGuard verifies the user's existing API key. The API key is not exposed to the AI client or returned through MCP.

For local/stdio use, the API key is supplied to the local server process through `PATHGUARD_API_KEY`.

## Install

The package is currently installed directly from this public repository and is not published to PyPI yet.

```bash
git clone https://github.com/Utee/pathguard-mcp.git
cd pathguard-mcp
python -m pip install .
```

For development, use an editable install:

```bash
python -m pip install -e .
```

Requires **Python 3.10+** and **mcp >= 2.0**.

## Get an API key

Create a PathGuard account and API key from the [PathGuard API documentation](https://pathguard.cieltech.org/docs).

Keep your API key private. Do not commit it to GitHub or expose it in browser-side code.

## Local MCP clients

For local clients, the server uses stdio and authenticates to the PathGuard API with `PATHGUARD_API_KEY`.

### Claude Desktop

Add this to your Claude Desktop config:

```json
{
  "mcpServers": {
    "pathguard": {
      "command": "pathguard-mcp",
      "env": {
        "PATHGUARD_API_KEY": "pg_your_key_here"
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add --transport stdio pathguard -- pathguard-mcp
```

Set `PATHGUARD_API_KEY` in the environment that starts Claude Code.

### Gemini CLI

```json
{
  "mcpServers": {
    "pathguard": {
      "command": "pathguard-mcp",
      "env": {
        "PATHGUARD_API_KEY": "pg_your_key_here"
      }
    }
  }
}
```

### Grok CLI

```bash
export PATHGUARD_API_KEY=pg_your_key_here
grok mcp add pathguard -- pathguard-mcp
```

### Codex, Cursor, VS Code, and other local MCP clients

Use the same stdio server definition as the Claude Desktop example. The exact configuration location varies by client.

## Remote clients

For remote clients, use the production OAuth-protected Streamable HTTP endpoint shown above. Never put a PathGuard API key in browser-side configuration.

### ChatGPT

In a ChatGPT workspace with Developer Mode enabled, create a custom MCP app and provide:

```text
https://api.pathguard.cieltech.org/mcp/
```

Choose OAuth authentication. ChatGPT will use the PathGuard authorization flow to connect an existing PathGuard account.

The authorization flow verifies the user's PathGuard API key, then issues OAuth credentials for the MCP connection. The raw PathGuard API key is not returned to ChatGPT.

## Available tools

| Tool | What it does |
|---|---|
| `check_transaction` | Inspect one crypto destination and optional amount for PathGuard risk signals. |
| `preflight_transaction` | Run the full pre-send check and return `ALLOW`, `REVIEW`, or `BLOCK`. |
| `check_transactions_batch` | Check up to 1,000 transactions and return a compact risk summary or full results. |
| `report_scam_address` | Record a suspected scam address when the user explicitly asks to report it. |
| `get_usage_status` | View the connected account's plan and monthly scan usage. |
| `get_profile` | Identify the PathGuard account represented by the OAuth connection. |

### Tool safety boundary

PathGuard MCP is analysis-only. Its tools do not:

- sign transactions;
- broadcast transactions;
- transfer funds;
- request private keys or seed phrases;
- replace your application's authorization controls.

A `BLOCK` result is a PathGuard safety signal. The wallet, application, or agent remains responsible for authorization, signing, and final transaction execution.

## Batch checking

`check_transactions_batch` supports up to **1,000** items.

By default it returns a compact summary containing:

- total items;
- processed items;
- ALLOW / REVIEW / BLOCK counts;
- maximum risk score;
- flag counts;
- a sample of flagged transactions.

Use `detail_level="full"` when individual results are required.

## Security

- Keep API keys server-side and private.
- Use HTTPS for remote deployments.
- OAuth protects the production remote MCP connection.
- The production MCP server maps the authenticated OAuth subject to an existing PathGuard account.
- Internal server-to-server authentication is not exposed as an MCP argument or model-visible credential.
- Never commit API keys, production credentials, or local `.env` files.

## Full API reference

See the [PathGuard API documentation](https://pathguard.cieltech.org/docs) for endpoint schemas, rate limits, pricing, and risk-flag information.

PathGuard MCP: https://pathguard.cieltech.org/mcp

## Moving existing connections to the custom domain

Remote OAuth clients previously connected to the Railway address must create a new connection using `https://api.pathguard.cieltech.org/mcp/` and authorize again with their existing PathGuard API key. The old Railway endpoint is in maintenance; imported OAuth records do not automatically update a client's saved server URL or issuer.

For local stdio clients, update your checkout (`git pull` and `python -m pip install .`) or explicitly set `PATHGUARD_API_BASE=https://api.pathguard.cieltech.org` alongside `PATHGUARD_API_KEY`, then restart the MCP client. Existing API keys remain valid.


## Optional token and deposit details

Existing tool names are unchanged. `check_transaction` and each `check_transactions_batch` item accept an optional `transfer` object:

```json
{"address":"TAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA","chain":"TRON","transfer":{"token":"USDC","token_kind":"token","network":"TRON","destination_type":"exchange","exchange":"Kraken"}}
```

Exact networks: ETHEREUM, BASE, ARBITRUM, OPTIMISM, BSC, POLYGON, BITCOIN, SOLANA, TRON, XRPL, STELLAR. The address family remains EVM/BTC/SOL/TRON/XRP/XLM. Optional transfer fields include token_contract, recipient_network, memo and memo_required. Use native only for an actual native coin, not a wrapped token. The response includes compatibility reasons and official-source review dates where available. Initial exchange rules cover select Kraken requirements; unverified combinations and personal wallet acceptance remain Unknown—confirm with the recipient. OFAC screening covers EVM/BTC/SOL/TRON only. Token identity, memo account ownership and live deposit availability are not verified.

Update your GitHub-installed package and restart your MCP client to refresh its tool schemas. This source update does not publish a package release. The hosted OAuth MCP at https://api.pathguard.cieltech.org/mcp/ also extends its existing preflight_transaction tool with the same transfer object. Existing address-only calls still work.
