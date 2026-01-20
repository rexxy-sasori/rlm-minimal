#!/usr/bin/env python3
"""Clarify model ordering and depth level mapping."""

print("=" * 80)
print("Model Ordering Explanation")
print("=" * 80)
print()

recursive_models = ["gpt-5-mini", "llama-3.1-70b", "llama-3.1-8b"]
depth = 3

print(f"Model List: {recursive_models}")
print(f"Requested Depth: {depth}")
print()
print("=" * 80)
print("How Models Map to Depth Levels:")
print("=" * 80)
print()

print("IMPORTANT CONCEPT:")
print("- The model list is ORDERED from HIGHER depth to LOWER depth")
print("- Index 0 = Used when depth > number of remaining models")
print("- Models are 'shifted' as we go deeper into recursion")
print()
print("=" * 80)
print()

print("Call Chain Visualization:")
print()

current_depth = depth
current_models = recursive_models.copy()

for level in range(1, depth + 1):
    indent = "  " * level
    
    if current_depth > 1:
        model_used = current_models[0]
        models_passed = current_models[1:] if len(current_models) > 1 else current_models
        
        print(f"{indent}Level {level} (depth={current_depth}):")
        print(f"{indent}  Models available: {current_models}")
        print(f"{indent}  Model used at this depth: {model_used}")
        print(f"{indent}  Models passed to next level: {models_passed}")
        print(f"{indent}  → Creates RLM_REPL(depth={current_depth - 1})")
        
        current_models = models_passed
        current_depth -= 1
    else:
        model_used = current_models[0] if current_models else "(none)"
        
        print(f"{indent}Level {level} (depth={current_depth}):")
        print(f"{indent}  Models available: {current_models}")
        print(f"{indent}  Model used at this depth: {model_used}")
        print(f"{indent}  → BASE CASE: Creates Sub_RLM with this model")
        print(f"{indent}  ✓ Recursion stops here")

print()
print("=" * 80)
print("Summary of Model Usage by Depth Level:")
print("=" * 80)
print()

print(f"Depth 3 (highest level): {recursive_models[0]}")
print(f"Depth 2 (middle level):  {recursive_models[1]}")
print(f"Depth 1 (base case):     {recursive_models[2]}")
print()

print("=" * 80)
print("Key Takeaways:")
print("=" * 80)
print()
print("1. Model list order: [depth-3-model, depth-2-model, depth-1-model]")
print("2. First model in list = used at the highest depth level")
print("3. Last model in list = used at the base case (depth=1)")
print("4. Models are consumed from the front as we go deeper")
print("5. If you want a specific model at depth=1, put it last in the list")
print()
print("=" * 80)
print("Example: Optimized Model Strategy")
print("=" * 80)
print()
print("# Use smarter model at higher levels, cheaper at base case")
print("recursive_models = [\"gpt-5-mini\", \"llama-3.1-70b\", \"llama-3.1-8b\"]")
print()
print("Depth 3: gpt-5-mini    (smart, expensive - for complex decisions)")
print("Depth 2: llama-3.1-70b (capable, medium cost - for reasoning)")
print("Depth 1: llama-3.1-8b  (fast, cheap - for final answers)")
print()
print("This strategy optimizes cost while maintaining quality!")
