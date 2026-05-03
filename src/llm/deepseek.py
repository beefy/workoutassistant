#!/usr/bin/env python3
"""
DeepSeek LLM Integration
Uses the DeepSeek API to make prompts and get responses,
with the same tool call functionality as LocalLLM.
"""

import os
import json
import time
import logging
from typing import List, Dict, Any, Optional, Callable
from utils.logging_config import setup_logging
from llm.utils import ToolCallHandler
from llm.prompts import build_initial_prompt, build_intermediate_prompt, build_final_prompt, build_crypto_prompt
from clients.crypto_trade import execute_crypto_trade
from utils.web_search import web_search, get_apnews_article_titles
from clients.moltbook import MoltbookClient
from clients.gmail import GmailClient, get_system_info
from clients.generate_image import HuggingFaceImageGenerator
from clients.image_captioning import LocalImageCaptioner
from utils.tracking_api import status_update, login, get_indicators

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class DeepSeekLLM:
    """
    DeepSeek LLM integration using the DeepSeek API.
    Supports the same tool call interface as LocalLLM.
    """
    
    # Available DeepSeek models
    MODELS = {
        "deepseek-chat": "deepseek-chat",  # General purpose (V3)
        "deepseek-reasoner": "deepseek-reasoner",  # Reasoning (R1)
    }
    
    def __init__(self, model: str = "deepseek-chat", api_key: Optional[str] = None, 
                 base_url: str = "https://api.deepseek.com", max_retries: int = 3):
        """
        Initialize the DeepSeek LLM client.
        
        Args:
            model: Model name to use (default: deepseek-chat)
            api_key: DeepSeek API key (defaults to DEEPSEEK_API_KEY env var)
            base_url: API base URL (default: https://api.deepseek.com)
            max_retries: Maximum number of retries on API failure
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DeepSeek API key is required. Set DEEPSEEK_API_KEY environment variable "
                "or pass api_key to the constructor."
            )
        
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.max_retries = max_retries
        
        # Tool call handler (shared utilities)
        self.tool_handler = ToolCallHandler()
        self.generated_images = self.tool_handler.generated_images
        self.tools_enabled = self.tool_handler.tools_enabled
        
        # Initialize clients
        try:
            self.moltbook_client = MoltbookClient()
        except ValueError as e:
            logger.warning(f"⚠️ MoltbookClient not available: {e}")
            self.moltbook_client = None
        
        try:
            self.gmail_client = GmailClient()
        except ValueError as e:
            logger.warning(f"⚠️ GmailClient not available: {e}")
            self.gmail_client = None
        
        try:
            self.image_captioner = LocalImageCaptioner()
        except ValueError as e:
            logger.warning(f"⚠️ LocalImageCaptioner not available: {e}")
            self.image_captioner = None
        
        self.indicators = None  # For crypto trading
        
        logger.info(f"DeepSeek LLM Configuration:")
        logger.info(f"  Model: {self.model}")
        logger.info(f"  Base URL: {self.base_url}")
        logger.info(f"  Max Retries: {self.max_retries}")
    
    def set_tools_enabled(self, enabled: bool):
        """Enable or disable tool functionality"""
        self.tool_handler.set_tools_enabled(enabled)
        self.tools_enabled = self.tool_handler.tools_enabled
    
    def reset_session(self):
        """Reset generated images and tool call memo for a new session"""
        self.tool_handler.reset_session()
        self.generated_images = self.tool_handler.generated_images
    
    def _make_api_request(self, messages: List[Dict[str, str]], 
                          max_tokens: int = 2048, 
                          temperature: float = 0.7) -> str:
        """
        Make a request to the DeepSeek API.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            max_tokens: Maximum tokens in the response
            temperature: Sampling temperature
            
        Returns:
            Response text from the API
        """
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.info(f"📡 DeepSeek API request (attempt {attempt + 1}/{self.max_retries})")
                response = requests.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=120
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content']
                    logger.info(f"✅ DeepSeek API response received ({len(content)} chars)")
                    return content
                elif response.status_code == 429:
                    logger.warning(f"⚠️ Rate limited, retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    error_msg = f"API error {response.status_code}: {response.text}"
                    logger.error(f"❌ {error_msg}")
                    last_error = error_msg
                    
                    # Don't retry on 4xx errors (except 429)
                    if 400 <= response.status_code < 500 and response.status_code != 429:
                        break
                    
            except requests.exceptions.Timeout:
                logger.warning(f"⚠️ Request timed out (attempt {attempt + 1})")
                last_error = "Request timed out"
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"⚠️ Connection error (attempt {attempt + 1}): {e}")
                last_error = f"Connection error: {e}"
            except Exception as e:
                logger.error(f"❌ Unexpected API error: {e}")
                last_error = str(e)
                break
            
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"⏳ Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
        
        raise RuntimeError(f"DeepSeek API request failed after {self.max_retries} attempts: {last_error}")
    
    def execute_prompt(self, prompt: str, max_tokens: int = 2048, 
                       temperature: float = 0.7, stop: Optional[List[str]] = None) -> str:
        """
        Execute a prompt against the DeepSeek API.
        
        Args:
            prompt: The formatted prompt string
            max_tokens: Maximum tokens in the response
            temperature: Sampling temperature
            stop: Optional list of stop sequences
            
        Returns:
            Response text
        """
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        response = self._make_api_request(messages, max_tokens=max_tokens, temperature=temperature)
        return response
    
    def execute_tool_call(self, tool_name: str, parameters: dict, 
                          use_crypto_prompt: bool = False) -> str:
        """
        Execute a tool call and return the result.
        Same tool set as LocalLLM.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters dict
            use_crypto_prompt: Whether crypto trading is enabled
            
        Returns:
            Result string from the tool execution
        """
        logger.info(f"🔧 Executing tool call: {tool_name} with parameters {parameters}")
        
        if tool_name == "web_search":
            query = parameters.get('query', '')
            if query:
                results = web_search(query)
                formatted_results = []
                for i, result in enumerate(results, 1):
                    content = result['content'][:800] if result['content'] else result['snippet'][:200]
                    formatted_results.append(
                        f"Source {i}: {result['title']}\n"
                        f"Info: {content}\n"
                        f"URL: {result['url'][:500]}"
                    )
                return "\n\n".join(formatted_results)
            else:
                return "Error: No search query provided"
        
        elif tool_name == "get_news":
            try:
                max_articles = parameters.get('max_articles', 5)
                articles = get_apnews_article_titles(max_articles=max_articles)
                if articles:
                    formatted_articles = []
                    for i, article in enumerate(articles, 1):
                        formatted_articles.append(f"{i}. {article}")
                    return f"AP News Headlines (Top {len(articles)} stories):\n\n" + "\n".join(formatted_articles)
                else:
                    return "No news articles found."
            except Exception as e:
                return f"❌ Failed to get news: {e}"
        
        elif tool_name == "get_system_info":
            try:
                system_info = get_system_info()
                return f"System Information:\n\n{system_info}"
            except Exception as e:
                return f"❌ Failed to get system info: {e}"
        
        elif tool_name == "generate_image":
            try:
                prompt = parameters.get('prompt')
                if not prompt:
                    return "❌ Error: Image prompt is required"
                
                logger.info(f"🎨 Generating image: {prompt[:50]}...")
                image_client = HuggingFaceImageGenerator()
                result = image_client.generate_and_save(prompt)
                self.generated_images.append(result)
                
                if result:
                    return f"✅ Image generated successfully!\n📸 Saved to: {result}\n💡 Prompt: {prompt}"
                else:
                    return f"❌ Failed to generate image for prompt: {prompt}"
            except Exception as e:
                return f"❌ Failed to generate image: {e}"
        
        elif tool_name == "modify_image":
            try:
                image_path = parameters.get('image_path')
                prompt = parameters.get('prompt')
                strength = parameters.get('strength', 0.8)
                
                if not image_path or not prompt:
                    return "❌ Error: Both image_path and prompt are required"
                
                logger.info(f"✏️ Modifying image: {image_path} with prompt: {prompt[:50]}...")
                image_client = HuggingFaceImageGenerator()
                result = image_client.modify_and_save(image_path, prompt, strength=strength)
                
                if result:
                    self.generated_images.append(result)
                    return f"✅ Image modified successfully!\n📸 Original: {image_path}\n📸 Modified: {result}\n💡 Prompt: {prompt}"
                else:
                    return f"❌ Failed to modify image: {image_path} with prompt: {prompt}"
            except Exception as e:
                return f"❌ Failed to modify image: {e}"
        
        elif tool_name == "caption_image":
            try:
                image_path = parameters.get('image_path')
                if not image_path:
                    return "❌ Error: Image path is required"
                if self.image_captioner is None:
                    return "❌ Error: Local image captioning not available."
                
                logger.info(f"📝 Generating caption for: {image_path}")
                caption = self.image_captioner.caption_image(image_path, auto_unload=True)
                
                if "❌" in caption:
                    return caption
                else:
                    return f"✅ Image caption generated!\n📸 Image: {image_path}\n📝 Caption: {caption}"
            except Exception as e:
                return f"❌ Failed to caption image: {e}"
        
        elif tool_name == "analyze_image":
            try:
                image_path = parameters.get('image_path')
                question = parameters.get('question')
                
                if not image_path or not question:
                    return "❌ Error: Both image_path and question are required"
                if self.image_captioner is None:
                    return "❌ Error: Local image captioning not available."
                
                logger.info(f"🔍 Analyzing image: {image_path} with question: {question}")
                answer = self.image_captioner.analyze_image_with_question(image_path, question, auto_unload=True)
                
                if "❌" in answer:
                    return answer
                else:
                    return f"✅ Image analysis completed!\n📸 Image: {image_path}\n❓ Question: {question}\n💬 Answer: {answer}"
            except Exception as e:
                return f"❌ Failed to analyze image: {e}"
        
        elif tool_name == "trade_crypto":
            if not use_crypto_prompt:
                return "❌ Error: Crypto trading is disabled. Use crypto prompt mode to enable trading."
            
            try:
                symbol = parameters.get('token_symbol')
                action = parameters.get('action')
                amount = parameters.get('amount')
                result = execute_crypto_trade(
                    token_symbol=symbol,
                    action=action,
                    amount=amount,
                    indicators=self.indicators
                )
                return f"✅ Trade executed: {action} {amount} of {symbol}\nResult: {result}"
            except Exception as e:
                return f"❌ Failed to execute crypto trade: {e}"
        
        else:
            return f"Error: Unknown tool '{tool_name}'"
    
    def prompt(self, prompt: str, max_tokens: int = 2048, temperature: float = 0.7,
               stop: Optional[List[str]] = None, max_tool_iterations: int = 3,
               final_query: bool = True, use_crypto_prompt: bool = False,
               request_history: Optional[List[Dict[str, str]]] = None,
               attachments: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate a response using the DeepSeek API with tool call support.
        
        Args:
            prompt: The user's prompt
            max_tokens: Maximum tokens in the response
            temperature: Sampling temperature
            stop: Optional list of stop sequences
            max_tool_iterations: Maximum number of tool call iterations
            final_query: Whether this is the final query
            use_crypto_prompt: Whether to use crypto-specific prompting
            request_history: Optional conversation history
            attachments: Optional list of file paths
            
        Returns:
            Dict with 'response' (str) and 'generated_images' (List[str]) keys
        """
        # Reset session at the beginning of each prompt
        self.reset_session()
        
        attachments = attachments or []
        
        if use_crypto_prompt:
            token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
            indicators = get_indicators(token)
            indicators = indicators['indicators']
            self.indicators = indicators
        
        # Initial LLM call
        logger.info(f"🤔 Generating response for: \"{prompt[:50]}...\"")
        if not use_crypto_prompt:
            response = self.execute_prompt(
                build_initial_prompt(attachments, prompt, request_history),
                max_tokens, temperature, stop
            )
        else:
            response = self.execute_prompt(
                build_crypto_prompt("None", "None", indicators),
                max_tokens, temperature, stop
            )
        
        logger.info(f"Initial response generated. Checking for tool calls...")
        
        if not self.tools_enabled:
            logger.warning("⚠️ Tools are disabled, returning response without tool execution")
            return {
                'response': self.tool_handler.clean_response(response),
                'generated_images': self.generated_images.copy()
            }
        
        tool_calls = self.tool_handler.parse_tool_calls(response)
        
        if not tool_calls:
            logger.info("✅ No tool calls found, returning response")
            return {
                'response': self.tool_handler.clean_response(response),
                'generated_images': self.generated_images.copy()
            }
        
        iteration_count = 0
        history = ""
        tool_results = ""
        logger.info(f"🔧 Iteration {iteration_count}: Found {len(tool_calls)} tool call(s)")
        
        while len(tool_calls) > 0 and iteration_count < max_tool_iterations:
            iteration_count += 1
            logger.info(f"🔧 Iteration {iteration_count}: Found {len(tool_calls)} tool call(s)")
            tool_results = self.tool_handler.process_tool_calls(
                tool_calls, self.execute_tool_call, use_crypto_prompt
            )
            
            # Build history
            history = f"{history}\nIteration {iteration_count} Tool Calls:\n{json.dumps(tool_calls, indent=2)}\nIteration {iteration_count} Tool Results:\n{tool_results}"
            logger.info(f"✅ Tool calls executed. Building final response with tool results...")
            
            # Intermediate LLM call
            if not use_crypto_prompt:
                response = self.execute_prompt(
                    build_intermediate_prompt(attachments, prompt, tool_results, iteration_count, history, request_history),
                    max_tokens, temperature, stop
                )
            else:
                response = self.execute_prompt(
                    build_crypto_prompt(tool_results, history, indicators),
                    max_tokens, temperature, stop
                )
            
            tool_calls = self.tool_handler.parse_tool_calls(response)
        
        # Final LLM call
        if final_query:
            response = self.execute_prompt(
                build_final_prompt(attachments, prompt, tool_results, history, request_history),
                max_tokens, temperature, stop
            )
            cleaned_response = self.tool_handler.clean_response(response)
            return {
                'response': cleaned_response,
                'generated_images': self.generated_images.copy()
            }
        else:
            return {
                'response': self.tool_handler.clean_response(response),
                'generated_images': self.generated_images.copy()
            }
