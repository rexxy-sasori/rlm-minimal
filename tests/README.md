# Tests Organization

This directory contains test files organized by category for the RLM (Recursive Language Model) project.

## Directory Structure

```
tests/
├── depth_logic/           # Tests for recursion depth logic
├── model_propagation/     # Tests for model propagation through recursion
├── examples/              # Example tests demonstrating specific scenarios
├── benchmarks/            # Tests for benchmark framework
└── README.md              # This file
```

## Test Categories

### 1. depth_logic/
Tests related to recursion depth calculation and base case handling.

**Files:**
- `test_depth_numbering.py` - Tests 0-based depth numbering
- `test_depth_simple.py` - Simple depth logic tests
- `test_base_case.py` - Tests base case to prevent infinite recursion

**Purpose:** Verify that the recursion depth is correctly tracked and that the base case (Sub_RLM) is properly triggered.

**Key Concepts:**
- 0-based depth numbering (root = depth 0)
- max_depth vs current_depth
- Base case detection
- Recursion termination

### 2. model_propagation/
Tests related to how models are propagated through recursive calls.

**Files:**
- `test_correct_model_propagation.py` - Tests correct model selection at each depth
- `test_model_ordering.py` - Tests model ordering in recursive_models list
- `test_per_depth_models.py` - Tests per-depth model configuration
- `test_root_vs_recursive_models.py` - Tests separation between root and recursive models

**Purpose:** Ensure that the correct model is used at each recursion depth based on the `recursive_models` list.

**Key Concepts:**
- Root model vs recursive models
- Model index selection
- Model propagation through recursion levels
- All models in list are used

### 3. examples/
Example tests demonstrating specific user scenarios or edge cases.

**Files:**
- `test_user_example.py` - Tests user's specific example (model='gpt-5', recursive_models=['1','2','3'], max_depth=3)

**Purpose:** Document and verify specific usage patterns and examples.

### 4. benchmarks/
Tests for the benchmark framework components.

**Files:**
- `test_benchmarks.py` - Unit tests for benchmark framework

**Purpose:** Verify that the benchmark framework components work correctly.

**Key Components Tested:**
- BaseBenchmark class
- BenchmarkConfig and dataset configs
- OOLONGBenchmark
- DeepResearchBenchmark
- RULERBenchmark
- BenchmarkRunner
- BenchmarkAnalyzer

## Running Tests

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Specific Category
```bash
python -m pytest tests/depth_logic/ -v
python -m pytest tests/model_propagation/ -v
python -m pytest tests/examples/ -v
python -m pytest tests/benchmarks/ -v
```

### Run Specific Test File
```bash
python tests/depth_logic/test_depth_numbering.py
python tests/model_propagation/test_correct_model_propagation.py
```

## Test Naming Conventions

- Use `test_` prefix for test files
- Use descriptive names indicating what is being tested
- Group related tests in the same directory

## Adding New Tests

1. **Choose the appropriate directory** based on test category:
   - Depth/recursion logic → `depth_logic/`
   - Model selection/propagation → `model_propagation/`
   - User examples/demos → `examples/`
   - Benchmark framework → `benchmarks/`

2. **Create a new test file** with `test_` prefix:
   ```bash
   touch tests/depth_logic/test_new_feature.py
   ```

3. **Follow existing patterns** from similar tests in the directory.

4. **Update this README** if adding a new category or significant test type.

## Test Guidelines

### General
- Each test file should focus on a single concept or feature
- Tests should be self-documenting with clear names
- Include print statements for clarity (many tests are designed to be run directly)
- Add docstrings explaining what the test verifies

### Depth Logic Tests
- Test both 0-based and edge cases
- Verify base case triggers correctly
- Test max_depth boundary conditions
- Include visualizations of call chains

### Model Propagation Tests
- Test various recursive_models configurations
- Verify all models in list are used
- Test root model separation
- Include model index verification

### Example Tests
- Document specific user scenarios
- Include detailed call chain visualization
- Show expected vs actual behavior

### Benchmark Tests
- Use unittest framework
- Test individual components in isolation
- Use mocks for external dependencies

## Common Test Patterns

### Visual Call Chain
```python
print("Call Chain:")
print("Level 0: RLM_REPL(model='gpt-5', current_depth=0)")
print("  └─> Level 1: RLM_REPL(model='gpt-5-mini', current_depth=1)")
print("       └─> Level 2: Sub_RLM(model='gpt-4')")
```

### Depth Verification
```python
max_depth = 3
current_depth = 0
should_recurse = (current_depth + 1) < max_depth
print(f"should_recurse = {should_recurse}")
```

### Model Selection
```python
recursive_models = ['model-a', 'model-b', 'model-c']
model_index = current_depth  # For recursive calls
selected_model = recursive_models[model_index]
print(f"Selected model at depth {current_depth}: {selected_model}")
```

## Troubleshooting

### Test Import Errors
If you see import errors when running tests:

1. Ensure project root is in PYTHONPATH:
   ```bash
   export PYTHONPATH="$(pwd):$PYTHONPATH"
   ```

2. Run tests from project root:
   ```bash
   cd /path/to/rlm-minimal
   python tests/depth_logic/test_depth_numbering.py
   ```

### Test Discovery Issues
If pytest doesn't find tests:

1. Check that `__init__.py` files exist in all directories
2. Verify test files start with `test_`
3. Run with `-v` flag to see discovery details:
   ```bash
   python -m pytest tests/ -v
   ```

## Contributing

When adding new tests:

1. Place them in the appropriate category directory
2. Follow existing naming conventions
3. Include clear documentation
4. Run tests to ensure they pass
5. Update this README if introducing new concepts

## See Also

- [DEPTH_IMPLEMENTATION.md](../doc/DEPTH_IMPLEMENTATION.md) - Documentation on depth implementation
- [RECURSIVE_LOGGING.md](../rlm/logger/doc/RECURSIVE_LOGGING.md) - Documentation on recursive logging
- [README.md](../README.md) - Main project README
