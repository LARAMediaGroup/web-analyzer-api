# src/api/bulk_integration.py

import logging
import time
import asyncio
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import BackgroundTasks # Added

from src.core.bulk_processor import BulkContentProcessor
# Removed get_target_urls_for_site as it's no longer used here

# Configure logging
logger = logging.getLogger("web_analyzer_api.bulk_integration")

# In-memory storage for active jobs. Consider Redis or DB for persistence if needed.
active_jobs: Dict[str, Dict[str, Any]] = {}

async def start_bulk_processing(
    # --- ADDED background_tasks ---
    background_tasks: BackgroundTasks,
    # --- END ADDED ---
    content_items: List[Dict[str, Any]],
    site_id: Optional[str] = None,
    batch_size: Optional[int] = None,
    knowledge_building: bool = False
) -> Dict[str, Any]:
    """
    Start a bulk processing job using background tasks.

    Args:
        background_tasks: FastAPI BackgroundTasks instance.
        content_items: The content items to process.
        site_id: The site identifier.
        batch_size: The batch size.
        knowledge_building: Whether to run in knowledge building mode.

    Returns:
        Job information dictionary.
    """
    start_time = time.time()
    site_id = site_id or "default" # Ensure site_id is set
    logger.info(f"Starting bulk processing job for {len(content_items)} items, site ID: {site_id}, knowledge building: {knowledge_building}")

    try:
        # Generate a job ID
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{site_id}"

        # Create a new processor instance (associated with this specific job)
        # Config path assumption needs verification depending on execution context
        # Assuming config.json is at project root relative to where main.py runs
        processor = BulkContentProcessor(config_path="config.json", site_id=site_id)

        # Store initial job metadata
        active_jobs[job_id] = {
            "processor": processor, # Store the instance (be mindful of memory if many concurrent jobs)
            "start_time": start_time,
            "site_id": site_id,
            "total_items": len(content_items),
            "processed_items": 0,
            "status": "queued", # Initial status is queued
            "knowledge_building": knowledge_building,
            "last_update": time.time(),
            "results": None, # Placeholder for final results/stats
            "stats": None,
            "report_path": None,
            "error": None
        }

        # --- Use background_tasks.add_task ---
        # Schedule the actual processing function to run in the background
        background_tasks.add_task(
            _run_bulk_processing, # The function to run
            job_id=job_id,        # Arguments for the function
            processor=processor,
            content_items=content_items,
            site_id=site_id,
            batch_size=batch_size,
            knowledge_building=knowledge_building
        )
        # --- END Use background_tasks.add_task ---

        logger.info(f"Job {job_id} successfully queued for background processing.")

        # Return confirmation immediately
        return {
            "job_id": job_id,
            "status": "queued", # Return queued status
            "total_items": len(content_items),
            "site_id": site_id,
            "knowledge_building": knowledge_building
        }

    except Exception as e:
        logger.error(f"Error starting bulk processing job: {e}", exc_info=True)
        # If error happens during setup, don't leave a broken job entry
        if 'job_id' in locals() and job_id in active_jobs:
            del active_jobs[job_id]
        # Re-raise or return error response for main endpoint to handle
        # For simplicity, returning dict here, main endpoint will raise HTTPException
        return {
            "status": "error",
            "error": f"Failed to initialize job: {e}"
        }

async def _run_bulk_processing(
    job_id: str,
    processor: BulkContentProcessor,
    content_items: List[Dict[str, Any]],
    site_id: Optional[str] = None,
    batch_size: Optional[int] = None,
    knowledge_building: bool = False
) -> None:
    """
    The actual function that runs the bulk processing in the background.
    Updates the shared active_jobs dictionary.

    Args:
        job_id: The job ID.
        processor: The BulkContentProcessor instance for this job.
        content_items: The content items to process.
        site_id: The site identifier.
        batch_size: The batch size.
        knowledge_building: Whether to run in knowledge building mode.
    """
    logger.info(f"Background task started for job_id: {job_id}")
    try:
        # Ensure job exists before proceeding (should always be true here)
        if job_id not in active_jobs:
             logger.error(f"Job {job_id} not found in active_jobs at start of background task. Aborting.")
             return

        # Update job status to processing
        active_jobs[job_id]["status"] = "processing"
        active_jobs[job_id]["last_update"] = time.time()

        # Define progress callback (updates shared dict)
        def progress_callback(current: int, total: int, status: Dict[str, Any]):
             if job_id in active_jobs: # Check if job still exists (might be cancelled)
                 active_jobs[job_id]["processed_items"] = current + 1 # current is 0-indexed
                 active_jobs[job_id]["last_update"] = time.time()
                 # Optionally store last item status if needed for detailed progress
                 # active_jobs[job_id]["last_item_status"] = status
             else:
                  logger.warning(f"Progress callback for job {job_id} fired, but job not found in active_jobs.")


        processor.register_progress_callback(progress_callback)

        # Get initial KB stats (if needed)
        # db_stats_before = processor.knowledge_db.get_database_stats()
        # if job_id in active_jobs: active_jobs[job_id]["db_stats_before"] = db_stats_before

        # --- Run the potentially long process ---
        results, stats = await processor.process_content_items(
            content_items=content_items,
            site_id=site_id,
            batch_size=batch_size,
            knowledge_building_mode=knowledge_building
        )
        # --- Processing finished ---

        # Generate report (consider if this should also be async or if it's quick)
        # If report generation is slow, it could delay marking job as complete
        report_path = ""
        try:
            report_path = await processor.generate_report(
                results=results,
                stats=stats,
                report_format="html", # Or load from config
                site_id=site_id
            )
        except Exception as report_err:
            logger.error(f"Error generating report for job {job_id}: {report_err}", exc_info=True)


        # Update final job status in shared dict
        if job_id in active_jobs:
            active_jobs[job_id]["status"] = stats.get("status", "completed") # Use status from processor if available
            active_jobs[job_id]["report_path"] = report_path
            active_jobs[job_id]["results"] = results # Store results if needed, careful with memory
            active_jobs[job_id]["stats"] = stats
            active_jobs[job_id]["last_update"] = time.time()
            active_jobs[job_id]["processed_items"] = stats.get("processed_items", active_jobs[job_id]["total_items"]) # Ensure final count matches
            # Optionally update db stats after
            # db_stats_after = processor.knowledge_db.get_database_stats()
            # active_jobs[job_id]["db_stats_after"] = db_stats_after
            logger.info(f"Background task completed for job_id: {job_id}. Final status: {active_jobs[job_id]['status']}")
        else:
            logger.warning(f"Job {job_id} finished processing, but was not found in active_jobs to update status.")

    except Exception as e:
        logger.error(f"Exception during background processing for job {job_id}: {e}", exc_info=True)
        # Update job status to error in shared dict
        if job_id in active_jobs:
            active_jobs[job_id]["status"] = "error"
            active_jobs[job_id]["error"] = str(e)
            active_jobs[job_id]["last_update"] = time.time()
    finally:
        # Optional: Clean up processor instance if needed, though instance-per-job might be okay
        # if job_id in active_jobs:
        #      active_jobs[job_id]["processor"] = None # Allow garbage collection if processor holds large objects
        pass


