"""
RLM Integration with TimescaleDB Latency Tracking

This demonstrates how to integrate TimescaleDB client with RLM_REPL
for tracking code execution and LLM interaction latency.
"""

import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from rlm import RLM
from rlm.repl import REPLEnv
from rlm.utils.llm import LLMClient
from rlm.utils.prompts import DEFAULT_QUERY, next_action_prompt, build_system_prompt
import rlm.utils.utils as utils

from rlm.logger.root_logger import ColorfulLogger
from rlm.logger.repl_logger import REPLEnvLogger
from rlm.logger.timescale_client import TimescaleDBClient


class RLM_REPL_With_Timescale(RLM):
    """
    RLM_REPL with TimescaleDB latency tracking.
    Tracks code execution and LLM interaction latency.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        recursive_models: Optional[List[str]] = None,
        recursive_base_urls: Optional[List[str]] = None,
        max_iterations: int = 20,
        max_depth: int = 1,
        current_depth: int = 0,
        enable_logging: bool = False,
        enable_timescale: bool = True,
        timescale_db_url: Optional[str] = None
    ):
        import os
        self.api_key = api_key
        self.model = model or os.getenv("LLM_MODEL", "gpt-5")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        
        default_recursive_model = os.getenv("LLM_RECURSIVE_MODEL", "gpt-5-mini")
        default_recursive_base_url = os.getenv("LLM_RECURSIVE_BASE_URL") or os.getenv("LLM_BASE_URL")
        
        self.recursive_models = recursive_models or [default_recursive_model]
        self.recursive_base_urls = recursive_base_urls or ([default_recursive_base_url] if default_recursive_base_url else [])
        
        self.llm = LLMClient(api_key, self.model, self.base_url)

        self.repl_env = None
        self.max_depth = max_depth
        self.current_depth = current_depth
        self._max_iterations = max_iterations

        # Traditional loggers
        self.logger = ColorfulLogger(enabled=enable_logging)
        self.repl_env_logger = REPLEnvLogger(enabled=enable_logging)

        # TimescaleDB client for latency tracking
        self.enable_timescale = enable_timescale
        self.timescale_client: Optional[TimescaleDBClient] = None
        self.current_query_id: Optional[str] = None
        self.current_run_id: Optional[datetime] = None

        if enable_timescale:
            db_url = timescale_db_url or os.getenv("TIMESCALE_DB_URL", "postgresql://user:password@localhost:5432/rlm_logs")
            self.timescale_client = TimescaleDBClient(db_url, pool_size=10)

        self.messages: List[Dict[str, str]] = []
        self.query: Optional[str] = None
        self.execution_count = 0

    def setup_context(
        self,
        context: List[str] | str | List[Dict[str, str]],
        query: Optional[str] = None,
        query_id: Optional[str] = None
    ):
        """
        Setup the context for the RLMClient with latency tracking.

        Args:
            context: The large context to analyze
            query: The user's question
            query_id: Query identifier from benchmark dataset
        """
        if query is None:
            query = DEFAULT_QUERY

        self.query = query
        self.current_query_id = query_id or f"query_{datetime.now(timezone.utc).timestamp()}"
        self.current_run_id = datetime.now(timezone.utc)

        # Initialize TimescaleDB tracking with recursion context
        if self.timescale_client:
            recursion_id = self.timescale_client.generate_recursion_id(self.current_depth)
            self.timescale_client.set_context(
                query_id=self.current_query_id,
                run_id=self.current_run_id,
                iteration=0,
                current_depth=self.current_depth,
                max_depth=self.max_depth,
                recursion_id=recursion_id,
                parent_recursion_id=None,
                model=self.model,
                model_index=None
            )
            self.timescale_client.initialize_query_run(
                self.current_query_id,
                self.current_run_id,
                metadata={
                    "model": self.model,
                    "recursive_model": self.recursive_model,
                    "max_iterations": self._max_iterations
                }
            )

        self.logger.log_query_start(query)
        self.messages = build_system_prompt()
        self.logger.log_initial_messages(self.messages)

        context_data, context_str = utils.convert_context_for_repl(context)

        self.repl_env = REPLEnv(
            context_json=context_data,
            context_str=context_str,
            recursive_model=self.recursive_model,
            recursive_base_url=self.recursive_base_url,
            recursive_api_key=self.api_key,
        )

        return self.messages

    def completion(
        self,
        context: List[str] | str | List[Dict[str, str]],
        query: Optional[str] = None,
        query_id: Optional[str] = None
    ) -> str:
        """
        Given a query and context, recursively call the LM with latency tracking.
        """
        self.messages = self.setup_context(context, query, query_id)
        self.execution_count = 0

        for iteration in range(self._max_iterations):
            # Update iteration context
            if self.timescale_client:
                self.timescale_client.set_context(iteration=iteration + 1)

            # Query root LM with latency tracking
            self.logger.log_model_response(
                f"Querying root LM (iteration {iteration + 1})",
                has_tool_calls=False
            )

            # Track LLM interaction latency
            llm_start_time = datetime.now(timezone.utc)
            try:
                with self.timescale_client.track_latency(
                    event_type="llm_interaction",
                    event_subtype="root_llm",
                    metadata={
                        "iteration": iteration + 1,
                        "model": self.model,
                        "message_count": len(self.messages)
                    },
                    source_component="RLM_REPL_With_Timescale",
                    source_function="completion"
                ):
                    response = self.llm.completion(
                        self.messages + [next_action_prompt(query, iteration)]
                    )
            except Exception as e:
                self.logger.log_tool_execution("LLM Query", str(e))
                if self.timescale_client:
                    self.timescale_client.complete_query_run(
                        self.current_query_id,
                        self.current_run_id,
                        status="error"
                    )
                raise

            llm_end_time = datetime.now(timezone.utc)
            llm_duration_ms = (llm_end_time - llm_start_time).total_seconds() * 1000

            # Check for code blocks
            code_blocks = utils.find_code_blocks(response)
            self.logger.log_model_response(response, has_tool_calls=code_blocks is not None)

            # Process code execution or add assistant message
            if code_blocks is not None:
                self.messages = self._process_code_execution_with_tracking(
                    response, self.messages, code_blocks, iteration
                )
            else:
                assistant_message = {
                    "role": "assistant",
                    "content": "You responded with:\n" + response
                }
                self.messages.append(assistant_message)

            # Check for final answer
            final_answer = utils.check_for_final_answer(
                response, self.repl_env, self.logger
            )

            if final_answer:
                self.logger.log_final_response(final_answer)
                if self.timescale_client:
                    self.timescale_client.complete_query_run(
                        self.current_query_id,
                        self.current_run_id,
                        status="completed"
                    )
                return final_answer

        # If no final answer found
        print("No final answer found in any iteration")
        self.messages.append(next_action_prompt(query, iteration, final_answer=True))
        
        with self.timescale_client.track_latency(
            event_type="llm_interaction",
            event_subtype="root_llm",
            metadata={"iteration": "final"}
        ):
            final_answer = self.llm.completion(self.messages)

        self.logger.log_final_response(final_answer)
        
        if self.timescale_client:
            self.timescale_client.complete_query_run(
                self.current_query_id,
                self.current_run_id,
                status="completed"
            )

        return final_answer

    def _process_code_execution_with_tracking(
        self,
        response: str,
        messages: List[Dict[str, str]],
        code_blocks: List[str],
        iteration: int
    ) -> List[Dict[str, str]]:
        """
        Process code execution with latency tracking.
        """
        for code in code_blocks:
            self.execution_count += 1

            # Track code execution latency
            exec_start_time = datetime.now(timezone.utc)
            
            try:
                with self.timescale_client.track_latency(
                    event_type="code_execution",
                    event_subtype="python_execution",
                    metadata={
                        "iteration": iteration + 1,
                        "execution_number": self.execution_count,
                        "code_length": len(code)
                    },
                    source_component="RLM_REPL_With_Timescale",
                    source_function="_process_code_execution_with_tracking"
                ):
                    result = self.repl_env.execute_code(code)
                    
            except Exception as e:
                self.logger.log_tool_execution(code, str(e))
                if self.timescale_client:
                    self.timescale_client.complete_query_run(
                        self.current_query_id,
                        self.current_run_id,
                        status="error"
                    )
                raise

            exec_end_time = datetime.now(timezone.utc)
            exec_duration_ms = (exec_end_time - exec_start_time).total_seconds() * 1000

            # Log to REPL logger
            self.repl_env_logger.log_execution(
                code=code,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=exec_duration_ms / 1000
            )
            self.repl_env_logger.display_last()

            # Also record detailed code execution
            if self.timescale_client:
                from rlm.logger.timescale_client import CodeExecutionRecord
                
                code_record = CodeExecutionRecord(
                    query_id=self.current_query_id,
                    run_id=self.current_run_id,
                    execution_number=self.execution_count,
                    code=code,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    output_length=len(result.stdout or '') + len(result.stderr or ''),
                    duration_ms=exec_duration_ms,
                    start_time=exec_start_time,
                    end_time=exec_end_time,
                    success=not bool(result.stderr),
                    error_message=result.stderr if result.stderr else None,
                    error_type=None,
                    metadata={"iteration": iteration + 1}
                )
                self.timescale_client.record_code_execution(code_record)

            # Add to messages
            tool_message = {
                "role": "tool",
                "content": f"Executed code:\n{code}\n\nOutput:\n{result.stdout}"
            }
            messages.append(tool_message)

        return messages

    def get_latency_summary(self) -> Optional[Dict[str, Any]]:
        """
        Get latency summary for the current query run.
        """
        if self.timescale_client and self.current_query_id and self.current_run_id:
            return self.timescale_client.get_query_run_summary(
                self.current_query_id, self.current_run_id
            )
        return None

    def get_latency_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive latency metrics for the current query run.
        """
        if self.timescale_client and self.current_query_id and self.current_run_id:
            return self.timescale_client.get_latency_metrics(
                self.current_query_id, self.current_run_id
            )
        return None

    def close(self):
        """Close the TimescaleDB client."""
        if self.timescale_client:
            self.timescale_client.close()

    def __del__(self):
        """Destructor to ensure client is closed."""
        self.close()


