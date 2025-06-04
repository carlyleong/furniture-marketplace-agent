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
                # Add fallback vision result with UNIQUE values per image to prevent incorrect grouping
                
                # Generate unique fallback values based on image index to prevent grouping
                fallback_colors = ["Brown", "Black", "White", "Gray", "Blue", "Red", "Green", "Wood", "Beige", "Silver"]
                fallback_types = ["Chair", "Table", "Sofa", "Desk", "Cabinet", "Bed", "Dresser", "Bookshelf", "Nightstand", "Ottoman"]
                fallback_materials = ["Wood", "Metal", "Fabric", "Leather", "Plastic", "Glass", "Composite", "Wicker", "Stone", "Ceramic"]
                fallback_styles = ["Modern", "Traditional", "Contemporary", "Rustic", "Industrial", "Scandinavian", "Vintage", "Minimalist", "Classic", "Farmhouse"]
                
                # Use modulo to cycle through options, ensuring different images get different fallback values
                color_idx = i % len(fallback_colors)
                type_idx = i % len(fallback_types)
                material_idx = i % len(fallback_materials)
                style_idx = i % len(fallback_styles)
                
                vision_results.append({
                    "furniture_detected": True,
                    "furniture_type": fallback_types[type_idx],
                    "visual_details": {
                        "primary_color": fallback_colors[color_idx],
                        "material_appearance": fallback_materials[material_idx],
                        "style_indicators": fallback_styles[style_idx],
                        "condition_visible": "Good",
                        "brand_visible": False,
                        "unique_features": [f"Feature_{i+1}"]
                    },
                    "image_quality": "Medium",
                    "analysis_confidence": 0.3,
                    "image_path": image_path,
                    "image_index": i,
                    "error": str(e),
                    "fallback_used": True
                })
                state["errors"].append(f"Vision analysis failed for image {i+1}: {str(e)}")
                print(f"    🔄 Fallback assigned: {fallback_types[type_idx]} in {fallback_colors[color_idx]} ({fallback_materials[material_idx]})")
        
        state["vision_results"] = vision_results
        state["current_step"] = "classification"
        
        print(f"✅ Vision analysis complete: {len(vision_results)} images processed")
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
- Features: {classification_result.get('key_features', [])}
- Condition: {classification_result.get('source_vision', {}).get('visual_details', {}).get('condition_visible', 'Good')}

Provide market pricing as JSON:
{{
    "suggested_price": 125,
    "price_range": {{"min": 100, "max": 150}},
    "pricing_factors": ["Material quality", "Brand recognition", "Market demand"],
    "condition_impact": "Good condition adds value",
    "market_comparison": "Similar items: $100-$160",
    "pricing_confidence": 0.8
}}

