"""
Flexible LLM Client wrapper supporting multiple OpenAI-compatible backends.
"""

import os
import requests
from typing import Optional, Dict, Any
from openai import OpenAI, APIError, APIConnectionError, RateLimitError, AuthenticationError
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-5", base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        self.model = model or os.getenv("LLM_MODEL", "gpt-5")
        
        if not self.api_key:
            raise ValueError(
                "LLM API key is required. Set OPENAI_API_KEY or LLM_API_KEY environment variable, "
                "or pass api_key parameter."
            )
        
        client_args = {"api_key": self.api_key}
        if self.base_url:
            client_args["base_url"] = self.base_url
            
        self.client = OpenAI(**client_args)
        self.is_local_backend = self.base_url and ("localhost" in self.base_url or "127.0.0.1" in self.base_url)

    def completion(
        self,
        messages: list[dict[str, str]] | str,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        try:
            if isinstance(messages, str):
                messages = [{"role": "user", "content": messages}]
            elif isinstance(messages, dict):
                messages = [messages]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content

        except AuthenticationError as e:
            raise RuntimeError(
                f"Authentication failed: {str(e)}. Please check your API key. "
                f"Set OPENAI_API_KEY or LLM_API_KEY environment variable."
            )
        except APIConnectionError as e:
            error_msg = f"Failed to connect to LLM backend: {str(e)}"
            if self.base_url:
                error_msg += f"\nConfigured endpoint: {self.base_url}"
                if self.is_local_backend:
                    error_msg += "\nIs your local LLM server running?"
            else:
                error_msg += "\nNo LLM_BASE_URL configured. Using OpenAI default endpoint."
            raise RuntimeError(error_msg)
        except RateLimitError as e:
            raise RuntimeError(
                f"Rate limit exceeded: {str(e)}. "
                f"Please wait and retry, or check your backend's rate limits."
            )
        except APIError as e:
            raise RuntimeError(f"LLM API error: {str(e)}")
        except Exception as e:
            error_msg = f"Unexpected error generating completion: {str(e)}"
            if not self.base_url:
                error_msg += "\nHint: Set LLM_BASE_URL environment variable to use a different backend."
            raise RuntimeError(error_msg)

    def get_config_info(self) -> Dict[str, str]:
        """Get current configuration information for debugging."""
        return {
            "model": self.model,
            "base_url": self.base_url or "OpenAI default",
            "api_key_set": "Yes" if self.api_key else "No",
            "backend_type": "Local" if self.is_local_backend else "Cloud"
        }