# Example usage
if __name__ == "__main__":
    print("RLM_REPL with TimescaleDB Latency Tracking")
    print("=" * 60)

    # Initialize RLM with TimescaleDB tracking
    rlm = RLM_REPL_With_Timescale(
        enable_logging=True,
        enable_timescale=True,
        timescale_db_url=os.getenv("TIMESCALE_DB_URL")
    )

    try:
        # Example query from benchmark dataset
        query_id = "benchmark-001"
        query = "What is the capital of France?"
        context = [
            "Paris is the capital and most populous city of France.",
            "It is located in the northern part of the country."
        ]

        print(f"\nQuery ID: {query_id}")
        print(f"Query: {query}")
        print("Running RLM...\n")

        result = rlm.completion(context, query, query_id=query_id)

        print(f"\nResult: {result}")

        # Get latency metrics
        print("\n" + "=" * 60)
        print("Latency Metrics:")
        print("=" * 60)

        summary = rlm.get_latency_summary()
        if summary:
            print(f"Total duration: {summary['total_duration_ms']:.2f}ms")
            print(f"LLM interactions: {summary['total_llm_interactions']}")
            print(f"Code executions: {summary['total_code_executions']}")
            print(f"Avg LLM latency: {summary['avg_llm_latency_ms']:.2f}ms")
            print(f"Avg code latency: {summary['avg_code_latency_ms']:.2f}ms")

    finally:
        rlm.close()
