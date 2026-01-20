import asyncio
import json
import os
from typing import Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from rlm.repl_wasm import WASMREPLExecutor, WASMResult

class WASMREPLHandler(BaseHTTPRequestHandler):
    """HTTP handler for WASM REPL service."""
    
    executor: Optional[WASMREPLExecutor] = None
    
    def do_GET(self):
        """Handle GET requests for health checks."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
            return
            
        elif parsed_path.path == '/ready':
            if self.executor and self.executor._initialized:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ready"}).encode())
            else:
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "not_ready"}).encode())
            return
            
        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        """Handle POST requests for code execution."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path != '/execute':
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
            return
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            request_data = json.loads(post_data)
            
            code = request_data.get('code', '')
            context = request_data.get('context', {})
            timeout = request_data.get('timeout', 30)
            
            if not code:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Code is required"}).encode())
                return
            
            result = asyncio.run(self._execute_async(code, context, timeout))
            
            response = {
                "success": result.success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "locals": result.locals,
                "execution_time": result.execution_time,
                "error": result.error
            }
            
            self.send_response(200 if result.success else 500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    async def _execute_async(self, code: str, context: dict, timeout: int) -> WASMResult:
        """Execute code asynchronously."""
        if not self.executor:
            self.executor = WASMREPLExecutor(timeout=timeout)
            await self.executor.initialize()
        
        return await self.executor.execute_code(code, context)
    
    def log_message(self, format, *args):
        """Custom logging format."""
        print(f"[{self.address_string()}] {format % args}")

def run_server(host: str = '0.0.0.0', port: int = 8000):
    """Run the WASM REPL server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, WASMREPLHandler)
    
    print(f"Starting WASM REPL server on {host}:{port}")
    print(f"Health check: http://{host}:{port}/health")
    print(f"Ready check: http://{host}:{port}/ready")
    print(f"Execute endpoint: POST http://{host}:{port}/execute")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='WASM REPL Service')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to listen on')
    
    args = parser.parse_args()
    
    run_server(args.host, args.port)
