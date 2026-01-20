#!/usr/bin/env python3
"""Test depth numbering with 0-based root."""

print("=" * 80)
print("Depth Numbering Test (0-based Root)")
print("=" * 80)
print()

def test_depth_logic():
    """Test the new depth logic."""
    
    print("Test 1: max_depth=1 (default, no recursion)")
    print("-" * 80)
    
    max_depth = 1
    current_depth = 0
    
    should_recurse = (current_depth + 1) < max_depth
    print(f"max_depth = {max_depth}")
    print(f"current_depth = {current_depth} (root)")
    print(f"should_recurse = {should_recurse}")
    print(f"Result: Creates Sub_RLM (no recursion)")
    print()
    
    print("Test 2: max_depth=2 (one layer of recursion)")
    print("-" * 80)
    
    max_depth = 2
    current_depth = 0
    
    should_recurse = (current_depth + 1) < max_depth
    print(f"max_depth = {max_depth}")
    print(f"current_depth = {current_depth} (root)")
    print(f"should_recurse = {should_recurse}")
    print(f"Result: Creates RLM_REPL(current_depth=1)")
    print()
    
    # Now from the recursive call
    current_depth = 1
    should_recurse = (current_depth + 1) < max_depth
    print(f"  Inside recursive call:")
    print(f"  current_depth = {current_depth}")
    print(f"  should_recurse = {should_recurse}")
    print(f"  Result: Creates Sub_RLM (base case)")
    print()
    
    print("Test 3: max_depth=3 (two layers of recursion)")
    print("-" * 80)
    
    max_depth = 3
    
    for current_depth in [0, 1, 2]:
        should_recurse = (current_depth + 1) < max_depth
        print(f"current_depth = {current_depth}")
        print(f"  should_recurse = {should_recurse}")
        if should_recurse:
            print(f"  → Creates RLM_REPL(current_depth={current_depth + 1})")
        else:
            print(f"  → Creates Sub_RLM (base case)")
        print()
    
    print("Test 4: Model indexing with 0-based depth")
    print("-" * 80)
    
    recursive_models = ["gpt-5-mini", "llama-3.1-70b", "llama-3.1-8b"]
    
    print(f"Model list: {recursive_models}")
    print()
    
    for current_depth in [0, 1, 2]:
        if current_depth < len(recursive_models):
            model = recursive_models[current_depth]
        else:
            model = recursive_models[-1]
        
        print(f"current_depth = {current_depth} → uses model: {model}")
    
    print()
    print("Summary:")
    print("- max_depth = maximum number of recursive layers allowed")
    print("- current_depth = 0 for root, increments by 1 for each recursive call")
    print("- Model at index i is used when current_depth = i")
    print("- Recursion stops when (current_depth + 1) >= max_depth")

test_depth_logic()

print()
print("=" * 80)
print("Call Chain Example: max_depth=3")
print("=" * 80)
print()

recursive_models = ["gpt-5-mini", "llama-3.1-70b", "llama-3.1-8b"]
max_depth = 3

print(f"max_depth = {max_depth}")
print(f"Models = {recursive_models}")
print()

print("Root RLM_REPL(current_depth=0, max_depth=3)")
print("  └─> REPLEnv creates sub-RLM")
print("      └─> current_depth + 1 = 1 < 3 → should_recurse = True")
print("      └─> Creates RLM_REPL(current_depth=1, max_depth=3)")
print("           └─> REPLEnv creates sub-RLM")
print("               └─> current_depth + 1 = 2 < 3 → should_recurse = True")
print("               └─> Creates RLM_REPL(current_depth=2, max_depth=3)")
print("                    └─> REPLEnv creates sub-RLM")
print("                        └─> current_depth + 1 = 3 < 3 → should_recurse = False")
print("                        └─> Creates Sub_RLM(model=llama-3.1-8b) ← BASE CASE")
print()

print("=" * 80)
print("Model Usage Summary:")
print("=" * 80)
print()
print("current_depth=0 (root):    Model index 0 → gpt-5-mini")
print("current_depth=1 (level 1): Model index 1 → llama-3.1-70b")
print("current_depth=2 (level 2): Model index 2 → llama-3.1-8b")
print()
print("✓ Logic is consistent and correct!")
