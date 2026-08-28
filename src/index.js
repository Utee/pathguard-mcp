import { Container, getContainer } from "@cloudflare/containers";
import { env } from "cloudflare:workers";


export class PathGuardContainer extends Container {
  defaultPort = 8000;
  sleepAfter = "10m";
  envVars = {
    PATHGUARD_API_KEY: env.PATHGUARD_API_KEY,
    PATHGUARD_API_BASE: env.PATHGUARD_API_BASE || "https://pathguard-v2.up.railway.app",
    PATHGUARD_MCP_ALLOWED_HOSTS: env.PATHGUARD_MCP_ALLOWED_HOSTS,
  };
}

export default {
  async fetch(request, bindings) {
    const url = new URL(request.url);

    if (url.pathname === "/") {
      return Response.json({
        name: "PathGuard MCP",
        endpoint: "/mcp",
      });
    }

    if (url.pathname !== "/mcp") {
      return new Response("Not Found", { status: 404 });
    }

    return getContainer(bindings.PATHGUARD_CONTAINER, "pathguard-mcp").fetch(request);
  },
};
