# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pillow==10.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
sqlalchemy==2.0.23
aiosqlite==0.19.0
pydantic==2.5.0
pandas==2.1.4
python-magic==0.4.27
opencv-python==4.8.1.78

# ===================================

# main.py
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
        
        # Process image (resize, optimize, enhance)
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
        except FileNotFoundError:
            pass
    
    db.delete(listing)
    db.commit()
    
    return {"message": "Listing deleted successfully"}

@app.post("/api/export-csv")
async def export_csv(
    listing_ids: List[str],
    db = Depends(get_db)
):
    """Export selected listings to Facebook Marketplace CSV format"""
    
    if not listing_ids:
        raise HTTPException(status_code=400, detail="No listings selected")
    
    # Get listings from database
    listings = db.query(ListingModel).filter(ListingModel.id.in_(listing_ids)).all()
    
    if not listings:
        raise HTTPException(status_code=404, detail="No listings found")
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Facebook Marketplace headers
    headers = ['TITLE', 'PRICE', 'CONDITION', 'DESCRIPTION', 'CATEGORY']
    writer.writerow(headers)
    
    # Add listing data
    for listing in listings:
        writer.writerow([
            listing.title,
            int(listing.price),
            listing.condition,
            listing.description,
            listing.category
        ])
    
    # Create file response
    csv_content = output.getvalue()
    output.close()
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"facebook_marketplace_listings_{timestamp}.csv"
    
    return StreamingResponse(
        io.BytesIO(csv_content.encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/api/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    """Analyze a single image and suggest listing details"""
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save temporary file
    temp_filename = f"temp_{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    temp_path = f"uploads/{temp_filename}"
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Analyze with AI
        analysis = furniture_ai.analyze_image(temp_path)
        
        # Generate suggestions
        suggestions = furniture_ai.suggest_listing_details(analysis)
        
        return {
            "analysis": analysis,
            "suggestions": suggestions
        }
    
    finally:
        # Clean up temp file
        try:
            os.remove(temp_path)
        except FileNotFoundError:
            pass

@app.post("/api/enhance-description")
async def enhance_description(
    title: str = Form(...),
    condition: str = Form(...),
    category: str = Form(...),
    current_description: str = Form("")
):
    """Enhance furniture description using AI"""
    
    enhanced = furniture_ai.generate_description(title, condition, category, current_description)
    
    return {"enhanced_description": enhanced}

@app.get("/api/categories")
async def get_categories():
    """Get available furniture categories"""
    return {
        "categories": [
            "Home & Garden//Furniture//Living Room Furniture",
            "Home & Garden//Furniture//Bedroom Furniture", 
            "Home & Garden//Furniture//Dining Room Furniture",
            "Home & Garden//Furniture//Office Furniture",
            "Home & Garden//Furniture//Outdoor Furniture",
            "Home & Garden//Furniture//Storage & Organization",
            "Home & Garden//Furniture//Tables",
            "Home & Garden//Furniture//Chairs & Seating",
            "Home & Garden//Furniture//Other Furniture"
        ]
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ===================================

# models.py
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

SQLITE_DATABASE_URL = "sqlite:///./furniture_marketplace.db"

engine = create_engine(
    SQLITE_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.now)

class Listing(Base):
    __tablename__ = "listings"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=True)
    title = Column(String, index=True)
    price = Column(Float)
    condition = Column(String)
    description = Column(Text)
    category = Column(String)
    images = Column(Text)  # JSON string of image data
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# ===================================

# schemas.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ImageData(BaseModel):
    id: str
    filename: str
    url: str
    original_name: str

class ListingBase(BaseModel):
    title: str
    price: float
    condition: str
    description: str
    category: str

class ListingCreate(ListingBase):
    images: List[Dict[str, Any]] = []
    auto_enhance_description: bool = False

class ListingResponse(ListingBase):
    id: str
    images: List[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    email: str
    name: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# ===================================

# image_processor.py
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import os

class ImageProcessor:
    def __init__(self):
        self.max_size = (1200, 1200)  # Max dimensions for processed images
        self.quality = 85  # JPEG quality
        
    def process_image(self, input_path: str, output_path: str) -> str:
        """Process image: resize, enhance, and optimize"""
        try:
            # Open image with PIL
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # Resize if too large
                img.thumbnail(self.max_size, Image.Resampling.LANCZOS)
                
                # Enhance image
                img = self._enhance_image(img)
                
                # Save processed image
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                img.save(output_path, 'JPEG', quality=self.quality, optimize=True)
                
                return output_path
                
        except Exception as e:
            print(f"Error processing image {input_path}: {e}")
            return input_path  # Return original if processing fails
    
    def _enhance_image(self, img: Image.Image) -> Image.Image:
        """Apply image enhancements for better marketplace photos"""
        # Auto-adjust brightness and contrast
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)  # Slight brightness boost
        
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.15)  # Slight contrast boost
        
        # Enhance sharpness slightly
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)
        
        return img
    
    def create_thumbnail(self, input_path: str, output_path: str, size: tuple = (300, 300)) -> str:
        """Create thumbnail version of image"""
        try:
            with Image.open(input_path) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                img.save(output_path, 'JPEG', quality=80, optimize=True)
                return output_path
        except Exception as e:
            print(f"Error creating thumbnail for {input_path}: {e}")
            return input_path

# ===================================

# furniture_ai.py
import cv2
import numpy as np
from typing import Dict, List, Any
import os

