import os
import json
import uuid
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from rlm.repl import REPLResult

@dataclass
class RemoteExecutionConfig:
    """Configuration for remote WASM execution."""
    wasm_service_url: str
    timeout: int = 35
    max_retries: int = 3
    retry_backoff: float = 0.5
    verify_ssl: bool = True

class RemoteREPLEnv:
    """
    REPL environment that executes code remotely via WASM service.
    
    This provides security isolation by running generated code
    in a separate WASM execution plane, not in the RLM inference pod.
    """
    
    def __init__(
        self,
        wasm_service_url: Optional[str] = None,
        config: Optional[RemoteExecutionConfig] = None,
        recursive_models: Optional[List[str]] = None,
        recursive_base_urls: Optional[List[str]] = None,
        api_key: Optional[str] = None,
        context_json: Optional[dict | list] = None,
        context_str: Optional[str] = None,
        setup_code: str = None,
        max_depth: int = 1,
        current_depth: int = 0,
    ):
        """
        Initialize remote REPL environment.
        
        Args:
            wasm_service_url: URL of WASM execution service
            config: Remote execution configuration
            recursive_models: List of models for recursive calls
            recursive_base_urls: List of base URLs for recursive calls
            api_key: LLM API key (passed to sub-RLM if needed)
            context_json: Context data as JSON
            context_str: Context data as string
            setup_code: Code to run during initialization
            max_depth: Maximum recursion depth
            current_depth: Current recursion depth
        """
        self.config = config or RemoteExecutionConfig(
            wasm_service_url=wasm_service_url or os.getenv(
                'WASM_SERVICE_URL', 'http://wasm-repl-service:8000'
            )
        )
        
        self.session_id = str(uuid.uuid4())
        self.max_depth = max_depth
        self.current_depth = current_depth
        self.api_key = api_key
        
        # Initialize HTTP session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Store context for injection into remote execution
        self.context_json = context_json
        self.context_str = context_str
        self.setup_code = setup_code
        
        # Track variables across executions
        self.variables: Dict[str, Any] = {}
        
        # Load context if provided
        if context_json or context_str:
            self._load_context()
        
        # Run setup code if provided
        if setup_code:
            self.code_execution(setup_code)
        
        # Check if we should allow more recursion
        should_recurse = (current_depth + 1) < max_depth
        
        if should_recurse:
            from rlm.rlm_repl import RLM_REPL
            next_depth = current_depth + 1
            
            # Get model for next level
            default_models = recursive_models or ["gpt-5-mini"]
            if current_depth < len(default_models):
                next_model = default_models[current_depth]
            else:
                next_model = default_models[-1]
            
            # Get base URL for next level
            default_base_urls = recursive_base_urls or []
            if current_depth < len(default_base_urls):
                next_base_url = default_base_urls[current_depth]
            else:
                next_base_url = default_base_urls[-1] if default_base_urls else None
            
            self.sub_rlm = RLM_REPL(
                api_key=api_key,
                model=next_model,
                base_url=next_base_url,
                recursive_models=recursive_models,
                recursive_base_urls=recursive_base_urls,
                max_depth=max_depth,
                current_depth=next_depth,
                enable_logging=False
            )
        else:
            from rlm.repl import Sub_RLM
            self.sub_rlm = Sub_RLM(
                model=recursive_models[0] if recursive_models else "gpt-5-mini",
                base_url=recursive_base_urls[0] if recursive_base_urls else None,
                api_key=api_key
            )
    
    def _load_context(self):
        """Load context into variables dictionary."""
        if self.context_json is not None:
            self.variables['context'] = self.context_json
        
        if self.context_str is not None:
            self.variables['context_str'] = self.context_str
    
    def code_execution(self, code: str) -> REPLResult:
        """
        Execute code remotely via WASM service.
        
        Args:
            code: Python code to execute
            
        Returns:
            REPLResult with execution results
        """
        start_time = time.time()
        
        try:
            # Prepare execution request
            payload = {
                'code': code,
                'context': self.variables,
                'timeout': self.config.timeout - 5,  # Leave buffer for HTTP timeout
                'session_id': self.session_id
            }
            
            # Send request to WASM service
            response = self.session.post(
                f"{self.config.wasm_service_url}/execute",
                json=payload,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl
            )
            
            # Check response status
            response.raise_for_status()
            
            # Parse response
            result_data = response.json()
            
            # Update variables with results
            if result_data.get('locals'):
                self.variables.update(result_data['locals'])
            
            execution_time = time.time() - start_time
            
            return REPLResult(
                stdout=result_data.get('stdout', ''),
                stderr=result_data.get('stderr', ''),
                locals=self.variables.copy(),
                execution_time=execution_time
            )
            
        except requests.exceptions.Timeout:
            execution_time = time.time() - start_time
            return REPLResult(
                stdout='',
                stderr='Execution timeout: Code execution exceeded time limit',
                locals=self.variables.copy(),
                execution_time=execution_time
            )
            
        except requests.exceptions.ConnectionError as e:
            execution_time = time.time() - start_time
            return REPLResult(
                stdout='',
                stderr=f'Connection error: Could not reach WASM service: {str(e)}',
                locals=self.variables.copy(),
                execution_time=execution_time
            )
            
        except requests.exceptions.RequestException as e:
            execution_time = time.time() - start_time
            return REPLResult(
                stdout='',
                stderr=f'Execution error: {str(e)}',
                locals=self.variables.copy(),
                execution_time=execution_time
            )
            
        except json.JSONDecodeError:
            execution_time = time.time() - start_time
            return REPLResult(
                stdout='',
                stderr='Response error: Invalid JSON from WASM service',
                locals=self.variables.copy(),
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return REPLResult(
                stdout='',
                stderr=f'Unexpected error: {str(e)}',
                locals=self.variables.copy(),
                execution_time=execution_time
            )
    
    def llm_query(self, prompt: str) -> str:
        """Query the LLM via sub-RLM."""
        return self.sub_rlm.completion(prompt)
    
    def FINAL_VAR(self, variable_name: str) -> str:
        """Return the value of a variable."""
        variable_name = variable_name.strip().strip('"').strip("'").strip('\n').strip('\r')
        
        if variable_name in self.variables:
            return str(self.variables[variable_name])
        else:
            return f"Error: Variable '{variable_name}' not found in REPL environment"
    
    def cleanup(self):
        """Clean up resources."""
        try:
            self.session.close()
        except:
            pass
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()

class RemoteREPLFactory:
    """Factory for creating remote REPL environments."""
    
    def __init__(self, wasm_service_url: Optional[str] = None):
        self.wasm_service_url = wasm_service_url or os.getenv(
            'WASM_SERVICE_URL', 'http://wasm-repl-service:8000'
        )
    
    def create(
        self,
        max_depth: int = 1,
        current_depth: int = 0,
        **kwargs
    ) -> RemoteREPLEnv:
        """Create a new remote REPL environment."""
        return RemoteREPLEnv(
            wasm_service_url=self.wasm_service_url,
            max_depth=max_depth,
            current_depth=current_depth,
            **kwargs
        )
    
    def health_check(self) -> bool:
        """Check if WASM service is healthy."""
        try:
            response = requests.get(
                f"{self.wasm_service_url}/health",
                timeout=5,
                verify=False
            )
            return response.status_code == 200
        except:
            return False
    
    def readiness_check(self) -> bool:
        """Check if WASM service is ready."""
        try:
            response = requests.get(
                f"{self.wasm_service_url}/ready",
                timeout=5,
                verify=False
            )
            return response.status_code == 200
        except:
            return False
