#!/usr/bin/env python3
"""
Local LLM Test using GGUF models via llama-cpp-python on Raspberry Pi 5
Tests local LLM models running via llama.cpp backend for text generation.
"""

import time
import os
import json
import re
from llama_cpp import Llama
from web_search import web_search


class LocalLLM:
    def __init__(self, model_path=None, n_ctx=4096, n_threads=4):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.model = None
        self.tools_enabled = True
        
        # Tool definitions
        self.tools = {
            "web_search": {
                "name": "web_search",
                "description": "Search the web for current information. Use this when you need up-to-date information or facts not in your training data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to look up on the web"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
        
        print(f"Local LLM Configuration:")
        print(f"  Model Path: {self.model_path}")
        print(f"  Context Length: {self.n_ctx}")
        print(f"  CPU Threads: {self.n_threads}")
        print(f"  Tools Enabled: {self.tools_enabled}")

        self.load_model()
    
    def set_tools_enabled(self, enabled):
        """Enable or disable tool functionality"""
        self.tools_enabled = enabled
        print(f"🔧 Tools {'enabled' if enabled else 'disabled'}")

    def find_model_file(self):
        print("\n🔍 Searching for model files...")
        expanded_path = os.path.expanduser("~/models/")
        full_path = os.path.join(expanded_path, "Phi-3-mini-4k-instruct-q4.gguf")
        if os.path.exists(full_path):
            print(f"✅ Found model: {full_path}")
            return full_path

        print("❌ No model files found in common locations")
        print("\nTo download a model:")
        print("  mkdir -p ~/models")
        print("  cd ~/models")
        print("  # Download a small model (TinyLlama ~600MB):")
        print("  wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.q4_0.gguf")
        print("  # Or download Phi-3-mini (~2.4GB):")
        print("  wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf")
        
        return None
    
    def load_model(self):
        """Load the GGUF model"""
        print("🔄 Loading model... (this may take a few minutes)")
        start_time = time.time()
        
        # Find model if not specified
        if self.model_path is None:
            self.model_path = self.find_model_file()
            if self.model_path is None:
                return False
        
        try:
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                verbose=False,  # Reduce output noise
                use_mmap=True,
                use_mlock=False  # Don't lock memory on Pi
            )
            
            load_time = time.time() - start_time
            print(f"✅ Model loaded successfully in {load_time:.1f} seconds")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            print("This may be due to:")
            print("  1. Corrupted model file - try re-downloading")
            print("  2. Incompatible GGUF version - try a different quantization")
            print("  3. Insufficient RAM - try a smaller model")
            return False
    
    def execute_prompt(self, prompt, max_tokens=500, temperature=0.7, stop=None):
        try:
            cleaned_prompt = self.truncate_to_context(prompt, max_tokens)

            # Generate response
            output = self.model(
                cleaned_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop or ["User:"],
                echo=False
            )
            
            response = output['choices'][0]['text'].strip()
            return response
        except Exception as e:
            print(f"❌ Error during generation: {e}")
            return "Sorry, I encountered an error while generating a response."
    
    def process_tool_calls(self, tool_calls):
        try:
            tool_results = []
            for tool_call in tool_calls:
                tool_result = self.execute_tool_call(
                    tool_call['tool'], 
                    tool_call['parameters']
                )
                tool_results.append(tool_result)
            
            combined_results = "\n\n".join(tool_results)
            return combined_results
        except Exception as e:
            print(f"❌ Error during tool execution: {e}")
            return "Sorry, I encountered an error while executing a tool."

    def prompt(self, prompt, max_tokens=500, temperature=0.7, stop=None, max_tool_iterations=3):
        """Generate a response using the loaded model with tool call support"""
        if self.model is None:
            print("❌ Model not loaded. Call load_model() first.")
            return None
        
        # LLM Call
        print(f"🤔 Generating response for: \"{prompt[:50]}...\"")
        response = self.execute_prompt(self._build_tool_prompt(prompt), max_tokens, temperature, stop)
        print(f"Initial response generated. Checking for tool calls...")

        if not self.tools_enabled:
            print("⚠️  Tools are disabled, returning response without tool execution")
            return self.clean_response(response)

        tool_calls = self.parse_tool_calls(response)
        if not tool_calls:
            print("✅ No tool calls found, returning response")
            return self.clean_response(response)

        print(f"🔧 Found {len(tool_calls)} tool call(s)")
        tool_results = self.process_tool_calls(tool_calls)
        print(f"✅ Tool calls executed. Building final response with tool results...")

        # LLM Call with tool results
        response = self.execute_prompt(self._build_secondary_prompt(prompt, response, tool_results), max_tokens, temperature, stop)

        cleaned_response = self.clean_response(response)
        return cleaned_response    
    
    def _build_tool_prompt(self, user_prompt):
        """Build a prompt that includes tool instructions"""
        if not self.tools_enabled:
            return user_prompt
        
        tool_instructions = """
You are an AI assistant that replies to user questions that are submitted over email. Your response is directly emailed back to the user with your entire response text as the email body.

You have access to web search. If you need current information or facts not in your knowledge, use:
[TOOL:web_search]{"query": "your search terms here"}

If you can answer without web search, respond directly. Do not use a tool call unless you need to, to save time and energy. Do not prefix your response with anything like "Response:" or "Answer:" because that will be shown to the user. Just provide the answer ONLY. Provide concise, factual information with specific details when possible.
Please keep your response short because the context window is limited.
Thank you!

Your Response:
        """
        
        return f"Tool Instructions:\n{tool_instructions}\nUser Prompt: {user_prompt}\n\nYour Response: "
    
    def _build_secondary_prompt(self, original_prompt, initial_response, tool_results):
        """Build a prompt for the second LLM call that includes tool results"""
        return f"""Original Prompt: "{original_prompt}"
Additional Info: "{tool_results}"
Additional Instructions: You are an AI assistant that replies to user questions that are submitted over email. Your next response is directly emailed back to the user with your entire response text as the email body. Using the specific information above, provide a complete and helpful answer to the original prompt with actual details (like numbers, temperatures, conditions, etc.). Please keep your response short because the context window is limited. Do not repeat the original question in your answer. Just provide the answer ONLY. Thank you!
Your Final Response:
        """
    
    def estimate_tokens(self, text):
        """Rough estimate of token count (approximately 4 characters per token)"""
        return len(text) // 4
    
    def truncate_to_context(self, conversation, max_tokens_for_response=500):
        """Truncate conversation to fit within context window, leaving room for response"""
        max_context_tokens = self.n_ctx - max_tokens_for_response
        estimated_tokens = self.estimate_tokens(conversation)
        
        if estimated_tokens <= max_context_tokens:
            return conversation
        
        print(f"⚠️  Context too long ({estimated_tokens} tokens), truncating to fit...")
        
        # Calculate how many characters to keep (roughly)
        max_chars = max_context_tokens * 4
        
        # Try to truncate at a reasonable boundary
        if len(conversation) > max_chars:
            truncated = conversation[:max_chars]
            # Try to end at a sentence or line break
            last_sentence = max(truncated.rfind('.'), truncated.rfind('\n'))
            if last_sentence > max_chars * 0.8:  # If we find a good break point
                truncated = truncated[:last_sentence + 1]
            
            return truncated + "\n\n[Content truncated to fit context window]"
        
        return conversation
       
    def execute_tool_call(self, tool_name, parameters):
        """Execute a tool call and return the result"""
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
                        f"URL: {result['url'][:50]}..."
                    )
                return "\n\n".join(formatted_results)
            else:
                return "Error: No search query provided"
        else:
            return f"Error: Unknown tool '{tool_name}'"
    
    def parse_tool_calls(self, text):
        """Parse tool calls from LLM response"""
        tool_calls = []
        
        # Look for tool call patterns like [TOOL:web_search]{"query": "something"}
        pattern = r'\[TOOL:(\w+)\]\s*({.*?})'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for tool_name, params_str in matches:
            try:
                parameters = json.loads(params_str)
                tool_calls.append({
                    'tool': tool_name,
                    'parameters': parameters,
                    'raw': f'[TOOL:{tool_name}]{params_str}'
                })
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse tool call parameters: {e}")
                
        return tool_calls
    
    def clean_response(self, response):
        """Clean up the response by removing unwanted prefixes and formatting"""
        if not response:
            return response
        
        # Remove common prefixes that LLMs sometimes add
        keywords_to_remove = [
            "response:",
            "answer:", 
            "assistant:",
            "ai:",
            "support:",
            "response=",
            "answer=", 
            "assistant=",
            "ai=",
            "support=",
            "output:",
            "output=",
            "<|assistant|>"
        ]
        
        cleaned = response.replace("\n===\n", "").strip()
        
        for keyword in keywords_to_remove:
            # Remove whitespace before and after the keyword
            pattern = re.compile(re.escape(keyword) + r'\s*', re.IGNORECASE)
            cleaned = pattern.sub("", cleaned)
        
        # Final strip to clean up any remaining leading/trailing whitespace
        return cleaned.strip()