class FurnitureAI:
    """AI-powered furniture analysis and description generation"""
    
    def __init__(self):
        self.furniture_keywords = {
            'chair': ['chair', 'seat', 'stool', 'bench'],
            'table': ['table', 'desk', 'surface'],
            'sofa': ['sofa', 'couch', 'sectional', 'loveseat'],
            'bed': ['bed', 'mattress', 'frame', 'headboard'],
            'dresser': ['dresser', 'chest', 'drawers', 'bureau'],
            'cabinet': ['cabinet', 'cupboard', 'armoire', 'wardrobe'],
            'shelf': ['shelf', 'bookcase', 'shelving', 'rack']
        }
        
        self.condition_descriptions = {
            'New': 'brand new, unused',
            'Used - Like New': 'excellent condition with minimal signs of use',
            'Used - Good': 'good condition with normal wear',
            'Used - Fair': 'functional with visible wear'
        }
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze furniture image and extract features"""
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                return {"error": "Could not load image"}
            
            # Basic image analysis
            height, width, channels = img.shape
            
            # Color analysis
            colors = self._analyze_colors(img)
            
            # Edge detection for furniture outline
            edges = self._detect_edges(img)
            
            # Estimate furniture type (simplified)
            furniture_type = self._estimate_furniture_type(image_path)
            
            return {
                "dimensions": {"width": width, "height": height},
                "dominant_colors": colors,
                "edge_density": np.sum(edges) / (height * width),
                "estimated_type": furniture_type,
                "confidence": 0.75  # Placeholder confidence score
            }
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _analyze_colors(self, img: np.ndarray) -> List[str]:
        """Extract dominant colors from image"""
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Reshape image to be a list of pixels
        pixels = img_rgb.reshape(-1, 3)
        
        # Simple color categorization
        colors = []
        avg_color = np.mean(pixels, axis=0)
        
        if avg_color[0] > 150 and avg_color[1] > 150 and avg_color[2] > 150:
            colors.append("light")
        elif avg_color[0] < 80 and avg_color[1] < 80 and avg_color[2] < 80:
            colors.append("dark")
        
        if avg_color[0] > avg_color[1] and avg_color[0] > avg_color[2]:
            colors.append("reddish")
        elif avg_color[1] > avg_color[0] and avg_color[1] > avg_color[2]:
            colors.append("greenish")
        elif avg_color[2] > avg_color[0] and avg_color[2] > avg_color[1]:
            colors.append("bluish")
        else:
            colors.append("neutral")
            
        return colors[:3]  # Return top 3 color characteristics
    
    def _detect_edges(self, img: np.ndarray) -> np.ndarray:
        """Detect edges in the image"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        return edges
    
    def _estimate_furniture_type(self, image_path: str) -> str:
        """Estimate furniture type from filename or basic analysis"""
        filename = os.path.basename(image_path).lower()
        
        for furniture_type, keywords in self.furniture_keywords.items():
            if any(keyword in filename for keyword in keywords):
                return furniture_type
        
        return "furniture"
    
    def generate_description(self, title: str, condition: str, category: str, current_description: str = "") -> str:
        """Generate enhanced furniture description"""
        
        # Extract furniture type from title or category
        furniture_type = "furniture"
        title_lower = title.lower()
        
        for ftype, keywords in self.furniture_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                furniture_type = ftype
                break
        
        # Start with base description
        if current_description:
            description = current_description + " "
        else:
            description = f"Beautiful {title.lower()} in {self.condition_descriptions.get(condition, condition.lower())} condition. "
        
        # Add furniture-specific details
        if furniture_type == 'chair':
            description += "Comfortable seating with excellent support. Perfect for dining, office, or accent use. "
        elif furniture_type == 'table':
            description += "Sturdy construction with ample surface space. Great for dining, work, or display. "
        elif furniture_type == 'sofa':
            description += "Comfortable seating perfect for relaxing. Ideal for living room or family room. "
        elif furniture_type == 'bed':
            description += "Provides excellent comfort for a good night's sleep. "
        elif furniture_type == 'dresser':
            description += "Excellent storage solution with spacious drawers. Perfect for bedroom organization. "
        elif furniture_type == 'cabinet':
            description += "Great storage with ample space. Perfect for organizing and display. "
        
        # Add selling points
        description += "Well-maintained and ready for immediate use. "
        description += "Perfect addition to any home. Must see to appreciate the quality and craftsmanship!"
        
        return description
    
    def suggest_listing_details(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest listing details based on image analysis"""
        
        estimated_type = analysis.get("estimated_type", "furniture")
        
        # Suggest category based on furniture type
        category_map = {
            'chair': 'Home & Garden//Furniture//Chairs & Seating',
            'table': 'Home & Garden//Furniture//Tables',
            'sofa': 'Home & Garden//Furniture//Living Room Furniture',
            'bed': 'Home & Garden//Furniture//Bedroom Furniture',
            'dresser': 'Home & Garden//Furniture//Bedroom Furniture',
            'cabinet': 'Home & Garden//Furniture//Storage & Organization'
        }
        
        suggested_category = category_map.get(estimated_type, 'Home & Garden//Furniture//Other Furniture')
        
        # Suggest title based on analysis
        colors = analysis.get("dominant_colors", [])
        color_desc = colors[0] if colors else ""
        
        suggested_title = f"{color_desc.title()} {estimated_type.title()}" if color_desc else estimated_type.title()
        
        return {
            "suggested_title": suggested_title,
            "suggested_category": suggested_category,
            "furniture_type": estimated_type,
            "confidence": analysis.get("confidence", 0.5)
        }


