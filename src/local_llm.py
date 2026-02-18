#!/usr/bin/env python3
"""
Local LLM Test using GGUF models via llama-cpp-python on Raspberry Pi 5
Tests local LLM models running via llama.cpp backend for text generation.
"""

import time
import os
import json
import re
import requests
from bs4 import BeautifulSoup
from llama_cpp import Llama


class LocalLLM:
    def __init__(self, model_path=None, n_ctx=2048, n_threads=4):
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
    
    def prompt(self, prompt, max_tokens=256, temperature=0.7, stop=None, max_tool_iterations=3):
        """Generate a response using the loaded model with tool call support"""
        if self.model is None:
            print("❌ Model not loaded. Call load_model() first.")
            return None
        
        print(f"🤔 Generating response for: \"{prompt[:50]}...\"")
        
        # Build the conversation with tool instructions
        conversation = self._build_tool_prompt(prompt)
        
        iteration = 0
        while iteration < max_tool_iterations:
            start_time = time.time()
            
            try:
                # Generate response
                output = self.model(
                    conversation,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=stop or ["User:"],
                    echo=False
                )
                
                response = output['choices'][0]['text'].strip()
                
                generation_time = time.time() - start_time
                tokens_generated = output['usage']['completion_tokens']
                tokens_per_second = tokens_generated / generation_time if generation_time > 0 else 0
                
                print(f"⚡ Generated {tokens_generated} tokens in {generation_time:.1f}s ({tokens_per_second:.1f} tokens/s)")
                
                # Check for tool calls
                if self.tools_enabled:
                    tool_calls = self.parse_tool_calls(response)
                    
                    if tool_calls:
                        print(f"🔧 Found {len(tool_calls)} tool call(s)")
                        
                        # Execute tool calls and build new conversation
                        tool_results = []
                        for tool_call in tool_calls:
                            tool_result = self.execute_tool_call(
                                tool_call['tool'], 
                                tool_call['parameters']
                            )
                            tool_results.append(tool_result)
                        
                        # Build a clean conversation with tool results
                        combined_results = "\n\n".join(tool_results)
                        conversation = f"""A user asked: "{prompt}"

Here is the information found from web searches:
{combined_results}

Based on this information, provide a complete and helpful answer. Do not use prefixes like "Response:" or "Answer:" - just provide the answer directly:"""
                        
                        iteration += 1
                        continue
                
                # No tool calls found or tools disabled, return final response
                cleaned_response = self.clean_response(response)
                return cleaned_response
                
            except Exception as e:
                print(f"❌ Error generating response: {e}")
                return None
        
        print(f"⚠️  Reached maximum tool iterations ({max_tool_iterations})")
        return response
    
    def _build_tool_prompt(self, user_prompt):
        """Build a prompt that includes tool instructions"""
        if not self.tools_enabled:
            return f"User: {user_prompt}\nAssistant: "
        
        tool_instructions = """You have access to web search. If you need current information or facts not in your knowledge, use:
[TOOL:web_search]{"query": "your search terms here"}

If you can answer without web search, respond directly. Do not prefix your response with "Response:" or "Answer:" - just provide the answer."""
        
        return f"{tool_instructions}\n\nUser: {user_prompt}\nAssistant: "
    
    def web_search(self, query, num_results=3):
        """Perform a web search and return summarized results"""
        print(f"🔍 Searching web for: {query}")
        
        try:
            # Use DuckDuckGo search (no API key required)
            search_url = f"https://duckduckgo.com/html/?q={requests.utils.quote(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Find search results
            for result in soup.find_all('a', class_='result__a')[:num_results]:
                title = result.get_text(strip=True)
                url = result.get('href')
                
                # Get snippet from result
                snippet_elem = result.find_next('a', class_='result__snippet')
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                
                if title and url:
                    # Fetch actual content from the page
                    content = self.fetch_page_content(url)
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'content': content
                    })
            
            print(f"✅ Found {len(results)} search results with content")
            return results
            
        except Exception as e:
            print(f"❌ Web search failed: {e}")
            return [{"title": "Search Error", "snippet": f"Unable to search the web: {str(e)}", "url": "", "content": ""}]
    
    def fetch_page_content(self, url, max_length=2000):
        """Fetch and extract text content from a webpage"""
        try:
            print(f"📄 Fetching content from: {url[:50]}...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Truncate if too long
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return text
            
        except Exception as e:
            print(f"⚠️  Failed to fetch content from {url}: {e}")
            return "Content could not be retrieved from this page."
    
    def execute_tool_call(self, tool_name, parameters):
        """Execute a tool call and return the result"""
        if tool_name == "web_search":
            query = parameters.get('query', '')
            if query:
                results = self.web_search(query)
                # Format results for the LLM with actual content
                formatted_results = []
                for i, result in enumerate(results, 1):
                    content_preview = result['content'][:500] + "..." if len(result['content']) > 500 else result['content']
                    formatted_results.append(
                        f"{i}. {result['title']}\n"
                        f"   URL: {result['url']}\n"
                        f"   Content: {content_preview}"
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
        prefixes_to_remove = [
            "Response:",
            "Answer:", 
            "Assistant:",
            "AI:"
        ]
        
        cleaned = response.strip()
        
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        return cleaned
