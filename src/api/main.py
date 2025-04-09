# src/api/main.py

import logging.config
import os
from typing import List, Optional
# --- ADDED IMPORT ---
from datetime import datetime
# --- END ADDED IMPORT ---

from fastapi import FastAPI, HTTPException, Depends, Body, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Import API routers and dependencies
# Make sure schemas.py exists in the same directory or adjust path if needed
from src.api import schemas, auth, cache, analyzer_integration, enhanced_integration, bulk_integration
from src.core.knowledge_db.knowledge_database import KnowledgeDatabase

# Configure logging
log_config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'logging_config.json')
if os.path.exists(log_config_path):
    logging.config.fileConfig(log_config_path, disable_existing_loggers=False)
else:
    logging.basicConfig(level=logging.INFO) # Basic config if file not found

logger = logging.getLogger("web_analyzer_api")

# Create FastAPI app instance
app = FastAPI(
    title="Web Content Analyzer API",
    description="API for analyzing web content and suggesting internal links.",
    version="1.1.1", # Incremented version
)

# Configure CORS (Cross-Origin Resource Sharing)
# Adjust origins as needed for your frontend applications
origins = [
    "http://localhost",
    "http://localhost:8080", # Example for local dev
    "https://thevou.com", # Add your WordPress site URL
    # Add other allowed origins if necessary
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)

# --- API Routes ---

# Root endpoint (optional)
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Web Content Analyzer API!"}

# Health check endpoint
@app.get("/health", response_model=schemas.HealthResponse, tags=["Status"])
async def health_check():
    """Check the health of the API."""
    # Basic check, could be expanded later to check DB connection, etc.
    # Now 'datetime' is imported and can be used
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# --- V1 API Routes ---
api_v1_prefix = "/api/v1"

# Simple content analysis endpoint (using ContentAnalyzer)
@app.post(f"{api_v1_prefix}/analyze/content",
          response_model=schemas.AnalysisResponse,
          dependencies=[Depends(auth.check_rate_limit)], # Apply auth/rate limiting
          tags=["Analysis"])
@cache.cached(ttl=3600) # Cache results for 1 hour
async def analyze_content_simple(
    request: schemas.AnalysisRequest,
    site_info: dict = Depends(auth.get_site_from_api_key) # Get site info from API key
):
    """
    Analyze content using the simple analyzer (topic weights).
    """
    logger.info(f"Received simple analysis request for site: {site_info.get('site_id', 'N/A')}")
    # Note: site_id from site_info is currently NOT used by analyzer_integration.analyze_content_task
    result = await analyzer_integration.analyze_content_task(
        content=request.content,
        title=request.title,
        site_id=site_info.get('site_id'), # Pass site_id
        url=request.url
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("error", "Analysis failed"))
    return result

# Enhanced content analysis endpoint (using EnhancedContentAnalyzer)
@app.post(f"{api_v1_prefix}/analyze/enhanced",
          response_model=schemas.AnalysisResponse,
          dependencies=[Depends(auth.check_rate_limit)], # Apply auth/rate limiting
          tags=["Analysis"])
# @cache.cached(ttl=3600) # Caching might be less effective if KB changes frequently
async def analyze_content_enhanced(
    request: schemas.AnalysisRequest,
    site_info: dict = Depends(auth.get_site_from_api_key) # Get site info from API key
):
    """
    Analyze content using the enhanced analyzer (embeddings, KB).
    Requires site_id derived from API Key.
    """
    site_id = site_info.get('site_id')
    if not site_id:
         # Should not happen if get_site_from_api_key worked, but defensive check
         raise HTTPException(status_code=401, detail="Could not determine site ID from API Key.")

    logger.info(f"Received enhanced analysis request for site: {site_id}")
    # Pass site_id; analyzer_integration now handles calling EnhancedContentAnalyzer correctly
    result = await enhanced_integration.analyze_content_enhanced(
        content=request.content,
        title=request.title,
        site_id=site_id, # Pass validated site_id
        url=request.url
    )
    if result.get("status") == "error":
        # Determine appropriate status code based on error type if possible
        status_code = 500 if "Internal" in result.get("error", "") else 400
        raise HTTPException(status_code=status_code, detail=result.get("error", "Analysis failed"))
    return result

# --- Bulk Processing Endpoints ---

@app.post(f"{api_v1_prefix}/bulk/process",
          response_model=schemas.JobSubmissionResponse,
          status_code=202, # Accepted
          dependencies=[Depends(auth.check_rate_limit)],
          tags=["Bulk Processing"])
