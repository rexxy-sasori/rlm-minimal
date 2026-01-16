"""
Root logger for RLM client that tracks model outputs and message changes using Python's logging module.
"""

import logging
from typing import List, Dict
from datetime import datetime


class ColorfulLogger:
    """
    A logger that tracks RLM client interactions with the model using Python's logging module.
    """

    # ANSI color codes
    COLORS = {
        'RESET': '\033[0m',
        'BOLD': '\033[1m',
        'DIM': '\033[2m',
        'RED': '\033[31m',
        'GREEN': '\033[32m',
        'YELLOW': '\033[33m',
        'BLUE': '\033[34m',
        'MAGENTA': '\033[35m',
        'CYAN': '\033[36m',
        'WHITE': '\033[37m',
        'BG_RED': '\033[41m',
        'BG_GREEN': '\033[42m',
        'BG_YELLOW': '\033[43m',
        'BG_BLUE': '\033[44m',
        'BG_MAGENTA': '\033[45m',
        'BG_CYAN': '\033[46m',
    }

    def __init__(self, enabled: bool = True, log_level: int = logging.INFO):
        """
        Initialize the logger.

        Args:
            enabled: Whether logging is enabled
            log_level: Logging level (e.g., logging.DEBUG, logging.INFO)
        """
        self.enabled = enabled
        self.conversation_step = 0
        self.last_messages_length = 0
        self.current_query = ""
        self.session_start_time = None
        self.current_depth = 0

        self.logger = logging.getLogger('RLM')
        self.logger.setLevel(log_level)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if logging is enabled."""
        if not self.enabled:
            return text
        return f"{self.COLORS[color]}{text}{self.COLORS['RESET']}"

    def _print_separator(self, char: str = "=", color: str = "CYAN"):
        """Print a colored separator line."""
        if self.enabled:
            separator = char * 80
            self.logger.info(self._colorize(separator, color))

    def log_query_start(self, query: str):
        """Log the start of a new query."""
        if not self.enabled:
            return

        self.current_query = query
        self.conversation_step = 0
        self.last_messages_length = 0
        self.session_start_time = datetime.now()
        self.current_depth = 0

        self._print_separator("=", "GREEN")
        self.logger.info(self._colorize("STARTING NEW QUERY", "BOLD") + self._colorize(" | ", "DIM") +
                         self._colorize(datetime.now().strftime("%H:%M:%S"), "DIM"))
        self._print_separator("=", "GREEN")

        self.logger.info(self._colorize("QUERY:", "BOLD") + f" {query}")
        self.logger.info("")

    def log_initial_messages(self, messages: List[Dict[str, str]]):
        """Log the initial messages setup."""
        if not self.enabled:
            return

        self.logger.info(self._colorize("INITIAL MESSAGES SETUP:", "BOLD"))
        for i, msg in enumerate(messages):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')

            if len(content) > 2000:
                content = content[:2000] + "..."

            role_color = "BLUE" if role == "user" else "MAGENTA" if role == "assistant" else "YELLOW"
            self.logger.info(f"  {self._colorize(f'[{i+1}] {role.upper()}:', role_color)} {content}")

        self.logger.info("")
        self.last_messages_length = len(messages)

    def log_model_response(self, response: str, has_tool_calls: bool):
        """Log the model's response."""
        if not self.enabled:
            return

        self.conversation_step += 1

        self.logger.info(self._colorize(f"MODEL RESPONSE (Step {self.conversation_step}):", "BOLD"))

        display_response = response
        if len(response) > 500:
            display_response = response[:500] + "..."

        self.logger.info(f"  {self._colorize('Response:', 'CYAN')} {display_response}")

        if has_tool_calls:
            self.logger.info(self._colorize("  Contains tool calls - will execute them", "YELLOW"))
        else:
            self.logger.info(self._colorize("  No tool calls - final response", "GREEN"))

        self.logger.info("")

    def log_tool_execution(self, tool_call_str: str, tool_result: str):
        """Log tool execution and result."""
        if not self.enabled:
            return

        self.logger.info(self._colorize("TOOL EXECUTION:", "BOLD"))
        self.logger.info(f"  {self._colorize('Call:', 'YELLOW')} {tool_call_str}")

        display_result = tool_result
        if len(tool_result) > 300:
            display_result = tool_result[:300] + "..."

        self.logger.info(f"  {self._colorize('Result:', 'GREEN')} {display_result}")
        self.logger.info("")

    def log_final_response(self, response: str):
        """Log the final response from the model."""
        if not self.enabled:
            return

        self._print_separator("=", "GREEN")
        self.logger.info(self._colorize("FINAL RESPONSE:", "BOLD"))
        self._print_separator("=", "GREEN")
        self.logger.info(response)
        self._print_separator("=", "GREEN")
        self.logger.info("")
