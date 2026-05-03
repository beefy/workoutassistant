#!/usr/bin/env python3
"""
Shared utilities for LLM implementations (local and DeepSeek).
Provides common tool call parsing, execution, and response handling.
"""

import json
import hashlib
import re
import logging
from typing import List, Dict, Any, Optional, Set
from utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class ToolCallHandler:
    """
    Handles parsing, deduplication, and execution of tool calls for LLM responses.
    Shared between LocalLLM and DeepSeekLLM.
    """
    
    def __init__(self):
        self.tool_call_memo: Set[str] = set()
        self.generated_images: List[str] = []
        self.tools_enabled: bool = True
    
    def reset_session(self):
        """Reset generated images and tool call memo for a new session"""
        self.generated_images = []
        self.tool_call_memo = set()
        logger.info("🔄 Session reset: cleared generated images and tool call memo")
    
    def set_tools_enabled(self, enabled: bool):
        """Enable or disable tool functionality"""
        self.tools_enabled = enabled
        logger.info(f"🔧 Tools {'enabled' if enabled else 'disabled'}")
    
    def parse_tool_calls(self, text: str, max_calls: int = 5) -> List[Dict[str, Any]]:
        """
        Parse tool calls from LLM response - looking for JSON objects with 'tool' field.
        
        Args:
            text: The LLM response text to parse
            max_calls: Maximum number of tool calls to return (default 5)
            
        Returns:
            List of dicts with 'tool', 'parameters', and 'raw' keys
        """
        tool_calls = []
        
        # Find all JSON objects in the text
        brace_stack = []
        json_start = None
        
        for i, char in enumerate(text):
            if char == '{':
                if not brace_stack:  # Starting a new JSON object
                    json_start = i
                brace_stack.append('{')
            elif char == '}':
                if brace_stack:
                    brace_stack.pop()
                    if not brace_stack and json_start is not None:  # Complete JSON object found
                        json_str = text[json_start:i+1]
                        try:
                            parsed_json = json.loads(json_str)
                            # Check if this JSON object has a 'tool' field
                            if isinstance(parsed_json, dict) and 'tool' in parsed_json:
                                tool_name = parsed_json['tool']
                                parameters = parsed_json.get('parameters', {})
                                
                                # Check if this tool call was already executed this session
                                tool_hash = self._hash_tool_call(tool_name, parameters)
                                if tool_hash not in self.tool_call_memo:
                                    tool_calls.append({
                                        'tool': tool_name,
                                        'parameters': parameters,
                                        'raw': json_str
                                    })
                                    # Add to memo immediately to prevent duplicates in same response
                                    self.tool_call_memo.add(tool_hash)
                                else:
                                    logger.debug(f"🔄 Skipping duplicate tool call: {tool_name} with same parameters")
                        except json.JSONDecodeError:
                            # Invalid JSON, skip it
                            pass
                        json_start = None
        
        return tool_calls[:max_calls]
    
    def _hash_tool_call(self, tool_name: str, parameters: dict) -> str:
        """Create a hash of tool call for deduplication"""
        param_str = json.dumps(parameters, sort_keys=True)
        combined = f"{tool_name}:{param_str}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def clean_response(self, response: Optional[str]) -> Optional[str]:
        """
        Clean up the response by removing unwanted prefixes and formatting.
        
        Args:
            response: The raw LLM response
            
        Returns:
            Cleaned response string
        """
        if not response:
            return response
        
        cleaned = response.replace("\n===\n", "").strip()

        # If "Dear " in response, remove everything before it (case insensitive)
        dear_match = re.search(r"dear\s+", cleaned, re.IGNORECASE)
        if dear_match:
            cleaned = cleaned[dear_match.start():]

        # If Sincerely, Bob the Raspberry Pi is in the response, remove everything after it
        # Allow for text and newlines between "Sincerely," and "Bob the Raspberry Pi"
        sincerely_pattern = r"sincerely,.*?bob\s+the\s+raspberry\s+pi"
        match = re.search(sincerely_pattern, cleaned, re.IGNORECASE | re.DOTALL)
        if match:
            cleaned = cleaned[:match.end()]

        # Final strip to clean up any remaining leading/trailing whitespace
        return cleaned.strip()
    
    def process_tool_calls(self, tool_calls: List[Dict[str, Any]], execute_fn, use_crypto_prompt: bool = False) -> str:
        """
        Process a list of tool calls using the provided execution function.
        
        Args:
            tool_calls: List of tool call dicts with 'tool' and 'parameters' keys
            execute_fn: Callable that takes (tool_name, parameters, use_crypto_prompt) and returns result string
            use_crypto_prompt: Whether crypto trading tools are enabled
            
        Returns:
            Combined results string
        """
        try:
            tool_results = []
            for tool_call in tool_calls:
                tool_result = execute_fn(
                    tool_call['tool'],
                    tool_call['parameters'],
                    use_crypto_prompt=use_crypto_prompt
                )
                tool_results.append(tool_result)
            
            combined_results = "\n\n".join(tool_results)
            return combined_results
        except Exception as e:
            logger.error(f"❌ Error during tool execution: {e}")
            return "Sorry, I encountered an error while executing a tool."
