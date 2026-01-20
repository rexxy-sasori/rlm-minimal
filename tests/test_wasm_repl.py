import asyncio
import pytest
from rlm.repl_wasm import WASMREPLExecutor, WASMResult

class TestWASMREPL:
    """Test suite for WASM-based REPL executor."""
    
    @pytest.fixture
    async def executor(self):
        """Create and initialize a WASM REPL executor."""
        executor = WASMREPLExecutor(timeout=10)
        await executor.initialize()
        yield executor
        await executor.cleanup()
    
    @pytest.mark.asyncio
    async def test_basic_execution(self, executor):
        """Test basic code execution."""
        code = """
print('Hello World')
x = 42
y = 10
result = x + y
        """
        
        result = await executor.execute_code(code)
        
        assert result.success
        assert 'Hello World' in result.stdout
        assert result.stderr == ''
        assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_variable_creation(self, executor):
        """Test that variables are created and accessible."""
        code = """
message = 'test'
number = 123
pi = 3.14159
        """
        
        result = await executor.execute_code(code)
        
        assert result.success
        # Variables should be in locals
        assert 'message' in result.locals or 'message' in dir(result)
    
    @pytest.mark.asyncio
    async def test_stdout_capture(self, executor):
        """Test that stdout is captured correctly."""
        code = """
for i in range(3):
    print(f'Line {i}')
        """
        
        result = await executor.execute_code(code)
        
        assert result.success
        assert 'Line 0' in result.stdout
        assert 'Line 1' in result.stdout
        assert 'Line 2' in result.stdout
    
    @pytest.mark.asyncio
    async def test_stderr_capture(self, executor):
        """Test that stderr is captured correctly."""
        code = """
import sys
sys.stderr.write('Error message\n')
        """
        
        result = await executor.execute_code(code)
        
        assert result.success
        assert 'Error message' in result.stderr
    
    @pytest.mark.asyncio
    async def test_error_handling(self, executor):
        """Test that errors are handled properly."""
        code = """
undefined_variable  # This should raise NameError
        """
        
        result = await executor.execute_code(code)
        
        assert not result.success
        assert result.error is not None
        assert 'NameError' in result.error or 'undefined' in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_timeout(self):
        """Test that execution times out properly."""
        executor = WASMREPLExecutor(timeout=1)
        await executor.initialize()
        
        code = """
import time
time.sleep(5)  # This should timeout
        """
        
        result = await executor.execute_code(code)
        
        assert not result.success
        assert 'timeout' in result.error.lower()
        
        await executor.cleanup()
    
    @pytest.mark.asyncio
    async def test_context_injection(self, executor):
        """Test that context variables are injected."""
        context = {
            'injected_var': 'hello from context',
            'injected_num': 42
        }
        
        code = """
result = injected_var + ' - ' + str(injected_num)
print(result)
        """
        
        result = await executor.execute_code(code, context)
        
        assert result.success
        assert 'hello from context - 42' in result.stdout
    
    @pytest.mark.asyncio
    async def test_multiple_executions(self, executor):
        """Test that multiple executions work correctly."""
        # First execution
        result1 = await executor.execute_code("x = 10")
        assert result1.success
        
        # Second execution
        result2 = await executor.execute_code("y = 20")
        assert result2.success
        
        # Third execution using previous variables
        result3 = await executor.execute_code("z = x + y\nprint(z)")
        assert result3.success
        assert '30' in result3.stdout
    
    @pytest.mark.asyncio
    async def test_complex_code(self, executor):
        """Test execution of more complex code."""
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)
print(f'Fibonacci(10) = {result}')
        """
        
        result = await executor.execute_code(code)
        
        assert result.success
        assert 'Fibonacci(10) = 55' in result.stdout

if __name__ == '__main__':
    # Run basic test if executed directly
    async def run_basic_test():
        print("Testing WASM REPL Executor...")
        
        executor = WASMREPLExecutor(timeout=10)
        
        try:
            await executor.initialize()
            print("✓ Executor initialized")
            
            # Test 1: Basic execution
            result = await executor.execute_code("print('Hello WASM!')")
            if result.success:
                print(f"✓ Basic execution: {result.stdout.strip()}")
            else:
                print(f"✗ Basic execution failed: {result.error}")
            
            # Test 2: Arithmetic
            result = await executor.execute_code("x = 42 + 10\nprint(f'Result: {x}')")
            if result.success:
                print(f"✓ Arithmetic: {result.stdout.strip()}")
            else:
                print(f"✗ Arithmetic failed: {result.error}")
            
            print("\nAll tests completed!")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            print("\nNote: Pyodide may not be available in all environments.")
            print("Falling back to local Python execution is expected.")
        finally:
            await executor.cleanup()
    
    asyncio.run(run_basic_test())
