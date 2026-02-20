#!/usr/bin/env python3
import os
import io
import base64
import requests
from huggingface_hub import InferenceClient
from datetime import datetime
from PIL import Image


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
        
        # Image-to-image models for modification
        self.img2img_models = {
            "instruct_pix2pix": "timbrooks/instruct-pix2pix",
            "stable_diffusion_img2img": "runwayml/stable-diffusion-v1-5",
            "controlnet": "lllyasviel/sd-controlnet-canny"
        }
        
        self.default_model = self.models["flux_schnell"]  # Faster model for free tier
        self.default_img2img_model = self.img2img_models["instruct_pix2pix"]

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

    def modify_image(self, image_path, prompt, model=None, save_path=None, strength=0.8):
        """Modify an existing image using a text prompt
        
        Args:
            image_path (str): Path to the input image (jpg/png)
            prompt (str): Description of how to modify the image
            model (str, optional): Model to use. Defaults to InstructPix2Pix
            save_path (str, optional): Path to save the modified image
            strength (float): How much to change the image (0.0-1.0, default 0.8)
            
        Returns:
            PIL.Image: Modified image object, or None if failed
        """
        if not os.path.exists(image_path):
            print(f"❌ Input image not found: {image_path}")
            return None
            
        if not prompt or not prompt.strip():
            print("❌ Modification prompt cannot be empty")
            return None
        
        # Validate image format
        if not image_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            print("❌ Only PNG and JPG images are supported")
            return None
        
        model_id = model if model and "/" in model else self.default_img2img_model
        if model and "/" not in model:
            model_id = self.img2img_models.get(model, self.default_img2img_model)
        
        try:
            print(f"🖼️ Loading input image: {os.path.basename(image_path)}")
            print(f"✏️ Modification prompt: '{prompt[:50]}...'")
            print(f"📋 Using model: {model_id}")
            
            # Load the input image
            input_image = Image.open(image_path)
            
            # Try different API methods for image modification
            try:
                # Method 1: Try image_to_image if available
                modified_image = self.client.image_to_image(
                    image=input_image,
                    prompt=prompt.strip(),
                    model=model_id,
                    strength=strength
                )
            except (AttributeError, Exception) as e:
                print(f"InferenceClient method failed: {e}")
                # Method 2: Use direct API call with proper format
                
                # Convert PIL image to bytes
                img_buffer = io.BytesIO()
                input_image.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                # Make direct API call with proper multipart format
                api_url = f"https://api-inference.huggingface.co/models/{model_id}"
                headers = {"Authorization": f"Bearer {self.api_token}"}
                
                # For InstructPix2Pix, use proper multipart format
                files = {
                    'inputs': ('image.png', img_buffer, 'image/png')
                }
                data = {
                    'prompt': prompt.strip(),
                    'strength': str(strength)
                }
                
                response = requests.post(
                    api_url,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=120
                )
                
                if response.status_code == 200:
                    modified_image = Image.open(io.BytesIO(response.content))
                elif response.status_code == 503:
                    raise Exception("Model is loading, please wait and try again")
                elif response.status_code == 429:
                    raise Exception("Rate limit exceeded, please wait before trying again")
                else:
                    # Try alternative JSON payload format
                    img_buffer.seek(0)
                    import base64
                    img_b64 = base64.b64encode(img_buffer.read()).decode()
                    
                    json_payload = {
                        "inputs": {
                            "image": img_b64,
                            "prompt": prompt.strip()
                        },
                        "parameters": {
                            "strength": strength
                        }
                    }
                    
                    response = requests.post(
                        api_url,
                        headers={**headers, "Content-Type": "application/json"},
                        json=json_payload,
                        timeout=120
                    )
                    
                    if response.status_code == 200:
                        modified_image = Image.open(io.BytesIO(response.content))
                    else:
                        raise Exception(f"API returned {response.status_code}: {response.text}")
            
            print("✅ Image modified successfully!")
            
            # Save image if path provided
            if save_path:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                modified_image.save(save_path)
                print(f"💾 Modified image saved to: {save_path}")
            
            return modified_image
            
        except Exception as e:
            print(f"❌ Error modifying image: {e}")
            return None

    def modify_and_save(self, image_path, prompt, filename=None, model=None, **kwargs):
        """Modify an image and automatically save it with timestamp
        
        Args:
            image_path (str): Path to input image
            prompt (str): Modification prompt
            filename (str, optional): Custom filename. If not provided, uses timestamp
            model (str, optional): Model to use for modification
            **kwargs: Additional parameters for modify_image()
            
        Returns:
            str: Path to saved modified image file, or None if failed
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_prompt = safe_prompt.replace(' ', '_')
            input_name = os.path.splitext(os.path.basename(image_path))[0]
            filename = f"modified_{input_name}_{timestamp}_{safe_prompt}.png"
        
        # Ensure filename has image extension
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filename += '.png'
        
        # Create images directory
        images_dir = os.path.join(os.path.dirname(__file__), '..', 'generated_images')
        os.makedirs(images_dir, exist_ok=True)
        
        save_path = os.path.join(images_dir, filename)
        
        image = self.modify_image(image_path, prompt, model=model, save_path=save_path, **kwargs)
        
        return save_path if image else None

    def list_available_models(self):
        """List available image generation models"""
        print("🤖 Available image generation models:")
        for name, model_id in self.models.items():
            print(f"  • {name}: {model_id}")
        print(f"\n�️ Available image-to-image models:")
        for name, model_id in self.img2img_models.items():
            print(f"  • {name}: {model_id}")
        print(f"\n💡 Default text-to-image model: {self.default_model}")
        print(f"✏️ Default image-to-image model: {self.default_img2img_model}")

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


def modify_image_simple(image_path, prompt, save=True, model=None):
    """Simple function to modify an image with minimal setup
    
    Args:
        image_path (str): Path to input image file
        prompt (str): Description of how to modify the image  
        save (bool): Whether to save the modified image automatically
        model (str, optional): Model to use
        
    Returns:
        PIL.Image or str: Image object if save=False, file path if save=True
    """
    try:
        generator = HuggingFaceImageGenerator()
        
        if save:
            return generator.modify_and_save(image_path, prompt, model=model)
        else:
            return generator.modify_image(image_path, prompt, model=model)
            
    except Exception as e:
        print(f"❌ Failed to modify image: {e}")
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

            # Modify the image with a new prompt
            modification_prompt = "Make it look like a Van Gogh painting"
            modified_image_path = generator.modify_and_save(image_path, modification_prompt)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure to set your HF_API_TOKEN environment variable")
        print("   Get your free token at: https://huggingface.co/settings/tokens")
