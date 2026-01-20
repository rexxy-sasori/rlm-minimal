import asyncio
import json
import os
import tempfile
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class WASMResult:
    stdout: str
    stderr: str
    locals: Dict[str, Any]
    execution_time: float
    success: bool
    error: Optional[str] = None

class WASMREPLExecutor:
    """
    WASM-based REPL executor using Pyodide for secure, sandboxed Python code execution.
    Designed for k8s deployment with isolation between executions.
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._initialized = False
        self._pyodide = None
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize Pyodide runtime."""
        if self._initialized:
            return
        
        async with self._lock:
            if self._initialized:
                return
            
            try:
                from pyodide import loadPyodide
                
                print("Loading Pyodide...")
                self._pyodide = await loadPyodide(
                    indexURL="https://cdn.jsdelivr.net/pyodide/v0.26.0/full/"
                )
                print("Pyodide loaded successfully")
                
                await self._pyodide.runPythonAsync("import sys")
                await self._pyodide.runPythonAsync("import io")
                
                self._initialized = True
                print("WASM REPL executor initialized")
                
            except ImportError as e:
                print(f"Pyodide not available: {e}")
                print("Falling back to local Python execution")
                self._initialized = True
            except Exception as e:
                print(f"Failed to initialize Pyodide: {e}")
                raise
    
    async def execute_code(self, code: str, context: Optional[Dict[str, Any]] = None) -> WASMResult:
        """
        Execute Python code in WASM sandbox.
        
        Args:
            code: Python code to execute
            context: Optional dictionary of variables to inject into the execution context
            
        Returns:
            WASMResult containing execution results
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with self._lock:
                if self._pyodide:
                    result = await self._execute_pyodide(code, context)
                else:
                    result = await self._execute_local(code, context)
                    
                result.execution_time = asyncio.get_event_loop().time() - start_time
                return result
                
        except asyncio.TimeoutError:
            return WASMResult(
                stdout="",
                stderr="",
                locals={},
                execution_time=asyncio.get_event_loop().time() - start_time,
                success=False,
                error="Execution timed out"
            )
        except Exception as e:
            return WASMResult(
                stdout="",
                stderr=str(e),
                locals={},
                execution_time=asyncio.get_event_loop().time() - start_time,
                success=False,
                error=f"Execution error: {str(e)}"
            )
    
    async def _execute_pyodide(self, code: str, context: Optional[Dict[str, Any]]) -> WASMResult:
        """Execute code using Pyodide."""
        try:
            if context:
                for key, value in context.items():
                    self._pyodide.globals.set(key, value)
            
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()
            
            original_stdout = self._pyodide.globals.get("sys").stdout
            original_stderr = self._pyodide.globals.get("sys").stderr
            
            self._pyodide.globals.get("sys").stdout = stdout_buffer
            self._pyodide.globals.get("sys").stderr = stderr_buffer
            
            try:
                await asyncio.wait_for(
                    self._pyodide.runPythonAsync(code),
                    timeout=self.timeout
                )
                
                stdout = stdout_buffer.getvalue()
                stderr = stderr_buffer.getvalue()
                
                locals_dict = {}
                for key in self._pyodide.globals.to_js().keys():
                    if not key.startswith('_'):
                        try:
                            value = self._pyodide.globals.get(key)
                            locals_dict[key] = value
                        except:
                            pass
                
                return WASMResult(
                    stdout=stdout,
                    stderr=stderr,
                    locals=locals_dict,
                    execution_time=0,
                    success=True
                )
                
            finally:
                self._pyodide.globals.get("sys").stdout = original_stdout
                self._pyodide.globals.get("sys").stderr = original_stderr
                
        except Exception as e:
            return WASMResult(
                stdout="",
                stderr=str(e),
                locals={},
                execution_time=0,
                success=False,
                error=str(e)
            )
    
    async def _execute_local(self, code: str, context: Optional[Dict[str, Any]]) -> WASMResult:
        """Fallback to local Python execution when Pyodide is not available."""
        import io
        import sys
        from contextlib import redirect_stdout, redirect_stderr
        
        try:
            local_vars = context.copy() if context else {}
            global_vars = {}
            
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()
            
            with redirect_stdout(stdout_buffer):
                with redirect_stderr(stderr_buffer):
                    exec(code, global_vars, local_vars)
            
            return WASMResult(
                stdout=stdout_buffer.getvalue(),
                stderr=stderr_buffer.getvalue(),
                locals=local_vars,
                execution_time=0,
                success=True
            )
            
        except Exception as e:
            return WASMResult(
                stdout="",
                stderr=str(e),
                locals={},
                execution_time=0,
                success=False,
                error=str(e)
            )
    
    async def cleanup(self):
        """Clean up Pyodide runtime."""
        if self._pyodide:
            try:
                self._pyodide = None
                self._initialized = False
            except:
                pass

class WASMREPLEnv:
    """
    WASM-based REPL environment wrapper for use with RLM.
    Provides the same interface as REPLEnv but uses WASM for execution.
    """
    
    def __init__(
        self,
        max_depth: int = 1,
        current_depth: int = 0,
        timeout: int = 30
    ):
        self.max_depth = max_depth
        self.current_depth = current_depth
        self.timeout = timeout
        self.executor = WASMREPLExecutor(timeout=timeout)
        self.temp_dir = tempfile.mkdtemp(prefix="wasm_repl_")
    
    async def initialize(self):
        """Initialize the WASM executor."""
        await self.executor.initialize()
    
    async def code_execution(self, code: str, context: Optional[Dict[str, Any]] = None) -> WASMResult:
        """Execute code in WASM environment."""
        return await self.executor.execute_code(code, context)
    
    async def cleanup(self):
        """Clean up resources."""
        await self.executor.cleanup()
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except:
            pass

async def main():
    """Example usage of WASM REPL executor."""
    executor = WASMREPLExecutor(timeout=10)
    
    try:
        await executor.initialize()
        
        code = """
print('Hello from WASM!')
x = 42
y = 58
result = x + y
print(f'Result: {result}')
        """
        
        result = await executor.execute_code(code)
        
        print(f"Success: {result.success}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        print(f"Execution time: {result.execution_time:.2f}s")
        print(f"Locals: {result.locals}")
        
        if result.error:
            print(f"Error: {result.error}")
            
    finally:
        await executor.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
