from fastapi import FastAPI, HTTPException, Depends, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os
import json
import logging
from pydantic import BaseModel

# Import analyzer integrations
from src.api.analyzer_integration import analyze_content_task
from src.api.enhanced_integration import analyze_content_enhanced
from src.api.bulk_integration import start_bulk_processing, get_job_status, stop_job, list_jobs

# Import authentication and caching
from src.api.auth import get_site_from_api_key, check_rate_limit
from src.api.cache import cached

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("web_analyzer_api")

# Initialize FastAPI app
app = FastAPI(
    title="Web Analyzer API",
    description="API for analyzing web content and generating internal links",
    version="1.0.0"
)

# Create a new FastAPI app with the /api/v1 prefix
api_app = FastAPI()
app.mount("/api/v1", api_app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://thevou.com", "https://www.thevou.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Also add CORS middleware to the API app
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://thevou.com", "https://www.thevou.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request/response models
class ContentAnalysisRequest(BaseModel):
    content: str
    title: str
    url: Optional[str] = None
    site_id: Optional[str] = None

class LinkSuggestion(BaseModel):
    anchor_text: str
    target_url: str
    context: str
    confidence: float
    paragraph_index: int

class ContentAnalysisResponse(BaseModel):
    link_suggestions: List[LinkSuggestion]
    processing_time: float
    status: str
    analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Bulk processing models
class ContentItem(BaseModel):
    content: str
    title: str
    url: Optional[str] = None
    id: Optional[str] = None

class BulkProcessingRequest(BaseModel):
    content_items: List[ContentItem]
    site_id: Optional[str] = None
    batch_size: Optional[int] = None
    knowledge_building: Optional[bool] = False

class BulkProcessingResponse(BaseModel):
    job_id: str
    status: str
    total_items: int
    site_id: Optional[str] = None
    knowledge_building: Optional[bool] = False
    error: Optional[str] = None

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    site_id: Optional[str] = None
    total_items: int
    processed_items: int
    progress: float
    elapsed_seconds: float
    report_path: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    knowledge_building: Optional[bool] = False
    knowledge_db: Optional[Dict[str, Any]] = None

# Health check endpoint
@api_app.get("/health", tags=["Health"])
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Content analysis endpoint with authentication and caching
@api_app.post("/analyze/content", response_model=ContentAnalysisResponse, tags=["Analysis"])
async def analyze_content(
    request: ContentAnalysisRequest,
    site_info: Dict = Depends(check_rate_limit)  # This also validates the API key
):
    site_id = site_info["site_id"]
    logger.info(f"Analyzing content with title: {request.title} for site: {site_id}")

    try:
        # Use the site_id from authentication, not from the request
        # This ensures we're using the authenticated site's ID
        result = await analyze_content_with_cache(
            content=request.content,
            title=request.title,
            site_id=site_id,
            url=request.url
        )

        return result
    except Exception as e:
        logger.error(f"Error analyzing content for site {site_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing content: {str(e)}"
        )

# Helper function with caching applied
@cached(ttl=3600)  # Cache results for 1 hour
async def analyze_content_with_cache(content: str, title: str, site_id: str, url: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze content with caching.
    
    This function is wrapped with the @cached decorator to cache results.
    """
    return await analyze_content_task(
        content=content,
        title=title,
        site_id=site_id,
        url=url
    )

# Enhanced content analysis endpoint
@api_app.post("/analyze/enhanced", response_model=ContentAnalysisResponse, tags=["Analysis"])
async def analyze_content_enhanced_endpoint(
    request: ContentAnalysisRequest,
    site_info: Dict = Depends(check_rate_limit)  # This also validates the API key
):
    site_id = site_info["site_id"]
    logger.info(f"Starting enhanced analysis with title: {request.title} for site: {site_id}")

    try:
        # Use the site_id from authentication, not from the request
        # This ensures we're using the authenticated site's ID
        result = await analyze_enhanced_with_cache(
            content=request.content,
            title=request.title,
            site_id=site_id,
            url=request.url
        )

        return result
    except Exception as e:
        logger.error(f"Error in enhanced analysis for site {site_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing content: {str(e)}"
        )

@cached(ttl=3600)  # Cache results for 1 hour
async def analyze_enhanced_with_cache(content: str, title: str, site_id: str, url: Optional[str] = None) -> Dict[str, Any]:
    """
    Perform enhanced analysis with caching.
    
    This function is wrapped with the @cached decorator to cache results.
    """
    return await analyze_content_enhanced(
        content=content,
        title=title,
        site_id=site_id,
        url=url
    )

# Bulk processing endpoint
@api_app.post("/bulk/process", response_model=BulkProcessingResponse, tags=["Bulk Processing"])
async def bulk_process(
    request: BulkProcessingRequest,
    site_info: Dict = Depends(check_rate_limit)  # This also validates the API key
):
    site_id = site_info["site_id"]
    logger.info(f"Starting bulk processing for site: {site_id}, {len(request.content_items)} items")

    try:
        # Convert content items to dict format for processing
        content_items = [item.dict() for item in request.content_items]
        
        # Start bulk processing
        result = await start_bulk_processing(
            content_items=content_items,
            site_id=site_id,
            batch_size=request.batch_size,
            knowledge_building=request.knowledge_building
        )
        
        return result
    except Exception as e:
        logger.error(f"Error starting bulk processing for site {site_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting bulk processing: {str(e)}"
        )

# Job status endpoint
@api_app.get("/bulk/status/{job_id}", response_model=JobStatusResponse, tags=["Bulk Processing"])
async def job_status(
    job_id: str,
    site_info: Dict = Depends(check_rate_limit)  # This also validates the API key
):
    site_id = site_info["site_id"]
    logger.info(f"Getting job status for job: {job_id}, site: {site_id}")

    try:
        # Get job status
        result = get_job_status(job_id)
        
        # Check if job belongs to this site
        if result.get("site_id") and result.get("site_id") != site_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Job {job_id} does not belong to site {site_id}"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting job status: {str(e)}"
        )

# Stop job endpoint
@api_app.post("/bulk/stop/{job_id}", tags=["Bulk Processing"])
async def stop_processing_job(
    job_id: str,
    site_info: Dict = Depends(check_rate_limit)  # This also validates the API key
):
    site_id = site_info["site_id"]
    logger.info(f"Stopping job: {job_id}, site: {site_id}")

    try:
        # Get job info first
        job_info = get_job_status(job_id)
        
        # Check if job belongs to this site
        if job_info.get("site_id") and job_info.get("site_id") != site_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Job {job_id} does not belong to site {site_id}"
            )
        
        # Stop the job
        result = stop_job(job_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error stopping job: {str(e)}"
        )

# List jobs endpoint
@api_app.get("/bulk/jobs", tags=["Bulk Processing"])
async def list_all_jobs(
    site_info: Dict = Depends(check_rate_limit)  # This also validates the API key
):
    site_id = site_info["site_id"]
    logger.info(f"Listing jobs for site: {site_id}")

    try:
        # List jobs for this site
        jobs = list_jobs(site_id)
        return {"jobs": jobs, "count": len(jobs)}
    except Exception as e:
        logger.error(f"Error listing jobs for site {site_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing jobs: {str(e)}"
        )

# Knowledge stats endpoint
@api_app.get("/knowledge/stats", tags=["Knowledge Database"])
async def get_knowledge_stats(
    site_info: Dict = Depends(check_rate_limit)  # This also validates the API key
):
    site_id = site_info["site_id"]
    logger.info(f"Getting knowledge database stats for site: {site_id}")

    try:
        # Create a new processor to access the knowledge database
        # We do this to avoid importing the KnowledgeDatabase directly
        from src.core.bulk_processor import BulkContentProcessor
        processor = BulkContentProcessor(site_id=site_id)
        
        # Get the stats
        stats = processor.knowledge_db.get_database_stats()
        
        # Add a flag indicating if database is ready for analysis
        min_db_size = processor.config.get("initial_db_size", 100)
        stats["ready_for_analysis"] = stats.get("content_count", 0) >= min_db_size
        stats["minimum_required"] = min_db_size
        
        return {
            "site_id": site_id,
            "knowledge_db": stats
        }
    except Exception as e:
        logger.error(f"Error getting knowledge database stats for site {site_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting knowledge database stats: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)