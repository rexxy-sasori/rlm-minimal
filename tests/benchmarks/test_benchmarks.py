import unittest
import os
import sys
import tempfile
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from benchmarks.base import BaseBenchmark
from benchmarks.config import BenchmarkConfig, OOLONGConfig, DeepResearchConfig, RULERConfig
from benchmarks.oolong import OOLONGBenchmark
from benchmarks.deep_research import DeepResearchBenchmark
from benchmarks.ruler import RULERBenchmark
from benchmarks.runner import BenchmarkRunner
from benchmarks.analysis import BenchmarkAnalyzer

class TestBenchmarkFramework(unittest.TestCase):
    """Test the benchmark framework components."""
    
    def test_base_benchmark_initialization(self):
        """Test base benchmark initialization."""
        # Create a concrete subclass for testing
        class TestBenchmark(BaseBenchmark):
            def load_dataset(self):
                pass
            def evaluate(self, model):
                pass
            def compute_metrics(self, results):
                pass
        
        config = {"name": "test", "max_tasks": 10}
        benchmark = TestBenchmark(config)
        
        self.assertEqual(benchmark.config, config)
        self.assertEqual(benchmark.results, [])
        self.assertIsNone(benchmark.start_time)
        self.assertIsNone(benchmark.end_time)
    
    def test_config_initialization(self):
        """Test configuration initialization."""
        # Test base config
        base_config = BenchmarkConfig()
        self.assertEqual(base_config.name, "benchmark")
        self.assertEqual(base_config.max_tasks, 100)
        
        # Test OOLONG config
        oolong_config = OOLONGConfig()
        self.assertEqual(oolong_config.name, "oolong")
        self.assertEqual(oolong_config.max_tasks, 50)
        
        # Test Deep Research config
        deep_config = DeepResearchConfig()
        self.assertEqual(deep_config.name, "deep_research")
        self.assertEqual(deep_config.max_tasks, 30)
        
        # Test RULER config
        ruler_config = RULERConfig()
        self.assertEqual(ruler_config.name, "ruler")
        self.assertEqual(ruler_config.max_tasks, 100)
    
    def test_config_to_dict(self):
        """Test config serialization to dictionary."""
        config = OOLONGConfig(max_tasks=25)
        config_dict = config.to_dict()
        
        self.assertEqual(config_dict["name"], "oolong")
        self.assertEqual(config_dict["max_tasks"], 25)
        self.assertIn("context_lengths", config_dict)

class TestRULERBenchmark(unittest.TestCase):
    """Test RULER benchmark implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {"max_tasks": 5, "context_lengths": [1000, 5000]}
        self.benchmark = RULERBenchmark(self.config)
    
    def test_task_generation(self):
        """Test task generation."""
        task = self.benchmark.generate_task(1000, "beginning")
        
        self.assertIn("context", task)
        self.assertIn("needle", task)
        self.assertIn("query", task)
        self.assertIn("needle_position", task)
        self.assertIn("context_length", task)
        
        # Verify context length is approximately correct
        self.assertAlmostEqual(len(task["context"]), 1000, delta=100)
    
    def test_dataset_loading(self):
        """Test dataset loading/generation."""
        self.benchmark.load_dataset()
        
        self.assertEqual(len(self.benchmark.dataset), 5)
        for task in self.benchmark.dataset:
            self.assertIn("context", task)
            self.assertIn("needle", task)
    
    def test_evaluate_with_mock_model(self):
        """Test evaluation with mock model."""
        # Create mock model
        mock_model = Mock()
        mock_model.completion.return_value = {
            "choices": [{"message": {"content": "The needle is: NEEDLE:TEST123"}}]
        }
        
        # Generate a task with known needle
        task = self.benchmark.generate_task(1000, "beginning")
        self.benchmark.dataset = [task]
        
        # Evaluate
        results = self.benchmark.evaluate(mock_model)
        
        self.assertEqual(len(results), 1)
        self.assertIn("correct", results[0])
        self.assertIn("response", results[0])
        
        # Verify model was called
        mock_model.completion.assert_called_once()

class TestOOLONGBenchmark(unittest.TestCase):
    """Test OOLONG benchmark implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {"max_tasks": 3, "context_lengths": [1000, 5000]}
        self.benchmark = OOLONGBenchmark(self.config)
    
    def test_task_generation(self):
        """Test task generation."""
        task = self.benchmark.generate_task(1000, "multi_step_reasoning")
        
        self.assertIn("context", task)
        self.assertIn("query", task)
        self.assertIn("correct_answer", task)
        self.assertIn("task_type", task)
        self.assertIn("context_length", task)
        
        # Verify context length is approximately correct
        self.assertAlmostEqual(len(task["context"]), 1000, delta=200)
    
    def test_dataset_loading(self):
        """Test dataset loading/generation."""
        self.benchmark.load_dataset()
        
        self.assertEqual(len(self.benchmark.dataset), 3)
        for task in self.benchmark.dataset:
            self.assertIn("context", task)
            self.assertIn("query", task)
            self.assertIn("correct_answer", task)
    
    def test_evaluate_with_mock_model(self):
        """Test evaluation with mock model."""
        # Create mock model
        mock_model = Mock()
        mock_model.completion.return_value = {
            "choices": [{"message": {"content": "The answer is 42"}}]
        }
        
        # Generate a task
        task = self.benchmark.generate_task(1000, "multi_step_reasoning")
        self.benchmark.dataset = [task]
        
        # Evaluate
        results = self.benchmark.evaluate(mock_model)
        
        self.assertEqual(len(results), 1)
        self.assertIn("correct", results[0])
        self.assertIn("response", results[0])