Return only JSON.
"""
                
                response = self.llm.invoke([HumanMessage(content=pricing_prompt)])
                
                pricing_result = self._parse_json_response(response.content)
                pricing_result["image_index"] = classification_result["image_index"]
                pricing_result["source_classification"] = classification_result
                
                pricing_results.append(pricing_result)
                price = pricing_result.get("suggested_price", 100)
                print(f"    ✅ Priced: ${price}")
                
            except Exception as e:
                print(f"    ❌ Pricing failed for image {classification_result['image_index']}: {str(e)}")
                # Fallback pricing
                fallback_pricing = {
                    "suggested_price": 100,
                    "price_range": {"min": 75, "max": 125},
                    "pricing_factors": ["Standard market rate"],
                    "condition_impact": "Good condition",
                    "market_comparison": "Standard furniture pricing",
                    "pricing_confidence": 0.3,
                    "image_index": classification_result["image_index"],
                    "source_classification": classification_result,
                    "error": str(e)
                }
                pricing_results.append(fallback_pricing)
                state["errors"].append(f"Pricing failed for image {classification_result['image_index']}: {str(e)}")
        
        state["pricing_results"] = pricing_results
        state["current_step"] = "grouping"
        
        print(f"✅ Pricing complete: {len(pricing_results)} results")
        return state
    
    def _grouping_node(self, state: FurnitureAnalysisState) -> FurnitureAnalysisState:
        """Grouping node - use AI agent to intelligently group photos of the same furniture pieces"""
        print("🤖 Grouping Agent: AI analyzing all images to identify which photos show the same furniture")
        
        # Combine all analysis results
        all_items = []
        for pricing_result in state["pricing_results"]:
            item = {
                "image_index": pricing_result["image_index"],
                "pricing": pricing_result,
                "classification": pricing_result["source_classification"],
                "vision": pricing_result["source_classification"]["source_vision"]
            }
            all_items.append(item)
        
        if len(all_items) <= 1:
            # Only one image, no grouping needed
            groups = [{
                "group_id": "group_0",
                "primary_category": all_items[0]["classification"].get("category", "Furniture"),
                "subcategory": all_items[0]["classification"].get("subcategory", ""),
                "style": all_items[0]["classification"].get("style", ""),
                "material": all_items[0]["classification"].get("material", ""),
                "all_items": all_items,
                "total_price": all_items[0]["pricing"].get("suggested_price", 100),
                "avg_confidence": all_items[0]["classification"].get("classification_confidence", 0.5),
                "avg_price": all_items[0]["pricing"].get("suggested_price", 100)
            }]
        else:
            # Use AI Grouping Agent for multiple images
            try:
                groups = self._ai_grouping_agent(all_items)
            except Exception as e:
                print(f"❌ AI Grouping Agent failed: {str(e)}")
                print("🔄 Falling back to individual listings...")
                # Fallback: create individual groups for each item
                groups = []
                for i, item in enumerate(all_items):
                    groups.append({
                        "group_id": f"group_{i}",
                        "primary_category": item["classification"].get("category", "Furniture"),
                        "subcategory": item["classification"].get("subcategory", ""),
                        "style": item["classification"].get("style", ""),
                        "material": item["classification"].get("material", ""),
                        "all_items": [item],
                        "total_price": item["pricing"].get("suggested_price", 100),
                        "avg_confidence": item["classification"].get("classification_confidence", 0.5),
                        "avg_price": item["pricing"].get("suggested_price", 100)
                    })
        
        state["furniture_groups"] = groups
        state["current_step"] = "listing_generation"
        
        print(f"✅ AI Grouping complete: {len(all_items)} photos → {len(groups)} distinct furniture pieces")
        print(f"   🤖 AI agent identified which photos show the same physical furniture")
        return state
    
    def _ai_grouping_agent(self, all_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """AI Grouping Agent - analyze all images together to group photos of same furniture pieces"""
        print(f"🔍 AI Grouping Agent analyzing {len(all_items)} images...")
        
        # Prepare image data for AI analysis
        image_descriptions = []
        for i, item in enumerate(all_items):
            vision_data = item["vision"]
            classification_data = item["classification"]
            
            description = f"""Image {i+1}:
- Furniture Type: {vision_data.get('furniture_type', 'Unknown')}
- Color: {vision_data.get('visual_details', {}).get('primary_color', 'Unknown')}
- Material: {vision_data.get('visual_details', {}).get('material_appearance', 'Unknown')}
- Style: {vision_data.get('visual_details', {}).get('style_indicators', 'Unknown')}
- Category: {classification_data.get('subcategory', 'Unknown')}
- Price: ${item['pricing'].get('suggested_price', 100)}
- Path: {vision_data.get('image_path', '')}"""
            
            image_descriptions.append(description)
        
        # Create AI prompt for grouping decision
        grouping_prompt = f"""
You are an expert furniture analyst. Analyze these {len(all_items)} furniture images and determine which photos show the SAME physical furniture piece vs DIFFERENT pieces.

Image Analysis Data:
{chr(10).join(image_descriptions)}

