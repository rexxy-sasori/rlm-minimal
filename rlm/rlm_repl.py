"""
Simple Recursive Language Model (RLM) with REPL environment.
"""

from typing import Dict, List, Optional, Any 

from rlm import RLM
from rlm.repl import REPLEnv
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
                 depth: int = 1,
                 enable_logging: bool = False,
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
        self.depth = depth  # 1 = single layer of sub-calls, 2 = two layers, etc.
        self._max_iterations = max_iterations
        
        # Initialize colorful logger
        self.logger = ColorfulLogger(enabled=enable_logging)
        self.repl_env_logger = REPLEnvLogger(enabled=enable_logging)
        
        self.messages = [] # Initialize messages list
        self.query = None
    
    def get_recursive_model_for_depth(self, depth_level: int) -> str:
        """Get the model for a specific recursive depth level.
        
        Args:
            depth_level: The depth level (1-based index for recursive calls)
            
        Returns:
            The model name for that depth level
        """
        if depth_level <= len(self.recursive_models):
            return self.recursive_models[depth_level - 1]
        return self.recursive_models[-1]
    
    def get_recursive_base_url_for_depth(self, depth_level: int) -> Optional[str]:
        """Get the base URL for a specific recursive depth level.
        
        Args:
            depth_level: The depth level (1-based index for recursive calls)
            
        Returns:
            The base URL for that depth level, or None if not configured
        """
        if depth_level <= len(self.recursive_base_urls):
            return self.recursive_base_urls[depth_level - 1]
        return self.recursive_base_urls[-1] if self.recursive_base_urls else None
    
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
        
        self.repl_env = REPLEnv(
            context_json=context_data, 
            context_str=context_str, 
            recursive_models=self.recursive_models,
            recursive_base_urls=self.recursive_base_urls,
            depth=self.depth,
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
        for iteration in range(self._max_iterations):
            
            # Query root LM to interact with REPL environment
            response = self.llm.completion(self.messages + [next_action_prompt(query, iteration)])
            
            # Check for code blocks
            code_blocks = utils.find_code_blocks(response)
            self.logger.log_model_response(response, has_tool_calls=code_blocks is not None)
            
            # Process code execution or add assistant message
            if code_blocks is not None:
                self.messages = utils.process_code_execution(
                    response, self.messages, self.repl_env, 
                    self.repl_env_logger, self.logger
                )
            else:
                # Add assistant message when there are no code blocks
                assistant_message = {"role": "assistant", "content": "You responded with:\n" + response}
                self.messages.append(assistant_message)
            
            # Check that model produced a final answer
            final_answer = utils.check_for_final_answer(
                response, self.repl_env, self.logger,
            )

            # In practice, you may need some guardrails here.
            if final_answer:
                self.logger.log_final_response(final_answer)
                return final_answer

            
        # If we reach here, no final answer was found in any iteration
        print("No final answer found in any iteration")
        self.messages.append(next_action_prompt(query, iteration, final_answer=True))
        final_answer = self.llm.completion(self.messages)
        self.logger.log_final_response(final_answer)

        return final_answer
    
    def cost_summary(self) -> Dict[str, Any]:
        """Get the cost summary of the Root LM + Sub-RLM Calls."""
        raise NotImplementedError("Cost tracking not implemented for RLM REPL.")

    def reset(self):
        """Reset the (REPL) environment and message history."""
        self.repl_env = REPLEnv()
        self.messages = []
        self.query = None


if __name__ == "__main__":
    pass
