"""
TimescaleDB Client for RLM Latency Tracking

This client tracks code execution latency and LLM interaction latency
with query_id (from benchmark dataset) and run_id (from main script timestamp).
"""

import logging
import psycopg2
import psycopg2.pool
import psycopg2.extras
import json
import hashlib
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager, ContextDecorator
from functools import wraps
from typing import Optional, Dict, Any, List, Union, Callable
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class LatencyRecord:
    """Data class for latency records."""
    query_id: str
    run_id: datetime
    recursion_id: str
    parent_recursion_id: Optional[str] = None
    event_type: str
    event_subtype: Optional[str] = None
    duration_ms: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    iteration: Optional[int] = None
    current_depth: Optional[int] = None
    max_depth: Optional[int] = None
    model: Optional[str] = None
    model_index: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    source_component: Optional[str] = None
    source_function: Optional[str] = None


@dataclass
class LLMInteractionRecord:
    """Data class for LLM interaction records."""
    query_id: str
    run_id: datetime
    recursion_id: str
    parent_recursion_id: Optional[str] = None
    model: str
    model_index: Optional[int] = None
    model_type: Optional[str] = None
    current_depth: Optional[int] = None
    max_depth: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    
    # Token cache tracking (from prompt_tokens_details.cached_tokens)
    cached_tokens: Optional[int] = 0
    uncached_prompt_tokens: Optional[int] = None
    
    # Token pricing for cost calculation
    prompt_token_price: Optional[float] = None  # Price per 1k tokens
    completion_token_price: Optional[float] = None  # Price per 1k tokens
    total_cost: Optional[float] = None  # Calculated cost
    
    duration_ms: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    context_messages: Optional[int] = None
    context_tokens: Optional[int] = None
    response_length: Optional[int] = None
    iteration: Optional[int] = None
    has_tool_calls: Optional[bool] = None
    tool_call_count: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CodeExecutionRecord:
    """Data class for code execution records."""
    query_id: str
    run_id: datetime
    recursion_id: str
    parent_recursion_id: Optional[str] = None
    execution_number: int
    code: str
    current_depth: Optional[int] = None
    max_depth: Optional[int] = None
    model: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    output_length: Optional[int] = None
    duration_ms: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    iteration: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TimescaleDBClient:
    """TimescaleDB client for RLM latency tracking."""

    def __init__(self, db_url: str, pool_size: int = 10, auto_commit: bool = True):
        """
        Initialize the TimescaleDB client.

        Args:
            db_url: PostgreSQL connection URL
            pool_size: Maximum number of connections in pool
            auto_commit: Whether to auto-commit transactions
        """
        self.db_url = db_url
        self.pool_size = pool_size
        self.auto_commit = auto_commit
        self.pool: Optional[psycopg2.pool.SimpleConnectionPool] = None
        self._current_query_id: Optional[str] = None
        self._current_run_id: Optional[datetime] = None
        self._current_iteration: Optional[int] = None
        self._current_depth: Optional[int] = None
        self._current_max_depth: Optional[int] = None
        self._current_recursion_id: Optional[str] = None
        self._current_parent_recursion_id: Optional[str] = None
        self._current_model: Optional[str] = None
        self._current_model_index: Optional[int] = None

        self._init_pool()

    def _init_pool(self):
        """Initialize connection pool."""
        try:
            self.pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=self.pool_size,
                dsn=self.db_url,
                connect_timeout=10
            )
            logger.info(f"TimescaleDB connection pool initialized (size: {self.pool_size})")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise

    def set_context(self, query_id: Optional[str] = None, run_id: Optional[datetime] = None,
                   iteration: Optional[int] = None, current_depth: Optional[int] = None,
                   max_depth: Optional[int] = None, recursion_id: Optional[str] = None,
                   parent_recursion_id: Optional[str] = None, model: Optional[str] = None,
                   model_index: Optional[int] = None):
        """
        Set current logging context.

        Args:
            query_id: Query identifier from benchmark dataset
            run_id: Run identifier (timestamp from main script)
            iteration: Current conversation iteration
            current_depth: Current recursion depth (0 = root)
            max_depth: Maximum allowed recursion depth
            recursion_id: Unique ID for this recursive call
            parent_recursion_id: Parent recursion ID (for tree structure)
            model: Model used at this depth
            model_index: Index in recursive_models list
        """
        if query_id is not None:
            self._current_query_id = query_id
        if run_id is not None:
            self._current_run_id = run_id
        if iteration is not None:
            self._current_iteration = iteration
        if current_depth is not None:
            self._current_depth = current_depth
        if max_depth is not None:
            self._current_max_depth = max_depth
        if recursion_id is not None:
            self._current_recursion_id = recursion_id
        if parent_recursion_id is not None:
            self._current_parent_recursion_id = parent_recursion_id
        if model is not None:
            self._current_model = model
        if model_index is not None:
            self._current_model_index = model_index
    
    def generate_recursion_id(self, current_depth: int) -> str:
        """
        Generate a unique recursion ID.
        
        Args:
            current_depth: Current recursion depth
            
        Returns:
            Unique recursion ID string
        """
        return f"rec_{current_depth}_{uuid.uuid4().hex[:8]}"
    
    def enter_recursive_call(self, current_depth: int, max_depth: int, 
                            model: str, model_index: Optional[int] = None) -> str:
        """
        Enter a recursive call context.
        Saves current recursion ID as parent and generates new recursion ID.
        
        Args:
            current_depth: Current recursion depth
            max_depth: Maximum allowed depth
            model: Model used at this depth
            model_index: Index in recursive_models list
            
        Returns:
            New recursion ID
        """
        parent_recursion_id = self._current_recursion_id
        new_recursion_id = self.generate_recursion_id(current_depth)
        
        self.set_context(
            current_depth=current_depth,
            max_depth=max_depth,
            recursion_id=new_recursion_id,
            parent_recursion_id=parent_recursion_id,
            model=model,
            model_index=model_index
        )
        
        return new_recursion_id

    def get_connection(self):
        """Get a connection from the pool."""
        if not self.pool:
            self._init_pool()
        return self.pool.getconn()

    def release_connection(self, conn):
        """Release a connection back to the pool."""
        if self.pool and conn:
            self.pool.putconn(conn)

    @contextmanager
    def connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = self.get_connection()
            if self.auto_commit:
                conn.autocommit = True
            yield conn
        except Exception as e:
            logger.error(f"Database error: {e}")
            if conn and not self.auto_commit:
                conn.rollback()
            raise
        finally:
            if conn:
                self.release_connection(conn)

    def _execute(self, query: str, params: Dict[str, Any] = None, conn=None):
        """Execute a SQL query."""
        if conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(query, params)
            return cursor
        else:
            with self.connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute(query, params)
                return cursor

    def _execute_many(self, query: str, params_list: List[Dict[str, Any]], conn=None):
        """Execute a SQL query with multiple parameter sets."""
        if conn:
            cursor = conn.cursor()
            psycopg2.extras.execute_batch(cursor, query, params_list)
            return cursor
        else:
            with self.connection() as conn:
                cursor = conn.cursor()
                psycopg2.extras.execute_batch(cursor, query, params_list)
                return cursor

    # ========== Latency Events ==========

    def record_latency(self, record: LatencyRecord, conn=None) -> str:
        """Record a latency event."""
        if not record.start_time:
            record.start_time = datetime.now(timezone.utc)
        if not record.end_time:
            record.end_time = datetime.now(timezone.utc)
        if not record.duration_ms:
            record.duration_ms = (record.end_time - record.start_time).total_seconds() * 1000
        if not record.recursion_id:
            record.recursion_id = self._current_recursion_id or self.generate_recursion_id(record.current_depth or 0)

        query = """
            INSERT INTO latency_events (
                time, query_id, run_id, recursion_id, parent_recursion_id,
                event_type, event_subtype, duration_ms, start_time, end_time,
                iteration, current_depth, max_depth, model, model_index,
                metadata, success, error_message, error_type,
                source_component, source_function
            ) VALUES (
                %(time)s, %(query_id)s, %(run_id)s, %(recursion_id)s, %(parent_recursion_id)s,
                %(event_type)s, %(event_subtype)s, %(duration_ms)s, %(start_time)s, %(end_time)s,
                %(iteration)s, %(current_depth)s, %(max_depth)s, %(model)s, %(model_index)s,
                %(metadata)s, %(success)s, %(error_message)s, %(error_type)s,
                %(source_component)s, %(source_function)s
            ) RETURNING event_id
        """

        params = {
            'time': datetime.now(timezone.utc),
            'query_id': record.query_id or self._current_query_id,
            'run_id': record.run_id or self._current_run_id,
            'recursion_id': record.recursion_id,
            'parent_recursion_id': record.parent_recursion_id or self._current_parent_recursion_id,
            'event_type': record.event_type,
            'event_subtype': record.event_subtype,
            'duration_ms': record.duration_ms,
            'start_time': record.start_time,
            'end_time': record.end_time,
            'iteration': record.iteration or self._current_iteration,
            'current_depth': record.current_depth or self._current_depth,
            'max_depth': record.max_depth or self._current_max_depth,
            'model': record.model or self._current_model,
            'model_index': record.model_index or self._current_model_index,
            'metadata': json.dumps(record.metadata) if record.metadata else None,
            'success': record.success,
            'error_message': record.error_message,
            'error_type': record.error_type,
            'source_component': record.source_component,
            'source_function': record.source_function
        }

        cursor = self._execute(query, params, conn)
        event_id = cursor.fetchone()['event_id']
        return str(event_id)

    # ========== LLM Interactions ==========

    def record_llm_interaction(self, record: LLMInteractionRecord, conn=None) -> str:
        """Record an LLM interaction."""
        if not record.start_time:
            record.start_time = datetime.now(timezone.utc)
        if not record.end_time:
            record.end_time = datetime.now(timezone.utc)
        if not record.duration_ms:
            record.duration_ms = (record.end_time - record.start_time).total_seconds() * 1000
        if not record.recursion_id:
            record.recursion_id = self._current_recursion_id or self.generate_recursion_id(record.current_depth or 0)
        
        # Calculate uncached tokens if not provided
        if record.uncached_prompt_tokens is None and record.prompt_tokens is not None:
            record.uncached_prompt_tokens = record.prompt_tokens - (record.cached_tokens or 0)
        
        # Calculate total cost if prices are provided
        if record.total_cost is None and record.prompt_token_price is not None:
            # Calculate cost: (prompt_tokens * prompt_price + completion_tokens * completion_price) / 1000
            prompt_cost = (record.prompt_tokens or 0) * (record.prompt_token_price or 0) / 1000
            completion_cost = (record.completion_tokens or 0) * (record.completion_token_price or 0) / 1000
            record.total_cost = prompt_cost + completion_cost

        query = """
            INSERT INTO llm_interactions (
                time, query_id, run_id, recursion_id, parent_recursion_id,
                model, model_index, model_type, current_depth, max_depth,
                prompt_tokens, completion_tokens, total_tokens,
                cached_tokens, uncached_prompt_tokens,
                prompt_token_price, completion_token_price, total_cost,
                duration_ms, start_time, end_time,
                context_messages, context_tokens, response_length, iteration,
                has_tool_calls, tool_call_count, success,
                error_message, error_type, metadata
            ) VALUES (
                %(time)s, %(query_id)s, %(run_id)s, %(recursion_id)s, %(parent_recursion_id)s,
                %(model)s, %(model_index)s, %(model_type)s, %(current_depth)s, %(max_depth)s,
                %(prompt_tokens)s, %(completion_tokens)s, %(total_tokens)s,
                %(cached_tokens)s, %(uncached_prompt_tokens)s,
                %(prompt_token_price)s, %(completion_token_price)s, %(total_cost)s,
                %(duration_ms)s, %(start_time)s, %(end_time)s,
                %(context_messages)s, %(context_tokens)s, %(response_length)s, %(iteration)s,
                %(has_tool_calls)s, %(tool_call_count)s, %(success)s,
                %(error_message)s, %(error_type)s, %(metadata)s
            ) RETURNING interaction_id
        """

        params = {
            'time': datetime.now(timezone.utc),
            'query_id': record.query_id or self._current_query_id,
            'run_id': record.run_id or self._current_run_id,
            'recursion_id': record.recursion_id,
            'parent_recursion_id': record.parent_recursion_id or self._current_parent_recursion_id,
            'model': record.model,
            'model_index': record.model_index or self._current_model_index,
            'model_type': record.model_type,
            'current_depth': record.current_depth or self._current_depth,
            'max_depth': record.max_depth or self._current_max_depth,
            'prompt_tokens': record.prompt_tokens,
            'completion_tokens': record.completion_tokens,
            'total_tokens': record.total_tokens,
            'cached_tokens': record.cached_tokens,
            'uncached_prompt_tokens': record.uncached_prompt_tokens,
            'prompt_token_price': record.prompt_token_price,
            'completion_token_price': record.completion_token_price,
            'total_cost': record.total_cost,
            'duration_ms': record.duration_ms,
            'start_time': record.start_time,
            'end_time': record.end_time,
            'context_messages': record.context_messages,
            'context_tokens': record.context_tokens,
            'response_length': record.response_length,
            'iteration': record.iteration or self._current_iteration,
            'has_tool_calls': record.has_tool_calls,
            'tool_call_count': record.tool_call_count,
            'success': record.success,
            'error_message': record.error_message,
            'error_type': record.error_type,
            'metadata': json.dumps(record.metadata) if record.metadata else None
        }

        cursor = self._execute(query, params, conn)
        interaction_id = cursor.fetchone()['interaction_id']
        return str(interaction_id)

    # ========== Code Executions ==========

    def record_code_execution(self, record: CodeExecutionRecord, conn=None) -> str:
        """Record a code execution."""
        if not record.start_time:
            record.start_time = datetime.now(timezone.utc)
        if not record.end_time:
            record.end_time = datetime.now(timezone.utc)
        if not record.duration_ms:
            record.duration_ms = (record.end_time - record.start_time).total_seconds() * 1000
        if not record.output_length:
            record.output_length = len(record.stdout or '') + len(record.stderr or '')

        code_hash = hashlib.md5(record.code.encode()).hexdigest()

        query = """
            INSERT INTO code_executions (
                time, query_id, run_id, execution_number, code, code_hash,
                stdout, stderr, output_length, duration_ms,
                start_time, end_time, success, error_message, error_type, metadata
            ) VALUES (
                %(time)s, %(query_id)s, %(run_id)s, %(execution_number)s, %(code)s, %(code_hash)s,
                %(stdout)s, %(stderr)s, %(output_length)s, %(duration_ms)s,
                %(start_time)s, %(end_time)s, %(success)s, %(error_message)s, %(error_type)s, %(metadata)s
            ) RETURNING execution_id
        """

        params = {
            'time': datetime.now(timezone.utc),
            'query_id': record.query_id or self._current_query_id,
            'run_id': record.run_id or self._current_run_id,
            'execution_number': record.execution_number,
            'code': record.code,
            'code_hash': code_hash,
            'stdout': record.stdout,
            'stderr': record.stderr,
            'output_length': record.output_length,
            'duration_ms': record.duration_ms,
            'start_time': record.start_time,
            'end_time': record.end_time,
            'success': record.success,
            'error_message': record.error_message,
            'error_type': record.error_type,
            'metadata': json.dumps(record.metadata) if record.metadata else None
        }

        cursor = self._execute(query, params, conn)
        execution_id = cursor.fetchone()['execution_id']
        return str(execution_id)

    # ========== Query Run Summaries ==========

    def initialize_query_run(self, query_id: str, run_id: datetime, metadata: Dict[str, Any] = None, conn=None):
        """Initialize a query run summary."""
        query = """
            INSERT INTO query_run_summaries (
                query_id, run_id, start_time, status, metadata
            ) VALUES (
                %(query_id)s, %(run_id)s, %(start_time)s, 'running', %(metadata)s
            ) ON CONFLICT (query_id, run_id) DO NOTHING
        """

        params = {
            'query_id': query_id,
            'run_id': run_id,
            'start_time': datetime.now(timezone.utc),
            'metadata': json.dumps(metadata) if metadata else None
        }

        self._execute(query, params, conn)

    def update_query_run_summary(self, query_id: str, run_id: datetime, conn=None):
        """Update query run summary with aggregated metrics."""
        with self.connection() as conn:
            cursor = self._execute("""
                SELECT
                    COUNT(*) FILTER (WHERE event_type = 'llm_interaction') AS total_llm_interactions,
                    COUNT(*) FILTER (WHERE event_type = 'code_execution') AS total_code_executions,
                    COUNT(*) FILTER (WHERE event_type = 'tool_call') AS total_tool_calls,
                    
                    AVG(duration_ms) FILTER (WHERE event_type = 'llm_interaction') AS avg_llm_latency_ms,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms) FILTER (WHERE event_type = 'llm_interaction') AS p50_llm_latency_ms,
                    PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY duration_ms) FILTER (WHERE event_type = 'llm_interaction') AS p90_llm_latency_ms,
                    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) FILTER (WHERE event_type = 'llm_interaction') AS p99_llm_latency_ms,
                    
                    AVG(duration_ms) FILTER (WHERE event_type = 'code_execution') AS avg_code_latency_ms,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms) FILTER (WHERE event_type = 'code_execution') AS p50_code_latency_ms,
                    PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY duration_ms) FILTER (WHERE event_type = 'code_execution') AS p90_code_latency_ms,
                    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) FILTER (WHERE event_type = 'code_execution') AS p99_code_latency_ms,
                    
                    COUNT(*) FILTER (WHERE success = FALSE) AS error_count,
                    COUNT(*) FILTER (WHERE success = FALSE)::FLOAT / COUNT(*) AS error_rate,
                    
                    MIN(start_time) AS first_start_time,
                    MAX(end_time) AS last_end_time
                FROM latency_events
                WHERE query_id = %(query_id)s AND run_id = %(run_id)s
            """, {'query_id': query_id, 'run_id': run_id}, conn)

            result = cursor.fetchone()
            if result:
                total_duration_ms = None
                if result['first_start_time'] and result['last_end_time']:
                    total_duration_ms = (result['last_end_time'] - result['first_start_time']).total_seconds() * 1000

                update_query = """
                    UPDATE query_run_summaries SET
                        end_time = %(end_time)s,
                        total_duration_ms = %(total_duration_ms)s,
                        total_llm_interactions = %(total_llm_interactions)s,
                        total_code_executions = %(total_code_executions)s,
                        total_tool_calls = %(total_tool_calls)s,
                        avg_llm_latency_ms = %(avg_llm_latency_ms)s,
                        p50_llm_latency_ms = %(p50_llm_latency_ms)s,
                        p90_llm_latency_ms = %(p90_llm_latency_ms)s,
                        p99_llm_latency_ms = %(p99_llm_latency_ms)s,
                        avg_code_latency_ms = %(avg_code_latency_ms)s,
                        p50_code_latency_ms = %(p50_code_latency_ms)s,
                        p90_code_latency_ms = %(p90_code_latency_ms)s,
                        p99_code_latency_ms = %(p99_code_latency_ms)s,
                        error_count = %(error_count)s,
                        error_rate = %(error_rate)s
                    WHERE query_id = %(query_id)s AND run_id = %(run_id)s
                """

                self._execute(update_query, {
                    'end_time': result['last_end_time'],
                    'total_duration_ms': total_duration_ms,
                    'total_llm_interactions': result['total_llm_interactions'],
                    'total_code_executions': result['total_code_executions'],
                    'total_tool_calls': result['total_tool_calls'],
                    'avg_llm_latency_ms': result['avg_llm_latency_ms'],
                    'p50_llm_latency_ms': result['p50_llm_latency_ms'],
                    'p90_llm_latency_ms': result['p90_llm_latency_ms'],
                    'p99_llm_latency_ms': result['p99_llm_latency_ms'],
                    'avg_code_latency_ms': result['avg_code_latency_ms'],
                    'p50_code_latency_ms': result['p50_code_latency_ms'],
                    'p90_code_latency_ms': result['p90_code_latency_ms'],
                    'p99_code_latency_ms': result['p99_code_latency_ms'],
                    'error_count': result['error_count'],
                    'error_rate': result['error_rate'],
                    'query_id': query_id,
                    'run_id': run_id
                }, conn)

    def complete_query_run(self, query_id: str, run_id: datetime, status: str = 'completed', conn=None):
        """Mark a query run as completed."""
        self.update_query_run_summary(query_id, run_id, conn)

        query = """
            UPDATE query_run_summaries SET
                status = %(status)s,
                end_time = COALESCE(end_time, %(end_time)s)
            WHERE query_id = %(query_id)s AND run_id = %(run_id)s
        """

        self._execute(query, {
            'status': status,
            'end_time': datetime.now(timezone.utc),
            'query_id': query_id,
            'run_id': run_id
        }, conn)

    # ========== Context Managers and Decorators ==========

    @contextmanager
    def track_latency(self, event_type: str, event_subtype: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None, source_component: Optional[str] = None,
                     source_function: Optional[str] = None):
        """
        Context manager to track latency of a code block.

        Usage:
            with client.track_latency('llm_interaction', 'root_llm'):
                # Code to track
                response = llm.completion(messages)
        """
        start_time = datetime.now(timezone.utc)
        success = True
        error_message = None
        error_type = None

        try:
            yield
        except Exception as e:
            success = False
            error_message = str(e)
            error_type = type(e).__name__
            raise
        finally:
            end_time = datetime.now(timezone.utc)
            duration_ms = (end_time - start_time).total_seconds() * 1000

            record = LatencyRecord(
                query_id=self._current_query_id or 'unknown',
                run_id=self._current_run_id or datetime.now(timezone.utc),
                recursion_id=self._current_recursion_id or self.generate_recursion_id(self._current_depth or 0),
                parent_recursion_id=self._current_parent_recursion_id,
                event_type=event_type,
                event_subtype=event_subtype,
                duration_ms=duration_ms,
                start_time=start_time,
                end_time=end_time,
                iteration=self._current_iteration,
                current_depth=self._current_depth,
                max_depth=self._current_max_depth,
                model=self._current_model,
                model_index=self._current_model_index,
                metadata=metadata,
                success=success,
                error_message=error_message,
                error_type=error_type,
                source_component=source_component,
                source_function=source_function
            )
            self.record_latency(record)

    def track_latency_decorator(self, event_type: str, event_subtype: Optional[str] = None,
                               metadata: Optional[Dict[str, Any]] = None):
        """
        Decorator to track function latency.

        Usage:
            @client.track_latency_decorator('code_execution', 'python_execution')
            def execute_code(code):
                # Function implementation
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.track_latency(
                    event_type=event_type,
                    event_subtype=event_subtype,
                    metadata=metadata,
                    source_function=func.__name__
                ):
                    return func(*args, **kwargs)
            return wrapper
        return decorator

    # ========== Analytics Queries ==========

    def get_query_run_summary(self, query_id: str, run_id: datetime) -> Optional[Dict[str, Any]]:
        """Get summary for a specific query run."""
        cursor = self._execute("""
            SELECT * FROM query_run_summaries
            WHERE query_id = %(query_id)s AND run_id = %(run_id)s
        """, {'query_id': query_id, 'run_id': run_id})

        result = cursor.fetchone()
        return dict(result) if result else None

    def get_latency_events(self, query_id: str, run_id: datetime, 
                          event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get latency events for a query run."""
        query = """
            SELECT * FROM latency_events
            WHERE query_id = %(query_id)s AND run_id = %(run_id)s
        """
        params = {'query_id': query_id, 'run_id': run_id}

        if event_type:
            query += " AND event_type = %(event_type)s"
            params['event_type'] = event_type

        query += " ORDER BY time ASC"

        cursor = self._execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_llm_interactions(self, query_id: str, run_id: datetime) -> List[Dict[str, Any]]:
        """Get LLM interactions for a query run."""
        cursor = self._execute("""
            SELECT * FROM llm_interactions
            WHERE query_id = %(query_id)s AND run_id = %(run_id)s
            ORDER BY time ASC
        """, {'query_id': query_id, 'run_id': run_id})

        return [dict(row) for row in cursor.fetchall()]

    def get_code_executions(self, query_id: str, run_id: datetime) -> List[Dict[str, Any]]:
        """Get code executions for a query run."""
        cursor = self._execute("""
            SELECT * FROM code_executions
            WHERE query_id = %(query_id)s AND run_id = %(run_id)s
            ORDER BY execution_number ASC
        """, {'query_id': query_id, 'run_id': run_id})

        return [dict(row) for row in cursor.fetchall()]

    def get_latency_metrics(self, query_id: str, run_id: datetime) -> Dict[str, Any]:
        """Get comprehensive latency metrics for a query run."""
        cursor = self._execute("""
            SELECT
                event_type,
                COUNT(*) as count,
                AVG(duration_ms) as avg_duration_ms,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms) as p50_duration_ms,
                PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY duration_ms) as p90_duration_ms,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) as p99_duration_ms,
                MIN(duration_ms) as min_duration_ms,
                MAX(duration_ms) as max_duration_ms,
                COUNT(*) FILTER (WHERE success = FALSE) as error_count
            FROM latency_events
            WHERE query_id = %(query_id)s AND run_id = %(run_id)s
            GROUP BY event_type
        """, {'query_id': query_id, 'run_id': run_id})

        results = cursor.fetchall()
        metrics = {}

        for row in results:
            event_type = row['event_type']
            metrics[event_type] = {
                'count': row['count'],
                'avg_duration_ms': row['avg_duration_ms'],
                'p50_duration_ms': row['p50_duration_ms'],
                'p90_duration_ms': row['p90_duration_ms'],
                'p99_duration_ms': row['p99_duration_ms'],
                'min_duration_ms': row['min_duration_ms'],
                'max_duration_ms': row['max_duration_ms'],
                'error_count': row['error_count'],
                'error_rate': row['error_count'] / row['count'] if row['count'] > 0 else 0
            }

        return metrics

    def get_slowest_llm_interactions(self, query_id: str, run_id: datetime, n: int = 10) -> List[Dict[str, Any]]:
        """Get slowest LLM interactions for a query run."""
        cursor = self._execute("""
            SELECT * FROM llm_interactions
            WHERE query_id = %(query_id)s AND run_id = %(run_id)s
            ORDER BY duration_ms DESC
            LIMIT %(n)s
        """, {'query_id': query_id, 'run_id': run_id, 'n': n})

        return [dict(row) for row in cursor.fetchall()]

    def get_slowest_code_executions(self, query_id: str, run_id: datetime, n: int = 10) -> List[Dict[str, Any]]:
        """Get slowest code executions for a query run."""
        cursor = self._execute("""
            SELECT * FROM code_executions
            WHERE query_id = %(query_id)s AND run_id = %(run_id)s
            ORDER BY duration_ms DESC
            LIMIT %(n)s
        """, {'query_id': query_id, 'run_id': run_id, 'n': n})

        return [dict(row) for row in cursor.fetchall()]

    # ========== Token Cache Analytics ==========

    def get_token_cache_summary(self, query_id: str, run_id: datetime) -> Optional[Dict[str, Any]]:
        """Get token cache summary for a query run."""
        cursor = self._execute("""
            SELECT
                SUM(prompt_tokens) AS total_prompt_tokens,
                SUM(completion_tokens) AS total_completion_tokens,
                SUM(total_tokens) AS total_tokens,
                SUM(cached_tokens) AS total_cached_tokens,
                SUM(uncached_prompt_tokens) AS total_uncached_tokens,
                
                -- Cache effectiveness
                CASE 
                    WHEN SUM(prompt_tokens) > 0 
                    THEN SUM(cached_tokens)::FLOAT / SUM(prompt_tokens) 
                    ELSE 0 
                END AS cache_hit_rate,
                
                -- Cost metrics
                SUM(total_cost) AS total_cost,
                AVG(total_cost) AS avg_cost_per_interaction,
                
                -- Interaction counts
                COUNT(*) AS total_interactions,
                COUNT(*) FILTER (WHERE cached_tokens > 0) AS interactions_with_cache,
                COUNT(*) FILTER (WHERE cached_tokens = 0 OR cached_tokens IS NULL) AS interactions_without_cache,
                
                -- Cache savings calculation
                SUM(prompt_tokens) AS original_prompt_tokens, -- Without cache
                SUM(uncached_prompt_tokens) AS cached_prompt_tokens, -- With cache
                SUM(prompt_tokens) - SUM(uncached_prompt_tokens) AS cache_savings_tokens
            FROM llm_interactions
            WHERE query_id = %(query_id)s AND run_id = %(run_id)s
        """, {'query_id': query_id, 'run_id': run_id})

        result = cursor.fetchone()
        if result:
            summary = dict(result)
            
            # Calculate cost savings
            if summary.get('original_prompt_tokens') and summary.get('cached_prompt_tokens'):
                summary['cache_savings_percentage'] = (
                    (summary['original_prompt_tokens'] - summary['cached_prompt_tokens']) / 
                    summary['original_prompt_tokens'] * 100
                )
            
            return summary
        return None

    def get_token_cache_optimization(self, query_id: str, run_id: datetime) -> Optional[Dict[str, Any]]:
        """Get detailed token cache optimization analysis."""
        cursor = self._execute("""
            SELECT * FROM token_cache_optimization
            WHERE query_id = %(query_id)s AND run_id = %(run_id)s
        """, {'query_id': query_id, 'run_id': run_id})

        result = cursor.fetchone()
        return dict(result) if result else None

    def calculate_and_store_cache_optimization(self, query_id: str, run_id: datetime, conn=None):
        """Calculate and store token cache optimization metrics."""
        with self.connection() as conn:
            cursor = self._execute("""
                SELECT
                    SUM(prompt_tokens) AS total_prompt_tokens,
                    SUM(cached_tokens) AS total_cached_tokens,
                    SUM(uncached_prompt_tokens) AS total_uncached_tokens,
                    SUM(total_cost) AS total_cached_cost,
                    COUNT(*) AS total_interactions,
                    COUNT(*) FILTER (WHERE cached_tokens > 0) AS interactions_with_cache,
                    COUNT(*) FILTER (WHERE cached_tokens = 0 OR cached_tokens IS NULL) AS interactions_without_cache,
                    
                    -- Calculate cost without cache (all prompt tokens at regular price)
                    AVG(prompt_token_price) AS avg_prompt_price,
                    AVG(completion_token_price) AS avg_completion_price
                FROM llm_interactions
                WHERE query_id = %(query_id)s AND run_id = %(run_id)s
            """, {'query_id': query_id, 'run_id': run_id}, conn)

            result = cursor.fetchone()
            if not result:
                return

            total_prompt_tokens = result['total_prompt_tokens'] or 0
            total_cached_tokens = result['total_cached_tokens'] or 0
            total_uncached_tokens = result['total_uncached_tokens'] or 0
            total_cached_cost = result['total_cached_cost'] or 0
            avg_prompt_price = result['avg_prompt_price'] or 0
            avg_completion_price = result['avg_completion_price'] or 0

            # Calculate cost without cache
            original_cost = (total_prompt_tokens * avg_prompt_price / 1000) + \
                           (result['total_completion_tokens'] or 0) * avg_completion_price / 1000

            cache_savings_tokens = total_cached_tokens
            cache_savings_percentage = (cache_savings_tokens / total_prompt_tokens * 100) if total_prompt_tokens > 0 else 0
            
            cost_savings = original_cost - total_cached_cost
            cost_savings_percentage = (cost_savings / original_cost * 100) if original_cost > 0 else 0

            # Get per-iteration cache evolution
            cursor2 = self._execute("""
                SELECT
                    iteration,
                    SUM(prompt_tokens) AS prompt_tokens,
                    SUM(cached_tokens) AS cached_tokens,
                    SUM(uncached_prompt_tokens) AS uncached_tokens,
                    COUNT(*) AS interaction_count
                FROM llm_interactions
                WHERE query_id = %(query_id)s AND run_id = %(run_id)s AND iteration IS NOT NULL
                GROUP BY iteration
                ORDER BY iteration
            """, {'query_id': query_id, 'run_id': run_id}, conn)

            cache_evolution = []
            for row in cursor2.fetchall():
                cache_evolution.append({
                    'iteration': row['iteration'],
                    'prompt_tokens': row['prompt_tokens'],
                    'cached_tokens': row['cached_tokens'],
                    'uncached_tokens': row['uncached_tokens'],
                    'cache_hit_rate': row['cached_tokens'] / row['prompt_tokens'] if row['prompt_tokens'] > 0 else 0
                })

            # Store optimization data
            insert_query = """
                INSERT INTO token_cache_optimization (
                    time, query_id, run_id,
                    total_prompt_tokens, total_cached_tokens,
                    cache_savings_tokens, cache_savings_percentage,
                    original_cost, cached_cost, cost_savings, cost_savings_percentage,
                    total_interactions, interactions_with_cache, interactions_without_cache,
                    cache_evolution
                ) VALUES (
                    %(time)s, %(query_id)s, %(run_id)s,
                    %(total_prompt_tokens)s, %(total_cached_tokens)s,
                    %(cache_savings_tokens)s, %(cache_savings_percentage)s,
                    %(original_cost)s, %(cached_cost)s, %(cost_savings)s, %(cost_savings_percentage)s,
                    %(total_interactions)s, %(interactions_with_cache)s, %(interactions_without_cache)s,
                    %(cache_evolution)s
                ) ON CONFLICT (query_id, run_id) DO UPDATE SET
                    total_prompt_tokens = EXCLUDED.total_prompt_tokens,
                    total_cached_tokens = EXCLUDED.total_cached_tokens,
                    cache_savings_tokens = EXCLUDED.cache_savings_tokens,
                    cache_savings_percentage = EXCLUDED.cache_savings_percentage,
                    original_cost = EXCLUDED.original_cost,
                    cached_cost = EXCLUDED.cached_cost,
                    cost_savings = EXCLUDED.cost_savings,
                    cost_savings_percentage = EXCLUDED.cost_savings_percentage,
                    total_interactions = EXCLUDED.total_interactions,
                    interactions_with_cache = EXCLUDED.interactions_with_cache,
                    interactions_without_cache = EXCLUDED.interactions_without_cache,
                    cache_evolution = EXCLUDED.cache_evolution
            """

            self._execute(insert_query, {
                'time': datetime.now(timezone.utc),
                'query_id': query_id,
                'run_id': run_id,
                'total_prompt_tokens': total_prompt_tokens,
                'total_cached_tokens': total_cached_tokens,
                'cache_savings_tokens': cache_savings_tokens,
                'cache_savings_percentage': cache_savings_percentage,
                'original_cost': original_cost,
                'cached_cost': total_cached_cost,
                'cost_savings': cost_savings,
                'cost_savings_percentage': cost_savings_percentage,
                'total_interactions': result['total_interactions'],
                'interactions_with_cache': result['interactions_with_cache'],
                'interactions_without_cache': result['interactions_without_cache'],
                'cache_evolution': json.dumps(cache_evolution)
            }, conn)

    def get_top_cache_savings(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get queries with highest token cache savings."""
        cursor = self._execute("""
            SELECT * FROM token_cache_optimization
            ORDER BY cost_savings DESC
            LIMIT %(limit)s
        """, {'limit': limit})

        return [dict(row) for row in cursor.fetchall()]

    def get_cache_effectiveness_by_model(self) -> List[Dict[str, Any]]:
        """Get token cache effectiveness aggregated by model."""
        cursor = self._execute("""
            SELECT
                model,
                COUNT(*) AS total_interactions,
                SUM(prompt_tokens) AS total_prompt_tokens,
                SUM(cached_tokens) AS total_cached_tokens,
                AVG(CASE WHEN prompt_tokens > 0 THEN cached_tokens::FLOAT / prompt_tokens ELSE 0 END) AS avg_cache_hit_rate,
                SUM(total_cost) AS total_cost
            FROM llm_interactions
            WHERE time > NOW() - INTERVAL '7 days'
            GROUP BY model
            ORDER BY total_interactions DESC
        """)

        return [dict(row) for row in cursor.fetchall()]

    # ========== Cleanup ==========

    def close(self):
        """Close the connection pool."""
        if self.pool:
            self.pool.closeall()
            logger.info("TimescaleDB connection pool closed")

    def __del__(self):
        """Destructor to ensure pool is closed."""
        self.close()


# Convenience function to create client
def create_timescale_client(db_url: str, **kwargs) -> TimescaleDBClient:
    """Create a TimescaleDB client instance."""
    return TimescaleDBClient(db_url, **kwargs)
