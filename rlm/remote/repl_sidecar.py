import os
import json
from typing import Optional, Dict, Any
import requests
from dataclasses import dataclass

from rlm.remote.repl_remote import RemoteREPLEnv, RemoteExecutionConfig

@dataclass
class SidecarExecutionConfig:
    """Configuration for sidecar WASM execution."""
    wasm_service_url: str = "http://localhost:8080"  # Sidecar runs on localhost
    timeout: int = 30
    session_ttl: int = 3600  # Session time-to-live in seconds

class SidecarREPLEnv(RemoteREPLEnv):
    """
    REPL environment that uses a sidecar WASM manager for stateful execution.
    Each session gets its own isolated WASM runtime for state persistence.
    """
    
    def __init__(self, config: SidecarExecutionConfig):
        super().__init__(RemoteExecutionConfig(
            wasm_service_url=config.wasm_service_url,
            timeout=config.timeout
        ))
        self.config = config
        self.session_id: Optional[str] = None
        self._session_created = False
    
    async def initialize(self):
        """Create WASM session with sidecar."""
        if self._session_created:
            return
        
        try:
            response = requests.post(
                f"{self.config.wasm_service_url}/session",
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            self.session_id = result["session_id"]
            self._session_created = True
            print(f"Created sidecar WASM session: {self.session_id}")
            
        except Exception as e:
            print(f"Failed to create WASM session: {e}")
            raise
    
    def set_context(self, context_json: Dict[str, Any], context_str: str):
        """Set context for REPL environment."""
        self.context_json = context_json
        self.context_str = context_str
        print(f"Set context for sidecar session: {self.session_id}")
    
    async def execute_code(self, code: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute code in sidecar session with state persistence."""
        if not self._session_created:
            await self.initialize()
        
        try:
            response = requests.post(
                f"{self.config.wasm_service_url}/session/{self.session_id}/execute",
                json={"code": code, "context": context},
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Failed to execute code in sidecar: {e}")
            return {
                "stdout": "",
                "stderr": str(e),
                "locals": {},
                "execution_time": 0,
                "success": False,
                "error": str(e)
            }
    
    def code_execution(self, code: str) -> Dict[str, Any]:
        """Synchronous wrapper for code execution."""
        import asyncio
        return asyncio.run(self.execute_code(code))
    
    async def cleanup(self):
        """Cleanup sidecar session."""
        if self._session_created and self.session_id:
            try:
                response = requests.delete(
                    f"{self.config.wasm_service_url}/session/{self.session_id}",
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                print(f"Cleaned up sidecar WASM session: {self.session_id}")
            except Exception as e:
                print(f"Failed to cleanup WASM session: {e}")
            finally:
                self._session_created = False
                self.session_id = None

class SidecarREPLFactory:
    """
    REPL factory that creates SidecarREPLEnv instances for sidecar architecture.
    Each instance gets its own isolated WASM runtime session.
    """
    
    def __init__(self, config: Optional[SidecarExecutionConfig] = None):
        if config is None:
            config = SidecarExecutionConfig(
                wasm_service_url=os.environ.get(
                    "WASM_MANAGER_SERVICE_URL", 
                    "http://localhost:8080"
                )
            )
        self.config = config
    
    def create_repl_env(self) -> SidecarREPLEnv:
        """Create new REPL environment with sidecar session."""
        return SidecarREPLEnv(self.config)
    
    async def create_session(self) -> str:
        """Create a new WASM session directly."""
        env = self.create_repl_env()
        await env.initialize()
        return env.session_id
    
    async def execute_in_session(self, session_id: str, code: str) -> Dict[str, Any]:
        """Execute code in existing session."""
        try:
            response = requests.post(
                f"{self.config.wasm_service_url}/session/{session_id}/execute",
                json={"code": code},
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "locals": {},
                "execution_time": 0,
                "success": False,
                "error": str(e)
            }
    
    async def destroy_session(self, session_id: str):
        """Destroy existing session."""
        try:
            response = requests.delete(
                f"{self.config.wasm_service_url}/session/{session_id}",
                timeout=self.config.timeout
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to destroy session: {e}")

# Helper function for easy initialization
def create_sidecar_repl_factory() -> SidecarREPLFactory:
    """Create sidecar REPL factory with default configuration."""
    config = SidecarExecutionConfig(
        wasm_service_url=os.environ.get(
            "WASM_MANAGER_SERVICE_URL", 
            "http://localhost:8080"
        )
    )
    return SidecarREPLFactory(config)
