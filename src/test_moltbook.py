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
    print("\n🔸 Test 1: Comment on a post")
    llm.set_tools_enabled(True)
    response = llm.prompt("Find an interesting post on Moltbook and make a relevant comment on it.", max_tokens=500, temperature=0.3)
    print(f"Response: {response}")


if __name__ == "__main__":
    main()
