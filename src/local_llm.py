#!/usr/bin/env python3
"""
Local LLM Test using GGUF models via llama-cpp-python on Raspberry Pi 5
Tests local LLM models running via llama.cpp backend for text generation.
"""

import time
import os
from llama_cpp import Llama


class LocalLLM:
    def __init__(self, model_path=None, n_ctx=2048, n_threads=4):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.model = None
        
        print(f"Local LLM Configuration:")
        print(f"  Model Path: {self.model_path}")
        print(f"  Context Length: {self.n_ctx}")
        print(f"  CPU Threads: {self.n_threads}")

        self.load_model()

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
    
    def prompt(self, prompt, max_tokens=256, temperature=0.7, stop=None):
        """Generate a response using the loaded model"""
        if self.model is None:
            print("❌ Model not loaded. Call load_model() first.")
            return None
        
        print(f"🤔 Generating response for: \"{prompt[:50]}...\"")
        start_time = time.time()
        
        try:
            # Format prompt - simple format for compatibility
            formatted_prompt = f"User: {prompt}\nAssistant: "
            
            # Generate response
            output = self.model(
                formatted_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop or ["User:"],  # Removed "\n\n" to allow multi-line responses
                echo=False
            )
            
            response = output['choices'][0]['text'].strip()
            
            generation_time = time.time() - start_time
            tokens_generated = output['usage']['completion_tokens']
            tokens_per_second = tokens_generated / generation_time if generation_time > 0 else 0
            
            print(f"⚡ Generated {tokens_generated} tokens in {generation_time:.1f}s ({tokens_per_second:.1f} tokens/s)")
            
            return response
            
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            return None
