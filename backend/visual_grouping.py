"""
Enhanced Visual Grouping System for LangGraph Furniture Classifier
Replaces the current AI grouping agent with more reliable visual similarity
"""

import numpy as np
from typing import List, Dict, Any, Tuple
import base64
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
import cv2
from PIL import Image
import os
from difflib import SequenceMatcher
from dataclasses import dataclass

@dataclass
class FurnitureAttributes:
    """Structured representation of furniture attributes"""
    type: str
    color: str
    material: str
    style: str
    condition: str
    size_indicators: List[str]
    
    @classmethod
    def from_item(cls, item: Dict[str, Any]) -> 'FurnitureAttributes':
        """Extract attributes from LangGraph analysis item"""
        vision = item.get("vision", {})
        classification = item.get("classification", {})
        
        return cls(
            type=vision.get("furniture_type", "").lower(),
            color=vision.get("visual_details", {}).get("primary_color", "").lower(),
            material=classification.get("material", "").lower(),
            style=classification.get("style", "").lower(),
            condition=classification.get("condition", "").lower(),
            size_indicators=cls._extract_size_indicators(vision, classification)
        )
    
    @staticmethod
    def _extract_size_indicators(vision: Dict, classification: Dict) -> List[str]:
        """Extract size-related terms from descriptions"""
        size_terms = []
        size_keywords = [
            'small', 'medium', 'large', 'mini', 'compact', 'oversized',
            'twin', 'full', 'queen', 'king', 'single', 'double', 'triple',
            'narrow', 'wide', 'tall', 'short', 'low', 'high'
        ]
        
        text_fields = [
            vision.get("furniture_type", ""),
            classification.get("subcategory", ""),
            classification.get("detailed_analysis", ""),
        ]
        
        for text in text_fields:
            if text:
                words = text.lower().split()
                size_terms.extend([word for word in words if word in size_keywords])
        
        return list(set(size_terms))

