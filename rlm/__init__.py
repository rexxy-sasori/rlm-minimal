"""
Recursive Language Model (RLM) Package.

This package provides two architectures for code execution:

1. Local Execution (Default):
   - Code runs in the same process as RLM inference
   - Simple setup, no additional services required
   - Suitable for development and testing
   
2. Remote WASM Execution (Secure):
   - Code runs in separate WASM execution plane
   - Complete isolation between inference and execution
   - Suitable for production deployment in k8s

Quick Start - Local Execution:
    from rlm.local import RLM_REPL
    
    rlm = RLM_REPL(model="gpt-5")
    result = rlm.completion(context, query)

Quick Start - Remote Execution:
    from rlm.remote import RemoteREPLFactory
    from rlm.local import RLM_REPL
    
    # Set up remote REPL factory
    factory = RemoteREPLFactory(wasm_service_url="http://wasm-service:8000")
    
    # Use RLM with remote execution
    rlm = RLM_REPL(model="gpt-5")
    result = rlm.completion(context, query)
"""

from .rlm import RLM

# Import local architecture
from .local import REPLEnv as LocalREPLEnv
from .local import RLM_REPL as LocalRLM_REPL

# Import remote architecture
from .remote import RemoteREPLEnv, RemoteREPLFactory, RemoteExecutionConfig

# Import WASM engine
from .wasm import WASMREPLExecutor, WASMResult, WASMREPLEnv

__all__ = [
    "RLM",
    # Local architecture
    "LocalREPLEnv",
    "LocalRLM_REPL",
    # Remote architecture
    "RemoteREPLEnv",
    "RemoteREPLFactory",
    "RemoteExecutionConfig",
    # WASM engine
    "WASMREPLExecutor",
    "WASMResult",
    "WASMREPLEnv",
]

