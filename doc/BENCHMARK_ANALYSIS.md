# Benchmark Analysis and Implementation Plan

Based on the analysis of the RLM blog post (https://alexzhang13.github.io/blog/2025/rlm/), this document identifies the benchmarks mentioned and provides a comprehensive implementation plan.

## Benchmarks Identified in Blog Post

### 1. OOLONG Benchmark
**Type:** Long-Context Reasoning Benchmark
**Description:** The "most difficult long-context benchmark" used in the RLM paper
**Key Findings:**
- RLM using GPT-5-mini outperformed GPT-5 by more than double the number of correct answers
- RLM was cheaper per query on average
**Purpose:** Evaluates long-context reasoning capabilities with complex tasks

### 2. Deep Research Task (BrowseComp-Plus)
**Type:** Deep Research / Agentic Browsing Benchmark
**Description:** New long-context Deep Research task constructed from BrowseComp-Plus
**Key Findings:**
- RLMs outperformed other methods like ReAct + test-time indexing
- RLMs outperformed retrieval over the prompt approaches
- RLMs showed no performance degradation with 10M+ tokens at inference time
**Purpose:** Evaluates deep research capabilities requiring extensive information synthesis

#### BrowseComp-Plus Setup Instructions
**Official Dataset:** [Tevatron/browsecomp-plus](https://huggingface.co/datasets/Tevatron/browsecomp-plus)

**Setup Steps:**
1. **Automatic Setup:**
   ```bash
   python setup_browsecomp_plus.py --data-dir data
   ```

2. **Manual Setup:**
   - Install required packages: `pip install datasets`
   - Download queries: `from datasets import load_dataset; queries = load_dataset("Tevatron/browsecomp-plus", split="queries")`
   - Download corpus: `corpus = load_dataset("Tevatron/browsecomp-plus-corpus", split="train")`

3. **Configuration Options:**
   ```python
   config = {
       "use_browsecomp_plus": True,
       "browsecomp_plus_data_dir": "data",
       "max_tasks": 30,
       "hf_token": "your_hugging_face_token"  # Optional
   }
   ```

4. **Evaluation Metrics:**
   - Accuracy (%)
   - Recall (%)
   - Calibration Error (%)
   - Tool Call Statistics
   - Status Analysis

### 3. RULER Benchmark (Needle-in-Haystack)
**Type:** Context Retrieval Benchmark
**Description:** Popular needle-in-the-haystack benchmark
**Key Findings:**
- Most frontier models achieve 90%+ accuracy on 1-year old models
- Used to illustrate context rot phenomenon
**Purpose:** Evaluates ability to retrieve specific information from large contexts

## Current Codebase Status

The codebase currently has:
- `benchmarks/__init__.py` imports for three benchmark classes (OOLONGBenchmark, DeepResearchBenchmark, RULERBenchmark)
- No actual benchmark implementations exist yet
- Basic RLM implementation in `rlm/` folder
- Example needle-in-haystack test in `main.py`

## Comprehensive Implementation Plan

### Phase 1: Core Benchmark Framework

#### 1.1 Base Benchmark Class
**File:** `benchmarks/base.py`
**Purpose:** Abstract base class defining the interface for all benchmarks
**Components:**
- `__init__()`: Initialize benchmark with configuration
- `load_dataset()`: Load and prepare benchmark data
- `evaluate(model)`: Run evaluation on a given model
- `compute_metrics(results)`: Calculate performance metrics
- `report(results)`: Generate human-readable report

#### 1.2 Benchmark Configuration
**File:** `benchmarks/config.py`
**Purpose:** Centralized configuration for all benchmarks
**Components:**
- Dataset paths and sources
- Model parameters
- Evaluation parameters
- Output directories

### Phase 2: Individual Benchmark Implementations

#### 2.1 OOLONG Benchmark Implementation
**File:** `benchmarks/oolong.py`

**Code Structure:**
```python
class OOLONGBenchmark(BaseBenchmark):
    def __init__(self, config):
        # Initialize with dataset path, context lengths, etc.
        pass
    
    def load_dataset(self):
        # Load OOLONG benchmark dataset
        # Parse complex reasoning tasks
        pass
    
    def evaluate(self, model):
        # Run each task through the model
        # Track accuracy, latency, cost
        pass
    
    def compute_metrics(self, results):
        # Calculate accuracy scores
        # Compare RLM vs baseline models
        pass
```

**Performance Metrics:**
- Correct answer rate (primary metric)
- Average query cost
- Latency per task
- Context length scalability

**Test Scenarios:**
- Standard OOLONG test split
- Variable context lengths (1M, 5M, 10M tokens)
- Comparison: GPT-5-mini (RLM) vs GPT-5 (baseline)

#### 2.2 Deep Research Benchmark (BrowseComp-Plus)
**File:** `benchmarks/deep_research.py`

**Code Structure:**
```python
class DeepResearchBenchmark(BaseBenchmark):
    def __init__(self, config):
        # Initialize with BrowseComp-Plus dataset
        pass
    
    def load_dataset(self):
        # Load research tasks
        # Parse web browsing scenarios
        pass
    
    def evaluate(self, model):
        # Simulate deep research scenarios
        # Compare with ReAct, retrieval methods
        pass
    
    def compute_metrics(self, results):
        # Research quality metrics
        # Information synthesis score
        pass
```

**Performance Metrics:**
- Research task completion rate
- Information synthesis quality
- Comparison with alternative methods (ReAct, retrieval)
- Performance at 10M+ tokens

**Test Scenarios:**
- Complex research questions requiring multiple sources
- Web browsing simulation
- Multi-step reasoning tasks
- Comparison: RLM vs ReAct + indexing vs retrieval

#### 2.3 RULER Benchmark (Needle-in-Haystack)
**File:** `benchmarks/ruler.py`

**Code Structure:**
```python
class RULERBenchmark(BaseBenchmark):
    def __init__(self, config):
        # Configure needle placement parameters
        pass
    
    def generate_task(self, context_length, needle_position):
        # Generate haystack context
        # Place needle at specified position
        pass
    
    def evaluate(self, model):
        # Test retrieval accuracy at various positions
        pass
    
    def compute_metrics(self, results):
        # Position-based accuracy
        # Context rot measurement
        pass
```

**Performance Metrics:**
- Needle retrieval accuracy
- Position-based accuracy distribution
- Context rot measurement
- Scalability to long contexts

**Test Scenarios:**
- Needle at beginning, middle, end of context
- Variable context lengths (100K to 10M tokens)
- Multiple needles per context
- Time-based context degradation

### Phase 3: Evaluation and Reporting

#### 3.1 Evaluation Runner
**File:** `benchmarks/runner.py`
**Purpose:** Orchestrate benchmark execution
**Features:**
- Run multiple benchmarks sequentially
- Parallel evaluation support
- Progress tracking
- Result aggregation

#### 3.2 Result Analysis
**File:** `benchmarks/analysis.py`
**Purpose:** Analyze and visualize results
**Features:**
- Statistical analysis
- Performance comparison charts
- Cost-benefit analysis
- Context degradation visualization

#### 3.3 Reporting
**File:** `benchmarks/reporting.py`
**Purpose:** Generate comprehensive reports
**Features:**
- Markdown reports
- JSON result files
- Comparison tables
- Visualization integration

### Phase 4: Test Scenarios

#### 4.1 Standard Test Suite
**File:** `tests/test_benchmarks.py`
**Test Cases:**
- Unit tests for each benchmark class
- Integration tests for evaluation pipeline
- Mock model tests
- Result validation tests

#### 4.2 Reproduction Scenarios
**Scenarios to Reproduce:**
1. **OOLONG Reproduction:**
   - RLM with GPT-5-mini vs GPT-5 baseline
   - Achieve 2x improvement in correct answers
   - Demonstrate cost savings

2. **Deep Research Reproduction:**
   - RLM vs ReAct + test-time indexing
   - RLM vs retrieval over prompt
   - Show no degradation at 10M+ tokens

3. **RULER Reproduction:**
   - 90%+ accuracy on 1-year old models
   - Measure context rot phenomenon

## Execution Instructions

### Prerequisites
```bash
pip install -r requirements.txt
# Install additional benchmark dependencies
pip install pandas numpy matplotlib seaborn scikit-learn
```

### Running Benchmarks

#### Single Benchmark
```python
from benchmarks import OOLONGBenchmark
from rlm import RLM_REPL

# Initialize model
model = RLM_REPL(model_name="gpt-5-mini")

# Initialize benchmark
benchmark = OOLONGBenchmark({
    'dataset_path': 'data/oolong.json',
    'context_lengths': [1_000_000, 5_000_000, 10_000_000]
})

# Run evaluation
results = benchmark.evaluate(model)

# Generate report
benchmark.report(results)
```

#### Multiple Benchmarks
```python
from benchmarks.runner import BenchmarkRunner

runner = BenchmarkRunner()
runner.add_benchmark('oolong', config)
runner.add_benchmark('deep_research', config)
runner.add_benchmark('ruler', config)

all_results = runner.run_all(models=[rlm_model, baseline_model])
```

#### Command Line Interface
```bash
# Run specific benchmark
python -m benchmarks.runner --benchmark oolong --model gpt-5-mini

# Run all benchmarks
python -m benchmarks.runner --all --output results/

# Compare models
python -m benchmarks.runner --compare rlm gpt-5 --benchmark oolong
```

### Expected Output

#### OOLONG Benchmark Results
```
OOLONG Benchmark Results
========================
Model: RLM (GPT-5-mini)
Correct Answers: 45/50 (90%)

Model: GPT-5 (Baseline)
Correct Answers: 20/50 (40%)

RLM Improvement: 2.25x
Cost Savings: 35% per query
```

#### Deep Research Results
```
Deep Research Benchmark Results
================================
Method               Accuracy  Context Size
RLM                  85%       10M+ tokens
ReAct + Indexing     62%       10M+ tokens
Retrieval            58%       10M+ tokens

No performance degradation observed at 10M+ tokens
```

#### RULER Results
```
RULER Benchmark Results
========================
Position       Accuracy
Beginning      95%
Middle         92%
End            88%

Context Rot: Minimal (3% degradation from beginning to end)
```

## Implementation Priority

### High Priority
1. Base benchmark class and framework
2. RULER benchmark (simplest, good starting point)
3. OOLONG benchmark (primary paper result)
4. Basic evaluation runner

### Medium Priority
5. Deep Research benchmark (more complex)
6. Result analysis and visualization
7. Comparison reporting

### Low Priority
8. Advanced visualization
9. Web-based reporting
10. Distributed evaluation

## Success Criteria

1. **Functional:** All three benchmarks can be executed and produce results
2. **Accurate:** Results match or closely approximate paper claims
3. **Usable:** Clear documentation and execution instructions
4. **Extensible:** Easy to add new benchmarks or models
5. **Comparable:** Direct comparison between RLM and baseline methods

## Notes

- The OOLONG benchmark dataset source needs to be identified and acquired
- BrowseComp-Plus dataset may require web crawling or specific access
- RULER benchmark can be synthetically generated
- All benchmarks should support both RLM and baseline model evaluations
- Cost tracking requires API pricing information
- Latency measurement needs timing infrastructure
