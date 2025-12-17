# Changelog

## [Unreleased] - 2025-12-16

### Changed - POST /sse Handler for TypingMind Compatibility

**Date**: 2025-12-16
**Reason**: TypingMind expects POST requests to `/sse` to process initialize requests directly and return the initialize response as SSE events, rather than just returning an endpoint URL.

**Changes Made**:
- Modified `handle_sse_post()` in `ads_mcp/server.py` to:
  - Read and parse the request body
  - Detect if the request is an `initialize` method call
  - If initialize: Process the request and return the initialize response as SSE events (`event: message` with JSON-RPC response)
  - If not initialize: Fall back to original behavior (return endpoint URL)
- Added `json` import for JSON serialization

**Files Modified**:
- `ads_mcp/server.py`

**Revert Instructions**:
To revert to the previous behavior (returning endpoint URL only), change the POST handler back to:

```python
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
```

**Testing**:
- Tested locally with curl POST request containing initialize method
- Should be tested with TypingMind after deployment

---

## Previous Changes

### Added - CORS Headers and OPTIONS Handler
- Added CORS headers to POST `/sse` handler
- Added OPTIONS handler for CORS preflight requests
- Enables cross-origin requests from TypingMind

### Added - POST Handler for /sse Endpoint
- Added custom POST route handler for `/sse` endpoint
- Enables TypingMind compatibility (TypingMind sends POST to `/sse`)

### Changed - Default Transport to SSE
- Changed default transport from `streamable-http` to `sse`
- Updated `render.yaml` to use SSE transport
- Updated documentation

### Added - Render Deployment Support
- Added support for creating credentials file from `GOOGLE_ADS_YAML` environment variable
- Updated server to use Render's `PORT` environment variable
- Created `render.yaml` configuration file
- Created `requirements.txt` for Render compatibility
- Created `RENDER_DEPLOYMENT.md` deployment guide


