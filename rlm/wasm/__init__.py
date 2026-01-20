"""
WASM Execution Engine.

This module contains the WASM execution engine using Pyodide.
It provides sandboxed Python code execution in WebAssembly.

Usage:
    from rlm.wasm import WASMREPLExecutor, WASMResult

    executor = WASMREPLExecutor(timeout=30)
    await executor.initialize()
    result = await executor.execute_code("print('Hello from WASM!')")
"""

from rlm.wasm.repl_wasm import WASMREPLExecutor, WASMResult, WASMREPLEnv

__all__ = ["WASMREPLExecutor", "WASMResult", "WASMREPLEnv"]
