# LangGraph Furniture Classification System - Application Flow Documentation

## 🏗️ **Application Architecture Overview**

### **Core Infrastructure**
- **Containerization**: Docker + Docker Compose
- **Backend**: FastAPI (Python 3.11)
- **Frontend**: React with Vite build system
- **Database**: SQLite with SQLAlchemy ORM
- **Caching**: Redis
- **AI/ML**: LangGraph + OpenAI GPT-4V + Google Gemini

---

## 🚀 **Application Startup Flow**

### **1. Docker Container Orchestration**
```bash
./docker-start.sh start-full
```
- **Script**: `docker-start.sh` - Main startup orchestrator
- **Config**: `docker-compose.yml` - Defines 3 services:
  - `backend`: FastAPI app (port 8000)
  - `frontend`: React app (port 3000) 
  - `redis`: Cache layer (port 6379)

### **2. Backend Initialization** (`backend/main.py`)
```python
# Core imports and setup
from furniture_classifier import LangGraphFurnitureClassifier
from ai_agent_system import AIAgentSystem
```
- **Database Setup**: `backend/models.py` + `backend/schemas.py`
- **File Processors**: `backend/image_processor.py`, `backend/furniture_ai.py`
- **Health Check**: `backend/health_check.py`

---

## 🔄 **User Interaction Flow**

### **Step 1: Image Upload** (Frontend → Backend)
- **Frontend Components**:
  - `ImageUploader.jsx` - Drag & drop interface (max 15 images)
  - `BulkProcessor.jsx` - Batch processing UI
- **API Endpoint**: `POST /api/auto-analyze-multiple`
- **File Storage**: Images saved to `uploads/` with timestamped names

### **Step 2: LangGraph Workflow Orchestration**
**Main Classifier**: `furniture_classifier.py` (30KB, 714 lines)
```python
class LangGraphFurnitureClassifier:
    async def classify_and_group_photos(self, image_paths)
```

**LangGraph Workflow Nodes**:
1. **Initialize Node** - Setup workflow state
2. **Vision Analysis Node** - GPT-4V image processing
3. **Classification Node** - Multi-agent analysis
4. **Pricing Node** - Gemini 1.5 Flash market research
5. **Grouping Node** - Similar furniture detection
6. **Listing Generation Node** - Marketplace listing creation
7. **Finalize Node** - Workflow completion

### **Step 3: Multi-Agent AI Analysis**
**AI Agent System**: `backend/ai_agent_system.py` (26KB)
```python
class AIAgentSystem:
    # 6 specialized agents running in parallel
```

**The 6 AI Agents**:
1. **🎯 Category Agent** - Furniture type classification
2. **🎨 Color Agent** - Color/finish analysis
3. **🏷️ Brand Agent** - Brand detection/style identification
4. **📏 Dimensions Agent** - Size estimation
5. **🎨 Style & Material Agent** - Design style/material analysis
6. **💰 Pricing Agent** - Market price research (Gemini API)

**Agent Processing Flow**:
```bash
# From logs:
🤖 Starting multi-agent analysis for uploads/image.jpg
🎯 Category Agent analyzing...
📝 Category response: "primary_category": "Sofa"
✅ Category extracted: ['furniture_type', 'specific_type', 'confidence']
```

### **Step 4: Intelligent Grouping**
**Grouping Algorithm** (in `backend/main.py`):
```python
def _calculate_title_similarity(title1: str, title2: str) -> float:
    # Jaccard similarity + furniture-specific boosting
```
- **Title Similarity**: Jaccard algorithm with stop word removal
- **Category Matching**: Same furniture type detection
- **Photo Batching**: Groups similar furniture pieces together

**Example Grouping**:
```bash
🔗 Grouping: 'ivory Modern Loveseat' with 'ivory Modern Loveseat' (similarity: 1.00)
✅ Created group: 'ivory Modern Loveseat' with 2 photos from 2 images
```

---

## 📊 **Data Processing Pipeline**

