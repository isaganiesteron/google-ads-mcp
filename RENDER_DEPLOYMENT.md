# Deploying to Render

This guide will help you deploy the Google Ads MCP server to Render.

## Prerequisites

1. A Render account (sign up at https://render.com)
2. Your Google Ads API credentials (`google-ads.yaml` file)
3. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)

## Deployment Steps

### Option 1: Using render.yaml (Recommended)

1. **Connect your repository to Render:**

   - Go to Render Dashboard → New → Web Service
   - Connect your Git repository
   - Render will automatically detect `render.yaml`

2. **Set Environment Variables in Render Dashboard:**

   - Go to your service → Environment
   - Add the following environment variables:

   **Required:**

   - `GOOGLE_ADS_YAML`: Paste the entire contents of your `google-ads.yaml` file here
     (This will be automatically written to a file at startup)

   **Optional:**

   - `MCP_TRANSPORT`: `sse` (default)
   - `MCP_HOST`: `0.0.0.0` (default)
   - `FASTMCP_SERVER_BASE_URL`: Your Render service URL (e.g., `https://your-service.onrender.com`)

3. **Deploy:**
   - Render will automatically build and deploy using the `render.yaml` configuration

### Option 2: Manual Configuration

1. **Create a new Web Service:**

   - Go to Render Dashboard → New → Web Service
   - Connect your Git repository

2. **Configure Build Settings:**

   - **Runtime**: Python 3.12
   - **Build Command**: `uv pip sync`
   - **Start Command**: `uv run -m ads_mcp.server`

3. **Set Environment Variables:**
   Same as Option 1 above.

## Environment Variables

### Required

- `GOOGLE_ADS_YAML`: The complete contents of your `google-ads.yaml` file as a string.
  Example format:
  ```yaml
  client_id: "your-client-id"
  client_secret: "your-client-secret"
  refresh_token: "your-refresh-token"
  developer_token: "your-developer-token"
  login_customer_id: "1234567890" # Optional
  ```

### Optional

- `GOOGLE_ADS_CREDENTIALS`: Path to credentials file (if you upload it separately)
- `MCP_TRANSPORT`: Transport type (`sse` is default)
- `MCP_HOST`: Host to bind to (`0.0.0.0` is default)
- `PORT`: Automatically set by Render (don't override)
- `FASTMCP_SERVER_BASE_URL`: Your Render service URL for OAuth callbacks

## Accessing Your Server

Once deployed, your server will be available at:

- `https://your-service-name.onrender.com/sse`

Use this URL in TypingMind or other MCP clients.

## Troubleshooting

### Build Fails

- Ensure Python 3.12 is selected
- Check that `uv` is available (it should be installed automatically)
- Verify all dependencies in `pyproject.toml` are valid

### Server Won't Start

- Check logs in Render dashboard
- Verify `GOOGLE_ADS_YAML` environment variable is set correctly
- Ensure the YAML content is properly formatted (no extra quotes needed)

### Connection Issues

- Verify the service is running (check status in Render dashboard)
- Test the endpoint: `curl https://your-service.onrender.com/sse`
- Check that `MCP_TRANSPORT` is set to `sse`

## Security Notes

- Never commit `google-ads.yaml` to your repository
- Always use Render's environment variables for sensitive data
- Consider using Render's secret management features
- The `GOOGLE_ADS_YAML` variable should be marked as "Secret" in Render
