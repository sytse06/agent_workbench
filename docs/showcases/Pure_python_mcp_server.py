#!/usr/bin/env python3
"""
Pure Python MCP Server Implementation
Supports stdio and SSE (Server-Sent Events) transports for server deployment
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import threading
from queue import Queue


class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"


@dataclass
class Tool:
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class Resource:
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None


class MCPServer:
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.tools: Dict[str, Tool] = {}
        self.resources: Dict[str, Resource] = {}
        self.tool_handlers = {}
        self.resource_handlers = {}
        self.sessions: Dict[str, Queue] = {}
        
    def add_tool(self, tool: Tool, handler):
        """Register a tool with its handler function"""
        self.tools[tool.name] = tool
        self.tool_handlers[tool.name] = handler
        
    def add_resource(self, resource: Resource, handler):
        """Register a resource with its handler function"""
        self.resources[resource.uri] = resource
        self.resource_handlers[resource.uri] = handler
    
    async def handle_initialize(self, params: Dict) -> Dict:
        """Handle initialization request"""
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": self.name,
                "version": self.version
            },
            "capabilities": {
                "tools": {} if self.tools else None,
                "resources": {} if self.resources else None,
            }
        }
    
    async def handle_tools_list(self, params: Dict) -> Dict:
        """List available tools"""
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.input_schema
                }
                for tool in self.tools.values()
            ]
        }
    
    async def handle_tools_call(self, params: Dict) -> Dict:
        """Execute a tool"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tool_handlers:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        handler = self.tool_handlers[tool_name]
        result = await handler(arguments)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": str(result)
                }
            ]
        }
    
    async def handle_resources_list(self, params: Dict) -> Dict:
        """List available resources"""
        return {
            "resources": [
                {
                    "uri": res.uri,
                    "name": res.name,
                    "description": res.description,
                    "mimeType": res.mime_type
                }
                for res in self.resources.values()
            ]
        }
    
    async def handle_resources_read(self, params: Dict) -> Dict:
        """Read a resource"""
        uri = params.get("uri")
        
        if uri not in self.resource_handlers:
            raise ValueError(f"Unknown resource: {uri}")
        
        handler = self.resource_handlers[uri]
        content = await handler()
        
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": self.resources[uri].mime_type or "text/plain",
                    "text": content
                }
            ]
        }
    
    async def handle_request(self, request: Dict) -> Dict:
        """Route and handle incoming requests"""
        method = request.get("method")
        params = request.get("params", {})
        
        handlers = {
            "initialize": self.handle_initialize,
            "tools/list": self.handle_tools_list,
            "tools/call": self.handle_tools_call,
            "resources/list": self.handle_resources_list,
            "resources/read": self.handle_resources_read,
        }
        
        if method not in handlers:
            raise ValueError(f"Unknown method: {method}")
        
        return await handlers[method](params)
    
    async def run_stdio(self):
        """Run server using stdio transport"""
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
        
        writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, asyncio.get_event_loop())
        
        while True:
            try:
                line = await reader.readline()
                if not line:
                    break
                
                request = json.loads(line.decode())
                request_id = request.get("id")
                
                try:
                    result = await self.handle_request(request)
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": result
                    }
                except Exception as e:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": str(e)
                        }
                    }
                
                writer.write((json.dumps(response) + "\n").encode())
                await writer.drain()
                
            except Exception as e:
                print(f"Error processing request: {e}", file=sys.stderr)
                break

    def run_sse(self, host: str = "0.0.0.0", port: int = 8000):
        """Run server using SSE (Server-Sent Events) transport over HTTP"""
        server = self
        
        class SSEHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                """Override to customize logging"""
                print(f"{self.address_string()} - {format % args}")
            
            def do_GET(self):
                """Handle SSE connections"""
                if self.path.startswith('/sse'):
                    # Generate session ID
                    session_id = f"session_{id(self)}"
                    server.sessions[session_id] = Queue()
                    
                    # Send SSE headers
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/event-stream')
                    self.send_header('Cache-Control', 'no-cache')
                    self.send_header('Connection', 'keep-alive')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    # Send endpoint information
                    endpoint_msg = {
                        "jsonrpc": "2.0",
                        "method": "endpoint",
                        "params": {
                            "endpoint": f"http://{host}:{port}/message?session_id={session_id}"
                        }
                    }
                    self.wfile.write(f"data: {json.dumps(endpoint_msg)}\n\n".encode())
                    self.wfile.flush()
                    
                    try:
                        # Keep connection alive and send queued messages
                        while True:
                            if not server.sessions.get(session_id):
                                break
                            
                            queue = server.sessions[session_id]
                            if not queue.empty():
                                message = queue.get()
                                self.wfile.write(f"data: {json.dumps(message)}\n\n".encode())
                                self.wfile.flush()
                            else:
                                # Send keepalive
                                self.wfile.write(": keepalive\n\n".encode())
                                self.wfile.flush()
                                asyncio.run(asyncio.sleep(15))
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                    finally:
                        if session_id in server.sessions:
                            del server.sessions[session_id]
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def do_POST(self):
                """Handle message posting"""
                if self.path.startswith('/message'):
                    # Parse session ID from query string
                    query = parse_qs(urlparse(self.path).query)
                    session_id = query.get('session_id', [None])[0]
                    
                    if not session_id or session_id not in server.sessions:
                        self.send_response(400)
                        self.end_headers()
                        self.wfile.write(b"Invalid session")
                        return
                    
                    # Read request body
                    content_length = int(self.headers['Content-Length'])
                    body = self.rfile.read(content_length)
                    
                    try:
                        request = json.loads(body.decode())
                        request_id = request.get("id")
                        
                        # Process request asynchronously
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        try:
                            result = loop.run_until_complete(server.handle_request(request))
                            response = {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "result": result
                            }
                        except Exception as e:
                            response = {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "error": {
                                    "code": -32603,
                                    "message": str(e)
                                }
                            }
                        finally:
                            loop.close()
                        
                        # Queue response for SSE stream
                        server.sessions[session_id].put(response)
                        
                        # Send acknowledgment
                        self.send_response(202)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({"status": "accepted"}).encode())
                        
                    except json.JSONDecodeError:
                        self.send_response(400)
                        self.end_headers()
                        self.wfile.write(b"Invalid JSON")
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def do_OPTIONS(self):
                """Handle CORS preflight"""
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
        
        print(f"Starting SSE server on {host}:{port}")
        print(f"SSE endpoint: http://{host}:{port}/sse")
        httpd = HTTPServer((host, port), SSEHandler)
        httpd.serve_forever()


