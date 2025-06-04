"""
LangGraph-Based Furniture Classification System
- Clean workflow with proper state management
- Reliable agent coordination 
- Professional Facebook Marketplace outputs
- Built on LangGraph for robust orchestration
"""

import os
import json
import base64
import asyncio
from typing import List, Dict, Any, Optional, TypedDict, Annotated
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import operator
import re
from collections import defaultdict

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

load_dotenv()

# Define the state that flows between agents
class FurnitureAnalysisState(TypedDict):
    """State object that flows through the LangGraph workflow"""
    # Input
    image_paths: List[str]
    current_image_index: int
    
    # Per-image analysis results
    vision_results: List[Dict[str, Any]]
    classification_results: List[Dict[str, Any]]
    pricing_results: List[Dict[str, Any]]
    
    # Grouped results
    furniture_groups: List[Dict[str, Any]]
    final_listings: List[Dict[str, Any]]
    
    # Workflow control
    current_step: str
    errors: List[str]
    processing_complete: bool
    
    # Metadata
    start_time: float
    total_images: int

class LangGraphFurnitureClassifier:
    """LangGraph-based furniture classification system"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = OpenAI(api_key=self.api_key)
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        
        # Facebook Marketplace categories
        self.fb_categories = {
            "Chair": "Home & Garden//Furniture//Chairs",
            "Table": "Home & Garden//Furniture//Tables",
            "Sofa": "Home & Garden//Furniture//Sofas & Loveseats",
            "Bed": "Home & Garden//Furniture//Beds & Mattresses",
            "Desk": "Home & Garden//Furniture//Desks",
            "Cabinet": "Home & Garden//Furniture//Cabinets & Storage",
            "Bookshelf": "Home & Garden//Furniture//Bookcases & Shelving",
            "Dresser": "Home & Garden//Furniture//Dressers & Armoires",
            "Nightstand": "Home & Garden//Furniture//Nightstands",
            "Ottoman": "Home & Garden//Furniture//Ottomans, Footrests & Poufs"
        }
        
        # Build the workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(FurnitureAnalysisState)
        
        # Add nodes for each processing step
        workflow.add_node("initialize", self._initialize_processing)
        workflow.add_node("vision_analysis", self._vision_analysis_node)
        workflow.add_node("classification", self._classification_node)
        workflow.add_node("pricing", self._pricing_node)
        workflow.add_node("grouping", self._grouping_node)
        workflow.add_node("listing_generation", self._listing_generation_node)
        workflow.add_node("finalize", self._finalize_results)
        
        # Define the workflow edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "vision_analysis")
        workflow.add_edge("vision_analysis", "classification")
        workflow.add_edge("classification", "pricing")
        workflow.add_edge("pricing", "grouping")
        workflow.add_edge("grouping", "listing_generation")
        workflow.add_edge("listing_generation", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    # Node implementations
    def _initialize_processing(self, state: FurnitureAnalysisState) -> FurnitureAnalysisState:
        """Initialize the processing workflow"""
        print(f"🚀 Initializing LangGraph workflow for {len(state['image_paths'])} images")
        
        state["current_image_index"] = 0
        state["vision_results"] = []
        state["classification_results"] = []
        state["pricing_results"] = []
        state["furniture_groups"] = []
        state["final_listings"] = []
        state["current_step"] = "vision_analysis"
        state["errors"] = []
        state["processing_complete"] = False
        state["start_time"] = datetime.now().timestamp()
        state["total_images"] = len(state["image_paths"])
        
        return state
    
    def _vision_analysis_node(self, state: FurnitureAnalysisState) -> FurnitureAnalysisState:
        """Vision analysis node - analyze each image with GPT-4V"""
        print("👁️ Vision Analysis Node: Analyzing images with GPT-4V")
        
        vision_results = []
        
        for i, image_path in enumerate(state["image_paths"]):
            try:
                print(f"  📸 Analyzing image {i+1}/{len(state['image_paths'])}: {os.path.basename(image_path)}")
                
                # Encode image
                base64_image = self._encode_image(image_path)
                
                # Vision analysis prompt
                vision_prompt = """
Analyze this furniture image and extract visual details.

Provide a JSON response with this structure:
{
    "furniture_detected": true,
    "furniture_type": "Chair",
    "visual_details": {
        "primary_color": "Black",
        "material_appearance": "Mesh fabric",
        "style_indicators": "Modern, ergonomic design",
        "condition_visible": "Good",
        "brand_visible": false,
        "unique_features": ["Adjustable height", "Armrests"]
    },
    "image_quality": "High",
    "analysis_confidence": 0.9
}

