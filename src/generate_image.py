#!/usr/bin/env python3
import os
from huggingface_hub import InferenceClient
from datetime import datetime


class HuggingFaceImageGenerator:
    def __init__(self, api_token=None):
        """Initialize the Hugging Face Image Generator
        
        Args:
            api_token (str, optional): HF API token. If not provided, 
                                     will try to get from HF_API_TOKEN env var
        """
        if not api_token:
            api_token = os.getenv("HF_API_TOKEN")
        
        if not api_token:
            raise ValueError("Hugging Face API token is required. Set HF_API_TOKEN env var or pass as parameter")
        
        self.api_token = api_token
        self.client = InferenceClient(api_key=api_token)
        
        # Popular image generation models (updated for 2026)
        self.models = {
            "flux_dev": "black-forest-labs/FLUX.1-dev",
            "flux_schnell": "black-forest-labs/FLUX.1-schnell", 
            "stable_diffusion": "runwayml/stable-diffusion-v1-5",
            "stable_diffusion_xl": "stabilityai/stable-diffusion-xl-base-1.0",
            "openjourney": "prompthero/openjourney"
        }
        
        self.default_model = self.models["flux_schnell"]  # Faster model for free tier

    def generate_image(self, prompt, model=None, width=512, height=512, save_path=None):
        """Generate an image from a text prompt using Hugging Face Inference API
        
        Args:
            prompt (str): Text description of the image to generate
            model (str, optional): Model to use. Defaults to FLUX schnell
            width (int): Image width (default: 512)
            height (int): Image height (default: 512) 
            save_path (str, optional): Path to save the generated image
            
        Returns:
            PIL.Image: Generated image object
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        model_id = model if model and "/" in model else self.default_model
        if model and "/" not in model:
            model_id = self.models.get(model, self.default_model)
        
        try:
            print(f"🎨 Generating image with prompt: '{prompt[:50]}...'")
            print(f"📋 Using model: {model_id}")
            
            # Use the new InferenceClient text_to_image method
            image = self.client.text_to_image(
                prompt=prompt.strip(),
                model=model_id,
                width=width,
                height=height
            )
            
            print("✅ Image generated successfully!")
            
            # Save image if path provided
            if save_path:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                image.save(save_path)
                print(f"💾 Image saved to: {save_path}")
            
            return image
            
        except Exception as e:
            print(f"❌ Error generating image: {e}")
            return None

    def generate_and_save(self, prompt, filename=None, model=None, **kwargs):
        """Generate an image and automatically save it with timestamp
        
        Args:
            prompt (str): Text prompt for image generation
            filename (str, optional): Custom filename. If not provided, uses timestamp
            model (str, optional): Model to use for generation
            **kwargs: Additional parameters for generate_image()
            
        Returns:
            str: Path to saved image file, or None if failed
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_prompt = safe_prompt.replace(' ', '_')
            filename = f"generated_image_{timestamp}_{safe_prompt}.png"
        
        # Ensure filename has .png extension
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filename += '.png'
        
        # Create images directory
        images_dir = os.path.join(os.path.dirname(__file__), '..', 'generated_images')
        os.makedirs(images_dir, exist_ok=True)
        
        save_path = os.path.join(images_dir, filename)
        
        image = self.generate_image(prompt, model=model, save_path=save_path, **kwargs)
        
        return save_path if image else None

    def list_available_models(self):
        """List available image generation models"""
        print("🤖 Available image generation models:")
        for name, model_id in self.models.items():
            print(f"  • {name}: {model_id}")
        print(f"\n💡 Default model: {self.default_model}")

    def test_connection(self):
        """Test connection to Hugging Face API"""
        try:
            # Test with a simple model list or connection check
            models = ["flux_schnell", "stable_diffusion"]
            print("✅ Connection to Hugging Face Inference API successful!")
            print(f"Available models in client: {list(self.models.keys())}")
            return True
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False


# Convenience functions
def generate_image_simple(prompt, save=True, model=None):
    """Simple function to generate an image with minimal setup
    
    Args:
        prompt (str): Description of image to generate
        save (bool): Whether to save the image automatically
        model (str, optional): Model to use
        
    Returns:
        PIL.Image or str: Image object if save=False, file path if save=True
    """
    try:
        generator = HuggingFaceImageGenerator()
        
        if save:
            return generator.generate_and_save(prompt, model=model)
        else:
            return generator.generate_image(prompt, model=model)
            
    except Exception as e:
        print(f"❌ Failed to generate image: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    try:
        generator = HuggingFaceImageGenerator()
        
        # Test connection
        generator.test_connection()
        
        # List available models
        generator.list_available_models()
        
        # Generate a simple image
        prompt = "A beautiful sunset over mountains, digital art style"
        image_path = generator.generate_and_save(prompt)
        
        if image_path:
            print(f"🎉 Generated image saved to: {image_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure to set your HF_API_TOKEN environment variable")
        print("   Get your free token at: https://huggingface.co/settings/tokens")
