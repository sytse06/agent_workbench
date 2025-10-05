This is what the implementation does.

**SSE Transport Features:**
- **HTTP-based**: Works over standard HTTP/HTTPS
- **Bidirectional**: Uses SSE for server→client and POST for client→server
- **Session management**: Handles multiple concurrent clients
- **CORS enabled**: Can be accessed from web browsers
- **Keepalive**: Maintains connection with periodic pings

**How to use:**

**1. Run with stdio (default):**
```bash
python3 mcp_server.py --transport stdio
```

**2. Run with SSE:**
```bash
python3 mcp_server.py --transport sse --host 0.0.0.0 --port 8000
```

**3. Test SSE endpoint:**
```bash
# Connect to SSE stream
curl http://localhost:8000/sse

# Send a request (use the session_id from SSE response)
curl -X POST http://localhost:8000/message?session_id=SESSION_ID \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

**Deployment options:**

**With nginx reverse proxy:**
```nginx
server {
    listen 443 ssl;
    server_name mcp.example.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
    }
}
```

**With systemd:**
```ini
[Unit]
Description=MCP SSE Server
After=network.target

[Service]
Type=simple
User=mcpuser
ExecStart=/usr/bin/python3 /path/to/mcp_server.py --transport sse --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

The SSE transport is perfect for web-based clients and remote access, while stdio is better for local CLI tools like Claude Desktop!

---

## Observations from POC Implementation (2025-10-03)

### MCP Client vs Server: Protocol Compatibility Analysis

**Context:** During the DeepL POC implementation, we investigated using the Firecrawl MCP service as a **client** to consume their web scraping tools. This revealed important insights about MCP protocol implementations.

### Key Findings

#### 1. SSE Protocol Pattern Mismatch

**Pure Python MCP Server** (this implementation):
- Uses **two-endpoint pattern**:
  - `GET /sse` → Server-to-client event stream
  - `POST /message?session_id=X` → Client-to-server requests
- Session handshake flow:
  ```json
  // Initial SSE response provides endpoint URL
  {
    "jsonrpc": "2.0",
    "method": "endpoint",
    "params": {
      "endpoint": "http://host:port/message?session_id=SESSION_ID"
    }
  }
  ```

**Firecrawl Node.js MCP Server**:
- Also uses two-endpoint pattern (confirmed by testing)
- Endpoint: `http://localhost:3000/mcp` (when running in HTTP_STREAMABLE_SERVER mode)
- Returns "No sessionId" error when accessed without proper session setup

**Python MCP Client SDK** (`mcp.client.sse.sse_client`):
- Expects simpler single-endpoint SSE protocol
- Does NOT implement session ID extraction and POST endpoint pattern
- Result: **Protocol incompatibility** between Python client and Node.js/Python servers using this pattern

#### 2. Tested Configurations

| Configuration | Transport | Result | Notes |
|--------------|-----------|--------|-------|
| Python client → Firecrawl hosted HTTP | SSE | ✗ 400 Bad Request | `https://mcp.firecrawl.dev/{API_KEY}/v2/mcp` |
| Python client → Firecrawl local HTTP | SSE | ✗ "No sessionId" | `http://localhost:3000/mcp` via npx |
| Python client → Firecrawl stdio | stdio | ✓ Works | `npx -y firecrawl-mcp` |

#### 3. Root Cause Analysis

The "No sessionId" error from Firecrawl's HTTP server indicates it expects:
1. Client connects to SSE endpoint
2. Client receives session information in SSE stream
3. Client extracts session ID
4. Client sends subsequent requests to POST endpoint with session ID

The Python MCP SDK's `sse_client` implementation doesn't follow this pattern - it attempts to use SSE as a simple bidirectional channel without the session/POST mechanism.

### Architectural Implications

#### For the POC (Current Decision)

**Selected: stdio transport**
- ✓ Works reliably with Python MCP SDK
- ✓ No protocol compatibility issues
- ✓ Sufficient for POC scale (10-50 URLs)
- ✗ Requires Node.js/npx in deployment
- ✗ Process spawning overhead

**Code:**
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="npx",
    args=["-y", "firecrawl-mcp"],
    env={"FIRECRAWL_API_KEY": api_key}
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("firecrawl_scrape", {...})
```

#### For Future Production Considerations

**Option 1: Continue with stdio** (Simplest)
- Deploy with Node.js + Python environment
- Docker example: Install both runtimes
- Accept process overhead for simplicity

**Option 2: Custom SSE Client** (Most flexible)
- Implement two-endpoint SSE pattern in Python
- Match protocol that Pure_python_mcp_server.py demonstrates
- Eliminates Node.js dependency
- Significant development effort

**Option 3: Firecrawl Python SDK** (Most practical)
- Use official SDK directly (no MCP)
- Production-ready, no protocol issues
- Loses MCP standardization benefits

**Option 4: Pure Python MCP Server** (For custom tools)
- Use this `Pure_python_mcp_server.py` implementation
- Create custom scraping server if needed
- Full control over implementation
- Would need to implement Firecrawl API calls ourselves

### Recommendation for Architecture Discussion

1. **For POC**: Stick with stdio implementation (current)
   - Proven to work
   - Minimal complexity
   - Good for learning MCP protocol

2. **For Production**: Depends on scale and requirements
   - **Low volume (<100 URLs/day)**: stdio is fine, accept Node.js dependency
   - **High volume**: Consider Firecrawl Python SDK directly
   - **Need MCP standardization**: Invest in custom SSE client matching this server pattern
   - **Full control needed**: Fork/extend `Pure_python_mcp_server.py` with Firecrawl integration

3. **Protocol Standardization Gap**
   - The MCP spec allows different SSE implementations
   - Python client SDK and this server use different patterns
   - This is a known limitation to consider when choosing MCP for production

### References

- POC Implementation: `src/poc_deepl_translations/src/scraper.py`
- Architecture Documentation: `src/poc_deepl_translations/docs/Product Requirements Document.md` (Appendix A)
- Testing Results: All documented in PRD changelog v1.1 (2025-10-03)