Your task: Group photos that show the SAME physical furniture piece together. Different furniture pieces should be in separate groups.

IMPORTANT GROUPING RULES:
- BE AGGRESSIVE in grouping photos of the same furniture piece
- If furniture type, color, and material are similar → likely same piece from different angles
- Only separate if clearly different pieces (different colors, different furniture types, or obviously different items)
- When in doubt about same vs different → GROUP THEM TOGETHER
- Multiple angles/views of same item should always be grouped

Examples of what to GROUP together:
- "Blue office chair" + "Blue office chair from side" → SAME GROUP
- "Brown wooden table" + "Brown wooden table different angle" → SAME GROUP  
- "Black leather sofa" + "Black leather sofa with pillows" → SAME GROUP

Examples of what to keep SEPARATE:
- "Blue chair" + "Red chair" → DIFFERENT GROUPS (different colors)
- "Office chair" + "Dining table" → DIFFERENT GROUPS (different furniture types)
- "Small desk" + "Large desk" → DIFFERENT GROUPS (clearly different sizes)

Provide your grouping decision as JSON:
{{
    "groups": [
        {{
            "group_id": "group_0",
            "image_indices": [0, 2, 3],
            "reasoning": "Same blue office chair from multiple angles",
            "furniture_description": "Blue Ergonomic Office Chair"
        }},
        {{
            "group_id": "group_1", 
            "image_indices": [1],
            "reasoning": "Different piece - wooden dining table",
            "furniture_description": "Wooden Dining Table"
        }}
    ],
    "total_groups": 2,
    "confidence": 0.9
}}

