import asyncio
import aiohttp
import json
import re
from typing import Dict, List, Optional, Any
from openai import OpenAI
import os
from datetime import datetime
import base64
import google.generativeai as genai

class AIAgentSystem:
    """Multi-AI Agent System for Furniture Analysis"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Configure Gemini
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
    async def analyze_furniture_with_agents(self, image_path: str) -> Dict[str, Any]:
        """Run all 6 agents in parallel for comprehensive furniture analysis"""
        try:
            print(f"🚀 Starting 6-Agent Analysis for: {image_path}")
            print("⚡ Running agents in parallel...")
            
            start_time = datetime.now()
            
            # Run all agents in parallel
            tasks = [
                self.category_agent(image_path),
                self.color_agent(image_path),
                self.brand_agent(image_path),
                self.dimensions_agent(image_path),
                self.style_material_agent(image_path)
            ]
            
            # Execute all agent tasks in parallel
            agent_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle any exceptions
            category_data = agent_results[0] if not isinstance(agent_results[0], Exception) else {}
            color_data = agent_results[1] if not isinstance(agent_results[1], Exception) else {}
            brand_data = agent_results[2] if not isinstance(agent_results[2], Exception) else {}
            dimensions_data = agent_results[3] if not isinstance(agent_results[3], Exception) else {}
            style_data = agent_results[4] if not isinstance(agent_results[4], Exception) else {}
            
            # Run pricing agent with the other results
            print("💰 Pricing Agent analyzing...")
            pricing_data = await self.pricing_agent(category_data, color_data, style_data, brand_data)
            
            # Compile final results
            analysis_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'category': category_data,
                'color': color_data,
                'brand': brand_data,
                'dimensions': dimensions_data,
                'style_material': style_data,
                'pricing': pricing_data,
                'timestamp': datetime.now().isoformat(),
                'agents_used': ['category', 'color', 'brand', 'dimensions', 'style_material', 'pricing'],
                'analysis_time': analysis_time
            }
            
            print(f"✅ 6-Agent Analysis Complete in {analysis_time:.1f}s")
            return result
            
        except Exception as e:
            print(f"❌ Multi-agent analysis failed: {e}")
            return self._create_fallback_data()
    
    async def category_agent(self, image_path: str) -> Dict[str, Any]:
        """🎯 Specialized agent for furniture category detection"""
        try:
            print("🎯 Category Agent analyzing...")
            
            prompt = """
            You are a furniture category classification expert. Analyze this image and determine:
            
            1. PRIMARY CATEGORY (choose ONE):
               - Chair, Table, Sofa, Bed, Desk, Cabinet, Bookshelf, Dresser, 
               - Nightstand, Coffee Table, Dining Table, Office Chair, Armchair, 
               - Sectional Sofa, Ottoman, Bench, Wardrobe, TV Stand, Sideboard
            
            2. SUBCATEGORY (be specific):
               - Examples: "Office Chair", "Dining Chair", "Coffee Table", "King Bed"
            
            3. FURNITURE TYPE DETAILS:
               - Number of pieces (if set)
               - Specific style descriptors
            
            Return ONLY a JSON object:
            {
                "primary_category": "exact category name",
                "subcategory": "specific type",
                "piece_count": 1,
                "category_confidence": 0.95,
                "notes": "any additional category details"
            }
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Classify this furniture item's category:"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{self._encode_image(image_path)}"}}
                    ]}
                ],
                max_tokens=300,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            print(f"📝 Category response (first 100 chars): {content[:100]}...")
            
            # Parse JSON response
            result = self._parse_json_response(content)
            if not result:
                # Fallback if JSON parsing fails
                result = {
                    "primary_category": "Furniture",
                    "subcategory": "General",
                    "piece_count": 1,
                    "category_confidence": 0.5,
                    "notes": "Parsed from text response"
                }
            
            print(f"✅ Category extracted: {list(result.keys())}")
            return result
            
        except Exception as e:
            print(f"❌ Category Agent failed: {e}")
            return {
                "primary_category": "Furniture",
                "subcategory": "Unknown",
                "piece_count": 1,
                "category_confidence": 0.3,
                "notes": f"Error: {str(e)}"
            }
    
    async def color_agent(self, image_path: str) -> Dict[str, Any]:
        """🎨 Specialized agent for color detection"""
        try:
            print("🎨 Color Agent analyzing...")
            
            prompt = """
            You are a color analysis expert for furniture. Analyze this image and determine:
            
            1. PRIMARY COLOR: The dominant color of the furniture
            2. SECONDARY COLORS: Any accent or secondary colors
            3. COLOR FINISH: Matte, glossy, satin, distressed, etc.
            4. WOOD TONE: If applicable (oak, walnut, cherry, pine, etc.)
            
            Return ONLY a JSON object:
            {
                "primary_color": "exact color name",
                "secondary_colors": ["color1", "color2"],
                "color_finish": "finish type",
                "wood_tone": "wood type if applicable or null",
                "color_description": "marketing-friendly color description",
                "color_confidence": 0.95
            }
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Analyze the colors in this furniture:"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{self._encode_image(image_path)}"}}
                    ]}
                ],
                max_tokens=300,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            print(f"📝 Color response (first 100 chars): {content[:100]}...")
            
            result = self._parse_json_response(content)
            if not result:
                result = {
                    "primary_color": "Brown",
                    "secondary_colors": [],
                    "color_finish": "Unknown",
                    "wood_tone": None,
                    "color_description": "Neutral tone",
                    "color_confidence": 0.5
                }
            
            print(f"✅ Color extracted: {list(result.keys())}")
            return result
            
        except Exception as e:
            print(f"❌ Color Agent failed: {e}")
            return {
                "primary_color": "Brown",
                "secondary_colors": [],
                "color_finish": "Unknown",
                "wood_tone": None,
                "color_description": "Neutral tone",
                "color_confidence": 0.3
            }
    
    async def brand_agent(self, image_path: str) -> Dict[str, Any]:
        """🏷️ Specialized agent for brand detection"""
        try:
            print("🏷️ Brand Agent analyzing...")
            
            prompt = """
            You are a furniture brand identification expert. Look for:
            
            1. VISIBLE LOGOS or brand marks
            2. DISTINCTIVE DESIGN SIGNATURES of known brands
            3. STYLE PATTERNS that indicate specific manufacturers
            
            Known furniture brands to look for:
            - IKEA, West Elm, CB2, Crate & Barrel, Room & Board, Herman Miller
            - Ashley Furniture, Wayfair, Target (Threshold), Pottery Barn
            - Article, Floyd, Burrow, Steelcase, Knoll, Eames
            
            Return ONLY a JSON object:
            {
                "detected_brand": "brand name or null",
                "brand_confidence": 0.85,
                "design_style_indicators": ["modern", "scandinavian"],
                "brand_reasoning": "why you think this brand",
                "similar_brands": ["brands with similar style"]
            }
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Identify any furniture brands or distinctive design signatures:"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{self._encode_image(image_path)}"}}
                    ]}
                ],
                max_tokens=300,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            print(f"📝 Brand response (first 100 chars): {content[:100]}...")
            
            result = self._parse_json_response(content)
            if not result:
                result = {
                    "detected_brand": None,
                    "brand_confidence": 0.0,
                    "design_style_indicators": [],
                    "brand_reasoning": "Could not analyze",
                    "similar_brands": []
                }
            
            print(f"✅ Brand extracted: {list(result.keys())}")
            return result
            
        except Exception as e:
            print(f"❌ Brand Agent failed: {e}")
            return {
                "detected_brand": None,
                "brand_confidence": 0.0,
                "design_style_indicators": [],
                "brand_reasoning": "Could not analyze",
                "similar_brands": []
            }
    
    async def dimensions_agent(self, image_path: str) -> Dict[str, Any]:
        """📏 Specialized agent for dimension estimation"""
        try:
            print("📏 Dimensions Agent analyzing...")
            
            prompt = """
            You are a furniture dimension estimation expert. Analyze this image and estimate:
            
            1. APPROXIMATE DIMENSIONS in standard furniture sizes
            2. SCALE REFERENCES from surrounding objects
            3. STANDARD SIZE CATEGORY for this furniture type
            
            Return ONLY a JSON object:
            {
                "estimated_width": "36 inches",
                "estimated_height": "32 inches", 
                "estimated_depth": "24 inches",
                "size_category": "Standard",
                "dimension_confidence": 0.75,
                "reference_reasoning": "based on door frame/room scale",
                "standard_dimensions": "typical size for this furniture type"
            }
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Estimate dimensions of this furniture:"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{self._encode_image(image_path)}"}}
                    ]}
                ],
                max_tokens=300,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            print(f"📝 Dimensions response (first 100 chars): {content[:100]}...")
            
            result = self._parse_json_response(content)
            if not result:
                result = {
                    "estimated_width": "Standard",
                    "estimated_height": "Standard",
                    "estimated_depth": "Standard",
                    "size_category": "Standard",
                    "dimension_confidence": 0.5,
                    "reference_reasoning": "Could not determine",
                    "standard_dimensions": "Standard size"
                }
            
            print(f"✅ Dimensions extracted: {list(result.keys())}")
            return result
            
        except Exception as e:
            print(f"❌ Dimensions Agent failed: {e}")
            return {
                "estimated_width": "Unknown",
                "estimated_height": "Unknown", 
                "estimated_depth": "Unknown",
                "size_category": "Unknown",
                "dimension_confidence": 0.3,
                "reference_reasoning": "Error in analysis",
                "standard_dimensions": "Cannot determine"
            }
    
    async def style_material_agent(self, image_path: str) -> Dict[str, Any]:
        """🎨 Specialized agent for style and material detection"""
        try:
            print("🎨 Style & Material Agent analyzing...")
            
            prompt = """
            You are a furniture style and material expert. Analyze this image and determine:
            
            1. DESIGN STYLE: Modern, Traditional, Industrial, Scandinavian, etc.
            2. PRIMARY MATERIAL: Wood, Metal, Fabric, Leather, Glass, etc.
            3. MATERIAL DETAILS: Specific wood type, fabric texture, metal finish
            4. CONSTRUCTION QUALITY: Visible craftsmanship indicators
            
            Return ONLY a JSON object:
            {
                "design_style": "specific style name",
                "primary_material": "main material",
                "secondary_materials": ["material1", "material2"],
                "material_quality": "High/Medium/Basic",
                "style_confidence": 0.90,
                "material_details": "specific material descriptions"
            }
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Analyze the style and materials of this furniture:"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{self._encode_image(image_path)}"}}
                    ]}
                ],
                max_tokens=300,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            print(f"📝 Style response (first 100 chars): {content[:100]}...")
            
            result = self._parse_json_response(content)
            if not result:
                result = {
                    "design_style": "Contemporary",
                    "primary_material": "Mixed Materials",
                    "secondary_materials": [],
                    "material_quality": "Medium",
                    "style_confidence": 0.5,
                    "material_details": "Standard construction"
                }
            
            print(f"✅ Style extracted: {list(result.keys())}")
            return result
            
        except Exception as e:
            print(f"❌ Style & Material Agent failed: {e}")
            return {
                "design_style": "Contemporary",
                "primary_material": "Mixed Materials",
                "secondary_materials": [],
                "material_quality": "Medium",
                "style_confidence": 0.3,
                "material_details": f"Error: {str(e)}"
            }
    
    async def pricing_agent(self, category_data: Dict, color_data: Dict, style_data: Dict, brand_data: Dict) -> Dict[str, Any]:
        """💰 Gemini-powered pricing agent"""
        try:
            print("🚀 Using Gemini Pro for market pricing...")
            
            # Build search query from agent data
            brand = brand_data.get('detected_brand', '')
            category = category_data.get('primary_category', 'furniture')
            subcategory = category_data.get('subcategory', '')
            style = style_data.get('design_style', '')
            color = color_data.get('primary_color', '')
            
            search_query = f"{brand} {category} {subcategory} {style} {color} used price marketplace".strip()
            
            # Simplified prompt for faster processing
            prompt = f"""
            Quick furniture pricing analysis for: {search_query}
            
            Category: {category_data.get('primary_category', 'furniture')}
            Style: {style_data.get('design_style', 'contemporary')}
            Quality: {style_data.get('material_quality', 'medium')}
            
            Provide realistic used marketplace price in JSON:
            {{
                "suggested_price": 150,
                "price_range_low": 100,
                "price_range_high": 200,
                "market_reasoning": "brief explanation",
                "price_confidence": 0.7
            }}
            """
            
            try:
                response = self.gemini_model.generate_content(prompt)
                
                if response and response.text:
                    pricing_data = self._parse_json_response(response.text)
                    if pricing_data and 'suggested_price' in pricing_data:
                        print(f"✅ Gemini Pricing: ${pricing_data.get('suggested_price')}")
                        return pricing_data
            except Exception as gemini_e:
                print(f"   ⚠️ Gemini pricing failed: {gemini_e}, using fallback")
            
            # Fallback pricing if Gemini fails
            return self._fallback_pricing(category_data, style_data, brand_data)
                
        except Exception as e:
            print(f"❌ Pricing Agent failed: {e}")
            return self._fallback_pricing(category_data, style_data, brand_data)
    
    def _fallback_pricing(self, category_data: Dict, style_data: Dict, brand_data: Dict) -> Dict[str, Any]:
        """Fallback pricing when Gemini is unavailable"""
        category = category_data.get('primary_category', 'Furniture').lower()
        quality = style_data.get('material_quality', 'Medium')
        brand = brand_data.get('detected_brand')
        
        # Base pricing by category
        base_prices = {
            'chair': 75, 'table': 120, 'sofa': 300, 'bed': 250,
            'desk': 100, 'cabinet': 150, 'bookshelf': 80, 'dresser': 180
        }
        
        base_price = base_prices.get(category, 100)
        
        # Adjust for quality
        quality_multipliers = {'high': 1.5, 'medium': 1.0, 'budget': 0.7}
        multiplier = quality_multipliers.get(quality.lower(), 1.0)
        
        # Adjust for brand
        if brand and brand.lower() in ['herman miller', 'knoll', 'west elm']:
            multiplier *= 1.3
        elif brand and brand.lower() in ['ikea', 'target']:
            multiplier *= 0.8
        
        suggested_price = int(base_price * multiplier)
        
        return {
            "suggested_price": suggested_price,
            "price_range_low": int(suggested_price * 0.7),
            "price_range_high": int(suggested_price * 1.3),
            "market_reasoning": "Estimated based on category, quality, and brand",
            "price_confidence": 0.6,
            "comparable_items": []
        }
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for OpenAI"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def get_condition_options(self) -> List[str]:
        """Return standardized condition options (only thing not AI-determined)"""
        return ["New", "Like New", "Good", "Fair", "Poor"]
    
    async def generate_enhanced_listing(self, agent_results: Dict, condition: str) -> Dict[str, Any]:
        """Generate final listing using all agent results"""
        try:
            category_data = agent_results.get('category', {})
            color_data = agent_results.get('color', {})
            brand_data = agent_results.get('brand', {})
            dimensions_data = agent_results.get('dimensions', {})
            style_data = agent_results.get('style_material', {})
            pricing_data = agent_results.get('pricing', {})
            
            # Build enhanced title
            brand = brand_data.get('detected_brand', '')
            color = color_data.get('primary_color', '')
            style = style_data.get('design_style', '')
            category = category_data.get('subcategory') or category_data.get('primary_category', 'Furniture')
            
            title_parts = [p for p in [brand, color, style, category] if p and p != 'Unknown']
            title = ' '.join(title_parts) or 'Quality Furniture'
            
            # Build enhanced description with dimensions and brand
            description_parts = []
            
            if brand_data.get('detected_brand'):
                description_parts.append(f"**Brand:** {brand_data['detected_brand']}")
            
            if dimensions_data.get('estimated_width') != 'Unknown':
                dims = f"{dimensions_data.get('estimated_width', '?')} (W) x {dimensions_data.get('estimated_height', '?')} (H) x {dimensions_data.get('estimated_depth', '?')} (D)"
                description_parts.append(f"**Dimensions:** {dims}")
            
            description_parts.append(f"**Style:** {style_data.get('design_style', 'Contemporary')}")
            description_parts.append(f"**Material:** {style_data.get('primary_material', 'Quality materials')}")
            
            if color_data.get('color_description'):
                description_parts.append(f"**Color:** {color_data['color_description']}")
            
            description = "\\n".join(description_parts)
            description += f"\\n\\nIn {condition.lower()} condition. {pricing_data.get('market_reasoning', 'Priced competitively for quick sale.')}"
            
            return {
                "title": title,
                "category": category_data.get('primary_category', 'Furniture'),
                "condition": condition,
                "price": str(pricing_data.get('suggested_price', 100)),
                "description": description,
                "style": style_data.get('design_style', 'Contemporary'),
                "material": style_data.get('primary_material', 'Mixed'),
                "color": color_data.get('primary_color', 'Neutral'),
                "brand": brand_data.get('detected_brand'),
                "dimensions": {
                    "width": dimensions_data.get('estimated_width'),
                    "height": dimensions_data.get('estimated_height'),
                    "depth": dimensions_data.get('estimated_depth')
                },
                "confidence": min([
                    category_data.get('category_confidence', 0.5),
                    color_data.get('color_confidence', 0.5),
                    pricing_data.get('price_confidence', 0.5)
                ]),
                "agent_analysis": agent_results
            }
            
        except Exception as e:
            print(f"❌ Error generating enhanced listing: {e}")
            return {
                "title": "Quality Furniture for Sale",
                "category": "Furniture",
                "condition": condition,
                "price": "100",
                "description": "Quality furniture in good condition.",
                "error": str(e)
            }

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON response with multiple fallback methods"""
        import re
        import json
        
        content = content.strip()
        
        # Method 1: Direct JSON parse
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Method 2: Extract JSON from markdown code blocks
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{[^{}]*\{[^{}]*\}[^{}]*\})',  # nested braces
            r'(\{[^{}]*\})'  # simple object
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        # Method 3: Return empty dict for complete failure
        print(f"⚠️ Could not parse JSON from: {content[:200]}...")
        return {}

    def _create_fallback_data(self) -> Dict[str, Any]:
        """Create fallback data when AI analysis fails"""
        return {
            'category': {
                'primary_category': 'Furniture',
                'subcategory': 'Unknown',
                'piece_count': 1,
                'category_confidence': 0.3,
                'notes': 'Could not analyze'
            },
            'color': {
                'primary_color': 'Unknown',
                'secondary_colors': [],
                'color_finish': 'Unknown',
                'wood_tone': None,
                'color_description': 'Could not determine',
                'color_confidence': 0.3
            },
            'brand': {
                'detected_brand': None,
                'brand_confidence': 0.3,
                'design_style_indicators': [],
                'brand_reasoning': 'Could not analyze',
                'similar_brands': []
            },
            'dimensions': {
                'estimated_width': 'Unknown',
                'estimated_height': 'Unknown',
                'estimated_depth': 'Unknown',
                'size_category': 'Standard',
                'dimension_confidence': 0.3,
                'reference_reasoning': 'Could not determine',
                'standard_dimensions': 'Unknown'
            },
            'style_material': {
                'design_style': 'Contemporary',
                'primary_material': 'Mixed Materials',
                'secondary_materials': [],
                'material_quality': 'Medium',
                'style_confidence': 0.3,
                'material_details': 'Could not analyze'
            }
        }