### **Async Processing with Fallbacks**:
1. **Primary**: LangGraph workflow
2. **Fallback 1**: Real AI agent system (if LangGraph fails)
3. **Fallback 2**: Simple classifier (if agents fail)

```python
# Error handling hierarchy:
try:
    result = await furniture_classifier.classify_and_group_photos(saved_paths)
except Exception as e:
    if "event loop" in error_msg:
        # Fall back to AI agent system
        ai_system = AIAgentSystem()
        result = await ai_system.analyze_furniture_with_agents(path)
```

### **Image Processing**:
- **Input**: Raw uploaded images
- **Processing**: `backend/image_processor.py`
- **Output**: Processed images in `processed/` directory
- **Serving**: Static file serving via FastAPI

---

## 🎨 **Frontend Architecture**

### **React Components**:
- **`Dashboard.jsx`** - Analytics & performance metrics
- **`ListingGrid.jsx`** - Responsive furniture grid display
- **`ListingCard.jsx`** - Individual furniture listings with confidence indicators
- **`ImageUploader.jsx`** - Multi-file upload interface
- **`BulkProcessor.jsx`** - Batch processing with progress tracking

### **Build System**:
- **Vite**: Modern build tool for React
- **Package Management**: `package.json` + `package-lock.json`
- **Build Output**: Static files served via Docker

---

## 📤 **Export & Download Flow**

### **CSV Export with Photo Organization**:
**API Endpoint**: `POST /api/export-csv-with-photos`

**Export Structure**:
```
langgraph_export_20250604_012345.zip
├── facebook_marketplace_listings.csv
├── README.txt
├── Listing_01_ivory_Modern_Loveseat/
│   ├── IvoryModernLoveseat_photo_01.jpg
│   └── IvoryModernLoveseat_photo_02.jpg
└── Listing_02_Mission_Writing_Desk/
    └── MissionWritingDesk_photo_01.jpg
```

**Photo Batching Logic**:
- Groups photos by furniture piece (not individual images)
- Creates descriptive folder names
- Copies all related photos to same folder
- Generates comprehensive README instructions

---

## 🛠️ **Development & Deployment Tools**

### **Main Scripts**:
- **`docker-start.sh`** - Primary startup script with multiple modes
- **`cleanup.sh`** - Repository cleanup and maintenance
- **`force_frontend_fix.sh`** - Frontend troubleshooting script

### **Archived Development Scripts** (in `.archive/`):
- **Test Scripts**: `test_*.py` - Various system tests
- **Debug Scripts**: `debug_*.sh`, `diagnose_*.py` - Troubleshooting tools
- **Setup Scripts**: `setup_*.sh`, `fix_*.sh` - Environment setup
- **Emergency Scripts**: `emergency_*.sh` - System recovery tools

### **Configuration Files**:
- **`.env`** - Environment variables (API keys)
- **`.dockerignore`** - Docker build exclusions
- **`.gitignore`** - Git tracking exclusions (120 lines)
- **`requirements.txt`** - Python dependencies

### **Database Schema**:
- **`backend/models.py`** - SQLAlchemy models
- **`backend/schemas.py`** - Pydantic validation schemas
- **Storage**: SQLite database (`backend/furniture.db`)

---

## 🔍 **Monitoring & Health Checks**

### **Health Monitoring**:
```bash
GET /api/health
# Returns:
{
  "status": "healthy",
  "langgraph_available": true,
  "classifier": "LangGraph",
  "api_key_configured": true
}
```

### **Performance Metrics**:
- **Processing Time**: Per-image analysis timing
- **Confidence Scores**: AI prediction confidence
- **Success Rates**: Agent performance tracking
- **Grouping Efficiency**: Photo batching effectiveness

---

## 🔧 **Detailed Workflow Example**

