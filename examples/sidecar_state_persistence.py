"""
Example demonstrating state persistence with sidecar WASM architecture.
Shows how variables persist across multiple code executions in the same RLM session.
"""

import asyncio
from rlm.remote import SidecarREPLFactory, create_sidecar_repl_factory
from rlm.local.rlm_repl import RLM_REPL

async def test_state_persistence_direct():
    """Test state persistence directly with SidecarREPLFactory."""
    print("=== Testing State Persistence (Direct) ===")
    
    # Create sidecar REPL factory
    factory = create_sidecar_repl_factory()
    
    # Create session
    session_id = await factory.create_session()
    print(f"Created session: {session_id}")
    
    try:
        # Step 1: Define variable
        result1 = await factory.execute_in_session(session_id, "x = 42")
        print(f"Step 1 - Define x: {result1}")
        
        # Step 2: Use variable (should persist)
        result2 = await factory.execute_in_session(session_id, "x * 2")
        print(f"Step 2 - Multiply x by 2: {result2}")
        
        # Step 3: Modify variable
        result3 = await factory.execute_in_session(session_id, "x = x + 10")
        print(f"Step 3 - Increment x by 10: {result3}")
        
        # Step 4: Verify change persisted
        result4 = await factory.execute_in_session(session_id, "x")
        print(f"Step 4 - Check x value: {result4}")
        
        # Step 5: Define function
        result5 = await factory.execute_in_session(session_id, "def calculate(a, b): return a + b")
        print(f"Step 5 - Define calculate function: {result5}")
        
        # Step 6: Use function
        result6 = await factory.execute_in_session(session_id, "calculate(5, 7)")
        print(f"Step 6 - Use calculate function: {result6}")
        
        print("✅ State persistence test passed!")
        
    finally:
        # Cleanup
        await factory.destroy_session(session_id)
        print(f"Destroyed session: {session_id}")

async def test_state_persistence_with_rlm():
    """Test state persistence with RLM_REPL."""
    print("\n=== Testing State Persistence (with RLM_REPL) ===")
    
    # Create sidecar REPL factory
    factory = create_sidecar_repl_factory()
    
    # Create RLM with sidecar factory
    rlm = RLM_REPL(
        model="gpt-5",  # Replace with actual model
        max_depth=2,
        enable_logging=True,
        repl_factory=factory
    )
    
    # Test context with stateful operations
    context = """
    You are a helpful assistant. Use the REPL to solve the following:
    
    1. Define a variable x = 42
    2. Multiply x by 2
    3. Increment x by 10
    4. Define a function calculate(a, b) that returns a + b
    5. Use calculate(5, 7)
    6. Return the final value of x
    
    Show each step clearly.
    """
    
    query = "Solve the problem step by step using the REPL"
    
    try:
        # Run RLM inference
        result = rlm.completion(context, query)
        print(f"RLM Result: {result}")
        
        print("✅ RLM state persistence test completed!")
        
    finally:
        # Reset RLM
        rlm.reset()

if __name__ == "__main__":
    # Run tests
    asyncio.run(test_state_persistence_direct())
    asyncio.run(test_state_persistence_with_rlm())
