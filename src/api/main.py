from fastapi import FastAPI, HTTPException, Depends, status, Request, BackgroundTasks, Path, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os
import json
import logging
from pydantic import BaseModel, Field

# Import analyzer integrations
from src.api.analyzer_integration import analyze_content_task
from src.api.enhanced_integration import analyze_content_enhanced
from src.api.bulk_integration import start_bulk_processing, get_job_status, stop_job, list_jobs

# Import authentication and caching
from src.api.auth import get_site_from_api_key, check_rate_limit
from src.api.cache import cached

# Import KnowledgeDatabase
from src.core.knowledge_db.knowledge_database import KnowledgeDatabase

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

# Download required NLTK data on startup
@app.on_event("startup")
async def download_nltk_data():
    import nltk
    nltk.download('punkt')
    nltk.download('punkt_tab')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('wordnet')
    nltk.download('stopwords')
    nltk.download('maxent_ne_chunker')
    nltk.download('words')

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://thevou.com", "https://www.thevou.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request/response models
class ContentAnalysisRequest(BaseModel):
    content: str = Field(..., min_length=1, description="The main text content to analyze.")
    title: str = Field(..., min_length=1, description="The title of the content.")
    url: Optional[str] = Field(None, description="The canonical URL of the content being analyzed (used to prevent self-links).")
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

# Health check endpoint at root level
@app.get("/health", tags=["Health"])
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Content analysis endpoint with authentication and caching
@app.post("/api/v1/analyze/content", response_model=ContentAnalysisResponse, tags=["Analysis"])
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
@app.post("/api/v1/analyze/enhanced", response_model=ContentAnalysisResponse, tags=["Analysis"])
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
@app.post("/api/v1/bulk/process", response_model=BulkProcessingResponse, tags=["Bulk Processing"])
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
@app.get("/api/v1/bulk/status/{job_id}", response_model=JobStatusResponse, tags=["Bulk Processing"])
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
@app.post("/api/v1/bulk/stop/{job_id}", tags=["Bulk Processing"])
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
@app.get("/api/v1/bulk/jobs", tags=["Bulk Processing"])
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
@app.get("/api/v1/knowledge/stats", tags=["Knowledge Database"])
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

# Knowledge Base Management Endpoints

@app.delete(
    "/api/v1/kb/content/{content_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Knowledge Base"],
    summary="Remove Content from Knowledge Base",
    description="Removes a specific content item and its associated data (entities, topics) from the site's knowledge base. Requires API key matching the site.",
)
async def remove_kb_content(
    content_id: str = Path(..., description="The unique identifier of the content to remove (e.g., WordPress Post ID)."),
    site_info: Dict = Depends(check_rate_limit) # Use the same auth dependency
):
    """
    Deletes content from the Knowledge Base.

    - Requires authentication via API Key.
    - The `site_id` associated with the API key determines which knowledge base is accessed.
    - Returns `204 No Content` on successful deletion or if the content was already gone.
    - Returns `403 Forbidden` if API key is invalid or rate limit exceeded.
    - Returns `500 Internal Server Error` on database errors.
    """
    site_id = site_info["site_id"]
    logger.info(f"API: Received request to remove content_id '{content_id}' from KB for site '{site_id}'.")

    if not content_id:
        logger.warning(f"API: Received remove request with empty content_id for site '{site_id}'.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content ID cannot be empty."
        )

    try:
        # Initialize KnowledgeDatabase for the specific site
        # Pass the main config path, KB will load its specific settings
        kb = KnowledgeDatabase(site_id=site_id)

        # Attempt to remove the content
        success = kb.remove_content(content_id=str(content_id)) # Ensure content_id is string

        if success:
            logger.info(f"API: Successfully processed removal request for content_id '{content_id}', site '{site_id}'. Content removed.")
            # Return 204 even if it was already gone, the desired state is achieved.
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        else:
            # Log that it wasn't found, but still return 204 as the end state (not present) is met.
            # If we wanted to differentiate between "deleted now" and "already gone", we could return a different response or body.
            # For simplicity and idempotency, 204 is often preferred for DELETE.
            logger.info(f"API: Processed removal request for content_id '{content_id}', site '{site_id}'. Content was not found (already removed or never existed).")
            return Response(status_code=status.HTTP_204_NO_CONTENT)

    except HTTPException as http_exc:
         # Re-raise HTTPExceptions (like rate limit errors from dependency)
         raise http_exc
    except Exception as e:
        # Log the detailed error
        logger.error(f"API: Error removing content_id '{content_id}' from KB for site '{site_id}': {str(e)}", exc_info=True)
        # Return a generic 500 error to the client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove content from knowledge base: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)