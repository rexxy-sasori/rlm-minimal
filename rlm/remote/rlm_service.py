import asyncio
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from typing import Optional

from rlm.rlm_repl import RLM_REPL
from rlm.repl_remote import RemoteREPLFactory

class RLMHandler(BaseHTTPRequestHandler):
    """HTTP handler for RLM inference service."""
    
    rlm: Optional[RLM_REPL] = None
    repl_factory: Optional[RemoteREPLFactory] = None
    
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
            if self.repl_factory and self.repl_factory.health_check():
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
        """Handle POST requests for RLM inference."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path != '/infer':
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
            return
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            request_data = json.loads(post_data)
            
            query = request_data.get('query', '')
            context = request_data.get('context', '')
            model = request_data.get('model', os.getenv('LLM_MODEL', 'gpt-5'))
            max_depth = request_data.get('max_depth', int(os.getenv('MAX_DEPTH', '1')))
            
            if not query:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Query is required"}).encode())
                return
            
            # Initialize RLM if not already initialized
            if not self.rlm:
                self._initialize_rlm(model, max_depth)
            
            # Run inference
            result = self.rlm.completion(context, query)
            
            response = {
                "success": True,
                "answer": result,
                "model": model,
                "max_depth": max_depth
            }
            
            self.send_response(200)
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
    
    def _initialize_rlm(self, model: str, max_depth: int):
        """Initialize RLM with remote REPL."""
        wasm_url = os.getenv('WASM_SERVICE_URL', 'http://wasm-repl-service:8000')
        
        self.repl_factory = RemoteREPLFactory(wasm_service_url=wasm_url)
        
        self.rlm = RLM_REPL(
            api_key=os.getenv('LLM_API_KEY'),
            model=model,
            base_url=os.getenv('LLM_BASE_URL'),
            max_depth=max_depth,
            enable_logging=False
        )
    
    def log_message(self, format, *args):
        """Custom logging format."""
        print(f"[{self.address_string()}] {format % args}")

def run_server(host: str = '0.0.0.0', port: int = 8000):
    """Run the RLM inference server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, RLMHandler)
    
    print(f"Starting RLM inference server on {host}:{port}")
    print(f"Health check: http://{host}:{port}/health")
    print(f"Ready check: http://{host}:{port}/ready")
    print(f"Infer endpoint: POST http://{host}:{port}/infer")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='RLM Inference Service')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to listen on')
    
    args = parser.parse_args()
    
    run_server(args.host, args.port)
