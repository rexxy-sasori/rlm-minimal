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
    event_type: str
    event_subtype: Optional[str] = None
    duration_ms: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    iteration: Optional[int] = None
    depth: Optional[int] = None
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
    model: str
    model_type: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    duration_ms: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    context_messages: Optional[int] = None
    context_tokens: Optional[int] = None
    response_length: Optional[int] = None
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
    execution_number: int
    code: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    output_length: Optional[int] = None
    duration_ms: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
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
                   iteration: Optional[int] = None, depth: Optional[int] = None):
        """
        Set current logging context.

        Args:
            query_id: Query identifier from benchmark dataset
            run_id: Run identifier (timestamp from main script)
            iteration: Current conversation iteration
            depth: Current recursion depth
        """
        if query_id is not None:
            self._current_query_id = query_id
        if run_id is not None:
            self._current_run_id = run_id
        if iteration is not None:
            self._current_iteration = iteration
        if depth is not None:
            self._current_depth = depth

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

        query = """
            INSERT INTO latency_events (
                time, query_id, run_id, event_type, event_subtype,
                duration_ms, start_time, end_time, iteration, depth,
                metadata, success, error_message, error_type,
                source_component, source_function
            ) VALUES (
                %(time)s, %(query_id)s, %(run_id)s, %(event_type)s, %(event_subtype)s,
                %(duration_ms)s, %(start_time)s, %(end_time)s, %(iteration)s, %(depth)s,
                %(metadata)s, %(success)s, %(error_message)s, %(error_type)s,
                %(source_component)s, %(source_function)s
            ) RETURNING event_id
        """

        params = {
            'time': datetime.now(timezone.utc),
            'query_id': record.query_id or self._current_query_id,
            'run_id': record.run_id or self._current_run_id,
            'event_type': record.event_type,
            'event_subtype': record.event_subtype,
            'duration_ms': record.duration_ms,
            'start_time': record.start_time,
            'end_time': record.end_time,
            'iteration': record.iteration or self._current_iteration,
            'depth': record.depth or self._current_depth,
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

        query = """
            INSERT INTO llm_interactions (
                time, query_id, run_id, model, model_type,
                prompt_tokens, completion_tokens, total_tokens,
                duration_ms, start_time, end_time,
                context_messages, context_tokens, response_length,
                has_tool_calls, tool_call_count, success,
                error_message, error_type, metadata
            ) VALUES (
                %(time)s, %(query_id)s, %(run_id)s, %(model)s, %(model_type)s,
                %(prompt_tokens)s, %(completion_tokens)s, %(total_tokens)s,
                %(duration_ms)s, %(start_time)s, %(end_time)s,
                %(context_messages)s, %(context_tokens)s, %(response_length)s,
                %(has_tool_calls)s, %(tool_call_count)s, %(success)s,
                %(error_message)s, %(error_type)s, %(metadata)s
            ) RETURNING interaction_id
        """

        params = {
            'time': datetime.now(timezone.utc),
            'query_id': record.query_id or self._current_query_id,
            'run_id': record.run_id or self._current_run_id,
            'model': record.model,
            'model_type': record.model_type,
            'prompt_tokens': record.prompt_tokens,
            'completion_tokens': record.completion_tokens,
            'total_tokens': record.total_tokens,
            'duration_ms': record.duration_ms,
            'start_time': record.start_time,
            'end_time': record.end_time,
            'context_messages': record.context_messages,
            'context_tokens': record.context_tokens,
            'response_length': record.response_length,
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
                event_type=event_type,
                event_subtype=event_subtype,
                duration_ms=duration_ms,
                start_time=start_time,
                end_time=end_time,
                iteration=self._current_iteration,
                depth=self._current_depth,
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
