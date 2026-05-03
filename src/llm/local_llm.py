#!/usr/bin/env python3
"""
Local LLM Test using GGUF models via llama-cpp-python on Raspberry Pi 5
Tests local LLM models running via llama.cpp backend for text generation.
"""

import time
import os
import json
import re
from clients.crypto_trade import execute_crypto_trade
import torch
from llama_cpp import Llama
from utils.web_search import web_search, get_apnews_article_titles
from clients.moltbook import MoltbookClient
from clients.gmail import GmailClient, get_system_info
from clients.generate_image import HuggingFaceImageGenerator
from clients.image_captioning import LocalImageCaptioner
from utils.tracking_api import status_update, login, get_indicators
from llm.prompts import build_initial_prompt, build_intermediate_prompt, build_final_prompt, build_crypto_prompt
from llm.utils import ToolCallHandler
import logging
from utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class LocalLLM:
    def __init__(self, model_path=None, n_ctx=8192, n_threads=3):  # Conservative settings for 6GB Pi
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.model = None
        self.attachments = []
        
        # Use shared ToolCallHandler for tool call parsing, deduplication, and response cleaning
        self.tool_handler = ToolCallHandler()
        self.tools_enabled = self.tool_handler.tools_enabled
        self.tool_call_memo = self.tool_handler.tool_call_memo
        self.generated_images = self.tool_handler.generated_images

        # Initialize MoltbookClient
        try:
            self.moltbook_client = MoltbookClient()
        except ValueError as e:
            logger.warning(f"⚠️ MoltbookClient not available: {e}")
            self.moltbook_client = None
        
        # Initialize GmailClient
        try:
            self.gmail_client = GmailClient()
        except ValueError as e:
            logger.warning(f"⚠️ GmailClient not available: {e}")
            self.gmail_client = None
        
        # Initialize LocalImageCaptioner
        try:
            self.image_captioner = LocalImageCaptioner()
        except ValueError as e:
            logger.warning(f"⚠️ LocalImageCaptioner not available: {e}")
            self.image_captioner = None
        
        logger.info(f"Local LLM Configuration:")
        logger.info(f"  Model Path: {self.model_path}")
        logger.info(f"  Context Length: {self.n_ctx}")
        logger.info(f"  CPU Threads: {self.n_threads}")
        logger.info(f"  Tools Enabled: {self.tools_enabled}")

        self.load_model()
    
    def set_tools_enabled(self, enabled):
        """Enable or disable tool functionality"""
        self.tool_handler.set_tools_enabled(enabled)
        self.tools_enabled = self.tool_handler.tools_enabled
    
    def reset_session(self):
        """Reset generated images and tool call memo for a new session"""
        self.tool_handler.reset_session()
        self.generated_images = self.tool_handler.generated_images
        self.tool_call_memo = self.tool_handler.tool_call_memo
    
    def _temporarily_unload_llm(self):
        """Temporarily unload LLM to free RAM for image processing"""
        if self.model is not None:
            logger.info("📋 Temporarily unloading LLM to free RAM for image processing...")
            # Store model path for reloading
            self._stored_model_path = self.model_path
            del self.model
            self.model = None
            
            # Force garbage collection
            import gc
            gc.collect()
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info("✅ LLM temporarily unloaded")
            return True
        return False
    
    def _reload_llm(self):
        """Reload LLM after image processing"""
        if self.model is None and hasattr(self, '_stored_model_path'):
            logger.info("🔄 Reloading LLM...")
            self.model_path = self._stored_model_path
            success = self.load_model()
            if success:
                logger.info("✅ LLM reloaded successfully")
            return success
        return True  # Already loaded

    def find_model_file(self):
        logger.info("🔍 Searching for model files...")
        
        # Search paths: containerized path first, then local development path
        search_paths = [
            "/app/models",  # Docker container mounted path
            os.path.expanduser("~/models")  # Local development path
        ]
        
        # Try 128k model first, fall back to 4k, and include the fine-tuned variant
        models_to_try = [
            "Phi-3-mini-128k-instruct-q4.gguf",
            "Phi-3-mini-128k-instruct-Q4_K_M.gguf",  # Alternative 128k model
            "Phi-3-mini-4k-instruct-q4.gguf"
        ]
        
        for search_path in search_paths:
            logger.info(f"🔍 Searching in: {search_path}")
            if os.path.exists(search_path):
                for model_name in models_to_try:
                    full_path = os.path.join(search_path, model_name)
                    if os.path.exists(full_path):
                        logger.info(f"✅ Found model: {full_path}")
                        return full_path
            else:
                logger.debug(f"📁 Directory not found: {search_path}")

        logger.error("❌ No model files found in common locations")
        logger.info("Searched in the following directories:")
        for path in search_paths:
            logger.info(f"  - {path}")
        logger.info("To download a model:")
        logger.info("  mkdir -p ~/models")
        logger.info("  cd ~/models")
        logger.info("  # Download a small model (TinyLlama ~600MB):")
        logger.info("  wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.q4_0.gguf")
        logger.info("  # Or download Phi-3-mini (~2.4GB):")
        logger.info("  wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf")
        logger.info("  # Or download Phi-3-mini 128k context (~2.4GB):")
        logger.info("  wget https://huggingface.co/microsoft/Phi-3-mini-128k-instruct-gguf/resolve/main/Phi-3-mini-128k-instruct-q4.gguf")
        
        return None
    
    def load_model(self):
        """Load the GGUF model"""
        logger.info("🔄 Loading model... (this may take a few minutes)")
        start_time = time.time()
        
        # Find model if not specified
        if self.model_path is None:
            self.model_path = self.find_model_file()
            if self.model_path is None:
                return False
        
        try:
            # Try with conservative settings for Pi
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                verbose=False,  # Reduce output noise
                use_mmap=True,
                use_mlock=False,  # Don't lock memory on Pi
                n_gpu_layers=0   # Force CPU-only for stability
            )
            
            load_time = time.time() - start_time
            logger.info(f"✅ Model loaded successfully in {load_time:.1f} seconds")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load model with default settings: {e}")
            logger.info("🔄 Trying with progressively smaller contexts to find optimal size...")
            
            # Try different context sizes to find what fits in available RAM
            context_sizes_to_try = [4096, 2048, 1024]  # 4k, 2k, 1k - very conservative for Pi
            
            for ctx_size in context_sizes_to_try:
                try:
                    logger.info(f"🔄 Trying {ctx_size//1024}k context...")
                    self.model = Llama(
                        model_path=self.model_path,
                        n_ctx=ctx_size,
                        n_threads=self.n_threads,
                        verbose=False,
                        use_mmap=True,
                        use_mlock=False,
                        n_gpu_layers=0  # Force CPU-only
                    )
                    
                    self.n_ctx = ctx_size
                    load_time = time.time() - start_time
                    logger.info(f"✅ Model loaded successfully with {ctx_size//1024}k context in {load_time:.1f} seconds")
                    logger.info(f"🎯 Optimal context size for your 6GB RAM: {ctx_size//1024}k tokens")
                    return True
                    
                except Exception as ctx_e:
                    logger.error(f"❌ {ctx_size//1024}k context failed: insufficient memory")
                    continue
    
    def execute_prompt(self, prompt, max_tokens=2048, temperature=0.7, stop=None):
        try:
            cleaned_prompt = self.truncate_to_context(prompt)

            # Generate response
            output = self.model(
                cleaned_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop or ["<|end|>"],
                echo=False
            )
            
            response = output['choices'][0]['text'].strip()
            return response
        except Exception as e:
            logger.error(f"❌ Error during generation: {e}")
            return "Sorry, I encountered an error while generating a response."
    
    def process_tool_calls(self, tool_calls, use_crypto_prompt=False):
        """Process tool calls using the shared handler"""
        return self.tool_handler.process_tool_calls(
            tool_calls, 
            self.execute_tool_call, 
            use_crypto_prompt=use_crypto_prompt
        )

    def prompt(self, prompt, max_tokens=2048, temperature=0.7, stop=None, max_tool_iterations=3, final_query=True, use_crypto_prompt=False, request_history=None):
        """Generate a response using the loaded model with tool call support"""
        if self.model is None:
            logger.error("❌ Model not loaded. Call load_model() first.")
            return None
        
        # Reset session at the beginning of each prompt
        self.reset_session()

        if use_crypto_prompt:
            token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
            indicators = get_indicators(token)
            indicators = indicators['indicators']
            self.indicators = indicators  # Store indicators for tool calls to access
        
        # LLM Call
        logger.info(f"🤔 Generating response for: \"{prompt[:50]}...\"")
        if not use_crypto_prompt:
            response = self.execute_prompt(build_initial_prompt(self.attachments, prompt, request_history), max_tokens, temperature, stop)
        else:
            response = self.execute_prompt(build_crypto_prompt("None", "None", indicators), max_tokens, temperature, stop)
        
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
            tool_results = self.process_tool_calls(tool_calls, use_crypto_prompt)

            # LLM call to summarize convo history
            history = f"{history}\nIteration {iteration_count} Tool Calls:\n{json.dumps(tool_calls, indent=2)}\nIteration {iteration_count} Tool Results:\n{tool_results}"
            # logger.debug(f"Summary thus far: {history}")
            logger.info(f"✅ Tool calls executed. Building final response with tool results...")

            # Intermediate LLM call (in loop)
            if not use_crypto_prompt:
                response = self.execute_prompt(build_intermediate_prompt(self.attachments, prompt, tool_results, iteration_count, history, request_history), max_tokens, temperature, stop)
            else:
                response = self.execute_prompt(build_crypto_prompt(tool_results, history, indicators), max_tokens, temperature, stop)

            tool_calls = self.tool_handler.parse_tool_calls(response)

        # Final LLM call
        if final_query:
            response = self.execute_prompt(build_final_prompt(self.attachments, prompt, tool_results, history, request_history), max_tokens, temperature, stop)
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
    
    def estimate_tokens(self, text):
        """Rough estimate of token count (approximately 3 characters per token)"""
        return len(text) // 3
    
    def truncate_to_context(self, conversation, max_tokens_for_response=2048):
        """Truncate conversation to fit within context window, leaving room for response"""
        max_context_tokens = self.n_ctx - max_tokens_for_response
        estimated_tokens = self.estimate_tokens(conversation)
        
        if estimated_tokens <= max_context_tokens:
            return conversation
        
        logger.warning(f"⚠️ Context too long ({estimated_tokens} tokens), truncating to fit...")
        
        # Calculate how many characters to keep (roughly)
        max_chars = max_context_tokens * 3
        
        # Try to truncate at a reasonable boundary
        if len(conversation) > max_chars:
            truncated = conversation[:max_chars]
            # Try to end at a sentence or line break
            last_sentence = max(truncated.rfind('.'), truncated.rfind('\n'))
            if last_sentence > max_chars * 0.8:  # If we find a good break point
                truncated = truncated[:last_sentence + 1]
            
            return truncated + "\n\n[Content truncated to fit context window]"
        
        return conversation
       
    def execute_tool_call(self, tool_name, parameters, use_crypto_prompt=False):
        """Execute a tool call and return the result"""
        logger.info(f"🔧 Executing tool call: {tool_name} with parameters {parameters}")
        if tool_name == "web_search":
            query = parameters.get('query', '')
            if query:
                results = web_search(query)
                # Format results for the LLM with actual content that's useful
                formatted_results = []
                for i, result in enumerate(results, 1):
                    # Use less content to stay within context limits
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
                
                # Generate the image
                image_client = HuggingFaceImageGenerator()
                result = image_client.generate_and_save(prompt)
                self.generated_images.append(result)  # Keep track of generated images in this session
                
                if result:
                    # Result is file path when save=True
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
                
                # Modify the image
                image_client = HuggingFaceImageGenerator()
                result = image_client.modify_and_save(image_path, prompt, strength=strength)
                
                if result:
                    self.generated_images.append(result)  # Keep track of modified images
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
                    return "❌ Error: Local image captioning not available. Install required packages: pip install torch transformers pillow"
                
                logger.info(f"📝 Generating caption for: {image_path}")
                
                # Temporarily unload LLM to free RAM
                llm_was_loaded = self._temporarily_unload_llm()
                
                try:
                    # Generate caption using local model
                    caption = self.image_captioner.caption_image(image_path, auto_unload=True)
                    
                    # Reload LLM
                    if llm_was_loaded:
                        self._reload_llm()
                    
                    if "❌" in caption:
                        return caption  # Return error message as-is
                    else:
                        return f"✅ Image caption generated!\n📸 Image: {image_path}\n📝 Caption: {caption}"
                        
                except Exception as e:
                    # Always try to reload LLM on error
                    if llm_was_loaded:
                        self._reload_llm()
                    raise e
                    
            except Exception as e:
                return f"❌ Failed to caption image: {e}"
        
        elif tool_name == "analyze_image":
            try:
                image_path = parameters.get('image_path')
                question = parameters.get('question')
                
                if not image_path or not question:
                    return "❌ Error: Both image_path and question are required"
                
                if self.image_captioner is None:
                    return "❌ Error: Local image captioning not available. Install required packages: pip install torch transformers pillow"
                
                logger.info(f"🔍 Analyzing image: {image_path} with question: {question}")
                
                # Temporarily unload LLM to free RAM
                llm_was_loaded = self._temporarily_unload_llm()
                
                try:
                    # Analyze image using local model
                    answer = self.image_captioner.analyze_image_with_question(image_path, question, auto_unload=True)
                    
                    # Reload LLM
                    if llm_was_loaded:
                        self._reload_llm()
                    
                    if "❌" in answer:
                        return answer  # Return error message as-is
                    else:
                        return f"✅ Image analysis completed!\n📸 Image: {image_path}\n❓ Question: {question}\n💬 Answer: {answer}"
                        
                except Exception as e:
                    # Always try to reload LLM on error
                    if llm_was_loaded:
                        self._reload_llm()
                    raise e
                    
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
    
    def parse_tool_calls(self, text):
        """Parse tool calls from LLM response - delegates to shared ToolCallHandler"""
        return self.tool_handler.parse_tool_calls(text)
    
    def clean_response(self, response):
        """Clean up the response - delegates to shared ToolCallHandler"""
        return self.tool_handler.clean_response(response)