Return only JSON.
"""
        
        try:
            # Call AI for grouping decision
            response = self.llm.invoke([HumanMessage(content=grouping_prompt)])
            grouping_result = self._parse_json_response(response.content)
            
            if not grouping_result or "groups" not in grouping_result:
                raise Exception("Invalid grouping response from AI")
            
            # Convert AI grouping decision to our group format
            groups = []
            for ai_group in grouping_result["groups"]:
                image_indices = ai_group.get("image_indices", [])
                if not image_indices:
                    continue
                
                # Get items for this group
                group_items = [all_items[idx] for idx in image_indices if idx < len(all_items)]
                if not group_items:
                    continue
                
                # Use first item as representative
                primary_item = group_items[0]
                
                # Calculate totals
                total_price = sum(item["pricing"].get("suggested_price", 100) for item in group_items)
                avg_confidence = sum(item["classification"].get("classification_confidence", 0.5) for item in group_items) / len(group_items)
                
                group = {
                    "group_id": ai_group.get("group_id", f"group_{len(groups)}"),
                    "primary_category": primary_item["classification"].get("category", "Furniture"),
                    "subcategory": primary_item["classification"].get("subcategory", ""),
                    "style": primary_item["classification"].get("style", ""),
                    "material": primary_item["classification"].get("material", ""),
                    "all_items": group_items,
                    "total_price": total_price,
                    "avg_confidence": avg_confidence,
                    "avg_price": total_price // len(group_items),
                    "ai_reasoning": ai_group.get("reasoning", "AI grouped these images"),
                    "ai_description": ai_group.get("furniture_description", "Furniture")
                }
                
                groups.append(group)
                print(f"    ✅ AI Group {len(groups)}: {len(group_items)} photos of {ai_group.get('furniture_description', 'furniture')}")
                print(f"       📝 Reasoning: {ai_group.get('reasoning', 'No reasoning provided')}")
            
            print(f"🎯 AI Grouping Agent confidence: {grouping_result.get('confidence', 0.5)}")
            return groups
            
        except Exception as e:
            print(f"❌ AI Grouping Agent error: {str(e)}")
            raise e
    
    def _listing_generation_node(self, state: FurnitureAnalysisState) -> FurnitureAnalysisState:
        """Listing generation node - create marketplace listings using AI"""
        print("📝 AI Listing Generation: Creating compelling marketplace listings")
        
        final_listings = []
        
        for group in state["furniture_groups"]:
            try:
                # Get primary item (first in group)
                primary_item = group["all_items"][0]
                
                # Gather all information about this furniture piece
                furniture_info = {
                    "ai_description": group.get("ai_description", "Furniture"),
                    "ai_reasoning": group.get("ai_reasoning", ""),
                    "category": group.get("subcategory") or group.get("primary_category", "Furniture"),
                    "style": group.get("style", ""),
                    "material": group.get("material", ""),
                    "num_photos": len(group["all_items"]),
                    "price": group["avg_price"],
                    "features": primary_item["classification"].get("key_features", []),
                    "condition": primary_item["vision"].get("visual_details", {}).get("condition_visible", "Good"),
                    "room": primary_item["classification"].get("target_room", ""),
                    "confidence": group["avg_confidence"]
                }
                
                # Use AI to generate compelling title and description
                listing_data = self._ai_listing_generator(furniture_info)
                
                # Prepare images
                images = self._prepare_image_data(group)
                
                # Create listing
                listing = {
                    "id": group["group_id"],
                    "title": listing_data.get("title", furniture_info["ai_description"]),
                    "price": str(group["avg_price"]),
                    "condition": self._map_condition(furniture_info["condition"]),
                    "description": listing_data.get("description", f"Quality {furniture_info['ai_description'].lower()} in good condition."),
                    "category": primary_item["classification"].get("facebook_category", "Home & Garden//Furniture"),
                    "confidence": group["avg_confidence"],
                    "images": images,
                    "analysis_source": "LANGGRAPH_WORKFLOW",
                    "processing_time": 0,  # Will be set later
                    "langgraph_data": {
                        "group_info": group,
                        "item_count": len(group["all_items"]),
                        "vision_results": [item["vision"] for item in group["all_items"]],
                        "classification_results": [item["classification"] for item in group["all_items"]],
                        "pricing_results": [item["pricing"] for item in group["all_items"]],
                        "ai_listing_data": listing_data
                    }
                }
                
                final_listings.append(listing)
                print(f"    ✅ Generated: {listing['title']} (${group['avg_price']})")
                
            except Exception as e:
                print(f"    ❌ Listing generation failed for group {group['group_id']}: {str(e)}")
                
                # Create fallback listing
                fallback_listing = {
                    "id": group["group_id"],
                    "title": f"Quality {group.get('primary_category', 'Furniture')}",
                    "price": "100",
                    "condition": "Used - Good",
                    "description": "Quality furniture in good condition. Perfect for your home!",
                    "category": "Home & Garden//Furniture",
                    "confidence": 0.3,
                    "images": self._prepare_image_data(group),
                    "analysis_source": "LANGGRAPH_WORKFLOW",
                    "processing_time": 0,
                    "error": str(e)
                }
                final_listings.append(fallback_listing)
                state["errors"].append(f"Listing generation failed for group {group['group_id']}: {str(e)}")
        
        state["final_listings"] = final_listings
        state["current_step"] = "finalize"
        
        print(f"✅ AI Listing generation complete: {len(final_listings)} compelling listings created")
        return state
    
    def _ai_listing_generator(self, furniture_info: Dict[str, Any]) -> Dict[str, str]:
        """AI-powered complete listing generator - ALL fields generated by AI"""
        print(f"🎯 AI generating ALL listing fields for: {furniture_info['ai_description']}")
        
        listing_prompt = f"""
You are an expert Facebook Marketplace listing agent. Create a COMPLETE, compelling listing for this furniture item.

