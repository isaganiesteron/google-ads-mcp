# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The server for the Google Ads API MCP."""
import asyncio
import json
import os
import threading
import uuid

from ads_mcp.coordinator import mcp_server
from ads_mcp.scripts.generate_views import update_views_yaml
from ads_mcp.tools import api
from ads_mcp.tools import docs

import dotenv
from fastmcp.server.auth.providers.google import GoogleProvider
from fastmcp.server.auth.providers.google import GoogleTokenVerifier
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse


dotenv.load_dotenv()


tools = [api, docs]

if os.getenv("USE_GOOGLE_OAUTH_ACCESS_TOKEN"):
  mcp_server.auth = GoogleTokenVerifier()

if os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID") and os.getenv(
    "FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET"
):
  base_url = os.getenv("FASTMCP_SERVER_BASE_URL", "http://localhost:8000")
  mcp_server.auth = GoogleProvider(
      base_url=base_url,
      required_scopes=["https://www.googleapis.com/auth/adwords"],
  )


# Add POST handler for /sse endpoint (for TypingMind compatibility)
# CHANGELOG: Updated to process initialize requests directly instead of returning endpoint URL
# This matches TypingMind's expected behavior where POST /sse should handle initialize
@mcp_server.custom_route("/sse", methods=["POST"])
async def handle_sse_post(request: Request) -> StreamingResponse:
  """Handle POST requests to /sse endpoint (TypingMind compatibility)."""
  # Read the request body
  try:
    body = await request.json()
  except:
    body = {}

  # Generate session ID
  session_id = str(uuid.uuid4()).replace("-", "")

  # If it's an initialize request, process it and return response
  if body.get("method") == "initialize":
    # Create initialize response matching FastMCP format
    init_response = {
        "jsonrpc": "2.0",
        "id": body.get("id"),
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "experimental": {},
                "prompts": {"listChanged": True},
                "resources": {"subscribe": False, "listChanged": True},
                "tools": {"listChanged": True},
            },
            "serverInfo": {
                "name": "Google Ads API",
                "version": "2.13.0.2",
            },
        },
    }

    async def event_stream():
      yield f"event: message\n"
      yield f"data: {json.dumps(init_response)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type, mcp-session-id, mcp-protocol-version",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Expose-Headers": "mcp-session-id",
            "Access-Control-Max-Age": "86400",
        },
    )
  else:
    # Fallback: return endpoint URL (original behavior)
    messages_url = f"/messages/?session_id={session_id}"

    async def event_stream():
      yield f"event: endpoint\n"
      yield f"data: {messages_url}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type, mcp-session-id, mcp-protocol-version",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Expose-Headers": "mcp-session-id",
            "Access-Control-Max-Age": "86400",
        },
    )


# Add OPTIONS handler for CORS preflight requests
@mcp_server.custom_route("/sse", methods=["OPTIONS"])
async def handle_sse_options() -> Response:
  """Handle CORS preflight requests."""
  return Response(
      status_code=200,
      headers={
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Headers": "Content-Type, mcp-session-id, mcp-protocol-version",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Expose-Headers": "mcp-session-id",
          "Access-Control-Max-Age": "86400",
      },
  )


def main():
  """Initializes and runs the MCP server."""
  # Allow transport to be configured via environment variable, default to SSE
  transport = os.getenv("MCP_TRANSPORT", "sse")
  host = os.getenv("MCP_HOST", "0.0.0.0")
  # Render provides PORT, fallback to MCP_PORT for local development
  port = int(os.getenv("PORT", os.getenv("MCP_PORT", "8000")))

  # Initialize in background to avoid blocking server startup
  # This allows the server to bind to the port quickly for Render's port scanner
  async def initialize_background():
    """Initialize views and credentials in the background."""
    try:
      print("Updating views YAML...")
      await update_views_yaml()
      print("Views YAML updated successfully")
    except Exception as e:
      print(f"Warning: Failed to update views YAML: {e}")
      print("Server will continue, but some features may be limited")

    try:
      print("Checking Google Ads credentials...")
      api.get_ads_client()
      print("Google Ads credentials verified")
    except Exception as e:
      print(f"Warning: Failed to verify Google Ads credentials: {e}")
      print("Server will start, but API calls will fail until credentials are configured")

  # Start initialization in background
  import threading
  init_thread = threading.Thread(target=lambda: asyncio.run(initialize_background()), daemon=True)
  init_thread.start()

  print("mcp server starting...")
  print(f"Binding to {host}:{port} with transport: {transport}")
  mcp_server.run(transport=transport, host=host, port=port)  # Initialize and run the server


if __name__ == "__main__":
  main()
