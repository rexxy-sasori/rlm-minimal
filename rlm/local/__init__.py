"""
Local Execution Architecture.

This module contains the original RLM implementation with local code execution.
The generated code runs in the same process as the RLM inference.

Usage:
    from rlm.local import RLM_REPL, REPLEnv

    rlm = RLM_REPL(model="gpt-5")
    result = rlm.completion(context, query)
"""

from rlm.local.repl import REPLEnv, Sub_RLM
from rlm.local.rlm_repl import RLM_REPL

__all__ = ["REPLEnv", "Sub_RLM", "RLM_REPL"]
