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
from moltbook import MoltbookClient


class LocalLLM:
    def __init__(self, model_path=None, n_ctx=4096, n_threads=4):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.model = None
        self.tools_enabled = True
        
        # Initialize MoltbookClient
        try:
            self.moltbook_client = MoltbookClient()
        except ValueError as e:
            print(f"⚠️  MoltbookClient not available: {e}")
            self.moltbook_client = None
        
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
            },
            "create_post": {
                "name": "create_post",
                "description": "Create a new post on Moltbook in a specific submolt.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "submolt": {"type": "string", "description": "The submolt to post in"},
                        "title": {"type": "string", "description": "The title of the post"},
                        "content": {"type": "string", "description": "The content/body of the post"}
                    },
                    "required": ["submolt", "title", "content"]
                }
            },
            "create_link_post": {
                "name": "create_link_post",
                "description": "Create a link post on Moltbook in a specific submolt.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "submolt": {"type": "string", "description": "The submolt to post in"},
                        "title": {"type": "string", "description": "The title of the post"},
                        "url": {"type": "string", "description": "The URL to link to"}
                    },
                    "required": ["submolt", "title", "url"]
                }
            },
            "get_feed": {
                "name": "get_feed",
                "description": "Get the hot feed from Moltbook.",
                "parameters": {"type": "object", "properties": {}, "required": []}
            },
            "get_personalized_feed": {
                "name": "get_personalized_feed",
                "description": "Get your personalized feed from Moltbook based on subscriptions and follows.",
                "parameters": {"type": "object", "properties": {}, "required": []}
            },
            "get_posts_from_submolt": {
                "name": "get_posts_from_submolt",
                "description": "Get posts from a specific submolt.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "submolt": {"type": "string", "description": "The submolt name"}
                    },
                    "required": ["submolt"]
                }
            },
            "get_single_post": {
                "name": "get_single_post",
                "description": "Get details of a specific post by ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "post_id": {"type": "string", "description": "The post ID"}
                    },
                    "required": ["post_id"]
                }
            },
            "add_comment": {
                "name": "add_comment",
                "description": "Add a comment to a post.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "post_id": {"type": "string", "description": "The post ID"},
                        "content": {"type": "string", "description": "The comment content"}
                    },
                    "required": ["post_id", "content"]
                }
            },
            "reply_to_comment": {
                "name": "reply_to_comment",
                "description": "Reply to a specific comment.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "post_id": {"type": "string", "description": "The post ID"},
                        "parent_comment_id": {"type": "string", "description": "The comment ID to reply to"},
                        "content": {"type": "string", "description": "The reply content"}
                    },
                    "required": ["post_id", "parent_comment_id", "content"]
                }
            },
            "get_comments": {
                "name": "get_comments",
                "description": "Get comments for a specific post.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "post_id": {"type": "string", "description": "The post ID"}
                    },
                    "required": ["post_id"]
                }
            },
            "upvote_post": {
                "name": "upvote_post",
                "description": "Upvote a post.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "post_id": {"type": "string", "description": "The post ID"}
                    },
                    "required": ["post_id"]
                }
            },
            "downvote_post": {
                "name": "downvote_post",
                "description": "Downvote a post.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "post_id": {"type": "string", "description": "The post ID"}
                    },
                    "required": ["post_id"]
                }
            },
            "upvote_comment": {
                "name": "upvote_comment",
                "description": "Upvote a comment.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "comment_id": {"type": "string", "description": "The comment ID"}
                    },
                    "required": ["comment_id"]
                }
            },
            "list_submolts": {
                "name": "list_submolts",
                "description": "Get a list of all available submolts.",
                "parameters": {"type": "object", "properties": {}, "required": []}
            },
            "subscribe_to_submolt": {
                "name": "subscribe_to_submolt",
                "description": "Subscribe to a submolt.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "submolt": {"type": "string", "description": "The submolt name"}
                    },
                    "required": ["submolt"]
                }
            },
            "unsubscribe_from_submolt": {
                "name": "unsubscribe_from_submolt",
                "description": "Unsubscribe from a submolt.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "submolt": {"type": "string", "description": "The submolt name"}
                    },
                    "required": ["submolt"]
                }
            },
            "follow_user": {
                "name": "follow_user",
                "description": "Follow a user/agent.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string", "description": "The username to follow"}
                    },
                    "required": ["username"]
                }
            },
            "unfollow_user": {
                "name": "unfollow_user",
                "description": "Unfollow a user/agent.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string", "description": "The username to unfollow"}
                    },
                    "required": ["username"]
                }
            },
            "search_posts_and_comments": {
                "name": "search_posts_and_comments",
                "description": "Search for posts and comments on Moltbook.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query"}
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
            cleaned_prompt = self.truncate_to_context(prompt)

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

    def prompt(self, prompt, max_tokens=500, temperature=0.7, stop=None, max_tool_iterations=20):
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
        
        tool_results = self.process_tool_calls(tool_calls)
        history = self.execute_prompt(f"Summarize the following conversation history in a concise way, keeping important details:\n\nInitial Prompt:{prompt}\n\nResponse:{response}\n\nTool Call Results:{tool_results}\n\nPrevious History Summary:None", max_tokens=300, temperature=0.5)
        print(f"Summary thus far: {history}")
        iteration_count = 0
        while len(tool_calls) > 0 and iteration_count < max_tool_iterations:
            iteration_count += 1
            print(f"🔧 Iteration {iteration_count}: Found {len(tool_calls)} tool call(s)")
            tool_results = self.process_tool_calls(tool_calls)

            # LLM call to summarize convo history
            history = self.execute_prompt(f"Summarize the following conversation history in a concise way, keeping important details but being extremely concise:\n\nInitial Prompt:{prompt}\n\nResponse:{response}\n\nTool Call Results:{tool_results}\n\nPrevious History Summary:{history}", max_tokens=300, temperature=0.5)
            print(f"✅ Tool calls executed. Building final response with tool results...")

            # Intermediate LLM call (in loop)
            response = self.execute_prompt(self._build_intermediate_prompt(prompt, tool_results, iteration_count, history), max_tokens, temperature, stop)
            tool_calls = self.parse_tool_calls(response)


        if not tool_calls:
            print("✅ No tool calls found, returning response")
            return self.clean_response(response)

        # Final LLM call
        response = self.execute_prompt(self._build_final_prompt(prompt, tool_results, history), max_tokens, temperature, stop)
        cleaned_response = self.clean_response(response)
        return cleaned_response    

    def _build_tool_prompt(self, user_prompt):
        """Build a prompt that includes tool instructions"""
        if not self.tools_enabled:
            return user_prompt
        
        tool_instructions = """
You have access to web search and Moltbook social platform tools. Available tools:
- Web search: [TOOL:web_search]{"query": "your search terms"}
- Moltbook tools:
  - [TOOL:get_feed]{} - Get hot posts
  - [TOOL:get_personalized_feed]{} - Get your personalized feed
  - [TOOL:create_post]{"submolt": "submolt_name", "title": "title", "content": "content"}
  - [TOOL:create_link_post]{"submolt": "submolt_name", "title": "title", "url": "url"}
  - [TOOL:get_posts_from_submolt]{"submolt": "submolt_name"}
  - [TOOL:get_single_post]{"post_id": "post_id"}
  - [TOOL:add_comment]{"post_id": "post_id", "content": "comment content"}
  - [TOOL:reply_to_comment]{"post_id": "post_id", "parent_comment_id": "comment_id", "content": "reply content"}
  - [TOOL:get_comments]{"post_id": "post_id"}
  - [TOOL:upvote_post]{"post_id": "post_id"}
  - [TOOL:downvote_post]{"post_id": "post_id"}
  - [TOOL:upvote_comment]{"comment_id": "comment_id"}
  - [TOOL:search_posts_and_comments]{"query": "search terms"}
  - [TOOL:list_submolts]{} - List all submolts
  - [TOOL:follow_user]{"username": "username"}
  - [TOOL:subscribe_to_submolt]{"submolt": "submolt_name"}
  - [TOOL:unsubscribe_from_submolt]{"submolt": "submolt_name"}
  - [TOOL:unfollow_user]{"username": "username"}

Do not use any tool calls if you do not need to.
Do use a tool call if it will help you get information you need to answer the user's question or complete the task.
Provide concise, factual information with specific details when possible.
Please keep your response short because the context window is limited.
Thank you!

IMPORTANT: If you are not using a tool call, start your response with "Dear User, ..." and end your response with "Sincerely, Bob the Raspberry Pi"
IMPORTANT: If you are using a tool call, be sure to include all required parameters in the correct format and only include the tool call in your response. Do not include any other text besides the tool call.
IMPORTANT: If you are using a tool call, make at most 3 tool calls at a time. Then wait for the tool results before making more tool calls to avoid overwhelming the context window. You can make multiple iterations of tool calls and LLM calls to complete the task.

Your Response:
        """
        
        return f"Tool Instructions:\n{tool_instructions}\nUser Prompt: {user_prompt}\n\nYour Response: "

    def _build_intermediate_prompt(self, original_prompt, tool_results, iteration_num, history):
        """Build a prompt for intermediate LLM call after tool execution"""
        if not self.tools_enabled:
            return original_prompt
        
        tool_instructions = """
You have access to web search and Moltbook social platform tools. Available tools:
- Web search: [TOOL:web_search]{"query": "your search terms"}
- Moltbook tools:
  - [TOOL:get_feed]{} - Get hot posts
  - [TOOL:get_personalized_feed]{} - Get your personalized feed
  - [TOOL:create_post]{"submolt": "submolt_name", "title": "title", "content": "content"}
  - [TOOL:create_link_post]{"submolt": "submolt_name", "title": "title", "url": "url"}
  - [TOOL:get_posts_from_submolt]{"submolt": "submolt_name"}
  - [TOOL:get_single_post]{"post_id": "post_id"}
  - [TOOL:add_comment]{"post_id": "post_id", "content": "comment content"}
  - [TOOL:reply_to_comment]{"post_id": "post_id", "parent_comment_id": "comment_id", "content": "reply content"}
  - [TOOL:get_comments]{"post_id": "post_id"}
  - [TOOL:upvote_post]{"post_id": "post_id"}
  - [TOOL:downvote_post]{"post_id": "post_id"}
  - [TOOL:upvote_comment]{"comment_id": "comment_id"}
  - [TOOL:search_posts_and_comments]{"query": "search terms"}
  - [TOOL:list_submolts]{} - List all submolts
  - [TOOL:follow_user]{"username": "username"}
  - [TOOL:subscribe_to_submolt]{"submolt": "submolt_name"}
  - [TOOL:unsubscribe_from_submolt]{"submolt": "submolt_name"}
  - [TOOL:unfollow_user]{"username": "username"}

Do not use any tool calls if you do not need to.
Do use a tool call if it will help you get information you need to answer the user's question or complete the task.
Provide concise, factual information with specific details when possible.
Please keep your response short because the context window is limited.
Thank you!

IMPORTANT: If you are not using a tool call, start your response with "Dear User, ..." and end your response with "Sincerely, Bob the Raspberry Pi"
IMPORTANT: If you are using a tool call, be sure to include all required parameters in the correct format and only include the tool call in your response. Do not include any other text besides the tool call.
IMPORTANT: If you are using a tool call, make at most 3 tool calls at a time. Then wait for the tool results before making more tool calls to avoid overwhelming the context window. You can make multiple iterations of tool calls and LLM calls to complete the task.

Your Response:
        """

        return f"Conversation History Summary: {history}\nTool Results: {tool_results}\nTool Instructions:\n{tool_instructions}\nUser Prompt: {original_prompt}\nNumber of tool calls thus far: {iteration_num}\nYour Response: "

    def _build_final_prompt(self, original_prompt, tool_results, history):
        """Build a prompt for the second LLM call that includes tool results"""
        return f"""Prompt: "{original_prompt}"
Additional Info: "{tool_results}"
Conversation History Summary: "{history}"
IMPORTANT: start your response with "Dear User, ..." and end your response with "Sincerely, Bob the Raspberry Pi"
Your Response:
        """
    
    def estimate_tokens(self, text):
        """Rough estimate of token count (approximately 4 characters per token)"""
        return len(text) // 4
    
    def truncate_to_context(self, conversation, max_tokens_for_response=1000):
        """Truncate conversation to fit within context window, leaving room for response"""
        max_context_tokens = self.n_ctx - max_tokens_for_response
        estimated_tokens = self.estimate_tokens(conversation)
        
        if estimated_tokens <= max_context_tokens:
            return conversation
        
        print(f"⚠️  Context too long ({estimated_tokens} tokens), truncating to fit...")
        
        # Calculate how many characters to keep (roughly)
        max_chars = max_context_tokens * 2
        
        # Try to truncate at a reasonable boundary
        if len(conversation) > max_chars:
            truncated = conversation[:max_chars]
            # Try to end at a sentence or line break
            last_sentence = max(truncated.rfind('.'), truncated.rfind('\n'))
            if last_sentence > max_chars * 0.7:  # If we find a good break point
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
        
        # Moltbook tool calls
        elif self.moltbook_client is None:
            return "Error: MoltbookClient not available (missing API key)"
        
        elif tool_name == "create_post":
            submolt = parameters.get('submolt')
            title = parameters.get('title')
            content = parameters.get('content')
            try:
                result = self.moltbook_client.create_post(submolt, title, content)
                return f"✅ Post created successfully in /{submolt}: '{title}'"
            except Exception as e:
                return f"❌ Failed to create post: {e}"
        
        elif tool_name == "create_link_post":
            submolt = parameters.get('submolt')
            title = parameters.get('title')
            url = parameters.get('url')
            try:
                result = self.moltbook_client.create_link_post(submolt, title, url)
                return f"✅ Link post created successfully in /{submolt}: '{title}' -> {url}"
            except Exception as e:
                return f"❌ Failed to create link post: {e}"
        
        elif tool_name == "get_feed":
            try:
                result = self.moltbook_client.get_feed()
                return f"Recent posts from hot feed:\n\n{result}\n\n"
            except Exception as e:
                return f"❌ Failed to get feed: {e}"
        
        elif tool_name == "get_personalized_feed":
            try:
                result = self.moltbook_client.get_personalized_feed()
                return f"Your personalized feed:\n\n{result}\n\n"
            except Exception as e:
                return f"❌ Failed to get personalized feed: {e}"
        
        elif tool_name == "get_posts_from_submolt":
            submolt = parameters.get('submolt')
            try:
                result = self.moltbook_client.get_posts_from_submolt(submolt)
                return f"Recent posts from /{submolt}:\n\n{result}\n\n"
            except Exception as e:
                return f"❌ Failed to get posts from /{submolt}: {e}"
        
        elif tool_name == "get_single_post":
            post_id = parameters.get('post_id')
            try:
                result = self.moltbook_client.get_single_post(post_id)
                return f"{result}"
            except Exception as e:
                return f"❌ Failed to get post {post_id}: {e}"
        
        elif tool_name == "add_comment":
            post_id = parameters.get('post_id')
            content = parameters.get('content')
            try:
                result = self.moltbook_client.add_comment(post_id, content)
                return f"✅ Comment added to post {post_id}"
            except Exception as e:
                return f"❌ Failed to add comment: {e}"
        
        elif tool_name == "reply_to_comment":
            post_id = parameters.get('post_id')
            parent_comment_id = parameters.get('parent_comment_id')
            content = parameters.get('content')
            try:
                result = self.moltbook_client.reply_to_comment(post_id, parent_comment_id, content)
                return f"✅ Reply added to comment {parent_comment_id}"
            except Exception as e:
                return f"❌ Failed to add reply: {e}"
        
        elif tool_name == "get_comments":
            post_id = parameters.get('post_id')
            try:
                result = self.moltbook_client.get_comments(post_id)
                return f"Comments on post {post_id}:\n\n{result}\n\n"
            except Exception as e:
                return f"❌ Failed to get comments: {e}"
        
        elif tool_name == "upvote_post":
            post_id = parameters.get('post_id')
            try:
                result = self.moltbook_client.upvote_post(post_id)
                return f"✅ Upvoted post {post_id}"
            except Exception as e:
                return f"❌ Failed to upvote post: {e}"
        
        elif tool_name == "downvote_post":
            post_id = parameters.get('post_id')
            try:
                result = self.moltbook_client.downvote_post(post_id)
                return f"✅ Downvoted post {post_id}"
            except Exception as e:
                return f"❌ Failed to downvote post: {e}"
        
        elif tool_name == "upvote_comment":
            comment_id = parameters.get('comment_id')
            try:
                result = self.moltbook_client.upvote_comment(comment_id)
                return f"✅ Upvoted comment {comment_id}"
            except Exception as e:
                return f"❌ Failed to upvote comment: {e}"
        
        elif tool_name == "list_submolts":
            try:
                result = self.moltbook_client.list_submolts()
                return f"Available submolts: {result}"
            except Exception as e:
                return f"❌ Failed to list submolts: {e}"
        
        elif tool_name == "subscribe_to_submolt":
            submolt = parameters.get('submolt')
            try:
                result = self.moltbook_client.subscribe_to_submolt(submolt)
                return f"✅ Subscribed to /{submolt}"
            except Exception as e:
                return f"❌ Failed to subscribe to /{submolt}: {e}"
        
        elif tool_name == "unsubscribe_from_submolt":
            submolt = parameters.get('submolt')
            try:
                result = self.moltbook_client.unsubscribe_from_submolt(submolt)
                return f"✅ Unsubscribed from /{submolt}"
            except Exception as e:
                return f"❌ Failed to unsubscribe from /{submolt}: {e}"
        
        elif tool_name == "follow_user":
            username = parameters.get('username')
            try:
                result = self.moltbook_client.follow_user(username)
                return f"✅ Now following @{username}"
            except Exception as e:
                return f"❌ Failed to follow @{username}: {e}"
        
        elif tool_name == "unfollow_user":
            username = parameters.get('username')
            try:
                result = self.moltbook_client.unfollow_user(username)
                return f"✅ Unfollowed @{username}"
            except Exception as e:
                return f"❌ Failed to unfollow @{username}: {e}"
        
        elif tool_name == "search_posts_and_comments":
            query = parameters.get('query')
            try:
                result = self.moltbook_client.search_posts_and_comments(query)
                return f"Search results for '{query}':\n\n{result}\n\n"
            except Exception as e:
                return f"❌ Failed to search: {e}"
        
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

        # if "Dear " in response, remove everything before it (case insensitive)
        dear_match = re.search(r"dear\s+", cleaned, re.IGNORECASE)
        if dear_match:
            cleaned = cleaned[dear_match.start():]

        # If Sincerely, Bob the Raspberry Pi is in the response, remove everything after it
        # Allow for text and newlines between "Sincerely," and "Bob the Raspberry Pi"
        sincerely_pattern = r"sincerely,.*?bob\s+the\s+raspberry\s+pi"
        match = re.search(sincerely_pattern, cleaned, re.IGNORECASE | re.DOTALL)
        if match:
            cleaned = cleaned[:match.end()]

        # for keyword in keywords_to_remove:
        #     # Remove whitespace before and after the keyword
        #     pattern = re.compile(re.escape(keyword) + r'\s*', re.IGNORECASE)
        #     cleaned = pattern.sub("", cleaned)
        
        # Final strip to clean up any remaining leading/trailing whitespace
        return cleaned.strip()
