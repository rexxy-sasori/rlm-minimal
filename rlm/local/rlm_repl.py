"""
Simple Recursive Language Model (RLM) with REPL environment.
"""

from typing import Dict, List, Optional, Any 

from rlm import RLM
from rlm.local.repl import REPLEnv
from rlm.utils.llm import LLMClient
from rlm.utils.prompts import DEFAULT_QUERY, next_action_prompt, build_system_prompt
import rlm.utils.utils as utils

from rlm.logger.root_logger import ColorfulLogger
from rlm.logger.repl_logger import REPLEnvLogger


class RLM_REPL(RLM):
    """
    LLM Client that can handle long contexts by recursively calling itself.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model: Optional[str] = None,
                 base_url: Optional[str] = None,
                 recursive_models: Optional[List[str]] = None,
                 recursive_base_urls: Optional[List[str]] = None,
                 max_iterations: int = 20,
                 max_depth: int = 1,
                 current_depth: int = 0,
                 enable_logging: bool = False,
                 repl_factory: Optional[Any] = None,
                 ):
        import os
        self.api_key = api_key
        self.model = model or os.getenv("LLM_MODEL", "gpt-5")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        
        # Initialize recursive models list with backward compatibility
        default_recursive_model = os.getenv("LLM_RECURSIVE_MODEL", "gpt-5-mini")
        default_recursive_base_url = os.getenv("LLM_RECURSIVE_BASE_URL") or os.getenv("LLM_BASE_URL")
        
        self.recursive_models = recursive_models or [default_recursive_model]
        self.recursive_base_urls = recursive_base_urls or ([default_recursive_base_url] if default_recursive_base_url else [])
        
        self.llm = LLMClient(api_key, self.model, self.base_url) # Replace with other client
        
        # Track recursive call depth to prevent infinite loops
        self.repl_env = None
        self.max_depth = max_depth  # Maximum recursion depth allowed
        self.current_depth = current_depth  # Current depth level (0 = root, 1 = first recursive call, etc.)
        self._max_iterations = max_iterations
        
        # Initialize colorful logger
        self.logger = ColorfulLogger(enabled=enable_logging)
        self.repl_env_logger = REPLEnvLogger(enabled=enable_logging)
        
        self.messages = [] # Initialize messages list
        self.query = None
        
        # REPL factory for creating environments (supports sidecar)
        self.repl_factory = repl_factory
    
    def setup_context(self, context: List[str] | str | List[Dict[str, str]], query: Optional[str] = None):
        """
        Setup the context for the RLMClient.

        Args:
            context: The large context to analyze in the form of a list of messages, string, or Dict
            query: The user's question
        """
        if query is None:
            query = DEFAULT_QUERY

        self.query = query
        self.logger.log_query_start(query)

        # Initialize the conversation with the REPL prompt
        self.messages = build_system_prompt()
        self.logger.log_initial_messages(self.messages)
        
        # Initialize REPL environment with context data
        context_data, context_str = utils.convert_context_for_repl(context)
        
        if self.repl_factory:
            # Use factory to create REPL environment (supports sidecar)
            self.repl_env = self.repl_factory.create_repl_env()
            # Pass context to the environment
            if hasattr(self.repl_env, 'set_context'):
                self.repl_env.set_context(context_data, context_str)
        else:
            # Default to local REPL environment
            self.repl_env = REPLEnv(
                context_json=context_data, 
                context_str=context_str, 
                recursive_models=self.recursive_models,
                recursive_base_urls=self.recursive_base_urls,
                max_depth=self.max_depth,
                current_depth=self.current_depth,
                api_key=self.api_key,
            )
        
        return self.messages

    def completion(self, context: List[str] | str | List[Dict[str, str]], query: Optional[str] = None) -> str:
        """
        Given a query and a (potentially long) context, recursively call the LM
        to explore the context and provide an answer using a REPL environment.
        """
        self.messages = self.setup_context(context, query)
        
        # Main loop runs for fixed # of root LM iterations
        for i in range(self._max_iterations):
            # Get response from LLM
            response = self.llm.get_completion(self.messages)
            
            # Add response to conversation history
            self.messages.append({"role": "assistant", "content": response})
            self.logger.log_assistant_response(response)
            
            # Check if LLM wants to use REPL
            if "REPL" in response:
                # Extract code to execute
                code = utils.extract_code(response)
                if code:
                    self.logger.log_execution_start(code)
                    
                    # Execute code in REPL environment
                    try:
                        result = self.repl_env.code_execution(code)
                        self.logger.log_execution_result(result)
                    except Exception as e:
                        result = {"error": str(e)}
                        self.logger.log_execution_error(str(e))
                    
                    # Add REPL result to conversation
                    repl_result = f"REPL Result: {str(result)}"
                    self.messages.append({"role": "user", "content": repl_result})
                    self.logger.log_repl_result(repl_result)
            elif "Final Answer:" in response:
                # Extract final answer
                final_answer = utils.extract_final_answer(response)
                self.logger.log_final_answer(final_answer)
                
                # Cleanup REPL environment
                if self.repl_env and hasattr(self.repl_env, 'cleanup'):
                    import asyncio
                    asyncio.run(self.repl_env.cleanup())
                
                return final_answer
        
        # If max iterations reached without final answer
        return "The model was unable to provide a final answer within the maximum number of iterations."

    def cost_summary(self) -> dict[str, float]:
        """Return cost summary."""
        return {"total_cost": 0.0}  # Placeholder

    def reset(self):
        """Reset RLM state."""
        self.messages = []
        self.query = None
        self.repl_env = None
