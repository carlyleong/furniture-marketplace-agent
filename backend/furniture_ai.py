import cv2
import numpy as np
from typing import Dict, Any, List
import random
import openai
import os
from dotenv import load_dotenv
import json

load_dotenv()

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
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                # Updated initialization for newer OpenAI client versions
                self.client = openai.OpenAI(
                    api_key=self.api_key,
                    # Remove any deprecated parameters like 'proxies'
                )
                print("✅ OpenAI client initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize OpenAI client: {e}")
                print("   Will use fallback methods for analysis")
                self.client = None
        else:
            print("⚠️  OpenAI API key not found - using fallback analysis")

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze furniture image and return detailed insights"""
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

            # Generate detailed analysis using OpenAI
            analysis = self._generate_detailed_analysis(furniture_type, colors)

            return {
                "colors": colors,
                "furniture_type": furniture_type,
                "condition": random.choice(self.conditions),
                "style": analysis["style"],
                "materials": analysis["materials"],
                "dimensions": analysis["dimensions"],
                "features": analysis["features"],
                "suggested_price": analysis["suggested_price"],
                "suggested_title": analysis["suggested_title"]
            }
        except Exception as e:
            raise Exception(f"Error analyzing image: {str(e)}")

    def _generate_detailed_analysis(self, furniture_type: str, colors: List[str]) -> Dict[str, Any]:
        """Generate detailed furniture analysis using OpenAI"""
        try:
            if not self.client:
                raise Exception("OpenAI client not initialized")

            prompt = f"""Analyze this {furniture_type} with colors {', '.join(colors)} and provide:
            1. Style (Modern, Traditional, Contemporary, Rustic, etc.)
            2. Likely materials
            3. Estimated dimensions
            4. Key features
            5. Suggested price range
            6. Suggested title
            Format as JSON with these exact fields: style, materials, dimensions, features, suggested_price, suggested_title"""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a furniture expert. Provide detailed analysis in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            # Parse the response and return structured data
            analysis = response.choices[0].message.content.strip()
            return json.loads(analysis)
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fallback to basic analysis
            return {
                "style": random.choice(["Modern", "Traditional", "Contemporary", "Rustic"]),
                "materials": random.sample(["Wood", "Metal", "Fabric", "Glass", "Leather"], 2),
                "dimensions": "Standard size",
                "features": ["Good condition", "Well maintained"],
                "suggested_price": random.randint(50, 1000),
                "suggested_title": f"{furniture_type} - {random.choice(['Modern', 'Classic', 'Vintage'])} Style"
            }

    def _analyze_colors(self, img: np.ndarray) -> List[str]:
        """Analyze dominant colors in the image"""
        pixels = img.reshape(-1, 3)
        pixels = np.float32(pixels)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 0.1)
        k = 5
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        centers = np.uint8(centers)
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
        """Generate an enhanced description for the furniture listing using OpenAI"""
        if current_description:
            return current_description

        prompt = (
            f"Write a compelling, professional, and friendly Facebook Marketplace description for a "
            f"{condition.lower()} {category.lower()} titled '{title}'. "
            f"Highlight its best features and suggest possible uses. Keep it under 80 words."
        )

        try:
            if not self.client:
                raise Exception("OpenAI client not initialized")

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for writing furniture listings."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=120,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return f"{condition} {category}: {title}"

    def suggest_listing_details(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest listing details based on image analysis"""
        return {
            "suggested_price": analysis.get("suggested_price", random.randint(50, 1000)),
            "suggested_title": analysis.get("suggested_title", f"{analysis['furniture_type']} - {analysis['style']} Style"),
            "suggested_description": self.generate_description(
                analysis['furniture_type'],
                analysis['condition'],
                analysis['furniture_type']
            ),
            "suggested_tags": analysis.get("materials", []) + [analysis.get("style", "")]
        } 