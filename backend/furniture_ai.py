import cv2
import numpy as np
from typing import Dict, Any, List
import random

class FurnitureAI:
    def __init__(self):
        self.furniture_categories = [
            "Sofa", "Chair", "Table", "Bed", "Cabinet", "Desk",
            "Bookshelf", "Dresser", "Coffee Table", "Dining Table"
        ]
        self.conditions = ["New", "Like New", "Good", "Fair", "Poor"]
        self.color_palette = {
            "brown": ["#8B4513", "#A0522D", "#D2691E"],
            "black": ["#000000", "#1C1C1C", "#363636"],
            "white": ["#FFFFFF", "#F5F5F5", "#FAFAFA"],
            "gray": ["#808080", "#A9A9A9", "#D3D3D3"],
            "beige": ["#F5F5DC", "#FAEBD7", "#FFE4C4"]
        }

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze furniture image and return insights"""
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise Exception("Could not read image")

            # Convert to RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Analyze colors
            colors = self._analyze_colors(img_rgb)

            # Detect edges
            edges = self._detect_edges(img_rgb)

            # Estimate furniture type
            furniture_type = self._estimate_furniture_type(image_path)

            return {
                "colors": colors,
                "furniture_type": furniture_type,
                "condition": random.choice(self.conditions),
                "style": random.choice(["Modern", "Traditional", "Contemporary", "Rustic"]),
                "materials": random.sample(["Wood", "Metal", "Fabric", "Glass", "Leather"], 2)
            }
        except Exception as e:
            raise Exception(f"Error analyzing image: {str(e)}")

    def _analyze_colors(self, img: np.ndarray) -> List[str]:
        """Analyze dominant colors in the image"""
        # Reshape image
        pixels = img.reshape(-1, 3)
        
        # Convert to float32
        pixels = np.float32(pixels)
        
        # Define criteria and apply kmeans
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 0.1)
        k = 5
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Convert centers to uint8
        centers = np.uint8(centers)
        
        # Get dominant colors
        colors = []
        for center in centers:
            color = f"#{center[0]:02x}{center[1]:02x}{center[2]:02x}"
            colors.append(color)
        
        return colors

    def _detect_edges(self, img: np.ndarray) -> np.ndarray:
        """Detect edges in the image"""
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        return edges

    def _estimate_furniture_type(self, image_path: str) -> str:
        """Estimate the type of furniture in the image"""
        # In a real implementation, this would use a trained ML model
        # For now, return a random category
        return random.choice(self.furniture_categories)

    def generate_description(self, title: str, condition: str, category: str, current_description: str = "") -> str:
        """Generate an enhanced description for the furniture listing"""
        if current_description:
            return current_description

        templates = [
            f"Beautiful {condition.lower()} {category.lower()} in excellent condition. {title}",
            f"Stunning {category.lower()} available for sale. {condition.lower()} condition. {title}",
            f"High-quality {category.lower()} for sale. {condition.lower()} condition. {title}"
        ]
        
        return random.choice(templates)

    def suggest_listing_details(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest listing details based on image analysis"""
        return {
            "suggested_price": random.randint(50, 1000),
            "suggested_title": f"{analysis['furniture_type']} - {analysis['style']} Style",
            "suggested_description": self.generate_description(
                analysis['furniture_type'],
                analysis['condition'],
                analysis['furniture_type']
            ),
            "suggested_tags": analysis['materials'] + [analysis['style']]
        } 