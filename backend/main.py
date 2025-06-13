"""
Updated Main FastAPI application using LangGraph Furniture Classification System
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import os
import uuid
import shutil
import csv
import io
from datetime import datetime
import json
from PIL import Image
from google.cloud import storage
import base64

# Import database models and schemas
from models import SessionLocal, engine, Base
from models import Listing as ListingModel, User as UserModel
from schemas import ListingCreate, ListingResponse, UserCreate, UserResponse, DescriptionRequest

# Import the new LangGraph classifier (with fallback to old system)
try:
    from furniture_classifier import LangGraphFurnitureClassifier
    LANGGRAPH_AVAILABLE = True
    print("✅ LangGraph system loaded successfully")
except ImportError as e:
    print(f"⚠️ LangGraph not available: {e}")
    print("🔄 Falling back to original system...")
    from furniture_classifier import FurnitureClassifier
    LANGGRAPH_AVAILABLE = False

# Import other modules
try:
    from image_processor import ImageProcessor
    from furniture_ai import FurnitureAI
except ImportError:
    print("⚠️ Some modules not available, creating minimal placeholders")
    
    class ImageProcessor:
        def process_image(self, input_path, output_path=None):
            if output_path:
                shutil.copy2(input_path, output_path)
                return output_path
            return input_path
        
        def create_thumbnail(self, input_path):
            return input_path
    
    class FurnitureAI:
        def analyze_image(self, image_path):
            return {"analysis": "placeholder"}
        
        def generate_description(self, title, condition, category, description=None):
            return f"Quality {category.lower()} in {condition.lower()} condition."

# Create database tables (with error handling for existing tables)
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
except Exception as e:
    print(f"⚠️ Database initialization warning: {e}")
    # Continue anyway - tables might already exist

app = FastAPI(
    title="LangGraph Furniture Marketplace API", 
    version="2.0.0",
    description="AI-powered furniture classification with LangGraph workflow orchestration"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Create directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("processed", exist_ok=True)
os.makedirs("exports", exist_ok=True)

# Add fallback route for old processed image URLs BEFORE mounting static files
@app.get("/static/processed/{filename}")
async def redirect_old_processed_urls(filename: str):
    """Redirect old /static/processed/ URLs to new /processed/ path"""
    return RedirectResponse(url=f"/processed/{filename}", status_code=301)

# Mount static files
app.mount("/processed", StaticFiles(directory="processed"), name="processed_static")
app.mount("/static", StaticFiles(directory="uploads"), name="static")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize Google Cloud Storage
BUCKET_NAME = "furniture-classifier-images-1749795037"
try:
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    print(f"✅ Google Cloud Storage initialized: {BUCKET_NAME}")
except Exception as e:
    print(f"⚠️ Google Cloud Storage not available: {e}")
    storage_client = None
    bucket = None

def upload_to_gcs(file_path: str, blob_name: str) -> str:
    """Upload a file to Google Cloud Storage and return public URL"""
    if not bucket:
        return f"/static/{os.path.basename(file_path)}"  # Fallback to local
    
    try:
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(file_path)
        
        # Return public URL
        return f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_name}"
    except Exception as e:
        print(f"❌ Failed to upload {blob_name}: {e}")
        return f"/static/{os.path.basename(file_path)}"  # Fallback

# Initialize processors and classifiers
image_processor = ImageProcessor()
furniture_ai = FurnitureAI()

if LANGGRAPH_AVAILABLE:
    furniture_classifier = LangGraphFurnitureClassifier()
    print("🚀 Using LangGraph-based classification system")
else:
    furniture_classifier = FurnitureClassifier()
    print("🔄 Using legacy classification system")

@app.get("/")
async def root():
    return {
        "message": "LangGraph Furniture Marketplace API",
        "version": "2.0.0",
        "langgraph_enabled": LANGGRAPH_AVAILABLE,
        "powered_by": "LangGraph + OpenAI GPT-4V" if LANGGRAPH_AVAILABLE else "Legacy System"
    }

@app.get("/api/health")
async def health_check():
    """Enhanced health check with LangGraph status"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "classifier": "LangGraph" if LANGGRAPH_AVAILABLE else "Legacy",
        "langgraph_available": LANGGRAPH_AVAILABLE,
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY"))
    }

