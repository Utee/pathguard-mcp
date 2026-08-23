# pathguard-mcp

Lets MCP-compatible AI agents check crypto transactions for scams and mistakes directly in conversation, using [PathGuard](https://pathguard.cieltech.org). It supports local MCP clients such as Claude Desktop, Claude Code, Gemini CLI, Grok CLI, Cursor, and Codex, plus remote Streamable HTTP deployments for ChatGPT and Grok web connectors.

Available on every plan, including Free this just calls the same authenticated API endpoints as everything else, so your existing API key's quota applies.

## Install

```bash
pip install pathguard-mcp
```

(Not published to PyPI yet for now, install directly from source: `pip install -e .` from this folder.)

Requires **mcp >= 2.0**. This was built and tested against the current MCP SDK if you're on an older version with the old `FastMCP` API, upgrade first (`pip install --upgrade mcp`), otherwise this won't work.

## Get an API key

Sign up free at [pathguard.cieltech.org/docs.html](https://pathguard.cieltech.org/docs.html) if you don't have one.

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

## Configure remote clients: ChatGPT and Grok web

ChatGPT and Grok's browser-based custom connectors cannot launch a command on your computer. Deploy PathGuard MCP with Streamable HTTP, behind HTTPS, then enter the public endpoint in the connector UI.

Start the HTTP server locally or in your deployment environment:

```bash
export PATHGUARD_API_KEY=pg_your_key_here
pathguard-mcp --transport streamable-http --host 0.0.0.0 --port 8000 \
  --allowed-host mcp.example.com
```

The MCP endpoint is `http://<host>:8000/mcp`. For ChatGPT or Grok web, publish it as a protected HTTPS URL such as `https://mcp.example.com/mcp`; do not expose an API key in a browser or a repository. Pass its hostname with `--allowed-host` (or set `PATHGUARD_MCP_ALLOWED_HOSTS=mcp.example.com`) so the server can safely accept requests made through that public domain. This server's PathGuard credential is server-side, so each deployed instance represents the PathGuard account associated with its `PATHGUARD_API_KEY`.

### ChatGPT

In a ChatGPT workspace with Developer Mode enabled, create a custom MCP app, provide the public `https://.../mcp` endpoint, scan its tools, and save/publish it as appropriate for your workspace. ChatGPT connects only to remote MCP servers, not local stdio commands. See OpenAI's [Developer Mode and MCP apps guide](https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt) for current plan availability and setup controls.

### Grok web

At [grok.com/connectors](https://grok.com/connectors), select **New Connector** then **Custom**, and enter the public `https://.../mcp` endpoint. Grok must be able to reach the server over the public internet. See xAI's [custom MCP connector guide](https://docs.x.ai/grok/connectors) for its current connector flow.

## Deployment notes

- Use Streamable HTTP for new remote deployments; it is the current MCP HTTP transport.
- Terminate TLS at your hosting platform or reverse proxy, and restrict access to trusted users or a gateway where possible. The server currently authenticates to PathGuard with one configured API key; it does not authenticate individual MCP users.
- Configure `PATHGUARD_MCP_TRANSPORT=streamable-http`, `PATHGUARD_MCP_HOST=0.0.0.0`, `PATHGUARD_MCP_PORT=8000`, and `PATHGUARD_MCP_ALLOWED_HOSTS=mcp.example.com` instead of command-line flags if that fits your deployment platform. `PORT` is also honoured when `PATHGUARD_MCP_PORT` is unset.
- Keep the default `stdio` transport for desktop and CLI clients.

## Available tools

| Tool | What it does |
|---|---|
| `check_transaction` | Scan a single transaction for scam addresses, clipboard-hijack patterns, and typo mistakes |
| `check_transactions_batch` | Scan up to 100 transactions in one call |
| `report_scam_address` | Flag an address as a scam (community reporting) |
| `get_usage_status` | Check your current plan, quota, and usage this month |

## Testing locally without a real deployment

Point at a local backend instead of production:

```bash
export PATHGUARD_API_KEY=pg_your_test_key
export PATHGUARD_API_BASE=http://localhost:8000
pathguard-mcp
```

## Full API reference

See [pathguard.cieltech.org/docs.html](https://pathguard.cieltech.org/docs.html) for complete endpoint documentation, rate limits, and flag meanings this MCP server is a thin wrapper over that same API.
