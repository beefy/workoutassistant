#!/usr/bin/env python3
"""
Simple test to verify the web search functionality works
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from local_llm import LocalLLM


def main():
    print("🚀 Testing LocalLLM with Web Search")
    print("=" * 50)
    
    # Test with tools disabled first to see if basic functionality works
    llm = LocalLLM()
    
    if llm.model is None:
        print("❌ Model failed to load")
        return
    
    # Test without web search first
    print("\n🔸 Test 1: Simple question without web search")
    llm.set_tools_enabled(False)
    response = llm.prompt("What is 2+2?", max_tokens=100, temperature=0.3)
    print(f"Response: {response}")
    
    # Test with web search enabled
    print("\n🔸 Test 2: Question that should trigger web search")
    llm.set_tools_enabled(True)
    response = llm.prompt("What's the current weather in New York?", max_tokens=300, temperature=0.3)
    print(f"Response: {response}")


if __name__ == "__main__":
    main()