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
import logging
from utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class LLMRequest:
    """Represents a single LLM request with priority"""
    
    def __init__(self, prompt: str, attachments: List[str] = None, priority: int = 1, 
                 max_tokens: int = None, temperature: float = None, final_query=True, use_crypto_prompt=False, task: str = "unknown"):
        self.prompt = prompt
        self.attachments = attachments or []
        self.priority = priority  # 1 for email (higher priority), 2 for moltbook (lower priority)
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.final_query = final_query
        self.use_crypto_prompt = use_crypto_prompt
        self.task = task  # Which task requested this (discord, email, newsletter, crypto, moltbook)
        self.future = Future()  # Used for thread synchronization
        self.timestamp = time.time()  # Add timestamp for FIFO ordering
        
    def __lt__(self, other):
        """Enable priority queue ordering (lower number = higher priority, older timestamp = first)"""
        if self.priority == other.priority:
            # Same priority: older request (smaller timestamp) goes first
            return self.timestamp < other.timestamp
        # Different priority: lower priority number goes first
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
        self.current_task = None  # Track what task is currently being processed
        self.current_request = None  # Track current request details
        
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
                logger.info("🤖 Initializing global LLM instance...")
                self._llm = LocalLLM()
                logger.info("✅ LLM initialized successfully")
                self.llm_ready.set()
    
    def _process_queue(self):
        """Background worker that processes LLM requests from the priority queue"""
        logger.info("🔄 LLM priority queue worker started")
        
        while self.running:
            try:
                # Get the next request from the priority queue (blocks until available)
                request = self.priority_queue.get(timeout=1.0)
                
                # Initialize LLM if not already done
                if self.llm is None:
                    self._initialize_llm()
                
                # Wait for LLM to be ready
                self.llm_ready.wait()
                
                # Set current task tracking
                self.current_task = f"{request.task} (priority {request.priority})"
                self.current_request = request
                
                # Process the request
                logger.info(f"🎯 Processing LLM request from {request.task} (priority {request.priority})")
                
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
                    
                    # Add the new parameters
                    kwargs['final_query'] = request.final_query
                    kwargs['use_crypto_prompt'] = request.use_crypto_prompt
                    
                    result = self.llm.prompt(request.prompt, **kwargs)
                    
                    # Clear attachments after use
                    if request.attachments:
                        self.llm.attachments = []
                    
                    # Set the result (now a dict with response and generated_images)
                    request.future.set_result(result)
                        
                    logger.info(f"✅ LLM request completed from {request.task} (priority {request.priority})")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing LLM request from {request.task}: {e}")
                    request.future.set_exception(e)
                
                # Clear current task tracking
                self.current_task = None
                self.current_request = None
                
                # Mark task as done
                self.priority_queue.task_done()
                
            except queue.Empty:
                # Timeout occurred, continue loop
                continue
            except Exception as e:
                logger.warning(f"⚠️ Unexpected error in queue worker: {e}")
    
    def submit_request(self, prompt: str, attachments: List[str] = None, priority: int = 1,
                      max_tokens: int = None, temperature: float = None, final_query=True, use_crypto_prompt=False, task: str = "unknown") -> Dict[str, Any]:
        """
        Submit a prompt request to the LLM priority queue.
        
        Args:
            prompt: The prompt to send to the LLM
            attachments: Optional list of file paths to attach
            priority: Priority level (1 = email/high priority, 2 = moltbook/low priority)
            max_tokens: Optional max tokens parameter
            temperature: Optional temperature parameter
            final_query: Whether this is the final query in a conversation
            use_crypto_prompt: Whether to use crypto-specific prompting
            task: Which task is making this request (discord, email, newsletter, crypto, moltbook)
            
        Returns:
            Dict with 'response' (str) and 'generated_images' (List[str]) keys
        """
        if not self.running:
            raise RuntimeError("LLM Priority Queue Manager is not running")
        
        # Create request
        request = LLMRequest(
            prompt=prompt,
            attachments=attachments,
            priority=priority,
            max_tokens=max_tokens,
            temperature=temperature,
            final_query=final_query,
            use_crypto_prompt=use_crypto_prompt,
            task=task
        )
        
        # Add to priority queue
        self.priority_queue.put(request)
        logger.info(f"📝 LLM request queued (priority {priority})")
        
        # Block until response is ready
        try:
            result = request.future.result()  # This will block until the request is processed
            return result
        except Exception as e:
            logger.error(f"❌ LLM request failed: {e}")
            raise
    
    def get_queue_size(self) -> int:
        """Get the current size of the priority queue"""
        return self.priority_queue.qsize()
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed status information about the queue and current processing"""
        return {
            'queue_size': self.priority_queue.qsize(),
            'current_task': self.current_task,
            'current_request': {
                'task': self.current_request.task if self.current_request else None,
                'priority': self.current_request.priority if self.current_request else None,
                'timestamp': self.current_request.timestamp if self.current_request else None,
                'prompt_preview': self.current_request.prompt[:100] + '...' if self.current_request and len(self.current_request.prompt) > 100 else self.current_request.prompt if self.current_request else None
            } if self.current_request else None,
            'running': self.running,
            'llm_ready': self.llm_ready.is_set() if self.llm_ready else False
        }
    
    def shutdown(self):
        """Shutdown the priority queue manager"""
        logger.info("🛑 Shutting down LLM Priority Queue Manager...")
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
        logger.info("✅ LLM Priority Queue Manager shutdown complete")


# Global instance
llm_queue_manager = LLMPriorityQueueManager()


def submit_llm_request(prompt: str, attachments: List[str] = None, priority: int = 1,
                      max_tokens: int = None, temperature: float = None, final_query=True, use_crypto_prompt=False, task: str = "unknown") -> Dict[str, Any]:
    """
    Convenience function to submit LLM requests.
    
    Args:
        prompt: The prompt to send to the LLM
        attachments: Optional list of file paths to attach
        priority: Priority level (1 = email/high priority, 2 = moltbook/low priority)
        max_tokens: Optional max tokens parameter
        temperature: Optional temperature parameter
        final_query: Whether this is the final query in a conversation
        use_crypto_prompt: Whether to use crypto-specific prompting
        task: Which task is making this request (discord, email, newsletter, crypto, moltbook)
        
    Returns:
        Dict with 'response' (str) and 'generated_images' (List[str]) keys
    """
    return llm_queue_manager.submit_request(
        prompt=prompt,
        attachments=attachments,
        priority=priority,
        max_tokens=max_tokens,
        temperature=temperature,
        final_query=final_query,
        use_crypto_prompt=use_crypto_prompt,
        task=task
    )