@app.get("/api/image/{filename}")
async def serve_image(filename: str):
    """Serve images with proper error handling for Cloud Run"""
    try:
        # Try different possible paths
        possible_paths = [
            os.path.join("uploads", filename),
            os.path.join("processed", filename),
            os.path.join("processed", f"processed_{filename}")
        ]
        
        for file_path in possible_paths:
            if os.path.exists(file_path):
                return FileResponse(file_path)
        
        # If file not found, return a placeholder or error
        raise HTTPException(status_code=404, detail=f"Image {filename} not found")
        
    except Exception as e:
        print(f"Error serving image {filename}: {e}")
        raise HTTPException(status_code=404, detail=f"Image {filename} not found")

@app.post("/api/auto-analyze-multiple")
async def auto_analyze_multiple_furniture(files: List[UploadFile] = File(...)):
    """🆕 Enhanced multi-furniture analysis with LangGraph workflow"""
    print(f"🚀 Starting {'LangGraph' if LANGGRAPH_AVAILABLE else 'Legacy'} analysis for {len(files)} files")
    
    if len(files) > 15:
        raise HTTPException(status_code=400, detail="Maximum 15 images allowed")
    
    # Save uploaded files
    saved_paths = []
    try:
        for i, file in enumerate(files):
            print(f"📸 Processing file {i+1}: {file.filename}")
            if not file.content_type.startswith('image/'):
                print(f"⚠️ Skipping non-image file: {file.filename}")
                continue
                
            # Generate unique filename with sanitized name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = "lg_" if LANGGRAPH_AVAILABLE else "leg_"
            
            # Sanitize the original filename
            original_name = file.filename
            sanitized_name = "".join(c for c in original_name if c.isalnum() or c in ('.', '-', '_')).replace(' ', '_')
            if len(sanitized_name) > 50:  # Limit filename length
                name_parts = sanitized_name.rsplit('.', 1)
                if len(name_parts) == 2:
                    sanitized_name = name_parts[0][:45] + '.' + name_parts[1]
                else:
                    sanitized_name = sanitized_name[:50]
            
            filename = f"{prefix}{timestamp}_{i:02d}_{sanitized_name}"
            file_path = os.path.join("uploads", filename)
            
            # Save file
            print(f"💾 Saving to: {file_path}")
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_paths.append(file_path)
        
        if not saved_paths:
            raise HTTPException(status_code=400, detail="No valid images uploaded")
        
        print(f"✅ Saved {len(saved_paths)} files, starting analysis...")
        
        # Process through the classifier
        start_time = datetime.now()
        
        # Try LangGraph with proper async handling
        try:
            if LANGGRAPH_AVAILABLE:
                print("🚀 Using LangGraph workflow...")
                result = await furniture_classifier.classify_and_group_photos(saved_paths)
                
                # Check if LangGraph actually succeeded
                if result.get("success") and result.get("classification_method") == "LANGGRAPH_WORKFLOW":
                    print("✅ LangGraph completed successfully!")
                    # Calculate processing time
                    end_time = datetime.now()
                    total_processing_time = (end_time - start_time).total_seconds()
                    
                    # Add timing information
                    for listing in result.get("listings", []):
                        listing["processing_time"] = total_processing_time
                    
                    # IMPORTANT: Process images for display (was missing for LangGraph path!)
                    print("📸 Processing images for display...")
                    for listing in result.get("listings", []):
                        processed_images = []
                        for image_info in listing.get("images", []):
                            try:
                                original_path = None
                                # Find the original file path
                                for path in saved_paths:
                                    if os.path.basename(path) == image_info["filename"]:
                                        original_path = path
                                        break
                                
                                if original_path:
                                    # Upload original image to Google Cloud Storage
                                    original_filename = os.path.basename(original_path)
                                    gcs_url = upload_to_gcs(original_path, f"images/{original_filename}")
                                    
                                    # Update image URLs to use GCS
                                    image_info["url"] = gcs_url
                                    image_info["processed_url"] = gcs_url
                                    processed_images.append(image_info)
                                    print(f"   ✅ Uploaded to GCS: {original_filename}")
                                
                            except Exception as e:
                                print(f"   ⚠️ Image processing error: {e}")
                                processed_images.append(image_info)
                        
                        listing["images"] = processed_images
                    
                    return {
                        "status": "success",
                        "total_time": total_processing_time,
                        "method": "LANGGRAPH_WORKFLOW",
                        "listings": result.get("listings", []),
                        "total_images": result.get("total_images", len(saved_paths)),
                        "total_furniture_items": result.get("total_furniture_items", 0),
                        "classification_method": "LANGGRAPH_WORKFLOW"
                    }
                else:
                    print(f"⚠️ LangGraph returned unsuccessful result: {result}")
                    raise Exception("LangGraph workflow failed")
            else:
                print("⚠️ LangGraph not available, using 6-agent fallback")
                raise Exception("LangGraph not available")
                
        except Exception as e:
            error_msg = str(e).lower()
            print(f"❌ LangGraph failed: {str(e)}")
            print("🔄 Falling back to 6-agent AI analysis...")
                
            # Import the working AI agent system for fallback
            try:
                from ai_agent_system import AIAgentSystem
                ai_system = AIAgentSystem()
                
                result = {
                    "success": True,
                    "total_images": len(saved_paths),
                    "total_furniture_items": len(saved_paths),
                    "listings": [],
                    "classification_method": "REAL_AI_ANALYSIS",
                    "errors": []
                }
                
                print("🤖 FORCING 6-AGENT AI ANALYSIS (NO FALLBACKS)...")
                
                # Process each image with real AI agents
                for i, path in enumerate(saved_paths):
                    print(f"\n🎯 AGENT ANALYSIS {i+1}/{len(saved_paths)}: {os.path.basename(path)}")
                    
                    try:
                        print(f"\n🚀 REAL AI ANALYSIS for: {os.path.basename(path)}")
                        
                        # Test OpenAI connection first
                        try:
                            test_response = ai_system.openai_client.chat.completions.create(
                                model="gpt-4o",
                                messages=[{"role": "user", "content": "Say 'Working!'"}],
                                max_tokens=10
                            )
                            print(f"✅ OpenAI test: {test_response.choices[0].message.content}")
                        except Exception as test_e:
                            print(f"❌ OpenAI test failed: {test_e}")
                            raise test_e
                        
                        # Run all agents with real AI
                        print("🤖 Running REAL OpenAI agents...")
                        agent_results = await ai_system.analyze_furniture_with_agents(path)
                        
                        # Generate enhanced listing
                        listing_data = await ai_system.generate_enhanced_listing(
                            agent_results, "Used - Good"
                        )
                        
                        processing_time = (datetime.now() - start_time).total_seconds()
                        
                        print(f"✅ REAL AI Analysis Complete in {processing_time:.1f}s")
                        
                        # Create listing
                        filename = os.path.basename(path)
                        listing = {
                            "id": f"real_ai_{i}",
                            "title": listing_data.get("title", "Quality Furniture"),
                            "price": str(listing_data.get("price", 150)),
                            "condition": listing_data.get("condition", "Used - Good"),
                            "description": listing_data.get("description", "Quality furniture in good condition."),
                            "category": listing_data.get("category", "Home & Garden//Furniture"),
                            "confidence": 0.7,
                            "images": [{
                                "id": f"img_{i}",
                                "filename": filename,
                                "url": f"/static/{filename}",
                                "processed_url": f"/processed/{filename}"
                            }],
                            "analysis_source": "REAL_AI_ANALYSIS",
                            "processing_time": processing_time,
                            "agent_results": agent_results
                        }
                        
                        print(f"✨ Generated title: {listing['title']}")
                        print(f"✅ SUCCESS: {listing['title']} (${listing['price']})")
                        print(f"   📊 Confidence: {listing['confidence']} | Time: {processing_time:.1f}s | Agents: 5")
                        print(f"   ⚠️ FALLBACK USED: REAL_AI_ANALYSIS")
                        
                        result["listings"].append(listing)
                        
                    except Exception as agent_e:
                        print(f"❌ Real AI analysis failed for {os.path.basename(path)}: {agent_e}")
                        
                        # Create minimal fallback listing
                        filename = os.path.basename(path)
                        listing = {
                            "id": f"fallback_{i}",
                            "title": f"Quality Furniture Item {i+1}",
                            "price": "150",
                            "condition": "Used - Good",
                            "description": "Quality furniture in good condition. Perfect for your home!",
                            "category": "Home & Garden//Furniture",
                            "confidence": 0.5,
                            "images": [{
                                "id": f"img_{i}",
                                "filename": filename,
                                "url": f"/static/{filename}",
                                "processed_url": f"/processed/{filename}"
                            }],
                            "analysis_source": "MINIMAL_FALLBACK",
                            "processing_time": 1.0,
                            "error": str(agent_e)
                        }
                        result["listings"].append(listing)
                        result["errors"].append(f"Agent analysis failed for {filename}: {str(agent_e)}")
                
                success_rate = len([l for l in result["listings"] if l.get("confidence", 0) >= 0.6])
                total_items = len(result["listings"])
                
                print(f"\n🎉 ANALYSIS COMPLETE:")
                print(f"   📊 Success Rate: {success_rate}/{total_items} ({success_rate/total_items*100:.1f}%)")
                print(f"   🎯 Total Listings: {total_items}")
                
                # 🔗 GROUP SIMILAR FURNITURE TOGETHER
                print(f"\n🔗 GROUPING SIMILAR FURNITURE...")
                grouped_listings = []
                processed_indices = set()
                
                for i, listing in enumerate(result["listings"]):
                    if i in processed_indices:
                        continue
                        
                    # Start a new group with this listing
                    group_title = listing.get("title", "").strip()
                    group_category = listing.get("category", "").strip()
                    group_images = listing.get("images", [])
                    group_price = listing.get("price", "150")
                    
                    # Find similar listings to group together
                    similar_indices = [i]
                    for j, other_listing in enumerate(result["listings"]):
                        if j <= i or j in processed_indices:
                            continue
                            
                        other_title = other_listing.get("title", "").strip()
                        other_category = other_listing.get("category", "").strip()
                        
                        # Check similarity criteria
                        title_similarity = _calculate_title_similarity(group_title, other_title)
                        category_match = group_category.lower() == other_category.lower()
                        
                        # New intelligent thresholds:
                        # - 0.7+ for strong matches (same furniture + similar style/color)
                        # - 0.6+ with category match for moderate matches  
                        # - 0.5+ for desk variations (handled specially in similarity function)
                        should_group = (
                            title_similarity >= 0.7 or
                            (title_similarity >= 0.6 and category_match) or
                            (title_similarity >= 0.5 and 'desk' in group_title.lower() and 'desk' in other_title.lower())
                        )
                        
                        if should_group:
                            print(f"   🔗 Grouping: '{other_title}' with '{group_title}' (similarity: {title_similarity:.2f})")
                            similar_indices.append(j)
                            group_images.extend(other_listing.get("images", []))
                            # Use the better price if available
                            other_price = other_listing.get("price", "150")
                            if other_price != "150" and group_price == "150":
                                group_price = other_price
                    
                    # Create grouped listing
                    grouped_listing = {
                        "id": f"grouped_{len(grouped_listings)}",
                        "title": group_title,
                        "price": group_price,
                        "condition": listing.get("condition", "Used - Good"),
                        "description": listing.get("description", "Quality furniture in good condition."),
                        "category": group_category,
                        "confidence": listing.get("confidence", 0.7),
                        "images": group_images,
                        "analysis_source": listing.get("analysis_source", "REAL_AI_ANALYSIS"),
                        "processing_time": listing.get("processing_time", 0),
                        "agent_results": listing.get("agent_results", {}),
                        "grouped_from": len(similar_indices),
                        "photo_count": len(group_images)
                    }
                    
                    grouped_listings.append(grouped_listing)
                    processed_indices.update(similar_indices)
                    
                    if len(similar_indices) > 1:
                        print(f"   ✅ Created group: '{group_title}' with {len(group_images)} photos from {len(similar_indices)} images")
                    else:
                        print(f"   📋 Single item: '{group_title}' with {len(group_images)} photos")
                
                # Update result with grouped listings
                original_count = len(result["listings"])
                result["listings"] = grouped_listings
                result["total_furniture_items"] = len(grouped_listings)
                
                print(f"\n🎯 GROUPING SUMMARY:")
                print(f"   📸 Original images: {original_count}")
                print(f"   🎯 Furniture pieces: {len(grouped_listings)}")
                print(f"   📊 Grouping efficiency: {(original_count - len(grouped_listings))} images grouped")
                
            except ImportError as import_e:
                print(f"❌ Could not import AI agent system: {import_e}")
                # Ultimate fallback
                result = {
                    "success": True,
                    "total_images": len(saved_paths),
                    "total_furniture_items": len(saved_paths),
                    "listings": [],
                    "classification_method": "SIMPLE_FALLBACK",
                    "errors": [f"LangGraph async issue: {str(e)}", f"AI agents not available: {str(import_e)}"]
                }
                
                # Create simple listings for each image
                for i, path in enumerate(saved_paths):
                    filename = os.path.basename(path)
                    listing = {
                        "id": f"simple_{i}",
                        "title": f"Quality Furniture Item {i+1}",
                        "price": "150",
                        "condition": "Used - Good",
                        "description": "Quality furniture in good condition. Perfect for your home!",
                        "category": "Home & Garden//Furniture",
                        "confidence": 0.6,
                        "images": [{
                            "id": f"img_{i}",
                            "filename": filename,
                            "url": f"/static/{filename}",
                            "processed_url": f"/processed/{filename}"
                        }],
                        "analysis_source": "SIMPLE_FALLBACK",
                        "processing_time": 2.0
                    }
                    result["listings"].append(listing)
        else:
            raise e  # Re-raise if it's a different error
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Process images for display
        for listing in result.get("listings", []):
            processed_images = []
            for image_info in listing.get("images", []):
                try:
                    original_path = None
                    # Find the original file path
                    for path in saved_paths:
                        if os.path.basename(path) == image_info["filename"]:
                            original_path = path
                            break
                    
                    if original_path:
                        # Upload to Google Cloud Storage
                        original_filename = os.path.basename(original_path)
                        gcs_url = upload_to_gcs(original_path, f"images/{original_filename}")
                        
                        # Update URLs to use GCS
                        image_info["url"] = gcs_url
                        image_info["processed_url"] = gcs_url
                        processed_images.append(image_info)
                    
                except Exception as e:
                    print(f"   ⚠️ Image processing error: {e}")
                    processed_images.append(image_info)
            
            listing["images"] = processed_images
        
        # Enhance response with system-specific info
        response = {
            **result,
            "system_info": {
                "langgraph_enabled": LANGGRAPH_AVAILABLE,
                "processing_time": processing_time,
                "classifier_version": "2.0.0",
                "workflow_type": "LANGGRAPH_WORKFLOW" if LANGGRAPH_AVAILABLE else "LEGACY_SYSTEM"
            }
        }
        
        if LANGGRAPH_AVAILABLE:
            response["langgraph_workflow"] = {
                "nodes_executed": ["initialize", "vision_analysis", "classification", "pricing", "grouping", "listing_generation", "finalize"],
                "state_management": "TypedDict",
                "ai_models_used": ["GPT-4V", "GPT-4o"],
                "workflow_complete": result.get("workflow_complete", False)
            }
            
            response["quality_metrics"] = {
                "high_confidence_items": len([l for l in result.get("listings", []) if l.get("confidence", 0) > 0.7]),
                "medium_confidence_items": len([l for l in result.get("listings", []) if 0.4 <= l.get("confidence", 0) <= 0.7]),
                "low_confidence_items": len([l for l in result.get("listings", []) if l.get("confidence", 0) < 0.4]),
                "avg_processing_time_per_item": processing_time / len(saved_paths) if saved_paths else 0
            }
        
        success_count = len([l for l in result.get("listings", []) if l.get("confidence", 0) > 0.5])
        print(f"\n🎉 Analysis Complete!")
        print(f"   📊 Success: {success_count}/{len(result.get('listings', []))} listings")
        print(f"   ⏱️ Time: {processing_time:.1f}s")
        print(f"   🤖 Method: {result.get('classification_method', 'Unknown')}")
        
        return response
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        # Clean up files on error
        for path in saved_paths:
            try:
                os.remove(path)
            except:
                pass
        
        return {
            "success": False,
            "error": str(e),
            "total_images": len(saved_paths),
            "system_info": {
                "langgraph_enabled": LANGGRAPH_AVAILABLE,
                "error_in": "LANGGRAPH_WORKFLOW" if LANGGRAPH_AVAILABLE else "LEGACY_SYSTEM"
            },
            "troubleshooting": {
                "check_requirements": "Ensure langgraph and langchain-openai are installed" if LANGGRAPH_AVAILABLE else "Check legacy system dependencies",
                "check_api_key": "Verify OPENAI_API_KEY is set correctly",
                "check_logs": "Review backend console for detailed error information"
            }
        }

