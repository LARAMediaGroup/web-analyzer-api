"""
Bulk Processing Integration Module

This module integrates the bulk processor with the API.
"""

import logging
import time
import asyncio
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.core.bulk_processor import BulkContentProcessor
from src.api.enhanced_integration import get_target_urls_for_site

# Configure logging
logger = logging.getLogger("web_analyzer_api.bulk_integration")

# Map of active bulk processors by job ID
active_jobs = {}

async def start_bulk_processing(
    content_items: List[Dict[str, Any]],
    site_id: Optional[str] = None,
    batch_size: Optional[int] = None,
    knowledge_building: bool = False
) -> Dict[str, Any]:
    """
    Start a bulk processing job.
    
    Args:
        content_items (List[Dict[str, Any]]): The content items to process
        site_id (str, optional): The site identifier
        batch_size (int, optional): The batch size
        knowledge_building (bool, optional): Whether to run in knowledge building mode
        
    Returns:
        Dict[str, Any]: Job information
    """
    start_time = time.time()
    logger.info(f"Starting bulk processing job for {len(content_items)} items, site ID: {site_id}, knowledge building: {knowledge_building}")

    try:
        # Generate a job ID
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{site_id or 'default'}"
        
        # Create a new processor
        processor = BulkContentProcessor(site_id=site_id)
        
        # Store in active jobs
        active_jobs[job_id] = {
            "processor": processor,
            "start_time": start_time,
            "site_id": site_id,
            "total_items": len(content_items),
            "processed_items": 0,
            "status": "starting",
            "knowledge_building": knowledge_building,
            "last_update": time.time()
        }
        
        # Get target URLs for the site
        target_urls = get_target_urls_for_site(site_id)
        
        # Start background task to run the processing
        asyncio.create_task(
            _run_bulk_processing(
                job_id=job_id,
                processor=processor,
                content_items=content_items,
                target_pages=target_urls,
                site_id=site_id,
                batch_size=batch_size,
                knowledge_building=knowledge_building
            )
        )
        
        return {
            "job_id": job_id,
            "status": "started",
            "total_items": len(content_items),
            "site_id": site_id,
            "knowledge_building": knowledge_building
        }

    except Exception as e:
        logger.error(f"Error starting bulk processing job: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

async def _run_bulk_processing(
    job_id: str,
    processor: BulkContentProcessor,
    content_items: List[Dict[str, Any]],
    target_pages: List[Dict[str, str]],
    site_id: Optional[str] = None,
    batch_size: Optional[int] = None,
    knowledge_building: bool = False
) -> None:
    """
    Run the bulk processing job.
    
    Args:
        job_id (str): The job ID
        processor (BulkContentProcessor): The processor instance
        content_items (List[Dict[str, Any]]): The content items to process
        target_pages (List[Dict[str, str]]): The target pages for links
        site_id (str, optional): The site identifier
        batch_size (int, optional): The batch size
        knowledge_building (bool, optional): Whether to run in knowledge building mode
    """
    try:
        # Update job status
        active_jobs[job_id]["status"] = "processing"
        
        # Define progress callback
        def progress_callback(current: int, total: int, status: Dict[str, Any]):
            active_jobs[job_id]["processed_items"] = current + 1
            active_jobs[job_id]["last_update"] = time.time()
            active_jobs[job_id]["last_status"] = status
        
        # Register callback
        processor.register_progress_callback(progress_callback)
        
        # Get current knowledge database stats
        db_stats = processor.knowledge_db.get_database_stats()
        active_jobs[job_id]["db_stats_before"] = db_stats
        
        # Run the processor
        results, stats = await processor.process_content_items(
            content_items=content_items,
            target_pages=target_pages,
            site_id=site_id,
            batch_size=batch_size,
            knowledge_building_mode=knowledge_building
        )
        
        # Get updated knowledge database stats
        db_stats_after = processor.knowledge_db.get_database_stats()
        active_jobs[job_id]["db_stats_after"] = db_stats_after
        
        # Generate report
        report_path = await processor.generate_report(
            results=results,
            stats=stats,
            report_format="html",
            site_id=site_id
        )
        
        # Update job status
        active_jobs[job_id]["status"] = "completed"
        active_jobs[job_id]["report_path"] = report_path
        active_jobs[job_id]["stats"] = stats
        
        logger.info(f"Bulk processing job {job_id} completed (knowledge building: {knowledge_building})")
    
    except Exception as e:
        logger.error(f"Error running bulk processing job {job_id}: {str(e)}")
        
        # Update job status
        if job_id in active_jobs:
            active_jobs[job_id]["status"] = "error"
            active_jobs[job_id]["error"] = str(e)

def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get the status of a bulk processing job.
    
    Args:
        job_id (str): The job ID
        
    Returns:
        Dict[str, Any]: Job status information
    """
    if job_id not in active_jobs:
        return {
            "status": "not_found",
            "error": f"Job ID {job_id} not found"
        }
    
    job = active_jobs[job_id]
    
    # Calculate progress
    total_items = job.get("total_items", 0)
    processed_items = job.get("processed_items", 0)
    progress = round((processed_items / total_items) * 100, 1) if total_items > 0 else 0
    
    # Calculate elapsed time
    start_time = job.get("start_time", time.time())
    elapsed_seconds = time.time() - start_time
    
    # Get current knowledge database stats
    db_stats = None
    if job.get("processor"):
        try:
            db_stats = job["processor"].knowledge_db.get_database_stats()
        except Exception as e:
            logger.error(f"Error getting knowledge DB stats: {str(e)}")
    
    return {
        "job_id": job_id,
        "status": job.get("status", "unknown"),
        "site_id": job.get("site_id"),
        "total_items": total_items,
        "processed_items": processed_items,
        "progress": progress,
        "elapsed_seconds": elapsed_seconds,
        "report_path": job.get("report_path"),
        "stats": job.get("stats"),
        "error": job.get("error"),
        "knowledge_building": job.get("knowledge_building", False),
        "knowledge_db": {
            "current": db_stats,
            "before": job.get("db_stats_before"),
            "after": job.get("db_stats_after")
        }
    }

def stop_job(job_id: str) -> Dict[str, Any]:
    """
    Stop a running bulk processing job.
    
    Args:
        job_id (str): The job ID
        
    Returns:
        Dict[str, Any]: Result of stop operation
    """
    if job_id not in active_jobs:
        return {
            "status": "not_found",
            "error": f"Job ID {job_id} not found"
        }
    
    job = active_jobs[job_id]
    
    # If the job is already completed or failed, can't stop it
    if job.get("status") in ("completed", "error", "stopped"):
        return {
            "status": "not_running",
            "message": f"Job {job_id} is already in state: {job.get('status')}"
        }
    
    # Signal the processor to stop
    processor = job.get("processor")
    if processor:
        processor.stop_processing()
        job["status"] = "stopping"
        
        return {
            "status": "stopping",
            "message": f"Job {job_id} is being stopped"
        }
    
    return {
        "status": "error",
        "error": f"Cannot stop job {job_id}: no processor found"
    }

def list_jobs(site_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all bulk processing jobs.
    
    Args:
        site_id (str, optional): Filter by site ID
        
    Returns:
        List[Dict[str, Any]]: List of job information
    """
    jobs = []
    
    for job_id, job in active_jobs.items():
        # Filter by site ID if specified
        if site_id and job.get("site_id") != site_id:
            continue
        
        # Add basic job info
        jobs.append({
            "job_id": job_id,
            "status": job.get("status", "unknown"),
            "site_id": job.get("site_id"),
            "total_items": job.get("total_items", 0),
            "processed_items": job.get("processed_items", 0),
            "start_time": datetime.fromtimestamp(job.get("start_time", 0)).isoformat()
        })
    
    return jobs