Focus on what you can clearly see in the image. Return only JSON.
"""
                
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": vision_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                                }
                            ]
                        }
                    ],
                    max_tokens=400,
                    temperature=0.1
                )
                
                # Parse response
                vision_result = self._parse_json_response(response.choices[0].message.content)
                vision_result["image_path"] = image_path
                vision_result["image_index"] = i
                
                vision_results.append(vision_result)
                print(f"    ✅ Detected: {vision_result.get('furniture_type', 'Unknown')}")
                
            except Exception as e:
                print(f"    ❌ Vision analysis failed for image {i+1}: {str(e)}")
                # Add fallback vision result
                vision_results.append({
                    "furniture_detected": True,
                    "furniture_type": "Furniture",
                    "visual_details": {
                        "primary_color": "Unknown",
                        "material_appearance": "Mixed materials",
                        "style_indicators": "Contemporary",
                        "condition_visible": "Good",
                        "brand_visible": False,
                        "unique_features": []
                    },
                    "image_quality": "Medium",
                    "analysis_confidence": 0.3,
                    "image_path": image_path,
                    "image_index": i,
                    "error": str(e)
                })
                state["errors"].append(f"Vision analysis failed for image {i+1}: {str(e)}")
        
        state["vision_results"] = vision_results
        state["current_step"] = "classification"
        
        print(f"✅ Vision analysis complete: {len(vision_results)} results")
        return state
    
    def _classification_node(self, state: FurnitureAnalysisState) -> FurnitureAnalysisState:
        """Classification node - determine specific furniture categories and attributes"""
        print("🏷️ Classification Node: Categorizing furniture items")
        
        classification_results = []
        
        for vision_result in state["vision_results"]:
            try:
                # Classification prompt using vision analysis
                classification_prompt = f"""
Based on the vision analysis, classify this furniture item for marketplace listing:

Vision Analysis:
- Furniture Type: {vision_result.get('furniture_type', 'Unknown')}
- Color: {vision_result.get('visual_details', {}).get('primary_color', 'Unknown')}
- Material: {vision_result.get('visual_details', {}).get('material_appearance', 'Unknown')}
- Style: {vision_result.get('visual_details', {}).get('style_indicators', 'Unknown')}
- Features: {vision_result.get('visual_details', {}).get('unique_features', [])}

Provide detailed classification as JSON:
{{
    "category": "Chair",
    "subcategory": "Office Chair",
    "material": "Mesh Fabric",
    "style": "Modern",
    "target_room": "Office",
    "key_features": ["Ergonomic", "Adjustable", "Swivel"],
    "facebook_category": "Home & Garden//Furniture//Chairs",
    "search_keywords": ["office chair", "mesh", "ergonomic"],
    "classification_confidence": 0.85
}}

Return only JSON.
"""
                
                response = self.llm.invoke([HumanMessage(content=classification_prompt)])
                
                classification_result = self._parse_json_response(response.content)
                classification_result["image_index"] = vision_result["image_index"]
                classification_result["source_vision"] = vision_result
                
                # Ensure Facebook category is set
                if "facebook_category" not in classification_result:
                    furniture_type = classification_result.get("category", "Furniture")
                    classification_result["facebook_category"] = self.fb_categories.get(furniture_type, "Home & Garden//Furniture")
                
                classification_results.append(classification_result)
                print(f"    ✅ Classified: {classification_result.get('subcategory', 'Unknown')}")
                
            except Exception as e:
                print(f"    ❌ Classification failed for image {vision_result['image_index']}: {str(e)}")
                # Fallback classification
                fallback = {
                    "category": vision_result.get("furniture_type", "Furniture"),
                    "subcategory": vision_result.get("furniture_type", "Furniture"),
                    "material": "Mixed Materials",
                    "style": "Contemporary",
                    "target_room": "Living Room",
                    "key_features": ["Well-maintained"],
                    "facebook_category": "Home & Garden//Furniture",
                    "search_keywords": ["furniture", "home"],
                    "classification_confidence": 0.3,
                    "image_index": vision_result["image_index"],
                    "source_vision": vision_result,
                    "error": str(e)
                }
                classification_results.append(fallback)
                state["errors"].append(f"Classification failed for image {vision_result['image_index']}: {str(e)}")
        
        state["classification_results"] = classification_results
        state["current_step"] = "pricing"
        
        print(f"✅ Classification complete: {len(classification_results)} results")
        return state
    
    def _pricing_node(self, state: FurnitureAnalysisState) -> FurnitureAnalysisState:
        """Pricing node - determine market-appropriate pricing"""
        print("💰 Pricing Node: Calculating market prices")
        
        pricing_results = []
        
        for classification_result in state["classification_results"]:
            try:
                # Pricing prompt
                pricing_prompt = f"""