Furniture Analysis Data:
- AI Description: {furniture_info['ai_description']}
- AI Grouping Reasoning: {furniture_info['ai_reasoning']}
- Detected Category: {furniture_info['category']}
- Style Detected: {furniture_info['style']}
- Material Detected: {furniture_info['material']}
- Visual Condition: {furniture_info['condition']}
- Key Features: {', '.join(furniture_info['features'][:5]) if furniture_info['features'] else 'Not specified'}
- Target Room: {furniture_info['room']}
- Number of Photos: {furniture_info['num_photos']}
- AI Suggested Price: ${furniture_info['price']}

Generate a COMPLETE marketplace listing with ALL fields optimized by AI:

1. **TITLE** (max 80 chars): Catchy, keyword-rich, includes condition
2. **DESCRIPTION** (150-250 words): Compelling story, features, benefits, call-to-action
3. **OPTIMIZED_CONDITION**: Best Facebook Marketplace condition category
4. **OPTIMIZED_CATEGORY**: Most accurate Facebook category path
5. **SEARCH_KEYWORDS**: Top 5 keywords buyers would search for
6. **SELLING_POINTS**: Top 3 key selling points
7. **TARGET_BUYER**: Who would buy this item

Use professional marketplace language that builds trust and drives sales.

Return as JSON:
{{
    "title": "Modern Blue Ergonomic Office Chair - Like New Condition!",
    "description": "Stunning blue ergonomic office chair in excellent condition! Perfect for remote work or home office setup. Features premium mesh backing for breathability, fully adjustable height mechanism, and 360-degree swivel base. The lumbar support provides all-day comfort during long work sessions. Originally purchased for $300, now priced to sell quickly at ${furniture_info['price']}! This chair has been gently used in a smoke-free, pet-free home. Multiple high-quality photos show all angles - what you see is exactly what you get. Great for students, professionals, or anyone upgrading their workspace. Must pick up due to moving. Serious buyers only, please! Cash only, first come first served.",
    "optimized_condition": "Used - Like New",
    "optimized_category": "Home & Garden//Furniture//Chairs",
    "search_keywords": ["ergonomic office chair", "blue mesh chair", "adjustable desk chair", "work from home chair", "computer chair"],
    "selling_points": ["Ergonomic design with lumbar support", "Like-new condition, barely used", "Great value - originally $300"],
    "target_buyer": "Remote workers, students, home office setups",
    "pricing_justification": "Comparable chairs retail for $250-400, this is priced to sell quickly",
    "condition_reasoning": "Excellent visual condition with minimal wear, functions perfectly"
}}