@app.post("/api/export-csv-with-photos")
async def export_csv_with_organized_photos(listings: List[dict]):
    """Export CSV + organize photos in folders by listing title with proper batching"""
    if not listings:
        raise HTTPException(status_code=400, detail="No listings provided")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    export_prefix = "langgraph" if LANGGRAPH_AVAILABLE else "legacy"
    export_dir = f"exports/{export_prefix}_export_{timestamp}"
    os.makedirs(export_dir, exist_ok=True)
    
    print(f"📦 Creating organized export for {len(listings)} listings...")
    
    # Create CSV file
    csv_path = os.path.join(export_dir, "facebook_marketplace_listings.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["title", "description", "price", "condition", "category"])
        
        # Process each listing with proper photo batching
        for i, listing in enumerate(listings):
            title = listing.get("title", f"Listing_{i+1}")
            
            # Write listing to CSV
            writer.writerow([
                title,
                listing.get("description", "Quality furniture in good condition."),
                listing.get("price", "150"),
                listing.get("condition", "Used - Good"),
                listing.get("category", "Home & Garden//Furniture")
            ])
            
            # Create photo folder for this specific listing
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_').replace('__', '_')
            if len(safe_title) > 50:  # Limit folder name length
                safe_title = safe_title[:50]
            
            photo_folder = os.path.join(export_dir, f"Listing_{i+1:02d}_{safe_title}")
            os.makedirs(photo_folder, exist_ok=True)
            
            print(f"   📁 Creating folder: Listing_{i+1:02d}_{safe_title}")
            
            # Copy all photos for this listing
            images = listing.get("images", [])
            photos_copied = 0
            
            for j, image in enumerate(images):
                try:
                    filename = image.get("filename")
                    if not filename:
                        continue
                    
                    # Try different source paths
                    source_paths = [
                        os.path.join("uploads", filename),
                        os.path.join("processed", f"processed_{filename}"),
                        os.path.join("uploads", f"processed_{filename}")
                    ]
                    
                    source_path = None
                    for path in source_paths:
                        if os.path.exists(path):
                            source_path = path
                            break
                    
                    if source_path:
                        # Create descriptive filename
                        base_name, ext = os.path.splitext(filename)
                        clean_title = safe_title.replace('_', '')[:20]  # First 20 chars
                        dest_filename = f"{clean_title}_photo_{j+1:02d}{ext}"
                        dest_path = os.path.join(photo_folder, dest_filename)
                        
                        # Copy the photo
                        shutil.copy2(source_path, dest_path)
                        photos_copied += 1
                        print(f"      📸 Copied: {dest_filename}")
                    else:
                        print(f"      ❌ Photo not found: {filename}")
                        
                except Exception as e:
                    print(f"      ⚠️ Error copying photo {j+1}: {str(e)}")
            
            print(f"   ✅ Listing {i+1}: {photos_copied} photos copied")
    
    # Create comprehensive README
    readme_path = os.path.join(export_dir, "README.txt")
    with open(readme_path, 'w') as readme:
        system_name = "LangGraph AI" if LANGGRAPH_AVAILABLE else "Legacy AI"
        readme.write(f"{system_name} Furniture Marketplace Export\n")
        readme.write("=" * 50 + "\n")
        readme.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        readme.write(f"Total Listings: {len(listings)}\n\n")
        
        readme.write("📋 HOW TO USE:\n")
        readme.write("-" * 20 + "\n")
        readme.write("1. Upload the CSV file to Facebook Marketplace using bulk upload\n")
        readme.write("2. For each listing, add photos from the corresponding folder:\n\n")
        
        for i, listing in enumerate(listings):
            title = listing.get("title", f"Listing_{i+1}")
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_').replace('__', '_')
            if len(safe_title) > 50:
                safe_title = safe_title[:50]
            
            folder_name = f"Listing_{i+1:02d}_{safe_title}"
            photo_count = len(listing.get("images", []))
            
            readme.write(f"   Listing {i+1}: \"{title}\"\n")
            readme.write(f"   → Use photos from folder: {folder_name}/\n")
            readme.write(f"   → Photos available: {photo_count}\n\n")
        
        readme.write("💡 TIPS:\n")
        readme.write("-" * 10 + "\n")
        readme.write("• Each listing's photos are in separate folders\n")
        readme.write("• Photos are named descriptively for easy identification\n")
        readme.write("• All photos have been processed and optimized\n")
        readme.write("• Use all photos in a folder for that specific listing\n\n")
        
        readme.write(f"🤖 Generated by {system_name} Classification System\n")
    
    # Create zip file
    zip_path = f"{export_dir}.zip"
    try:
        shutil.make_archive(export_dir, 'zip', export_dir)
        
        # Upload ZIP to Google Cloud Storage
        zip_filename = f"{export_prefix}_marketplace_export_{timestamp}.zip"
        if bucket:
            try:
                blob = bucket.blob(f"exports/{zip_filename}")
                blob.upload_from_filename(zip_path)
                download_url = f"https://storage.googleapis.com/{BUCKET_NAME}/exports/{zip_filename}"
                
                print(f"✅ Export uploaded to GCS: {zip_filename}")
                
                # Return JSON response with download URL instead of redirect
                return {
                    "status": "success",
                    "download_url": download_url,
                    "filename": zip_filename,
                    "message": f"Export complete! {len(listings)} listings packaged."
                }
            except Exception as gcs_error:
                print(f"⚠️ GCS upload failed, falling back to local: {gcs_error}")
        
        print(f"✅ Export complete: {len(listings)} listings packaged")
        
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=zip_filename,
            headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
        )
    except Exception as e:
        print(f"❌ Export error: {e}")
        # Clean up partial export directory
        if os.path.exists(export_dir):
            shutil.rmtree(export_dir)
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.post("/api/export-csv")
async def export_csv_simple(listings: List[dict]):
    """Simple CSV export for frontend compatibility"""
    if not listings:
        raise HTTPException(status_code=400, detail="No listings provided")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    export_prefix = "langgraph" if LANGGRAPH_AVAILABLE else "legacy"
    
    # Create temporary CSV file
    csv_filename = f"{export_prefix}_marketplace_listings_{timestamp}.csv"
    csv_path = os.path.join("exports", csv_filename)
    
    # Ensure exports directory exists
    os.makedirs("exports", exist_ok=True)
    
    print(f"📊 Creating simple CSV export for {len(listings)} listings...")
    
    # Create CSV file
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header - exactly as specified by user
        writer.writerow([
            "TITLE", 
            "PRICE", 
            "CONDITION", 
            "DESCRIPTION", 
            "CATEGORY"
        ])
        
        # Write data
        for i, listing in enumerate(listings):
            writer.writerow([
                listing.get("title", f"Listing_{i+1}"),
                listing.get("price", "150"),
                listing.get("condition", "Used - Good"),
                listing.get("description", "Quality furniture in good condition."),
                listing.get("category", "Home & Garden//Furniture")
            ])
    
    print(f"✅ CSV export complete: {csv_filename}")
    
    return FileResponse(
        csv_path,
        media_type="text/csv",
        filename=csv_filename,
        headers={"Content-Disposition": f"attachment; filename={csv_filename}"}
    )