Calculate appropriate Facebook Marketplace pricing for this furniture:

Item Details:
- Category: {classification_result.get('category', 'Unknown')}
- Subcategory: {classification_result.get('subcategory', 'Unknown')}
- Material: {classification_result.get('material', 'Unknown')}
- Style: {classification_result.get('style', 'Unknown')}
- Condition: {classification_result.get('source_vision', {}).get('visual_details', {}).get('condition_visible', 'Good')}
- Features: {classification_result.get('key_features', [])}

Consider:
1. Facebook Marketplace pricing norms
2. Furniture category price ranges
3. Condition impact on value
4. Material quality indicators

Provide pricing analysis as JSON:
{{
    "estimated_price": 120,
    "price_range": {{"min": 100, "max": 150}},
    "pricing_factors": ["Good condition", "Popular category", "Quality materials"],
    "market_position": "Competitive",
    "price_confidence": 0.8
}}

Return only JSON.
"""
                
                response = self.llm.invoke([HumanMessage(content=pricing_prompt)])
                
                pricing_result = self._parse_json_response(response.content)
                pricing_result["image_index"] = classification_result["image_index"]
                pricing_result["source_classification"] = classification_result
                
                pricing_results.append(pricing_result)
                print(f"    ✅ Priced: ${pricing_result.get('estimated_price', 100)}")
                
            except Exception as e:
                print(f"    ❌ Pricing failed for image {classification_result['image_index']}: {str(e)}")
                # Fallback pricing
                category = classification_result.get("category", "Furniture")
                base_prices = {
                    "Chair": 85, "Table": 140, "Sofa": 300, "Bed": 200, 
                    "Desk": 120, "Cabinet": 150, "Bookshelf": 80
                }
                fallback_price = base_prices.get(category, 100)
                
                fallback = {
                    "estimated_price": fallback_price,
                    "price_range": {"min": int(fallback_price * 0.8), "max": int(fallback_price * 1.2)},
                    "pricing_factors": ["Category baseline"],
                    "market_position": "Standard",
                    "price_confidence": 0.4,
                    "image_index": classification_result["image_index"],
                    "source_classification": classification_result,
                    "error": str(e)
                }
                pricing_results.append(fallback)
                state["errors"].append(f"Pricing failed for image {classification_result['image_index']}: {str(e)}")
        
        state["pricing_results"] = pricing_results
        state["current_step"] = "grouping"
        
        print(f"✅ Pricing complete: {len(pricing_results)} results")
        return state
    
    def _grouping_node(self, state: FurnitureAnalysisState) -> FurnitureAnalysisState:
        """Grouping node - group similar furniture items together"""
        print("🔗 Grouping Node: Grouping similar items")
        
        # Group items by similarity
        groups = defaultdict(list)
        
        for pricing_result in state["pricing_results"]:
            classification = pricing_result["source_classification"]
            
            # Create grouping key based on category, material, and style
            category = classification.get("category", "Furniture")
            material = classification.get("material", "Unknown")
            style = classification.get("style", "Contemporary")
            
            group_key = f"{category}_{material}_{style}"
            groups[group_key].append(pricing_result)
        
        # Convert to final group format
        furniture_groups = []
        
        for group_key, items in groups.items():
            if len(items) == 1:
                # Single item group
                item = items[0]
                group = {
                    "group_id": f"single_{item['image_index']}",
                    "group_type": "single",
                    "item_count": 1,
                    "representative_item": item,
                    "all_items": items,
                    "group_category": item["source_classification"]["category"],
                    "confidence": item.get("price_confidence", 0.5)
                }
            else:
                # Multiple items - create set
                representative = items[0]  # Use first as representative
                avg_confidence = sum(item.get("price_confidence", 0.5) for item in items) / len(items)
                
                group = {
                    "group_id": f"set_{group_key}",
                    "group_type": "set",
                    "item_count": len(items),
                    "representative_item": representative,
                    "all_items": items,
                    "group_category": representative["source_classification"]["category"],
                    "confidence": avg_confidence
                }
            
            furniture_groups.append(group)
        
        state["furniture_groups"] = furniture_groups
        state["current_step"] = "listing_generation"
        
        print(f"✅ Grouping complete: {len(furniture_groups)} groups created")
        return state
    
    def _listing_generation_node(self, state: FurnitureAnalysisState) -> FurnitureAnalysisState:
        """Listing generation node - create professional marketplace listings"""
        print("📝 Listing Generation Node: Creating marketplace listings")
        
        final_listings = []
        
        for group in state["furniture_groups"]:
            try:
                representative = group["representative_item"]
                classification = representative["source_classification"]
                vision = classification["source_vision"]
                
                # Generate listing content
                listing_prompt = f"""