Return only JSON.
"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=listing_prompt)])
            listing_result = self._parse_json_response(response.content)
            
            if not listing_result or "title" not in listing_result:
                raise Exception("Invalid listing response from AI")
            
            print(f"    🎯 AI Title: {listing_result.get('title', 'N/A')[:50]}...")
            print(f"    🎯 AI Condition: {listing_result.get('optimized_condition', 'N/A')}")
            print(f"    🎯 AI Category: {listing_result.get('optimized_category', 'N/A')}")
            return listing_result
            
        except Exception as e:
            print(f"    ❌ AI listing generation failed: {str(e)}")
            # Even fallback should use some AI reasoning
            return {
                "title": f"{furniture_info['style']} {furniture_info['ai_description']} - Great Condition".strip()[:80],
                "description": f"Quality {furniture_info['ai_description'].lower()} in {furniture_info['condition'].lower()} condition. {furniture_info['ai_reasoning']} Perfect for your home! Priced to sell at ${furniture_info['price']}. Multiple photos included. Cash only, serious buyers welcome!",
                "optimized_condition": "Used - Good",
                "optimized_category": "Home & Garden//Furniture",
                "search_keywords": [furniture_info['category'].lower(), "furniture", "home"],
                "selling_points": ["Good condition", "Quality furniture", "Multiple photos"],
                "target_buyer": "Home buyers",
                "pricing_justification": "Fair market price",
                "condition_reasoning": "Standard assessment"
            }
    
    def _finalize_results(self, state: FurnitureAnalysisState) -> FurnitureAnalysisState:
        """Finalize the workflow results"""
        print("🎯 Finalize Node: Completing workflow")
        
        # Mark as complete
        state["processing_complete"] = True
        
        # Calculate total processing time
        total_time = datetime.now().timestamp() - state["start_time"]
        for listing in state["final_listings"]:
            listing["processing_time"] = total_time
        
        # Summary
        print(f"   ✅ Processed: {state['total_images']} images")
        print(f"   🛋️ Created: {len(state['final_listings'])} listings")
        print(f"   ⏱️ Time: {total_time:.1f}s")
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
            image_path = item["vision"]["image_path"]
            filename = os.path.basename(image_path)
            
            images.append({
                "id": f"{group['group_id']}_{i}",
                "filename": filename,
                "url": f"/static/{filename}",
                "processed_url": f"/processed/{filename}"
            })
        
        return images
    
    # Test method to debug LangGraph workflow
    def test_simple_workflow_sync(self) -> Dict[str, Any]:
        """Simple test workflow to debug issues - synchronous version"""
        try:
            print("🧪 Testing simple LangGraph workflow...")
            
            # Create a very simple test state
            test_state = {
                "image_paths": ["test.jpg"],
                "current_image_index": 0,
                "vision_results": [],
                "classification_results": [],
                "pricing_results": [],
                "furniture_groups": [],
                "final_listings": [],
                "current_step": "initialize",
                "errors": [],
                "processing_complete": False,
                "start_time": datetime.now().timestamp(),
                "total_images": 1
            }
            
            # Try just the initialization node
            print("   🔄 Testing initialization node...")
            init_result = self._initialize_processing(test_state)
            print(f"   ✅ Init successful: {init_result['current_step']}")
            
            return {"success": True, "test": "passed"}
            
        except Exception as e:
            print(f"   ❌ Test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # Async wrapper for test
    async def test_simple_workflow(self) -> Dict[str, Any]:
        """Simple test workflow to debug async issues"""
        try:
            print("🧪 Testing simple LangGraph workflow...")
            
            # Create a very simple test state
            test_state = {
                "image_paths": ["test.jpg"],
                "current_image_index": 0,
                "vision_results": [],
                "classification_results": [],
                "pricing_results": [],
                "furniture_groups": [],
                "final_listings": [],
                "current_step": "initialize",
                "errors": [],
                "processing_complete": False,
                "start_time": datetime.now().timestamp(),
                "total_images": 1
            }
            
            # Try a simple workflow execution with async invoke
            print("   🔄 Testing full workflow...")
            result = await self.workflow.ainvoke(test_state)
            print("   ✅ Workflow completed successfully!")
            
            return {"success": True, "test": "passed"}
            
        except Exception as e:
            print(f"   ❌ Test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
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
    
    # Main async method
    async def classify_and_group_photos(self, image_paths: List[str]) -> Dict[str, Any]:
        """Main method to process furniture images through LangGraph workflow"""
        return await self.process_furniture_images(image_paths)
    
    # Synchronous wrapper for backwards compatibility - only use when not in async context
    def classify_and_group_photos_sync(self, image_paths: List[str]) -> Dict[str, Any]:
        """Synchronous wrapper for the async workflow - only use outside FastAPI"""
        import asyncio
        
        # Check if we're already in an async context
        try:
            loop = asyncio.get_running_loop()
            # If we get here, we're in an async context - this should not be called
            raise RuntimeError("Cannot use sync wrapper in async context. Use 'await classify_and_group_photos()' instead.")
        except RuntimeError:
            # No running loop - we can create one
            pass
        
        # Create new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(self.process_furniture_images(image_paths))
        finally:
            loop.close()
    
    # Legacy compatibility methods
    async def classify_photos(self, image_paths: List[str]) -> Dict[str, Any]:
        """Legacy compatibility - now async"""
        return await self.classify_and_group_photos(image_paths)
    
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