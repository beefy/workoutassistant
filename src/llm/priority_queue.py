#!/usr/bin/env python3
"""
Priority Queue Manager for LLM Requests
Manages a single LLM instance with a priority-based queuing system
to prevent multiple instantiations and manage memory usage.
"""

import threading
import queue
import time
from typing import Callable, List, Optional, Dict, Any
from concurrent.futures import Future
from llm.local_llm import LocalLLM


class LLMRequest:
    """Represents a single LLM request with priority"""
    
    def __init__(self, prompt: str, attachments: List[str] = None, priority: int = 1, 
                 max_tokens: int = None, temperature: float = None):
        self.prompt = prompt
        self.attachments = attachments or []
        self.priority = priority  # 1 for email (higher priority), 2 for moltbook (lower priority)
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.future = Future()  # Used for thread synchronization
        
    def __lt__(self, other):
        """Enable priority queue ordering (lower number = higher priority)"""
        return self.priority < other.priority


class LLMPriorityQueueManager:
    """Singleton manager for LLM requests with priority queuing"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.initialized = False
        return cls._instance
    
    def __init__(self):
        if self.initialized:
            return
            
        self.initialized = True
        self.llm = None
        self.priority_queue = queue.PriorityQueue()
        self.worker_thread = None
        self.running = False
        self.init_lock = threading.Lock()
        self.llm_ready = threading.Event()
        
        # Start the queue processor
        self._start_worker()
    
    def _start_worker(self):
        """Start the background worker thread"""
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
    
    def _initialize_llm(self):
        """Initialize the LLM instance (called once)"""
        with self.init_lock:
            if self.llm is None:
                print("🤖 Initializing global LLM instance...")
                self.llm = LocalLLM()
                print("✅ LLM initialized successfully")
                self.llm_ready.set()
    
    def _process_queue(self):
        """Background worker that processes LLM requests from the priority queue"""
        print("🔄 LLM priority queue worker started")
        
        while self.running:
            try:
                # Get the next request from the priority queue (blocks until available)
                request = self.priority_queue.get(timeout=1.0)
                
                # Initialize LLM if not already done
                if self.llm is None:
                    self._initialize_llm()
                
                # Wait for LLM to be ready
                self.llm_ready.wait()
                
                # Process the request
                print(f"🎯 Processing LLM request (priority {request.priority})")
                
                try:
                    # Set attachments if provided
                    if request.attachments:
                        self.llm.attachments = request.attachments
                    
                    # Generate response
                    kwargs = {}
                    if request.max_tokens is not None:
                        kwargs['max_tokens'] = request.max_tokens
                    if request.temperature is not None:
                        kwargs['temperature'] = request.temperature
                    
                    response = self.llm.prompt(request.prompt, **kwargs)
                    
                    # Clear attachments after use
                    if request.attachments:
                        self.llm.attachments = []
                    
                    # Set the result
                    request.future.set_result(response)
                        
                    print(f"✅ LLM request completed (priority {request.priority})")
                    
                except Exception as e:
                    print(f"❌ Error processing LLM request: {e}")
                    request.future.set_exception(e)
                
                # Mark task as done
                self.priority_queue.task_done()
                
            except queue.Empty:
                # Timeout occurred, continue loop
                continue
            except Exception as e:
                print(f"⚠️ Unexpected error in queue worker: {e}")
    
    def submit_request(self, prompt: str, attachments: List[str] = None, priority: int = 1,
                      max_tokens: int = None, temperature: float = None) -> str:
        """
        Submit a prompt request to the LLM priority queue.
        
        Args:
            prompt: The prompt to send to the LLM
            attachments: Optional list of file paths to attach
            priority: Priority level (1 = email/high priority, 2 = moltbook/low priority)
            max_tokens: Optional max tokens parameter
            temperature: Optional temperature parameter
            
        Returns:
            The LLM response (blocks until processed)
        """
        if not self.running:
            raise RuntimeError("LLM Priority Queue Manager is not running")
        
        # Create request
        request = LLMRequest(
            prompt=prompt,
            attachments=attachments,
            priority=priority,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Add to priority queue
        self.priority_queue.put(request)
        print(f"📝 LLM request queued (priority {priority})")
        
        # Block until response is ready
        try:
            response = request.future.result()  # This will block until the request is processed
            return response
        except Exception as e:
            print(f"❌ LLM request failed: {e}")
            raise
    
    def get_queue_size(self) -> int:
        """Get the current size of the priority queue"""
        return self.priority_queue.qsize()
    
    def shutdown(self):
        """Shutdown the priority queue manager"""
        print("🛑 Shutting down LLM Priority Queue Manager...")
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
        print("✅ LLM Priority Queue Manager shutdown complete")


# Global instance
llm_queue_manager = LLMPriorityQueueManager()


def submit_llm_request(prompt: str, attachments: List[str] = None, priority: int = 1,
                      max_tokens: int = None, temperature: float = None) -> str:
    """
    Convenience function to submit LLM requests.
    
    Args:
        prompt: The prompt to send to the LLM
        attachments: Optional list of file paths to attach
        priority: Priority level (1 = email/high priority, 2 = moltbook/low priority)
        max_tokens: Optional max tokens parameter
        temperature: Optional temperature parameter
        
    Returns:
        The LLM response (blocks until processed)
    """
    return llm_queue_manager.submit_request(
        prompt=prompt,
        attachments=attachments,
        priority=priority,
        max_tokens=max_tokens,
        temperature=temperature
    )