# Example usage
async def example_tool_handler(arguments: Dict) -> str:
    """Example tool that adds two numbers"""
    a = arguments.get("a", 0)
    b = arguments.get("b", 0)
    return f"The sum of {a} and {b} is {a + b}"


async def example_resource_handler() -> str:
    """Example resource that returns some data"""
    return "This is example resource content"


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='MCP Server')
    parser.add_argument('--transport', choices=['stdio', 'sse'], default='stdio',
                      help='Transport type (default: stdio)')
    parser.add_argument('--host', default='0.0.0.0',
                      help='Host for SSE server (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000,
                      help='Port for SSE server (default: 8000)')
    args = parser.parse_args()
    
    # Create server
    server = MCPServer("example-server", "1.0.0")
    
    # Register a tool
    add_tool = Tool(
        name="add",
        description="Add two numbers together",
        input_schema={
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["a", "b"]
        }
    )
    server.add_tool(add_tool, example_tool_handler)
    
    # Register a resource
    example_resource = Resource(
        uri="example://data",
        name="Example Data",
        description="Example data resource",
        mime_type="text/plain"
    )
    server.add_resource(example_resource, example_resource_handler)
    
    # Run server with selected transport
    if args.transport == 'stdio':
        asyncio.run(server.run_stdio())
    else:
        server.run_sse(host=args.host, port=args.port)


if __name__ == "__main__":
    main()