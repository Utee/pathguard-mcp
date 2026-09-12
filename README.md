# pathguard-mcp

PathGuard MCP lets MCP-compatible AI agents check crypto transactions for scams and mistakes directly in conversation. It supports local MCP clients such as Claude Desktop, Claude Code, Gemini CLI, Grok CLI, Cursor, and Codex, plus remote Streamable HTTP deployments.

[![MCP Registry](https://img.shields.io/badge/MCP%20Registry-org.cieltech.pathguard%2Fpathguard-blue)](https://registry.modelcontextprotocol.io/v0.1/servers?search=org.cieltech.pathguard/pathguard)

> Listed on the [official MCP Registry](https://registry.modelcontextprotocol.io/v0.1/servers?search=org.cieltech.pathguard/pathguard) as `org.cieltech.pathguard/pathguard`.

The MCP server is a thin wrapper around the authenticated PathGuard API. Your PathGuard API key remains the credential used by the server and should never be exposed to an AI client or committed to source control.

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

Create a PathGuard account and API key from the [PathGuard API documentation](https://pathguard.cieltech.org/docs.html).

Keep your API key private. Do not commit it to GitHub or expose it in browser-side code.

## Test locally

After installation, verify the MCP server starts with the default stdio transport:

```bash
export PATHGUARD_API_KEY=pg_your_key_here
pathguard-mcp
```

The stdio process waits for MCP messages from the client. This is normal; desktop and CLI MCP clients manage the process for you.

To point the MCP server at a local PathGuard API instead of production:

```bash
export PATHGUARD_API_KEY=pg_your_test_key
export PATHGUARD_API_BASE=http://localhost:8000
pathguard-mcp
```

## Configure local MCP clients

Install this package wherever the client runs, then give the server your PathGuard API key. The examples below use the installed `pathguard-mcp` command. If it is not on your `PATH`, replace it with the full executable path.

### Claude Desktop

Add this to your Claude Desktop config (`claude_desktop_config.json`):

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

Restart Claude Desktop, and Claude will have access to PathGuard's tools automatically.

### Claude Code

```bash
claude mcp add --transport stdio pathguard -- \
  pathguard-mcp
```

Set `PATHGUARD_API_KEY` in the environment that starts Claude Code. Alternatively, use Claude Code's MCP configuration to pass that variable explicitly.

### Gemini CLI

Add this entry to `~/.gemini/settings.json` for a user-wide setup, or `.gemini/settings.json` in a project:

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

Or add it from the command line after exporting your key:

```bash
export PATHGUARD_API_KEY=pg_your_key_here
gemini mcp add --scope user pathguard pathguard-mcp
```

### Grok CLI

After exporting your key, add the local stdio server:

```bash
export PATHGUARD_API_KEY=pg_your_key_here
grok mcp add pathguard -- pathguard-mcp
```

To store the configuration manually in `~/.grok/config.toml`, use:

```toml
[mcp_servers.pathguard]
command = "pathguard-mcp"
env = { PATHGUARD_API_KEY = "${PATHGUARD_API_KEY}" }
```

### Codex, Cursor, VS Code, and other local MCP clients

Use the same stdio server definition as the Claude Desktop example: command `pathguard-mcp`, no arguments, and `PATHGUARD_API_KEY` in its environment. The exact configuration-file location and UI differ by client; the MCP server settings are the same.

## Configure remote clients

For browser-based MCP clients such as ChatGPT or Grok, deploy PathGuard MCP with Streamable HTTP behind HTTPS. Never put a PathGuard API key in client-side browser configuration.

Start the HTTP server locally or in your deployment environment:

```bash
export PATHGUARD_API_KEY=pg_your_key_here
pathguard-mcp --transport streamable-http --host 0.0.0.0 --port 8000 \
  --allowed-host mcp.example.com
```

The MCP endpoint is `http://<host>:8000/mcp`. In production, publish it as a protected HTTPS URL such as `https://mcp.example.com/mcp`.

### Environment-based deployment

The server also supports deployment configuration through environment variables:

```bash
PATHGUARD_API_KEY=pg_your_key_here
PATHGUARD_API_BASE=https://pathguard-v2.up.railway.app
PATHGUARD_MCP_TRANSPORT=streamable-http
PATHGUARD_MCP_HOST=0.0.0.0
PATHGUARD_MCP_PORT=8000
PATHGUARD_MCP_ALLOWED_HOSTS=mcp.example.com
```

`PATHGUARD_MCP_ALLOWED_HOSTS` accepts a comma-separated list. `PORT` is used when `PATHGUARD_MCP_PORT` is not set.

### ChatGPT

In a ChatGPT workspace with Developer Mode enabled, create a custom MCP app, provide your public `https://.../mcp` endpoint, scan its tools, and save or publish it as appropriate for your workspace. ChatGPT connects to remote MCP servers for this use case.

### Grok web

Use Grok's custom connector flow and provide your public `https://.../mcp` endpoint. The server must be reachable over HTTPS.

## Security notes

- Keep `PATHGUARD_API_KEY` server-side and private.
- Use HTTPS for remote deployments.
- Restrict allowed hosts for Streamable HTTP deployments.
- The MCP server authenticates to PathGuard with the configured API key; it does not provide separate per-MCP-user authentication.
- Do not commit API keys, production credentials, or local `.env` files.

## Available tools

| Tool | What it does |
|---|---|
| `check_transaction` | Scan a single transaction for scam addresses, clipboard-hijack patterns, and typo mistakes |
| `check_transactions_batch` | Scan up to 1,000 transactions in one call |
| `report_scam_address` | Flag an address as a scam (community reporting) |
| `get_usage_status` | Check your current plan, quota, and usage this month |

## Full API reference

See the [PathGuard API documentation](https://pathguard.cieltech.org/docs.html) for complete endpoint documentation, rate limits, and flag meanings. This MCP server is a thin wrapper over the same API.