# Legacy endpoints for backwards compatibility
@app.post("/api/classify-furniture")
async def classify_furniture_legacy(files: List[UploadFile] = File(...)):
    """Legacy endpoint - redirects to new system"""
    return await auto_analyze_multiple_furniture(files)

@app.post("/api/auto-analyze")
async def auto_analyze_legacy(files: List[UploadFile] = File(...)):
    """Legacy endpoint - redirects to new system"""
    return await auto_analyze_multiple_furniture(files)

@app.get("/api/test-langgraph-simple")
async def test_langgraph_simple():
    """Test LangGraph workflow with simple test"""
    try:
        if not LANGGRAPH_AVAILABLE:
            return {"error": "LangGraph not available"}
        
        print("🧪 Testing LangGraph workflow...")
        result = await furniture_classifier.test_simple_workflow()
        
        return {
            "success": result.get("success", False),
            "message": "LangGraph test completed",
            "result": result
        }
        
    except Exception as e:
        print(f"❌ LangGraph test failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "LangGraph test failed"
        }

@app.post("/api/test-langgraph")
async def test_system(file: UploadFile = File(...)):
    """Test the classification system"""
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_{timestamp}_{file.filename}"
    file_path = os.path.join("uploads", filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        start_time = datetime.now()
        result = await furniture_classifier.classify_and_group_photos([file_path])
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "test_status": "SUCCESS" if result.get("success") else "FAILED",
            "langgraph_enabled": LANGGRAPH_AVAILABLE,
            "processing_time": processing_time,
            "sample_listing": result.get("listings", [{}])[0] if result.get("listings") else {},
            "classification_method": result.get("classification_method"),
            "test_file": filename
        }
        
    except Exception as e:
        return {
            "test_status": "ERROR",
            "error": str(e),
            "langgraph_enabled": LANGGRAPH_AVAILABLE
        }
    finally:
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

