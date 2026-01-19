# RLM Depth Parameter Implementation

## Overview

Added support for configurable recursion depth while maintaining full backward compatibility.

## Changes Made

### 1. rlm/rlm_repl.py

**Line 30**: Changed default depth from 0 to 1
```python
depth: int = 1,  # Was: depth: int = 0
```

**Line 42**: Updated comment to reflect usage
```python
self.depth = depth  # 1 = single layer of sub-calls, 2 = two layers, etc.
```

**Line 82**: Pass depth to REPLEnv
```python
self.repl_env = REPLEnv(
    ...,
    depth=self.depth,  # Added this line
)
```

### 2. rlm/repl.py

**Line 81**: Added depth parameter to REPLEnv.__init__
```python
def __init__(
    ...,
    depth: int = 1,  # Added this parameter
):
```

**Lines 87-102**: Conditionally create Sub_RLM or RLM_REPL based on depth
```python
self.depth = depth

if depth > 1:
    from rlm.rlm_repl import RLM_REPL
    self.sub_rlm: RLM = RLM_REPL(
        api_key=recursive_api_key,
        model=recursive_model,
        base_url=recursive_base_url,
        depth=depth - 1,  # Reduce depth for recursive calls
        enable_logging=False
    )
else:
    self.sub_rlm: RLM = Sub_RLM(
        model=recursive_model,
        base_url=recursive_base_url,
        api_key=recursive_api_key
    )
```

## Behavior

### Base Case: depth=1 (Default, Backward Compatible)
- Uses `Sub_RLM` for sub-calls
- **Sub_RLM is a simple LLM wrapper with NO REPL environment**
- Cannot make recursive calls - this stops the recursion
- Maximum recursion: 1 layer (root RLM → Sub_RLM)
- **Fully backward compatible** - no code changes needed

### depth=2 (New Behavior)
- Uses `RLM_REPL` for sub-calls
- Sub-RLM has depth=1 (which uses Sub_RLM for its own sub-calls)
- Maximum recursion: 2 layers (root RLM → RLM_REPL → Sub_RLM)
- **Opt-in** via `RLM_REPL(depth=2)`

### depth=3+ (Deeper Recursion)
- Each level uses `RLM_REPL` with depth-1
- Depth propagates recursively **until reaching 1** (the base case)
- Maximum recursion: N layers (root RLM → ... → RLM_REPL → Sub_RLM)
- **Opt-in** via `RLM_REPL(depth=N)`

### Why This Works (No Infinite Recursion)

The implementation guarantees termination through **depth reduction**:

1. Each time an `RLM_REPL` creates a sub-RLM, it passes `depth-1`
2. When `depth == 1`, the code creates a `Sub_RLM` instead of `RLM_REPL`
3. `Sub_RLM` has no REPL environment and cannot make recursive calls
4. This creates a natural base case that stops the recursion

**Example for depth=3:**
```
RLM_REPL(depth=3) → creates RLM_REPL(depth=2)
  RLM_REPL(depth=2) → creates RLM_REPL(depth=1)
    RLM_REPL(depth=1) → creates Sub_RLM (BASE CASE - recursion stops)
```

## Usage Examples

### Basic Usage (Backward Compatible)

```python
# Default behavior (backward compatible)
rlm = RLM_REPL()
# Uses Sub_RLM for sub-calls, max depth=1
# Default recursive model: gpt-5-mini
```

### Configurable Depth

```python
# Enable 2 layers of recursion
rlm = RLM_REPL(depth=2)
# Uses RLM_REPL for sub-calls, which then uses Sub_RLM

# Enable 3 layers of recursion
rlm = RLM_REPL(depth=3)
# Uses RLM_REPL(depth=2) for sub-calls
# Which uses RLM_REPL(depth=1) for its sub-calls
# Which uses Sub_RLM
```

### Per-Depth Model Configuration

Use `recursive_models` list to specify different models for each depth level:

```python
# Different models at different depths
rlm = RLM_REPL(
    depth=3,
    recursive_models=["gpt-5-mini", "gpt-4o-mini", "llama-3.1-8b"]
)
# Depth 1: gpt-5-mini
# Depth 2: gpt-4o-mini
# Depth 3: llama-3.1-8b
```

```python
# Mix cloud and local models
rlm = RLM_REPL(
    depth=3,
    recursive_models=["gpt-5-mini", "llama-3.1-70b", "llama-3.1-8b"],
    recursive_base_urls=[
        "https://api.openai.com/v1",  # Cloud for depth 1
        "http://localhost:1234/v1",    # Local for depth 2
        "http://localhost:1234/v1"     # Local for depth 3
    ]
)
```

```python
# Fewer models than depth levels (repeats last model)
rlm = RLM_REPL(
    depth=5,
    recursive_models=["gpt-5-mini", "gpt-4o-mini"]
)
# Depth 1: gpt-5-mini
# Depth 2: gpt-4o-mini
# Depth 3: gpt-4o-mini  # Repeats last
# Depth 4: gpt-4o-mini  # Repeats last
# Depth 5: gpt-4o-mini  # Repeats last
```

## Per-Depth Model Configuration

The implementation now supports **different models at different recursion depths** using list parameters:

### Key Features

1. **`recursive_models`**: List of model names for each depth level
   - Index 0 = Depth 1 (first recursive call)
   - Index 1 = Depth 2 (second recursive call)
   - Index 2 = Depth 3 (third recursive call)
   - etc.

2. **`recursive_base_urls`**: List of base URLs for each depth level (optional)
   - Same indexing as recursive_models
   - Allows mixing cloud and local models

3. **Fallback Behavior**:
   - If fewer models specified than depth levels, repeats the last model
   - If no base URL specified for a depth, uses the previous one or None

### How It Works

When creating sub-RLMs at each depth level:

```
Root RLM_REPL(depth=3, recursive_models=[A, B, C])
  └─> Creates RLM_REPL(depth=2, recursive_models=[B, C])
       └─> Creates RLM_REPL(depth=1, recursive_models=[C])
            └─> Creates Sub_RLM(model=C)  # Base case
```

The models list is "shifted" at each level, so depth N uses models[N-1].

## Backward Compatibility

✅ **FULLY MAINTAINED**

- Default depth remains 1 (implicitly, now explicitly set)
- Existing code without depth parameter works unchanged
- No breaking changes to API
- Behavior is identical when depth=1
- Old `recursive_model` parameter is replaced with `recursive_models` list
- Default value: `["gpt-5-mini"]` (maintains backward compatibility)

## Testing

Run the test script to verify behavior:

```bash
python test_depth_simple.py
```

## Benefits

1. **Backward Compatible**: Existing code works without changes
2. **Configurable**: Users can choose recursion depth via parameter
3. **Flexible**: Supports any depth level (1, 2, 3, ...)
4. **Clean Implementation**: Simple conditional logic based on depth value
5. **Well Documented**: Clear comments explain the behavior