class TestDeepResearchBenchmark(unittest.TestCase):
    """Test Deep Research benchmark implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {"max_tasks": 3, "context_lengths": [1000, 5000]}
        self.benchmark = DeepResearchBenchmark(self.config)
    
    def test_task_generation(self):
        """Test task generation."""
        task = self.benchmark.generate_research_task("artificial intelligence")
        
        self.assertIn("topic", task)
        self.assertIn("sources", task)
        self.assertIn("query", task)
        self.assertIn("correct_answer", task)
        self.assertIn("context", task)
        self.assertIn("context_length", task)
        
        # Verify sources are generated
        self.assertGreater(len(task["sources"]), 0)
    
    def test_dataset_loading(self):
        """Test dataset loading/generation."""
        self.benchmark.load_dataset()
        
        self.assertEqual(len(self.benchmark.dataset), 3)
        for task in self.benchmark.dataset:
            self.assertIn("topic", task)
            self.assertIn("sources", task)
            self.assertIn("query", task)
            self.assertIn("correct_answer", task)
    
    def test_evaluate_with_mock_model(self):
        """Test evaluation with mock model."""
        # Create mock model
        mock_model = Mock()
        mock_model.completion.return_value = {
            "choices": [{"message": {"content": "Based on the sources, the key points are..."}}]
        }
        
        # Generate a task
        task = self.benchmark.generate_research_task("artificial intelligence")
        self.benchmark.dataset = [task]
        
        # Evaluate
        results = self.benchmark.evaluate(mock_model)
        
        self.assertEqual(len(results), 1)
        self.assertIn("correct", results[0])
        self.assertIn("response", results[0])

class TestBenchmarkRunner(unittest.TestCase):
    """Test benchmark runner."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.runner = BenchmarkRunner()
    
    def test_add_benchmark(self):
        """Test adding benchmarks to runner."""
        # Add OOLONG benchmark
        self.runner.add_benchmark("oolong")
        self.assertIn("oolong", self.runner.benchmarks)
        self.assertIsInstance(self.runner.benchmarks["oolong"], OOLONGBenchmark)
        
        # Add Deep Research benchmark
        self.runner.add_benchmark("deep_research")
        self.assertIn("deep_research", self.runner.benchmarks)
        self.assertIsInstance(self.runner.benchmarks["deep_research"], DeepResearchBenchmark)
        
        # Add RULER benchmark
        self.runner.add_benchmark("ruler")
        self.assertIn("ruler", self.runner.benchmarks)
        self.assertIsInstance(self.runner.benchmarks["ruler"], RULERBenchmark)
    
    def test_invalid_benchmark(self):
        """Test adding invalid benchmark."""
        with self.assertRaises(ValueError):
            self.runner.add_benchmark("invalid_benchmark")
    
    def test_run_benchmark_with_mock_model(self):
        """Test running benchmark with mock model."""
        # Create mock model
        mock_model = Mock()
        mock_model.completion.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        
        # Add benchmark and run
        self.runner.add_benchmark("ruler", {"max_tasks": 1, "context_lengths": [1000]})
        
        # Create temporary directory for output
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run benchmark
            results = self.runner.run_benchmark("ruler", mock_model, output_dir=tmpdir)
            
            # Verify results
            self.assertIsInstance(results, list)
            self.assertEqual(len(results), 1)
            
            # Verify output files were created
            expected_files = [
                "ruler_results.json",
                "ruler_report.txt"
            ]
            
            for filename in expected_files:
                file_path = os.path.join(tmpdir, filename)
                self.assertTrue(os.path.exists(file_path))

class TestBenchmarkAnalyzer(unittest.TestCase):
    """Test benchmark analyzer."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = BenchmarkAnalyzer()
        self.assertEqual(analyzer.results_dir, "results")
        self.assertEqual(analyzer.results, {})
    
    def test_accuracy_analysis(self):
        """Test accuracy analysis with mock results."""
        # Create mock results
        mock_results = [
            {"correct": True, "task_type": "test1", "context_length": 1000},
            {"correct": False, "task_type": "test1", "context_length": 5000},
            {"correct": True, "task_type": "test2", "context_length": 10000}
        ]
        
        # Create temporary results file
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock results file
            results_data = {
                "benchmark": "test",
                "results": mock_results
            }
            
            import json
            results_file = os.path.join(tmpdir, "test_results.json")
            with open(results_file, 'w') as f:
                json.dump(results_data, f)
            
            # Test analyzer
            analyzer = BenchmarkAnalyzer(tmpdir)
            analysis = analyzer.analyze_accuracy("test")
            
            self.assertEqual(analysis["overall_accuracy"], 2/3)
            self.assertEqual(analysis["total_tasks"], 3)
            self.assertEqual(analysis["correct_tasks"], 2)
            
            # Test task type accuracy
            self.assertIn("test1", analysis["task_accuracy"])
            self.assertIn("test2", analysis["task_accuracy"])
            self.assertEqual(analysis["task_accuracy"]["test1"], 0.5)
            self.assertEqual(analysis["task_accuracy"]["test2"], 1.0)

if __name__ == "__main__":
    unittest.main()
