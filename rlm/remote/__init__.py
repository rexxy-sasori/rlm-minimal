"""
Remote Execution Architecture.

This module contains the RLM implementation with remote code execution.
The generated code runs in a separate WASM execution plane via HTTP API.

Usage:
    from rlm.remote import RemoteREPLEnv, RemoteREPLFactory

    factory = RemoteREPLFactory(wasm_service_url="http://wasm-service:8000")
    repl_env = factory.create(max_depth=3)
    result = repl_env.code_execution("print('Hello')")
"""

from rlm.remote.repl_remote import RemoteREPLEnv, RemoteREPLFactory, RemoteExecutionConfig

__all__ = ["RemoteREPLEnv", "RemoteREPLFactory", "RemoteExecutionConfig"]
