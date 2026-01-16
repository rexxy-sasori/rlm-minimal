from typing import Dict, Any, Optional
import os
from dataclasses import dataclass, field

@dataclass
class BenchmarkConfig:
    """Base configuration for all benchmarks."""
    
    # Common configuration
    name: str = "benchmark"
    output_dir: str = "results"
    dataset_path: Optional[str] = None
    max_tasks: int = 100
    verbose: bool = False
    seed: int = 42
    
    # Model configuration
    model_name: str = "gpt-5-mini"
    temperature: float = 0.0
    max_tokens: int = 1000
    
    # Context configuration
    context_lengths: list = field(default_factory=lambda: [100000, 1000000, 10000000])
    batch_size: int = 1
    
    # Evaluation configuration
    timeout: int = 300  # seconds
    retries: int = 3
    cost_tracking: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "output_dir": self.output_dir,
            "dataset_path": self.dataset_path,
            "max_tasks": self.max_tasks,
            "verbose": self.verbose,
            "seed": self.seed,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "context_lengths": self.context_lengths,
            "batch_size": self.batch_size,
            "timeout": self.timeout,
            "retries": self.retries,
            "cost_tracking": self.cost_tracking,
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "BenchmarkConfig":
        """Create from dictionary."""
        return cls(**config_dict)

@dataclass
class OOLONGConfig(BenchmarkConfig):
    """Configuration for OOLONG benchmark."""
    
    name: str = "oolong"
    dataset_path: Optional[str] = "data/oolong.json"
    max_tasks: int = 50
    context_lengths: list = field(default_factory=lambda: [1000000, 5000000, 10000000])

@dataclass  
class DeepResearchConfig(BenchmarkConfig):
    """Configuration for Deep Research benchmark."""
    
    name: str = "deep_research"
    dataset_path: Optional[str] = "data/browsecomp_plus.json"
    max_tasks: int = 30
    context_lengths: list = field(default_factory=lambda: [1000000, 5000000, 10000000])
    
    # BrowseComp-Plus specific configuration
    use_browsecomp_plus: bool = False
    browsecomp_plus_data_dir: str = "data"
    hf_token: Optional[str] = None
    download_corpus: bool = True
    use_official_evaluation: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with BrowseComp-Plus fields."""
        base_dict = super().to_dict()
        base_dict.update({
            "use_browsecomp_plus": self.use_browsecomp_plus,
            "browsecomp_plus_data_dir": self.browsecomp_plus_data_dir,
            "hf_token": self.hf_token,
            "download_corpus": self.download_corpus,
            "use_official_evaluation": self.use_official_evaluation,
        })
        return base_dict

@dataclass
class RULERConfig(BenchmarkConfig):
    """Configuration for RULER benchmark."""
    
    name: str = "ruler"
    max_tasks: int = 100
    context_lengths: list = field(default_factory=lambda: [100000, 1000000, 10000000])
    needle_positions: list = field(default_factory=lambda: ["beginning", "middle", "end"])
    needles_per_context: int = 1

def get_default_config(benchmark_name: str) -> BenchmarkConfig:
    """Get default configuration for specified benchmark."""
    config_map = {
        "oolong": OOLONGConfig(),
        "deep_research": DeepResearchConfig(),
        "ruler": RULERConfig(),
    }
    
    if benchmark_name not in config_map:
        raise ValueError(f"Unknown benchmark: {benchmark_name}")
    
    return config_map[benchmark_name]

def ensure_output_dir(config: BenchmarkConfig):
    """Ensure output directory exists."""
    os.makedirs(config.output_dir, exist_ok=True)
