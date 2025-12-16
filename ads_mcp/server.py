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
import os
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
@mcp_server.custom_route("/sse", methods=["POST"])
async def handle_sse_post(request: Request) -> StreamingResponse:
  """Handle POST requests to /sse endpoint (TypingMind compatibility)."""
  # Generate session ID
  session_id = str(uuid.uuid4()).replace("-", "")
  # Return the messages endpoint URL (same as GET /sse)
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
  asyncio.run(update_views_yaml())  # Check and update docs resource
  api.get_ads_client()  # Check Google Ads credentials
  print("mcp server starting...")
  # Allow transport to be configured via environment variable, default to SSE
  transport = os.getenv("MCP_TRANSPORT", "sse")
  host = os.getenv("MCP_HOST", "0.0.0.0")
  # Render provides PORT, fallback to MCP_PORT for local development
  port = int(os.getenv("PORT", os.getenv("MCP_PORT", "8000")))
  mcp_server.run(transport=transport, host=host, port=port)  # Initialize and run the server


if __name__ == "__main__":
  main()