async def start_bulk_job(
    background_tasks: BackgroundTasks, # FastAPI injects this
    bulk_request: schemas.BulkAnalysisRequest,
    site_info: dict = Depends(auth.get_site_from_api_key)
):
    """
    Start a bulk processing job (knowledge building or suggestion generation).
    Runs the actual processing in the background.
    """
    site_id = site_info.get('site_id')
    if not site_id:
         raise HTTPException(status_code=401, detail="Could not determine site ID from API Key.")

    logger.info(f"Received bulk processing request for site: {site_id}, items: {len(bulk_request.content_items)}, knowledge_building: {bulk_request.knowledge_building}")

    if not bulk_request.content_items:
         raise HTTPException(status_code=400, detail="No content items provided for bulk processing.")

    # Use the bulk_integration module to start the job (which now uses background tasks)
    job_info = await bulk_integration.start_bulk_processing(
        background_tasks=background_tasks,
        content_items=[item.dict() for item in bulk_request.content_items], # Convert Pydantic models to dicts
        site_id=site_id,
        batch_size=bulk_request.batch_size,
        knowledge_building=bulk_request.knowledge_building
    )

    if job_info.get("status") == "error":
        raise HTTPException(status_code=500, detail=job_info.get("error", "Failed to start bulk job"))

    # Return 202 Accepted with Job ID
    return job_info


@app.get(f"{api_v1_prefix}/bulk/status/{{job_id}}",
         response_model=schemas.JobStatusResponse,
         dependencies=[Depends(auth.check_rate_limit)],
         tags=["Bulk Processing"])
async def get_bulk_job_status(
    job_id: str,
    site_info: dict = Depends(auth.get_site_from_api_key) # Ensure user can only query jobs for their site? Maybe later.
):
    """
    Get the status of a specific bulk processing job.
    """
    logger.debug(f"Request for job status: {job_id}, requesting site: {site_info.get('site_id')}")
    status_info = bulk_integration.get_job_status(job_id)

    # Optional: Add check here to ensure the site_id from site_info matches the job's site_id for security
    # if not status_info.get("status") == "not_found" and status_info.get("site_id") != site_info.get("site_id"):
    #     raise HTTPException(status_code=404, detail="Job ID not found for your site.")

    if status_info.get("status") == "not_found":
        raise HTTPException(status_code=404, detail=status_info.get("error", "Job not found"))

    return status_info


@app.post(f"{api_v1_prefix}/bulk/stop/{{job_id}}",
          response_model=schemas.JobControlResponse,
          dependencies=[Depends(auth.check_rate_limit)],
          tags=["Bulk Processing"])
async def stop_bulk_job(
    job_id: str,
    site_info: dict = Depends(auth.get_site_from_api_key) # Add security check?
):
    """
    Request to stop a running bulk processing job.
    """
    logger.info(f"Received request to stop job: {job_id}, requesting site: {site_info.get('site_id')}")
    # Optional: Add site_id check for security
    stop_info = bulk_integration.stop_job(job_id)

    if stop_info.get("status") == "not_found":
         raise HTTPException(status_code=404, detail=stop_info.get("error", "Job not found"))
    if stop_info.get("status") == "error":
        raise HTTPException(status_code=500, detail=stop_info.get("error", "Failed to stop job"))

    return stop_info


@app.get(f"{api_v1_prefix}/bulk/jobs",
         response_model=List[schemas.JobListInfo],
         dependencies=[Depends(auth.check_rate_limit)],
         tags=["Bulk Processing"])
async def list_bulk_jobs(
    site_info: dict = Depends(auth.get_site_from_api_key)
):
    """
    List recent bulk processing jobs for the site associated with the API key.
    """
    site_id = site_info.get('site_id')
    if not site_id:
        raise HTTPException(status_code=401, detail="Could not determine site ID from API Key.")

    logger.debug(f"Request to list jobs for site: {site_id}")
    # Filter jobs by site_id in the integration layer
    jobs = bulk_integration.list_jobs(site_id=site_id)
    return jobs

# --- Knowledge Base Endpoints (Optional) ---

@app.get(f"{api_v1_prefix}/knowledge/stats",
         response_model=schemas.KnowledgeBaseStats,
         dependencies=[Depends(auth.check_rate_limit)],
         tags=["Knowledge Base"])
async def get_kb_stats(
    site_info: dict = Depends(auth.get_site_from_api_key)
):
    """
    Get statistics about the knowledge base for the site.
    """
    site_id = site_info.get('site_id')
    if not site_id:
         raise HTTPException(status_code=401, detail="Could not determine site ID from API Key.")

    logger.debug(f"Request for KB stats for site: {site_id}")
    try:
        # Consider if KB instance should be shared/cached or created per request
        kb = KnowledgeDatabase(site_id=site_id)
        stats = kb.get_database_stats()
        if not stats:
             # Return empty stats object or 404? Let's return empty for now
             # Use default values from Pydantic model if possible, or return empty dict
              logger.warning(f"Knowledge base for site {site_id} returned empty stats.")
              # Raise 404 instead?
              raise HTTPException(status_code=404, detail=f"Could not retrieve stats for site {site_id}. KB might be empty.")
        return stats
    except Exception as e:
        logger.error(f"Error getting KB stats for site {site_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve knowledge base statistics.")

# Add more endpoints as needed (e.g., delete KB entry, query specific entry)


# Include other routers if you split endpoints into separate files later
# app.include_router(other_router.router, prefix="/api/v1/other", tags=["Other"])

logger.info("FastAPI application configured and ready.")

# Note: Uvicorn or similar will run this app instance. Example command:
# uvicorn src.api.main:app --reload --log-config config/logging_config.json