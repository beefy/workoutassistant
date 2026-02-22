#!/usr/bin/env python3
"""
Test script for the LLM Priority Queue System
Simulates multiple threads making LLM requests with different priorities
"""

import threading
import time
from llm.priority_queue import submit_llm_request


def simulate_email_processing(email_id):
    """Simulate an email thread making high-priority requests"""
    print(f"📧 Email {email_id}: Starting email processing...")
    
    # Email requests get priority 1 (high)
    response = submit_llm_request(
        prompt=f"Generate a brief response to email {email_id}: 'Hello, how are you today?'",
        priority=1,  # High priority for emails
        max_tokens=50,
        temperature=0.7
    )
    
    print(f"📧 Email {email_id}: Got response - {response[:100]}...")
    return response


def simulate_moltbook_browsing(task_id):
    """Simulate a moltbook thread making low-priority requests"""
    print(f"🔍 Moltbook {task_id}: Starting browsing...")
    
    # Moltbook requests get priority 2 (low)
    response = submit_llm_request(
        prompt=f"Generate a short comment for moltbook post {task_id} about technology",
        priority=2,  # Lower priority for moltbook
        max_tokens=30,
        temperature=0.8
    )
    
    print(f"🔍 Moltbook {task_id}: Got response - {response[:100]}...")
    return response


def test_priority_queue():
    """Test the priority queue system with multiple concurrent requests"""
    print("🚀 Testing LLM Priority Queue System")
    print("=" * 50)
    
    threads = []
    
    # Start some moltbook tasks first (low priority)
    for i in range(2):
        thread = threading.Thread(target=simulate_moltbook_browsing, args=(i + 1,))
        threads.append(thread)
        thread.start()
        time.sleep(0.1)  # Small delay
    
    # Then start email tasks (high priority) - these should jump ahead in the queue
    for i in range(2):
        thread = threading.Thread(target=simulate_email_processing, args=(i + 1,))
        threads.append(thread)
        thread.start()
        time.sleep(0.1)  # Small delay
    
    # Add another moltbook task
    thread = threading.Thread(target=simulate_moltbook_browsing, args=(3,))
    threads.append(thread)
    thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("=" * 50)
    print("✅ Priority queue test completed!")


if __name__ == "__main__":
    test_priority_queue()