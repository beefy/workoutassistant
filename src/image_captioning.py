#!/usr/bin/env python3
"""
Local Image Captioning Module
Provides lightweight image analysis using open source models optimized for local execution.
"""

import os
import torch
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import warnings

# Suppress some transformer warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)


class LocalImageCaptioner:
    """Local image captioning using BLIP model optimized for CPU inference"""
    
    def __init__(self, model_name="Salesforce/blip-image-captioning-base"):
        """
        Initialize the local image captioning model
        
        Args:
            model_name (str): Hugging Face model identifier. 
                            Default uses BLIP-base (~1.2GB, good for Pi/CPU)
        """
        self.model_name = model_name
        self.processor = None
        self.model = None
        self.device = "cpu"  # Force CPU for compatibility
        
        # Check if we're on Raspberry Pi
        self.is_pi = self._is_raspberry_pi()
        
        self._load_model()
    
    def _is_raspberry_pi(self):
        """Detect if running on Raspberry Pi"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                return 'raspberry' in f.read().lower()
        except:
            return False
    
    def _load_model(self):
        """Load the image captioning model and processor"""
        try:
            print(f"🤖 Loading local image captioning model: {self.model_name}")
            if self.is_pi:
                print("🍓 Raspberry Pi detected - optimizing for CPU")
            
            # Load processor
            print("📋 Loading image processor...")
            self.processor = BlipProcessor.from_pretrained(self.model_name)
            
            # Load model with CPU optimization
            print("🧠 Loading language model...")
            self.model = BlipForConditionalGeneration.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,  # Use float32 for CPU compatibility
                device_map="cpu",
                low_cpu_mem_usage=True  # Optimize memory usage
            )
            
            # Set to evaluation mode
            self.model.eval()
            
            print("✅ Local image captioning model loaded successfully!")
            
        except Exception as e:
            print(f"❌ Failed to load local image captioning model: {e}")
            print("💡 Try installing: pip install torch transformers pillow")
            self.model = None
            self.processor = None
    
    def is_available(self):
        """Check if the local model is available for use"""
        return self.model is not None and self.processor is not None
    
    def caption_image(self, image_path, max_length=50, num_beams=4):
        """
        Generate a caption for an image using the local model
        
        Args:
            image_path (str): Path to the image file
            max_length (int): Maximum length of generated caption
            num_beams (int): Number of beams for beam search (higher = better quality, slower)
            
        Returns:
            str: Generated image caption or error message
        """
        if not self.is_available():
            return "❌ Local image captioning model not available"
        
        if not os.path.exists(image_path):
            return f"❌ Image file not found: {image_path}"
        
        try:
            print(f"🔍 Analyzing image: {os.path.basename(image_path)}")
            
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            
            # Process image for model input
            inputs = self.processor(image, return_tensors="pt")
            
            # Generate caption
            print("🧠 Generating caption..." + (" (This may take 10-30 seconds on Pi)" if self.is_pi else ""))
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=num_beams,
                    do_sample=False,
                    early_stopping=True
                )
            
            # Decode the generated caption
            caption = self.processor.decode(outputs[0], skip_special_tokens=True)
            
            # Remove any "caption" prefix that BLIP sometimes adds
            caption = caption.replace("a picture of ", "").replace("an image of ", "")
            caption = caption.strip().capitalize()
            
            print("✅ Caption generated successfully!")
            return caption
            
        except Exception as e:
            return f"❌ Error generating caption: {e}"
    
    def analyze_image_with_question(self, image_path, question, max_length=50):
        """
        Answer a question about an image using visual question answering
        
        Args:
            image_path (str): Path to the image file
            question (str): Question to ask about the image
            max_length (int): Maximum length of generated answer
            
        Returns:
            str: Generated answer or error message
        """
        if not self.is_available():
            return "❌ Local image captioning model not available"
        
        if not os.path.exists(image_path):
            return f"❌ Image file not found: {image_path}"
        
        try:
            print(f"🔍 Analyzing image: {os.path.basename(image_path)}")
            print(f"❓ Question: {question}")
            
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            
            # Process image and question for model input
            inputs = self.processor(image, question, return_tensors="pt")
            
            # Generate answer
            print("🧠 Generating answer..." + (" (This may take 10-30 seconds on Pi)" if self.is_pi else ""))
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=4,
                    do_sample=False,
                    early_stopping=True
                )
            
            # Decode the generated answer
            answer = self.processor.decode(outputs[0], skip_special_tokens=True)
            answer = answer.strip().capitalize()
            
            print("✅ Answer generated successfully!")
            return answer
            
        except Exception as e:
            return f"❌ Error generating answer: {e}"
    
    def get_model_info(self):
        """Get information about the loaded model"""
        if not self.is_available():
            return "❌ No model loaded"
        
        info = {
            "model_name": self.model_name,
            "device": self.device,
            "is_raspberry_pi": self.is_pi,
            "model_parameters": sum(p.numel() for p in self.model.parameters()),
            "memory_usage": "~1-2GB RAM during inference"
        }
        
        return info


# Convenience functions for easy usage
def caption_image_local(image_path, model_name="Salesforce/blip-image-captioning-base"):
    """
    Simple function to caption an image using local model
    
    Args:
        image_path (str): Path to image file
        model_name (str): Model to use (default: BLIP-base)
        
    Returns:
        str: Image caption
    """
    captioner = LocalImageCaptioner(model_name)
    return captioner.caption_image(image_path)


def ask_about_image_local(image_path, question, model_name="Salesforce/blip-image-captioning-base"):
    """
    Simple function to ask a question about an image using local model
    
    Args:
        image_path (str): Path to image file
        question (str): Question about the image
        model_name (str): Model to use (default: BLIP-base)
        
    Returns:
        str: Answer to the question
    """
    captioner = LocalImageCaptioner(model_name)
    return captioner.analyze_image_with_question(image_path, question)


if __name__ == "__main__":
    # Example usage and testing
    try:
        print("🧪 Testing Local Image Captioning")
        
        # Initialize captioner
        captioner = LocalImageCaptioner()
        
        if captioner.is_available():
            print("✅ Model loaded successfully!")
            print(f"📊 Model info: {captioner.get_model_info()}")
            
            # Look for test image in generated_images folder
            test_image_dir = os.path.join(os.path.dirname(__file__), '..', 'generated_images')
            if os.path.exists(test_image_dir):
                image_files = [f for f in os.listdir(test_image_dir) 
                             if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                
                if image_files:
                    test_image = os.path.join(test_image_dir, image_files[0])
                    print(f"\n🖼️ Testing with image: {image_files[0]}")
                    
                    # Test basic captioning
                    caption = captioner.caption_image(test_image)
                    print(f"📝 Caption: {caption}")
                    
                    # Test question answering
                    question = "What colors are in this image?"
                    answer = captioner.analyze_image_with_question(test_image, question)
                    print(f"❓ Question: {question}")
                    print(f"💬 Answer: {answer}")
                    
                else:
                    print("⚠️ No test images found in generated_images folder")
            else:
                print("⚠️ generated_images folder not found")
                
        else:
            print("❌ Failed to load model")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("💡 Make sure to install required packages:")
        print("   pip install torch transformers pillow")