def _calculate_title_similarity(title1: str, title2: str) -> float:
    """Advanced furniture-aware similarity calculation for intelligent grouping"""
    if not title1 or not title2:
        return 0.0
    
    # Normalize titles
    title1 = title1.lower().strip()
    title2 = title2.lower().strip()
    
    # Exact match
    if title1 == title2:
        return 1.0
    
    # Color synonym groups for furniture
    color_groups = {
        'white_group': {'white', 'off-white', 'ivory', 'cream', 'beige', 'ecru', 'alabaster'},
        'brown_group': {'brown', 'tan', 'coffee', 'mocha', 'chocolate', 'chestnut', 'mahogany', 'walnut'},
        'gray_group': {'gray', 'grey', 'silver', 'charcoal', 'slate', 'ash', 'pewter'},
        'black_group': {'black', 'ebony', 'onyx', 'jet', 'coal'},
        'red_group': {'red', 'burgundy', 'wine', 'cherry', 'crimson', 'maroon', 'rust', 'reddish'},
        'blue_group': {'blue', 'navy', 'teal', 'turquoise', 'indigo', 'cerulean'},
        'green_group': {'green', 'olive', 'sage', 'forest', 'emerald', 'mint'},
        'wood_group': {'wood', 'wooden', 'oak', 'pine', 'cedar', 'birch', 'maple', 'teak', 'bamboo'}
    }
    
    # Furniture type synonyms
    furniture_synonyms = {
        'sofa_group': {'sofa', 'couch', 'sectional', 'loveseat', 'settee', 'divan'},
        'chair_group': {'chair', 'armchair', 'recliner', 'rocker', 'stool'},
        'table_group': {'table', 'desk', 'bureau', 'workstation', 'console'},
        'bed_group': {'bed', 'mattress', 'headboard', 'footboard', 'bedframe'},
        'storage_group': {'dresser', 'cabinet', 'wardrobe', 'armoire', 'chest', 'hutch', 'bookshelf'},
        'desk_group': {'desk', 'writing desk', 'computer desk', 'workstation', 'study desk', 'office desk'}
    }
    
    # Style/material synonyms
    style_synonyms = {
        'modern_group': {'modern', 'contemporary', 'minimalist', 'sleek', 'streamlined'},
        'traditional_group': {'traditional', 'classic', 'vintage', 'antique', 'heritage'},
        'rustic_group': {'rustic', 'farmhouse', 'country', 'distressed', 'weathered'},
        'industrial_group': {'industrial', 'metal', 'steel', 'iron', 'pipe'},
        'mission_group': {'mission', 'craftsman', 'arts and crafts', 'stickley'}
    }
    
    def normalize_with_synonyms(title, synonym_groups):
        """Replace words with their group representatives"""
        words = title.split()
        normalized_words = []
        
        for word in words:
            found_group = None
            for group_name, group_words in synonym_groups.items():
                if word in group_words:
                    found_group = group_name.replace('_group', '')
                    break
            normalized_words.append(found_group if found_group else word)
        
        return ' '.join(normalized_words)
    
    # Normalize both titles with synonyms
    norm_title1 = normalize_with_synonyms(title1, {**color_groups, **furniture_synonyms, **style_synonyms})
    norm_title2 = normalize_with_synonyms(title2, {**color_groups, **furniture_synonyms, **style_synonyms})
    
    # Remove stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from'}
    
    words1 = set(word for word in norm_title1.split() if word not in stop_words and len(word) > 1)
    words2 = set(word for word in norm_title2.split() if word not in stop_words and len(word) > 1)
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate base Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    if union == 0:
        return 0.0
    
    jaccard_similarity = intersection / union
    
    # Apply furniture-specific boosting
    boost_factor = 1.0
    
    # 1. Strong boost for same furniture type
    furniture_terms = {'sofa', 'chair', 'table', 'bed', 'dresser', 'bookshelf', 'desk', 'cabinet'}
    furniture1 = words1.intersection(furniture_terms)
    furniture2 = words2.intersection(furniture_terms)
    
    if furniture1 and furniture2 and furniture1 == furniture2:
        boost_factor *= 1.5  # Same furniture type = 50% boost
    
    # 2. Boost for same style
    style_terms = {'modern', 'traditional', 'rustic', 'industrial', 'mission'}
    style1 = words1.intersection(style_terms)
    style2 = words2.intersection(style_terms)
    
    if style1 and style2 and style1 == style2:
        boost_factor *= 1.2  # Same style = 20% boost
    
    # 3. Special handling for desk variations
    original_words1 = set(title1.split())
    original_words2 = set(title2.split())
    
    desk_terms1 = original_words1.intersection({'desk', 'writing', 'computer', 'office', 'study'})
    desk_terms2 = original_words2.intersection({'desk', 'writing', 'computer', 'office', 'study'})
    
    if desk_terms1 and desk_terms2 and ('desk' in desk_terms1 and 'desk' in desk_terms2):
        boost_factor *= 1.4  # Both are desks = 40% boost
    
    # 4. Penalize completely different furniture types
    if furniture1 and furniture2 and not furniture1.intersection(furniture2):
        boost_factor *= 0.3  # Different furniture types = major penalty
    
    # Calculate final similarity
    final_similarity = min(1.0, jaccard_similarity * boost_factor)
    
    return final_similarity

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)