def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get the status of a bulk processing job from the shared dictionary.
    """
    if job_id not in active_jobs:
        return {
            "status": "not_found",
            "error": f"Job ID {job_id} not found"
        }

    # Return relevant info from the job's dictionary entry
    job = active_jobs[job_id]
    total_items = job.get("total_items", 0)
    processed_items = job.get("processed_items", 0)
    progress = round((processed_items / total_items) * 100, 1) if total_items > 0 else (100 if job.get("status") == "completed" else 0)
    elapsed_seconds = time.time() - job.get("start_time", time.time())

    # Return a subset of the job data suitable for status check
    return {
        "job_id": job_id,
        "status": job.get("status", "unknown"),
        "site_id": job.get("site_id"),
        "total_items": total_items,
        "processed_items": processed_items,
        "progress": progress,
        "elapsed_seconds": round(elapsed_seconds, 2),
        "report_path": job.get("report_path"), # May be None until completed
        "stats": job.get("stats"), # May be None until completed
        "error": job.get("error"), # Populated on error
        "knowledge_building": job.get("knowledge_building", False),
        "last_update": datetime.fromtimestamp(job.get("last_update", 0)).isoformat() # Show last update time
    }

def stop_job(job_id: str) -> Dict[str, Any]:
    """
    Signal a running bulk processing job to stop.
    """
    if job_id not in active_jobs:
        return {
            "status": "not_found",
            "error": f"Job ID {job_id} not found"
        }

    job = active_jobs[job_id]

    # Check current status
    current_status = job.get("status")
    if current_status in ("completed", "error", "stopped", "stopping"):
        return {
            "status": "not_running_or_stopping",
            "message": f"Job {job_id} is already in state: {current_status}"
        }

    # Signal the processor (if it exists)
    processor = job.get("processor")
    if processor and hasattr(processor, 'stop_processing'):
        try:
            processor.stop_processing()
            job["status"] = "stopping" # Update status in the shared dict
            job["last_update"] = time.time()
            logger.info(f"Stop signal sent for job {job_id}.")
            return {
                "status": "stopping",
                "message": f"Stop signal sent to job {job_id}."
            }
        except Exception as e:
             logger.error(f"Error trying to signal stop for job {job_id}: {e}", exc_info=True)
             return {
                "status": "error",
                "error": f"Failed to send stop signal for job {job_id}: {e}"
            }
    else:
         logger.warning(f"Cannot stop job {job_id}: no processor instance found or stop method unavailable.")
         # If no processor to signal, maybe just mark as stopped? Or error?
         # Marking as error might be safer if we expect a processor.
         job["status"] = "error"
         job["error"] = "Processor unavailable for stopping."
         job["last_update"] = time.time()
         return {
            "status": "error",
            "error": f"Cannot stop job {job_id}: processor unavailable."
        }


def list_jobs(site_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List basic information about recent bulk processing jobs.
    Optionally filter by site ID.
    """
    jobs = []
    # Iterate safely over potentially changing dict
    current_job_ids = list(active_jobs.keys())

    for job_id in current_job_ids:
         if job_id in active_jobs: # Check if job still exists
            job = active_jobs[job_id]
            job_site_id = job.get("site_id")

            # Filter by site ID if specified
            if site_id and job_site_id != site_id:
                continue

            # Add basic job info
            jobs.append({
                "job_id": job_id,
                "status": job.get("status", "unknown"),
                "site_id": job_site_id,
                "total_items": job.get("total_items", 0),
                "processed_items": job.get("processed_items", 0),
                "start_time": datetime.fromtimestamp(job.get("start_time", 0)).isoformat(),
                "knowledge_building": job.get("knowledge_building", False),
            })

    # Sort by start time descending (most recent first)
    jobs.sort(key=lambda x: x["start_time"], reverse=True)
    return jobs

# Optional: Add cleanup mechanism for old jobs in active_jobs if memory becomes an issue