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

    print("\n🔸 Test 1: Find a post and give me the post ID")
    llm.set_tools_enabled(True)
    response = llm.prompt("Find an interesting post on Moltbook from your feed and give me the post ID.", max_tokens=500, temperature=0.3)
    print(f"Response: {response}")

    print("\n🔸 Test 2: Add a comment on a post")
    llm.set_tools_enabled(True)
    response = llm.prompt(f"Add a comment to this post: ```{response}```. Your comment should be relevant and interesting.", max_tokens=500, temperature=0.3)
    print(f"Response: {response}")


if __name__ == "__main__":
    main()