class EnhancedGroupingAgent:
    """
    Enhanced grouping system that replaces the current _ai_grouping_agent
    Uses visual embeddings + rule-based fallbacks for reliable grouping
    """
    
    def __init__(self, openai_client=None):
        self.client = openai_client
        
        # Define furniture category synonyms (from existing system)
        self.furniture_synonyms = {
            'seating': {
                'chair', 'seat', 'stool', 'bench', 'armchair', 'recliner', 
                'rocker', 'gaming chair', 'office chair', 'dining chair'
            },
            'tables': {
                'table', 'desk', 'surface', 'workstation', 'console', 
                'coffee table', 'dining table', 'end table', 'side table'
            },
            'storage': {
                'cabinet', 'dresser', 'shelf', 'bookcase', 'bookshelf', 
                'chest', 'armoire', 'wardrobe', 'hutch', 'credenza'
            },
            'beds': {
                'bed', 'mattress', 'headboard', 'footboard', 'bedframe',
                'daybed', 'futon', 'sofa bed'
            },
            'sofas': {
                'sofa', 'couch', 'sectional', 'loveseat', 'settee', 
                'divan', 'chaise', 'ottoman'
            }
        }
        
        # Color synonym groups
        self.color_groups = {
            'white_family': {'white', 'off-white', 'ivory', 'cream', 'beige', 'ecru'},
            'black_family': {'black', 'ebony', 'charcoal', 'dark gray', 'dark grey'},
            'brown_family': {'brown', 'tan', 'coffee', 'mocha', 'chocolate', 'walnut', 'oak'},
            'gray_family': {'gray', 'grey', 'silver', 'slate', 'ash'},
            'wood_family': {'wood', 'wooden', 'natural', 'pine', 'cedar', 'maple'}
        }
    
    def group_furniture_images(self, all_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Main grouping method - DIRECT REPLACEMENT for _ai_grouping_agent
        Returns the same format as the original method
        """
        print(f"🔍 Enhanced Grouping Agent analyzing {len(all_items)} images...")
        
        if len(all_items) <= 1:
            return self._create_individual_groups(all_items)
        
        try:
            # Method 1: Try visual embeddings (most accurate)
            if self.client:
                groups = self._group_by_visual_embeddings(all_items)
                if groups:
                    print("✅ Used visual embedding grouping")
                    return groups
        except Exception as e:
            print(f"⚠️ Visual embeddings failed: {e}")
        
        try:
            # Method 2: Use structured comparison (reliable fallback)
            groups = self._group_by_structured_comparison(all_items)
            if groups:
                print("✅ Used structured comparison grouping")
                return groups
        except Exception as e:
            print(f"⚠️ Structured comparison failed: {e}")
        
        # Method 3: Simple heuristics (final fallback)
        print("✅ Using heuristic grouping (final fallback)")
        return self._group_by_heuristics(all_items)
    
    def _group_by_visual_embeddings(self, all_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group using OpenAI vision embeddings for visual similarity"""
        embeddings = []
        valid_items = []
        
        for item in all_items:
            try:
                # Get the image path from the vision data
                image_path = item["vision"].get("image_path")
                if not image_path or not os.path.exists(image_path):
                    continue
                    
                embedding = self._get_image_embedding(image_path)
                if embedding is not None:
                    embeddings.append(embedding)
                    valid_items.append(item)
            except Exception as e:
                print(f"⚠️ Embedding failed for image: {e}")
                continue
        
        if len(embeddings) < 2:
            return self._create_individual_groups(valid_items)
        
        # Calculate similarity and cluster
        embeddings_array = np.array(embeddings)
        similarity_matrix = cosine_similarity(embeddings_array)
        distance_matrix = 1 - similarity_matrix
        
        # Furniture-specific clustering parameters
        eps = 0.3  # Grouping threshold
        min_samples = 1
        
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
        cluster_labels = clustering.fit_predict(distance_matrix)
        
        # Convert clusters to groups
        groups = {}
        for idx, label in enumerate(cluster_labels):
            if label == -1:  # Noise points become individual groups
                label = f"single_{idx}"
            
            if label not in groups:
                groups[label] = []
            groups[label].append(valid_items[idx])
        
        # Convert to final format (matching original structure)
        final_groups = []
        for i, (label, items) in enumerate(groups.items()):
            group = self._create_group_from_items(items, f"visual_group_{i}")
            final_groups.append(group)
            print(f"    📸 Visual Group {i+1}: {len(items)} photos")
            
        return final_groups
    
    def _get_image_embedding(self, image_path: str) -> np.ndarray:
        """Get visual embedding using OpenAI or local features"""
        try:
            # Use OpenAI vision model for embeddings
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this furniture in exactly 50 words focusing on: type, color, material, style, size. Be consistent and precise."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }],
                max_tokens=100
            )
            
            description = response.choices[0].message.content
            
            # Convert to embedding
            embedding_response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=description
            )
            
            return np.array(embedding_response.data[0].embedding)
            
        except Exception as e:
            print(f"⚠️ OpenAI embedding failed: {e}")
            return self._get_local_visual_features(image_path)
    
    def _get_local_visual_features(self, image_path: str) -> np.ndarray:
        """Fallback: Extract local visual features using OpenCV"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return None
            
            # Convert to HSV for better color analysis
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            features = []
            
            # Color histogram features
            hist_h = cv2.calcHist([hsv], [0], None, [12], [0, 180])
            hist_s = cv2.calcHist([hsv], [1], None, [8], [0, 256])
            hist_v = cv2.calcHist([hsv], [2], None, [8], [0, 256])
            
            features.extend(hist_h.flatten())
            features.extend(hist_s.flatten()) 
            features.extend(hist_v.flatten())
            
            # Edge density (furniture outline/shape)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            features.append(edge_density)
            
            # Texture features
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            features.append(laplacian_var / 1000)
            
            # Aspect ratio
            h, w = img.shape[:2]
            aspect_ratio = w / h
            features.append(aspect_ratio)
            
            return np.array(features, dtype=np.float32)
            
        except Exception as e:
            print(f"⚠️ Local feature extraction failed: {e}")
            return None
    
    def _group_by_structured_comparison(self, all_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group using structured data comparison - matches existing system logic"""
        # Extract structured attributes
        furniture_attrs = [FurnitureAttributes.from_item(item) for item in all_items]
        
        # Calculate similarity matrix
        n = len(all_items)
        similarity_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i, n):
                if i == j:
                    similarity_matrix[i][j] = 1.0
                else:
                    sim = self._calculate_furniture_similarity(furniture_attrs[i], furniture_attrs[j])
                    similarity_matrix[i][j] = sim
                    similarity_matrix[j][i] = sim
        
        # Group based on similarity threshold
        threshold = 0.7  # Same as existing system
        groups = []
        used_indices = set()
        
        for i in range(n):
            if i in used_indices:
                continue
            
            group_indices = [i]
            used_indices.add(i)
            
            for j in range(i + 1, n):
                if j not in used_indices and similarity_matrix[i][j] >= threshold:
                    group_indices.append(j)
                    used_indices.add(j)
            
            group_items = [all_items[idx] for idx in group_indices]
            group = self._create_group_from_items(group_items, f"structured_group_{len(groups)}")
            groups.append(group)
            
            print(f"    📊 Structured Group {len(groups)}: {len(group_items)} photos")
        
        return groups
    
    def _calculate_furniture_similarity(self, attr1: FurnitureAttributes, attr2: FurnitureAttributes) -> float:
        """Calculate similarity between two furniture items using existing logic"""
        def text_similarity(text1: str, text2: str) -> float:
            t1, t2 = text1.lower().strip(), text2.lower().strip()
            if not t1 or not t2:
                return 0.0
            if t1 == t2:
                return 1.0
            
            # Check for partial matches
            words1 = set(t1.split())
            words2 = set(t2.split())
            if words1 and words2:
                intersection = len(words1.intersection(words2))
                union = len(words1.union(words2))
                return intersection / union if union > 0 else 0.0
            return 0.0
        
        # Define weights (same as existing system)
        weights = {
            'furniture_type': 0.4,
            'color': 0.3,
            'material': 0.2,
            'style': 0.1
        }
        
        # Calculate individual similarities
        similarities = {
            'furniture_type': text_similarity(attr1.type, attr2.type),
            'color': text_similarity(attr1.color, attr2.color),
            'material': text_similarity(attr1.material, attr2.material),
            'style': text_similarity(attr1.style, attr2.style)
        }
        
        # Weighted average
        total_similarity = sum(similarities[attr] * weights[attr] for attr in weights)
        return total_similarity
    
    def _group_by_heuristics(self, all_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simple heuristic-based grouping (uses existing _calculate_title_similarity logic)"""
        groups = []
        used_indices = set()
        
        for i, item in enumerate(all_items):
            if i in used_indices:
                continue
            
            group_items = [item]
            used_indices.add(i)
            
            # Get basic attributes
            item_type = item["vision"].get("furniture_type", "").lower()
            item_color = item["vision"].get("visual_details", {}).get("primary_color", "").lower()
            
            for j, other_item in enumerate(all_items[i+1:], i+1):
                if j in used_indices:
                    continue
                
                other_type = other_item["vision"].get("furniture_type", "").lower()
                other_color = other_item["vision"].get("visual_details", {}).get("primary_color", "").lower()
                
                # Use existing title similarity logic (from main.py)
                should_group = self._should_group_heuristic(item_type, item_color, other_type, other_color)
                
                if should_group:
                    group_items.append(other_item)
                    used_indices.add(j)
            
            group = self._create_group_from_items(group_items, f"heuristic_group_{len(groups)}")
            groups.append(group)
            print(f"    🔧 Heuristic Group {len(groups)}: {len(group_items)} photos")
        
        return groups
    
    def _should_group_heuristic(self, type1: str, color1: str, type2: str, color2: str) -> bool:
        """Simple grouping heuristics"""
        # Exact type and color match
        if type1 and type2 and type1 == type2:
            if color1 and color2 and color1 == color2:
                return True
        
        # Same furniture category
        for category, keywords in self.furniture_synonyms.items():
            if (any(kw in type1 for kw in keywords) and 
                any(kw in type2 for kw in keywords)):
                return True
        
        return False
    
    def _create_group_from_items(self, items: List[Dict], group_id: str) -> Dict[str, Any]:
        """Create a group in the EXACT format expected by the existing system"""
        if not items:
            return {}
        
        primary_item = items[0]
        
        # Calculate aggregated values (same as original)
        total_price = sum(item["pricing"].get("suggested_price", 100) for item in items)
        avg_confidence = sum(item["classification"].get("classification_confidence", 0.5) for item in items) / len(items)
        
        # Return in EXACT format expected by existing system
        return {
            "group_id": group_id,
            "primary_category": primary_item["classification"].get("category", "Furniture"),
            "subcategory": primary_item["classification"].get("subcategory", ""),
            "style": primary_item["classification"].get("style", ""),
            "material": primary_item["classification"].get("material", ""),
            "all_items": items,
            "total_price": total_price,
            "avg_confidence": avg_confidence,
            "avg_price": total_price // len(items),
            "ai_reasoning": f"Enhanced grouping: {len(items)} photos grouped by visual similarity",
            "ai_description": primary_item["vision"].get("furniture_type", "Furniture")
        }
    
    def _create_individual_groups(self, items: List[Dict]) -> List[Dict[str, Any]]:
        """Create individual groups for each item"""
        return [self._create_group_from_items([item], f"single_{i}") for i, item in enumerate(items)]
