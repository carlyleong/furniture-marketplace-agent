from PIL import Image, ImageEnhance
import os
import cv2
import numpy as np

class ImageProcessor:
    def __init__(self):
        self.max_size = (1200, 1200)
        self.quality = 85

    def process_image(self, input_path: str, output_path: str) -> str:
        """Process and optimize an image"""
        try:
            # Open image
            img = Image.open(input_path)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large
            if img.size[0] > self.max_size[0] or img.size[1] > self.max_size[1]:
                img.thumbnail(self.max_size, Image.Resampling.LANCZOS)
            
            # Enhance image
            img = self._enhance_image(img)
            
            # Save processed image
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            img.save(output_path, 'JPEG', quality=self.quality, optimize=True)
            
            return output_path
        except Exception as e:
            raise Exception(f"Error processing image: {str(e)}")

    def _enhance_image(self, img: Image.Image) -> Image.Image:
        """Enhance image quality"""
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        # Enhance brightness
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.3)
        
        return img

    def create_thumbnail(self, input_path: str, output_path: str, size: tuple = (300, 300)) -> str:
        """Create a thumbnail version of the image"""
        try:
            img = Image.open(input_path)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Create thumbnail
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            img.save(output_path, 'JPEG', quality=85, optimize=True)
            
            return output_path
        except Exception as e:
            raise Exception(f"Error creating thumbnail: {str(e)}") 