### **Real Processing Example** (from logs):
```bash
🚀 STARTING 6-AGENT AI ANALYSIS for 5 files

🎯 AGENT ANALYSIS 1/5: ivory_Modern_Loveseat.jpg
🤖 Category Agent calling OpenAI...
📝 Category response: "primary_category": "Sofa", "subcategory": "Loveseat"
✅ Category extracted: ['furniture_type', 'specific_type', 'confidence']

🎨 Color Agent calling OpenAI...
📝 Color response: "primary_color": "ivory", "color_finish": "matte"
✅ Color extracted: ['primary_color', 'finish_type', 'confidence']

✅ REAL AI Analysis Complete in 35.1s
✨ Generated title: ivory Modern Loveseat
✅ SUCCESS: ivory Modern Loveseat ($300)

🔗 GROUPING SIMILAR FURNITURE...
🔗 Grouping: 'ivory Modern Loveseat' with 'ivory Modern Loveseat' (similarity: 1.00)
✅ Created group: 'ivory Modern Loveseat' with 2 photos from 2 images

🎉 Analysis Complete!
📊 Success: 4/4 listings
⏱️ Time: 97.2s
🤖 Method: REAL_AI_ANALYSIS
```

---

## 🚀 **Key Technologies Summary**

| **Component** | **Technology** | **Purpose** |
|---------------|----------------|-------------|
| **Orchestration** | LangGraph | AI workflow management |
| **Vision AI** | OpenAI GPT-4V | Image analysis |
| **Pricing AI** | Google Gemini 1.5 Flash | Market price research |
| **Backend** | FastAPI + SQLAlchemy | REST API & data persistence |
| **Frontend** | React + Vite | User interface |
| **Containerization** | Docker + Compose | Deployment & scaling |
| **Caching** | Redis | Performance optimization |
| **Grouping** | Custom Algorithm | Photo batching logic |

---

## 📁 **File Structure Summary**

### **Root Directory**:
```
final_fb/
├── .gitignore (1.2KB, 120 lines)
├── README.md (4.6KB, 166 lines)
├── docker-compose.yml (1.6KB, 69 lines)
├── docker-start.sh (3.6KB, 130 lines)
├── furniture_classifier.py (30KB, 714 lines)
├── package.json (1.1KB, 25 lines)
├── cleanup.sh (2.4KB, 85 lines)
├── force_frontend_fix.sh (1.1KB, 37 lines)
├── backend/ (26 items)
├── frontend/ (10 items)
├── .archive/ (organized development files)
├── uploads/ (.gitkeep)
├── processed/ (.gitkeep)
└── exports/ (.gitkeep)
```

### **Backend Structure** (key files):
```
backend/
├── main.py (33KB) - FastAPI application
├── ai_agent_system.py (26KB) - 6-agent AI system
├── furniture_classifier.py (30KB) - LangGraph classifier
├── models.py - Database models
├── schemas.py - Pydantic schemas
├── image_processor.py - Image processing
├── furniture_ai.py - AI utilities
├── health_check.py - System monitoring
└── requirements.txt - Python dependencies
```

---

## 🎯 **System Capabilities**

### **What the System Does**:
1. **Accepts**: Up to 15 furniture images simultaneously
2. **Analyzes**: Each image through 6 specialized AI agents
3. **Extracts**: Category, color, brand, dimensions, style, pricing
4. **Groups**: Similar furniture pieces together intelligently
5. **Generates**: Facebook Marketplace-ready listings
6. **Exports**: CSV + organized photo folders in ZIP format
7. **Provides**: Real-time processing feedback and confidence scores

### **Advanced Features**:
- **Intelligent Photo Grouping**: Same furniture piece detection
- **Multi-Model AI**: OpenAI + Google Gemini integration
- **Fallback Systems**: 3-tier error handling
- **Real-time Monitoring**: Health checks and performance metrics
- **Scalable Architecture**: Docker-based deployment
- **Modern UI**: React with responsive design

This sophisticated system transforms raw furniture photos into organized, market-ready listings with intelligent photo grouping and comprehensive metadata extraction, all powered by cutting-edge AI workflow orchestration through LangGraph. 