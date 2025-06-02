from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import os
import uuid
import shutil
import csv
import io
from datetime import datetime
import json

from models import SessionLocal, engine, Base
from models import Listing as ListingModel, User as UserModel
from schemas import ListingCreate, ListingResponse, UserCreate, UserResponse
from image_processor import ImageProcessor
from furniture_ai import FurnitureAI

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Facebook Marketplace Furniture Agent API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("processed", exist_ok=True)
os.makedirs("exports", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="uploads"), name="static")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize AI processor
furniture_ai = FurnitureAI()
image_processor = ImageProcessor()

@app.get("/")
async def root():
    return {"message": "Facebook Marketplace Furniture Agent API", "version": "1.0.0"}

@app.post("/api/upload-images")
async def upload_images(
    files: List[UploadFile] = File(...),
    user_id: Optional[str] = Form(None)
):
    """Upload and process furniture images"""
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 images allowed")
    
    processed_images = []
    
    for file in files:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not an image")
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"{file_id}{file_extension}"
        filepath = f"uploads/{filename}"
        
        # Save original file
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process image
        processed_path = image_processor.process_image(filepath, f"processed/{filename}")
        
        # Analyze image with AI
        analysis = furniture_ai.analyze_image(processed_path)
        
        processed_images.append({
            "id": file_id,
            "filename": filename,
            "original_name": file.filename,
            "url": f"/static/{filename}",
            "processed_url": f"/static/processed/{filename}",
            "analysis": analysis,
            "size": os.path.getsize(filepath),
            "processed_size": os.path.getsize(processed_path) if os.path.exists(processed_path) else None
        })
    
    return {"images": processed_images, "count": len(processed_images)}

@app.post("/api/listings", response_model=ListingResponse)
async def create_listing(
    listing: ListingCreate,
    db = Depends(get_db)
):
    """Create a new furniture listing"""
    
    # Auto-enhance description if requested
    if listing.auto_enhance_description and listing.title:
        enhanced_description = furniture_ai.generate_description(
            listing.title, 
            listing.condition, 
            listing.category,
            listing.description
        )
        listing.description = enhanced_description
    
    # Create database entry
    db_listing = ListingModel(
        id=str(uuid.uuid4()),
        title=listing.title,
        price=listing.price,
        condition=listing.condition,
        description=listing.description,
        category=listing.category,
        images=json.dumps(listing.images),
        created_at=datetime.now()
    )
    
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)
    
    return ListingResponse(
        id=db_listing.id,
        title=db_listing.title,
        price=db_listing.price,
        condition=db_listing.condition,
        description=db_listing.description,
        category=db_listing.category,
        images=json.loads(db_listing.images),
        created_at=db_listing.created_at
    )

@app.get("/api/listings", response_model=List[ListingResponse])
async def get_listings(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    db = Depends(get_db)
):
    """Get all listings with pagination"""
    query = db.query(ListingModel)
    if user_id:
        query = query.filter(ListingModel.user_id == user_id)
    
    listings = query.offset(skip).limit(limit).all()
    
    return [
        ListingResponse(
            id=listing.id,
            title=listing.title,
            price=listing.price,
            condition=listing.condition,
            description=listing.description,
            category=listing.category,
            images=json.loads(listing.images) if listing.images else [],
            created_at=listing.created_at
        )
        for listing in listings
    ]

@app.delete("/api/listings/{listing_id}")
async def delete_listing(listing_id: str, db = Depends(get_db)):
    """Delete a listing"""
    listing = db.query(ListingModel).filter(ListingModel.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Delete associated images
    images = json.loads(listing.images) if listing.images else []
    for image in images:
        try:
            os.remove(f"uploads/{image['filename']}")
            os.remove(f"processed/{image['filename']}")
        except:
            pass
    
    db.delete(listing)
    db.commit()
    
    return {"message": "Listing deleted successfully"}

@app.post("/api/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    """Analyze a single image"""
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File is not an image")
    
    # Save file temporarily
    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{file_id}{file_extension}"
    filepath = f"uploads/{filename}"
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Process image
        processed_path = image_processor.process_image(filepath, f"processed/{filename}")
        
        # Analyze image
        analysis = furniture_ai.analyze_image(processed_path)
        
        # Get suggestions
        suggestions = furniture_ai.suggest_listing_details(analysis)
        
        return {
            "analysis": analysis,
            "suggestions": suggestions
        }
    finally:
        # Clean up temporary files
        try:
            os.remove(filepath)
            os.remove(processed_path)
        except:
            pass

@app.get("/api/categories")
async def get_categories():
    """Get list of furniture categories"""
    return {
        "categories": furniture_ai.furniture_categories,
        "conditions": furniture_ai.conditions
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    } 