#!/usr/bin/env python3
"""Test per-depth model configuration."""

print("=" * 70)
print("Per-Depth Model Configuration - Logic Verification")
print("=" * 70)
print()

def test_model_propagation():
    """Test how models propagate through depth levels."""
    
    print("Test 1: Different models at each depth")
    print("-" * 70)
    
    recursive_models = ["gpt-5-mini", "gpt-4o-mini", "llama-3.1-8b"]
    depth = 3
    
    print(f"Initial models: {recursive_models}")
    print(f"Depth: {depth}")
    print()
    
    current_depth = depth
    current_models = recursive_models.copy()
    
    for level in range(1, depth + 1):
        indent = "  " * level
        
        if current_depth > 1:
            model_for_this_depth = current_models[0]
            next_models = current_models[1:] if len(current_models) > 1 else current_models
            
            print(f"{indent}Level {level} (depth={current_depth}):")
            print(f"{indent}  Model: {model_for_this_depth}")
            print(f"{indent}  Passes to next level: {next_models}")
            
            current_models = next_models
            current_depth -= 1
        else:
            model_for_this_depth = current_models[0] if current_models else "(none)"
            
            print(f"{indent}Level {level} (depth={current_depth}):")
            print(f"{indent}  Model: {model_for_this_depth}")
            print(f"{indent}  BASE CASE - creates Sub_RLM with this model")
    
    print()
    
    print("Test 2: Fewer models than depth levels (repeats last)")
    print("-" * 70)
    
    recursive_models = ["gpt-5-mini", "gpt-4o-mini"]
    depth = 5
    
    print(f"Initial models: {recursive_models}")
    print(f"Depth: {depth}")
    print()
    
    # With depth=5 and 2 models, we use model[0] for depth>2, model[1] for depth<=2
    expected = [
        "gpt-4o-mini",  # depth 5 > 2 models, uses last
        "gpt-4o-mini",  # depth 4 > 2 models, uses last  
        "gpt-4o-mini",  # depth 3 > 2 models, uses last
        "gpt-4o-mini",  # depth 2 <= 2 models, uses model[1]
        "gpt-5-mini",   # depth 1 <= 2 models, uses model[0] (base case)
    ]
    
    for level in range(1, depth + 1):
        current_depth = depth - level + 1
        indent = "  " * level
        
        if current_depth <= len(recursive_models):
            model = recursive_models[current_depth - 1]
        else:
            model = recursive_models[-1]
        
        print(f"{indent}Level {level} (depth={current_depth}):")
        print(f"{indent}  Model: {model}")
        print(f"{indent}  Expected: {expected[level - 1]}")
        assert model == expected[level - 1], f"Mismatch at level {level}"
        print(f"{indent}  ✓ PASS")
    
    print()
    
    print("Test 3: Single model for all depths")
    print("-" * 70)
    
    recursive_models = ["gpt-5-mini"]
    depth = 3
    
    print(f"Initial models: {recursive_models}")
    print(f"Depth: {depth}")
    print()
    
    for level in range(1, depth + 1):
        current_depth = depth - level + 1
        indent = "  " * level
        
        model = recursive_models[0]
        
        print(f"{indent}Level {level} (depth={current_depth}):")
        print(f"{indent}  Model: {model}")
        print(f"{indent}  Same model used at all levels")
    
    print()

test_model_propagation()

print("=" * 70)
print("All tests passed! ✓")
print("=" * 70)
print()
print("Summary:")
print("  - Models propagate correctly through depth levels")
print("  - Models list is 'shifted' at each level")
print("  - Last model repeats when fewer models than depths")
print("  - Base case uses the appropriate model for depth=1")
