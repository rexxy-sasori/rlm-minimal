import asyncio
import uuid
from typing import Dict, Optional, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from rlm.wasm.repl_wasm import WASMREPLExecutor, WASMResult

class SessionCreate(BaseModel):
    pass

class CodeExecution(BaseModel):
    code: str
    context: Optional[Dict[str, Any]] = None

class SessionManager:
    """
    Manages multiple WASM runtime sessions for concurrent RLM inference.
    Each session has its own isolated Pyodide runtime for state persistence.
    """
    
    def __init__(self):
        self.sessions: Dict[str, WASMREPLExecutor] = {}
        self._lock = asyncio.Lock()
    
    async def create_session(self) -> str:
        """Create a new WASM session with isolated runtime."""
        session_id = f"session-{uuid.uuid4().hex[:8]}"
        
        async with self._lock:
            # Create new executor for this session
            executor = WASMREPLExecutor()
            
            # Initialize in background
            await executor.initialize()
            
            self.sessions[session_id] = executor
            print(f"Created new WASM session: {session_id}")
            return session_id
    
    async def execute_in_session(self, session_id: str, code: str, context: Optional[Dict[str, Any]] = None) -> WASMResult:
        """Execute code in specific session with state persistence."""
        async with self._lock:
            if session_id not in self.sessions:
                raise ValueError(f"Session {session_id} not found")
            
            executor = self.sessions[session_id]
        
        # Execute code in session's executor
        return await executor.execute_code(code, context)
    
    async def destroy_session(self, session_id: str):
        """Destroy session and free resources."""
        async with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                print(f"Destroyed WASM session: {session_id}")
            else:
                print(f"Session {session_id} not found for destruction")
    
    async def cleanup_expired_sessions(self, max_age_seconds: int = 3600):
        """Cleanup sessions that haven't been used in a while."""
        # Implementation would track last used time and cleanup old sessions
        pass

class WASMManagerService:
    """FastAPI service for WASM session management."""
    
    def __init__(self):
        self.app = FastAPI(
            title="WASM Manager Service",
            description="Manages multiple WASM runtime sessions for RLM inference",
            version="1.0.0"
        )
        self.session_manager = SessionManager()
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        @self.app.post("/session")
        async def create_session():
            """Create new WASM session."""
            session_id = await self.session_manager.create_session()
            return {"session_id": session_id}
        
        @self.app.post("/session/{session_id}/execute")
        async def execute_code(session_id: str, execution: CodeExecution):
            """Execute code in specific session."""
            try:
                result = await self.session_manager.execute_in_session(
                    session_id,
                    execution.code,
                    execution.context
                )
                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "locals": result.locals,
                    "execution_time": result.execution_time,
                    "success": result.success,
                    "error": result.error
                }
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/session/{session_id}")
        async def destroy_session(session_id: str):
            """Destroy WASM session."""
            await self.session_manager.destroy_session(session_id)
            return {"status": "ok"}
        
        @self.app.get("/sessions")
        async def list_sessions():
            """List active sessions."""
            return {"sessions": list(self.session_manager.sessions.keys())}
    
    def run(self, host: str = "0.0.0.0", port: int = 8080):
        """Run the WASM Manager service."""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)

# Command-line entry point
if __name__ == "__main__":
    service = WASMManagerService()
    service.run()
