"""
RLM Logger Package

This package provides comprehensive logging capabilities for RLM:
- ColorfulLogger: Console logging with colors
- REPLEnvLogger: Rich-formatted REPL execution logging
- TimescaleDBClient: Database-backed latency tracking
"""

from .root_logger import ColorfulLogger
from .repl_logger import REPLEnvLogger
from .timescale_client import (
    TimescaleDBClient,
    LatencyRecord,
    LLMInteractionRecord,
    CodeExecutionRecord,
    create_timescale_client
)

__all__ = [
    'ColorfulLogger',
    'REPLEnvLogger',
    'TimescaleDBClient',
    'LatencyRecord',
    'LLMInteractionRecord',
    'CodeExecutionRecord',
    'create_timescale_client'
]

__version__ = '1.0.0'