Create a professional Facebook Marketplace listing:

Item Details:
- Category: {classification.get('subcategory', 'Furniture')}
- Material: {classification.get('material', 'Mixed')}
- Style: {classification.get('style', 'Contemporary')}
- Color: {vision.get('visual_details', {}).get('primary_color', 'Neutral')}
- Features: {classification.get('key_features', [])}
- Condition: {vision.get('visual_details', {}).get('condition_visible', 'Good')}
- Price: ${representative.get('estimated_price', 100)}
- Item Count: {group['item_count']}

Create compelling listing content as JSON:
{{
    "title": "Black Mesh Office Chair - Ergonomic & Adjustable",
    "description": "Modern ergonomic office chair in excellent condition. Features adjustable height, comfortable mesh back, and sturdy construction. Perfect for home office or workspace. Selling due to office upgrade.",
    "highlights": ["Ergonomic design", "Adjustable height", "Excellent condition"],
    "facebook_category": "Home & Garden//Furniture//Chairs"
}}

Requirements:
- Title: 50-80 characters, compelling and searchable
- Description: 150-300 words, detailed and persuasive
- Highlights: 3-5 key selling points

Return only JSON.
"""
                
                response = self.llm.invoke([HumanMessage(content=listing_prompt)])
                listing_content = self._parse_json_response(response.content)
                
                # Build complete listing
                listing = {
                    "title": listing_content.get("title", f"{classification.get('subcategory', 'Furniture')}"),
                    "price": str(representative.get("estimated_price", 100)),
                    "condition": self._map_condition(vision.get('visual_details', {}).get('condition_visible', 'Good')),
                    "description": listing_content.get("description", "Quality furniture in good condition."),
                    "category": listing_content.get("facebook_category", classification.get("facebook_category", "Home & Garden//Furniture")),
                    
                    # Additional details
                    "style": classification.get("style", "Contemporary"),
                    "material": classification.get("material", "Mixed Materials"),
                    "color": vision.get('visual_details', {}).get('primary_color', 'Neutral'),
                    "brand": "Unknown",
                    "furniture_type": classification.get("category", "Furniture"),
                    
                    # Metadata
                    "confidence": group.get("confidence", 0.5),
                    "group_id": group["group_id"],
                    "item_count": group["item_count"],
                    "keywords": classification.get("search_keywords", []),
                    "highlights": listing_content.get("highlights", []),
                    
                    # Images
                    "images": self._prepare_image_data(group),
                    "photo_count": len(group["all_items"]),
                    
                    # Source tracking
                    "analysis_source": "LANGGRAPH_WORKFLOW",
                    "workflow_version": "1.0"
                }
                
                final_listings.append(listing)
                print(f"    ✅ Created listing: {listing['title']}")
                
            except Exception as e:
                print(f"    ❌ Listing generation failed for group {group['group_id']}: {str(e)}")
                # Create fallback listing
                representative = group["representative_item"]
                classification = representative["source_classification"]
                
                fallback_listing = {
                    "title": f"Quality {classification.get('category', 'Furniture')}",
                    "price": str(representative.get("estimated_price", 100)),
                    "condition": "Used - Good",
                    "description": f"Well-maintained {classification.get('category', 'furniture').lower()} in good condition. Perfect for your home!",
                    "category": classification.get("facebook_category", "Home & Garden//Furniture"),
                    "style": "Contemporary",
                    "material": "Mixed Materials",
                    "color": "Neutral",
                    "confidence": 0.3,
                    "group_id": group["group_id"],
                    "item_count": group["item_count"],
                    "images": self._prepare_image_data(group),
                    "photo_count": len(group["all_items"]),
                    "analysis_source": "LANGGRAPH_FALLBACK",
                    "error": str(e)
                }
                final_listings.append(fallback_listing)
                state["errors"].append(f"Listing generation failed for group {group['group_id']}: {str(e)}")
        
        state["final_listings"] = final_listings
        state["current_step"] = "finalize"
        
        print(f"✅ Listing generation complete: {len(final_listings)} listings created")
        return state
    
    def _finalize_results(self, state: FurnitureAnalysisState) -> FurnitureAnalysisState:
        """Finalize the processing workflow"""
        print("🎯 Finalize Node: Completing workflow")
        
        processing_time = datetime.now().timestamp() - state["start_time"]
        
        state["processing_complete"] = True
        state["current_step"] = "complete"
        
        # Calculate success metrics
        successful_listings = len([l for l in state["final_listings"] if l.get("confidence", 0) > 0.5])
        success_rate = (successful_listings / len(state["final_listings"]) * 100) if state["final_listings"] else 0
        
        print(f"🎉 LangGraph workflow complete!")
        print(f"   📊 Processed: {state['total_images']} images → {len(state['final_listings'])} listings")
        print(f"   ⏱️ Time: {processing_time:.1f}s")
        print(f"   ✅ Success rate: {success_rate:.1f}%")
        print(f"   ⚠️ Errors: {len(state['errors'])}")
        
        return state
    
    # Helper methods
    def _encode_image(self, image_path: str) -> str:
        """Convert image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON response with fallback methods"""
        content = content.strip()
        
        # Method 1: Direct JSON parse
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Method 2: Extract JSON from markdown
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{.*\})'
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        # Method 3: Return empty dict
        print(f"⚠️ Could not parse JSON from: {content[:100]}...")
        return {}
    
    def _map_condition(self, ai_condition: str) -> str:
        """Map AI condition to Facebook Marketplace condition"""
        condition_map = {
            "Excellent": "Used - Like New",
            "Very Good": "Used - Like New",
            "Good": "Used - Good", 
            "Fair": "Used - Fair",
            "Poor": "Used - Fair",
            "New": "New"
        }
        return condition_map.get(ai_condition, "Used - Good")
    
    def _prepare_image_data(self, group: Dict[str, Any]) -> List[Dict[str, str]]:
        """Prepare image data for listings"""
        images = []
        for i, item in enumerate(group["all_items"]):
            image_path = item["source_classification"]["source_vision"]["image_path"]
            filename = os.path.basename(image_path)
            
            images.append({
                "id": f"{group['group_id']}_{i}",
                "filename": filename,
                "url": f"/static/{filename}",
                "processed_url": f"/processed/{filename}"
            })
        
        return images
    
    # Main processing method
    async def process_furniture_images(self, image_paths: List[str]) -> Dict[str, Any]:
        """Main method to process furniture images through LangGraph workflow"""
        try:
            print(f"🚀 Starting LangGraph furniture processing for {len(image_paths)} images")
            
            # Initialize state
            initial_state = FurnitureAnalysisState(
                image_paths=image_paths,
                current_image_index=0,
                vision_results=[],
                classification_results=[],
                pricing_results=[],
                furniture_groups=[],
                final_listings=[],
                current_step="initialize",
                errors=[],
                processing_complete=False,
                start_time=datetime.now().timestamp(),
                total_images=len(image_paths)
            )
            
            # Run the workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Prepare response
            return {
                "success": True,
                "total_images": final_state["total_images"],
                "total_furniture_items": len(final_state["final_listings"]),
                "listings": final_state["final_listings"],
                "groups": final_state["furniture_groups"],
                "processing_time": datetime.now().timestamp() - final_state["start_time"],
                "classification_method": "LANGGRAPH_WORKFLOW",
                "errors": final_state["errors"],
                "workflow_complete": final_state["processing_complete"]
            }
            
        except Exception as e:
            print(f"❌ LangGraph workflow failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "total_images": len(image_paths),
                "classification_method": "LANGGRAPH_WORKFLOW"
            }
    
    # Synchronous wrapper for backwards compatibility
    def classify_and_group_photos(self, image_paths: List[str]) -> Dict[str, Any]:
        """Synchronous wrapper for the async workflow"""
        import asyncio
        
        # Create new event loop if none exists
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.process_furniture_images(image_paths))
    
    # Legacy compatibility methods
    def classify_photos(self, image_paths: List[str]) -> Dict[str, Any]:
        """Legacy compatibility"""
        return self.classify_and_group_photos(image_paths)
    
    def generate_listing_data(self, group_data: Dict) -> Dict[str, Any]:
        """Legacy compatibility"""
        return {
            "title": "Quality Furniture",
            "price": "100",
            "condition": "Used - Good",
            "description": "Quality furniture in good condition.",
            "category": "Home & Garden//Furniture"
        }


# For backwards compatibility
class FurnitureClassifier(LangGraphFurnitureClassifier):
    """Alias for backwards compatibility"""
    pass