#!/usr/bin/env python3
"""
Test script for the LocalLLM web search tool functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from local_llm import LocalLLM


def test_web_search():
    """Test the web search tool functionality"""
    print("🚀 Testing LocalLLM with Web Search Tools")
    print("=" * 50)
    
    # Initialize LLM
    llm = LocalLLM()
    
    if llm.model is None:
        print("❌ Model failed to load. Cannot run tests.")
        return False
    
    # Test queries that should trigger web search
    test_queries = [
        "What's the current weather in New York?",
        "What are the latest developments in AI in 2026?",
        "Tell me about the most recent space missions this year",
        "What is 2+2?",  # This shouldn't need web search
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔸 Test {i}: {query}")
        print("-" * 40)
        
        try:
            response = llm.prompt(query, max_tokens=512, temperature=0.3)
            
            if response:
                print(f"✅ Response: {response}")
            else:
                print("❌ No response generated")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "="*50)
    
    print("🏁 Testing complete!")


def test_manual_web_search():
    """Test the web search function directly"""
    print("\n🔍 Testing direct web search functionality")
    print("-" * 40)
    
    llm = LocalLLM()
    
    # Test direct web search
    results = llm.web_search("Python programming tutorials", num_results=3)
    
    print("Search Results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   {result['snippet']}")
        print(f"   URL: {result['url']}")
        print()


def test_tool_parsing():
    """Test the tool call parsing functionality"""
    print("\n🔧 Testing tool call parsing")
    print("-" * 40)
    
    llm = LocalLLM()
    
    # Test text with tool calls
    test_text = """I need to search for information. [TOOL:web_search]{"query": "latest AI developments"}
    
    Also, let me search for something else. [TOOL:web_search]{"query": "weather today"}
    
    That should help me answer your question."""
    
    tool_calls = llm.parse_tool_calls(test_text)
    
    print(f"Found {len(tool_calls)} tool calls:")
    for i, call in enumerate(tool_calls, 1):
        print(f"{i}. Tool: {call['tool']}")
        print(f"   Parameters: {call['parameters']}")
        print(f"   Raw: {call['raw']}")


def main():
    """Run all tests"""
    try:
        # Test direct web search first
        test_manual_web_search()
        
        # Test tool parsing
        test_tool_parsing()
        
        # Test full LLM with web search
        user_input = input("\nDo you want to test the full LLM with web search? (y/n): ")
        if user_input.lower().startswith('y'):
            test_web_search()
            
    except KeyboardInterrupt:
        print("\n\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")


if __name__ == "__main__":
    main()