"""
Bulk Content Processor Module

This module handles processing multiple pieces of content efficiently
using parallelized processing and progress tracking.

It also manages the knowledge database for internal linking.
"""

import os
import json
import logging
import time
from typing import List, Dict, Any, Tuple, Optional, Callable
import asyncio
from datetime import datetime
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import traceback
import hashlib # Added for hash generation in _process_single_item if needed

# Import analysis components
from src.core.enhanced_analyzer import EnhancedContentAnalyzer
from src.core.knowledge_db.knowledge_database import KnowledgeDatabase

# Configure logging
logger = logging.getLogger("web_analyzer.bulk_processor")

class BulkContentProcessor:
    """
    Processor for handling multiple content items efficiently.
    """

    def __init__(self, config_path: str = "config.json", site_id: Optional[str] = None):
        """
        Initialize the bulk content processor.

        Args:
            config_path: Path to the configuration file
            site_id: Optional site identifier for multi-site support
        """
        self.config = self._load_config(config_path)
        self.analyzer = EnhancedContentAnalyzer(config_path) # Initialize the analyzer

        # Initialize knowledge database - REMOVED analyser argument
        self.site_id = site_id or "default"
        # The KnowledgeDatabase class now loads its own model internally
        self.knowledge_db = KnowledgeDatabase(config_path, self.site_id)

        # Processing parameters
        self.max_workers = self.config.get("max_workers", 4)
        self.progress_callback = None
        self.stop_signal = False
        self.knowledge_building_mode = False

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            # Determine project root relative to this file (src/core/bulk_processor.py)
            project_root = os.path.join(os.path.dirname(__file__), '..', '..')
            actual_config_path = os.path.join(project_root, config_path)
            logger.debug(f"Attempting to load main config from: {actual_config_path}")
            if os.path.exists(actual_config_path):
                with open(actual_config_path, 'r') as f:
                    config_data = json.load(f)
                    # Store the path used to load the config if needed elsewhere
                    config_data["config_path"] = config_path
                    return config_data
            else:
                logger.warning(f"Config file {actual_config_path} not found, using defaults")
                return {
                    "max_workers": 4,
                    "batch_size": 10,
                    "output_dir": "results",
                    "save_intermediate": True,
                    "initial_db_size": 100, # Added default
                    "embedding_text_field": "title", # Added default
                    "config_path": config_path # Store original path even for defaults
                }
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {str(e)}")
            # Return essential defaults on error
            return {
                    "max_workers": 4,
                    "batch_size": 10,
                    "output_dir": "results",
                    "save_intermediate": True,
                    "initial_db_size": 100,
                    "embedding_text_field": "title",
                    "config_path": config_path
            }


    def register_progress_callback(self, callback: Callable[[int, int, Dict[str, Any]], None]) -> None:
        """
        Register a callback for progress updates.

        Args:
            callback: Function to call with progress updates

        The callback will receive:
        - current_item: Index of current item
        - total_items: Total number of items
        - status: Dictionary with processing status
        """
        self.progress_callback = callback

    def stop_processing(self) -> None:
        """Signal to stop processing."""
        self.stop_signal = True
        logger.info("Stop signal received.")

    def reset_stop_signal(self) -> None:
        """Reset the stop signal."""
        self.stop_signal = False

    async def process_content_items(
        self,
        content_items: List[Dict[str, Any]],
        site_id: Optional[str] = None,
        batch_size: Optional[int] = None,
        knowledge_building_mode: bool = False
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Process multiple content items asynchronously.

        Args:
            content_items: List of content items to process
            site_id: Optional site identifier
            batch_size: Optional batch size (defaults to config value)
            knowledge_building_mode: Whether to build knowledge database without suggestions

        Returns:
            Tuple of results list and processing stats
        """
        start_time = time.time()
        self.reset_stop_signal()
        self.knowledge_building_mode = knowledge_building_mode

        # Use provided site_id or the one from initialization
        current_site_id = site_id if site_id else self.site_id

        # If site_id changes, re-initialize site-specific components
        if site_id and site_id != self.site_id:
            logger.info(f"Switching site context to: {site_id}")
            self.site_id = site_id
            # Re-initialize KB for the new site_id
            self.knowledge_db = KnowledgeDatabase(self.config.get("config_path", "config.json"), self.site_id)
            # Re-initialize analyzer if it's site-specific (EnhancedAnalyzer likely is via KB)
            self.analyzer = EnhancedContentAnalyzer(self.config.get("config_path", "config.json"), self.site_id)

        # Check knowledge database status
        db_stats = self.knowledge_db.get_database_stats()
        db_content_count = db_stats.get("content_count", 0)
        logger.info(f"Knowledge database for site '{current_site_id}' has {db_content_count} entries")

        if batch_size is None:
            batch_size = self.config.get("batch_size", 10)

        total_items = len(content_items)
        results = []
        stats = {
            "total_items": total_items,
            "processed_items": 0,
            "successful_items": 0,
            "failed_items": 0,
            "total_suggestions": 0,
            "knowledge_db_initial_items": db_content_count,
            "knowledge_db_final_items": db_content_count, # Will be updated at the end
            "knowledge_building_mode": knowledge_building_mode,
            "site_id": current_site_id,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration_seconds": 0,
            "status": "in_progress"
        }

        logger.info(f"Starting bulk processing of {total_items} items for site '{current_site_id}' (knowledge building: {knowledge_building_mode})")

        # Process in batches
        for batch_start in range(0, total_items, batch_size):
            if self.stop_signal:
                logger.info("Processing stopped by user signal.")
                stats["status"] = "stopped"
                break # Exit batch loop

            batch_end = min(batch_start + batch_size, total_items)
            current_batch_items = content_items[batch_start:batch_end]
            logger.info(f"Processing batch {batch_start // batch_size + 1}, items {batch_start+1}-{batch_end} ({len(current_batch_items)} items)")

            try:
                batch_results = await self._process_batch(
                    current_batch_items,
                    current_site_id, # Pass current site_id
                    batch_start,
                    total_items
                )

                # Check if stop signal was set during batch processing
                if self.stop_signal:
                     logger.info("Stop signal detected after processing batch. Results from this batch may be incomplete or contain cancellations.")
                     results.extend(batch_results)
                     processed_in_batch = len(batch_results)
                     successful_in_batch = sum(1 for r in batch_results if r.get("status") == "success")
                     failed_in_batch = processed_in_batch - successful_in_batch
                     stats["processed_items"] += processed_in_batch
                     stats["successful_items"] += successful_in_batch
                     stats["failed_items"] += failed_in_batch
                     stats["total_suggestions"] += sum(len(r.get("link_suggestions", [])) for r in batch_results)
                     stats["status"] = "stopped"
                     if self.config.get("save_intermediate", True):
                         self._save_intermediate_results(results, stats, current_site_id)
                     break # Exit batch loop

                # If no stop signal during batch, proceed normally
                results.extend(batch_results)

                processed_in_batch = len(batch_results)
                successful_in_batch = sum(1 for r in batch_results if r.get("status") == "success")
                failed_in_batch = processed_in_batch - successful_in_batch

                stats["processed_items"] += processed_in_batch
                stats["successful_items"] += successful_in_batch
                stats["failed_items"] += failed_in_batch
                stats["total_suggestions"] += sum(len(r.get("link_suggestions", [])) for r in batch_results)

                logger.info(f"Batch {batch_start // batch_size + 1} completed. Processed: {processed_in_batch}, Success: {successful_in_batch}, Failed: {failed_in_batch}")

                if self.config.get("save_intermediate", True):
                    self._save_intermediate_results(results, stats, current_site_id)

            except Exception as e:
                logger.error(f"Fatal error processing batch starting at index {batch_start}: {str(e)}", exc_info=True)
                failed_count = len(current_batch_items)
                stats["processed_items"] += failed_count
                stats["failed_items"] += failed_count
                stats["status"] = "error"
                for i, item in enumerate(current_batch_items):
                    results.append({
                        "id": item.get("id", f"batch_err_{batch_start+i}"),
                        "title": item.get("title", "unknown"),
                        "url": str(item.get("url", "")),
                        "status": "error",
                        "error": f"Batch processing failed: {str(e)}",
                        "link_suggestions": [],
                        "analysis": {},
                        "processing_time": 0,
                        "in_knowledge_db": False
                    })
                logger.error("Stopping bulk processing due to fatal batch error.")
                break # Exit batch loop

        # Final stats calculation
        end_time = time.time()
        duration = end_time - start_time

        # Update final KB count
        final_db_stats = self.knowledge_db.get_database_stats()
        stats["knowledge_db_final_items"] = final_db_stats.get("content_count", db_content_count)

        stats["end_time"] = datetime.now().isoformat()
        stats["duration_seconds"] = duration
        if stats["status"] == "in_progress":
             stats["status"] = "completed"

        logger.info(f"Bulk processing {stats['status']} in {duration:.2f} seconds")
        stats["processed_items"] = min(stats["processed_items"], total_items)

        actual_processed = stats["processed_items"]
        actual_successful = stats["successful_items"]
        actual_failed = stats["failed_items"]

        if actual_successful + actual_failed != actual_processed and stats["status"] != "stopped":
            logger.warning(f"Stats inconsistency detected: Successful ({actual_successful}) + Failed ({actual_failed}) != Processed ({actual_processed}). Adjusting failed count.")
            actual_failed = actual_processed - actual_successful
            stats["failed_items"] = actual_failed

        logger.info(f"Final Stats for site '{current_site_id}': Processed={actual_processed}, Successful={actual_successful}, Failed={actual_failed}")
        logger.info(f"Generated {stats['total_suggestions']} link suggestions")
        logger.info(f"Knowledge base items: Initial={stats['knowledge_db_initial_items']}, Final={stats['knowledge_db_final_items']}")

        # Save final results
        self._save_final_results(results, stats, current_site_id)

        return results, stats

    async def _process_batch(
        self,
        batch_items: List[Dict[str, Any]],
        site_id: Optional[str], # Renamed for clarity
        batch_start: int = 0,
        total_items: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of content items using a thread pool.

        Args:
            batch_items: List of items in the current batch
            site_id: Current site identifier
            batch_start: Starting index of the batch in the overall list
            total_items: Total number of items

        Returns:
            List of processing results
        """
        loop = asyncio.get_event_loop()
        results = []
        item_futures = {} # Map future to original item data

        # Use context manager for ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for i, item in enumerate(batch_items):
                if self.stop_signal:
                    break # Stop submitting new tasks if signal received

                overall_index = batch_start + i
                # Submit task to executor
                future = loop.run_in_executor(
                    executor,
                    self._process_single_item, # Target function
                    item,                  # Arguments for the function
                    site_id,
                    overall_index,
                    total_items
                )
                futures.append(future)
                item_futures[future] = item # Store item context

            # Process completed futures as they finish
            for future in asyncio.as_completed(futures):
                if self.stop_signal:
                    # Cancel remaining futures if not already done
                    for f in futures:
                        if not f.done():
                            f.cancel()
                    logger.warning("Stop signal received during batch completion, cancelling remaining tasks.")
                    # We still process results for futures that completed *before* the check
                    # and handle cancellations for those caught by the except block below

                original_item = item_futures.get(future, {}) # Get context
                item_id = original_item.get("id", "unknown")
                item_title = original_item.get("title", "unknown")

                try:
                    # Get result from completed future
                    result = await future # This re-raises exceptions from the worker
                    results.append(result)
                    # Log errors handled within _process_single_item
                    if result.get("status") != "success":
                         logger.warning(f"Item {item_id} ('{item_title}') processed with error status: {result.get('error', 'Unknown error')}")

                except concurrent.futures.CancelledError:
                     logger.warning(f"Task for item {item_id} ('{item_title}') was cancelled.")
                     # Append consistent error result
                     results.append({
                        "id": item_id,
                        "title": item_title,
                        "url": str(original_item.get("url", "")),
                        "status": "error",
                        "error": "Task cancelled",
                        "link_suggestions": [],
                        "analysis": {},
                        "processing_time": 0,
                        "in_knowledge_db": False
                     })
                except Exception as e:
                    # Catch exceptions raised by _process_single_item (if not caught internally)
                    # or other errors during future execution
                    logger.error(f"Error retrieving result from worker future for item {item_id} ('{item_title}'): {e}", exc_info=True)
                     # Append consistent error result
                    results.append({
                        "id": item_id,
                        "title": item_title,
                        "url": str(original_item.get("url", "")),
                        "status": "error",
                        "error": f"Future execution failed: {e}",
                        "link_suggestions": [],
                        "analysis": {},
                        "processing_time": 0,
                        "in_knowledge_db": False
                    })

        # Final check on result count consistency
        if not self.stop_signal and len(results) != len(batch_items):
             logger.error(f"Batch processing mismatch: Submitted {len(batch_items)} tasks, got {len(results)} results. Investigate potential lost tasks or logic errors.")

        return results

    def _process_single_item(
        self,
        item: Dict[str, Any],
        site_id: Optional[str], # Renamed for clarity
        current_index: int = 0,
        total_items: int = 0
    ) -> Dict[str, Any]:
        """
        Process a single content item and report progress.

        Args:
            item: Content item to process (expects keys like 'id', 'title', 'content', 'url')
            site_id: Current site identifier
            current_index: Index of this item in the overall list
            total_items: Total number of items

        Returns:
            Dictionary with processing results including 'status', 'id', 'url' (as string), etc.
        """
        item_id = item.get("id", str(current_index))
        item_title = item.get("title", "") # Use title for logging
        logger.debug(f"Starting processing for item_id: {item_id} ('{item_title}')")
        start_time = time.time()
        result_status = "error" # Default status
        error_message = "Processing failed" # Default error
        db_success = False
        link_suggestions = []
        analysis_output = {} # Store analysis results here
        suggestion_error_msg = None

        try:
            # Extract item data - URL needs careful handling
            content = item.get("content", "")
            title = item_title # Already fetched
            url = item.get("url") # Keep original type (e.g., HttpUrl) for potential use in analyser
            url_str = str(url) if url else "" # Ensure we have a string version for saving/reporting

            # --- Progress Reporting ---
            if self.progress_callback:
                try:
                    self.progress_callback(current_index, total_items, {
                        "status": "processing", "item_id": item_id, "title": title
                    })
                except Exception as cb_err:
                    logger.warning(f"Progress callback failed during 'processing' state for {item_id}: {cb_err}")


            # --- Input Validation ---
            if not content or not title:
                error_message = "Missing content or title"
                logger.warning(f"Skipping item {item_id}: {error_message}")
                result_status = "error" # Ensure status is error before finally
                # Use finally block to construct and return result
                # Need to jump to finally block or ensure error_message is used
                raise ValueError(error_message) # Raise exception to go to except block

            else:
                # --- Core Processing ---
                # 1. Perform basic analysis (required for KB)
                # NOTE: Analyzer instance here is self.analyzer (EnhancedContentAnalyzer)
                analysis_for_kb = self.analyzer._perform_basic_analysis(content, title)
                analysis_output = analysis_for_kb # Store this analysis

                # --- ADD ERROR CHECK for basic analysis result ---
                if isinstance(analysis_output, dict) and analysis_output.get("error"):
                    error_message = f"Basic analysis failed: {analysis_output['error']}"
                    logger.warning(f"Processing failed for item {item_id} due to basic analysis error: {error_message}")
                    result_status = "error" # Ensure status is error before finally
                    # Raise exception to jump to the main except block, ensuring correct final status/error reporting
                    raise Exception(error_message)
                # --- END ERROR CHECK ---

                # 2. Generate embedding (based on config field)
                embedding_bytes = None
                embedding_source_text = None
                # Use self.knowledge_db.config, as KB handles embedding generation logic now
                embedding_field = self.knowledge_db.config.get("embedding_text_field", "title")

                if embedding_field == "content": embedding_source_text = content
                elif embedding_field == "title": embedding_source_text = title
                else:
                    logger.warning(f"Invalid embedding_text_field '{embedding_field}' for {item_id}. Defaulting to title.")
                    embedding_source_text = title

                if embedding_source_text:
                    try:
                        # Use KB's method to generate embedding (it handles model loading internally)
                        # Ensure _generate_embedding returns numpy array
                        embedding = self.knowledge_db._generate_embedding(embedding_source_text)
                        if embedding is not None:
                           # Ensure _embedding_to_bytes exists and handles numpy array
                           embedding_bytes = self.knowledge_db._embedding_to_bytes(embedding)
                           if embedding_bytes:
                               logger.debug(f"Generated embedding ({len(embedding_bytes)} bytes) for {item_id} from '{embedding_field}'.")
                           else: logger.warning(f"Failed to convert generated embedding to bytes for {item_id}.")
                        else: logger.warning(f"Embedding generation returned None for {item_id}.")
                    except Exception as embed_err:
                        logger.error(f"Error generating embedding for {item_id}: {embed_err}", exc_info=True)
                else: logger.warning(f"Source text for embedding ('{embedding_field}') is empty for {item_id}.")


                # 3. Prepare data and add to Knowledge Base
                knowledge_data = {
                    "id": item_id,
                    "title": title,
                    "url": url, # Pass original URL object; add_content handles str conversion
                    "content": content, # Pass content for hash generation in add_content
                    "entities": analysis_for_kb.get("fashion_entities", {}), # Use analysis result
                    "topics": {
                        # Extract topics from the basic analysis result
                        "primary": [analysis_for_kb.get("primary_topic")] if analysis_for_kb.get("primary_topic") else [],
                        "sub": analysis_for_kb.get("subtopics", [])
                    }
                    # Embedding bytes passed separately to add_content
                }

                # add_content now handles internal errors and returns bool
                # Use self.knowledge_db instance
                db_success = self.knowledge_db.add_content(knowledge_data, embedding_bytes)
                if not db_success:
                    logger.warning(f"Failed to add/update item {item_id} in knowledge database.")
                else:
                    logger.debug(f"Item {item_id} successfully added/updated in knowledge database (Embedding included: {embedding_bytes is not None}).")


                # 4. Generate Link Suggestions (if not in knowledge building mode and DB is large enough)
                if not self.knowledge_building_mode:
                    # Use self.knowledge_db instance
                    db_content_count = self.knowledge_db.get_content_count()
                    min_db_size = self.config.get("initial_db_size", 100)

                    if db_content_count >= min_db_size:
                        logger.debug(f"KB size ({db_content_count}) >= min ({min_db_size}). Generating suggestions for item {item_id}.")
                        try:
                            # Call the full analyzer method which uses the KB
                            # Use self.analyzer instance
                            # analyze_content needs string URL
                            analysis_result_for_suggestions = self.analyzer.analyze_content(
                                content=content, title=title, site_id=site_id, url=url_str
                            )
                            if analysis_result_for_suggestions:
                                if analysis_result_for_suggestions.get("status") == "success":
                                    link_suggestions = analysis_result_for_suggestions.get("link_suggestions", [])
                                    # Update analysis_output with potentially richer data from full analysis?
                                    # Convert target URLs back to string if needed for result dict? Schema expects HttpUrl.
                                    # Let's assume analyze_content returns suggestions compliant with schema expectations (or handle conversion)
                                    logger.info(f"Generated {len(link_suggestions)} suggestions for item {item_id}.")
                                else:
                                    suggestion_error_msg = analysis_result_for_suggestions.get("error", "Suggestion generation failed with unknown error")
                                    logger.warning(f"Suggestion generation failed for {item_id}: {suggestion_error_msg}")
                            else:
                                suggestion_error_msg = "Suggestion generation returned None"
                                logger.warning(f"Suggestion generation returned None for {item_id}.")
                        except Exception as suggestion_error:
                            suggestion_error_msg = f"Exception during suggestion generation: {suggestion_error}"
                            logger.error(f"Error during suggestion generation call for {item_id}: {suggestion_error}", exc_info=True)
                    else:
                        logger.info(f"KB size ({db_content_count}) < min ({min_db_size}). Skipping suggestions for {item_id}.")
                else:
                    logger.info(f"Knowledge building mode ON. Skipping suggestions for {item_id}.")

                # If we reached here without exception in the main logic block
                result_status = "success"
                error_message = None # Clear default error

        except Exception as e:
            # Catch unexpected errors OR the explicitly raised Exception from basic analysis/validation failure
            log_msg = f"Error processing item {item_id} ('{title}'): {str(e)}"
            # Check if it's one of our specific raised exceptions to avoid redundant traceback logging
            if "Basic analysis failed:" not in str(e) and "Missing content or title" not in str(e):
                logger.error(log_msg, exc_info=True) # Log full traceback for unexpected errors
            else:
                 logger.error(log_msg) # Log just the message for known/handled errors

            result_status = "error"
            error_message = str(e) # Use the exception message directly
            db_success = False # Assume DB failed if exception happened

        finally:
            # --- Construct Final Result ---
            processing_time = time.time() - start_time
            url_str = str(item.get("url", "")) # Ensure final URL is string

            # Ensure analysis_output is sanitized dict, handle case where it might be error dict
            final_analysis_output = {}
            if isinstance(analysis_output, dict) and not analysis_output.get("error"):
                final_analysis_output = self._sanitize_dict_for_json(analysis_output)

            result = {
                "id": item_id,
                "title": title,
                "url": url_str,
                "status": result_status, # Use status determined in try/except blocks
                "error": error_message, # Use error message from try/except blocks
                "link_suggestions": link_suggestions,
                "analysis": final_analysis_output, # Sanitize analysis dict
                "processing_time": round(processing_time, 3),
                "in_knowledge_db": db_success,
                "suggestion_error": suggestion_error_msg # Add specific suggestion error if any
            }

            # --- Final Progress Reporting ---
            if self.progress_callback:
                try:
                     # Pass the final constructed result to the callback
                    callback_status = "completed" if result_status == "success" else "error"
                    self.progress_callback(current_index, total_items, {
                        "status": callback_status,
                        "item_id": item_id,
                        "title": title,
                        "result": result # Send the whole result dict
                    })
                except Exception as cb_err:
                    logger.warning(f"Progress callback failed during '{callback_status}' state for {item_id}: {cb_err}")

            logger.debug(f"Finished processing item {item_id}. Status: {result_status}, Time: {processing_time:.3f}s")
            return result


    def _sanitize_dict_for_json(self, data: Any) -> Any:
        """Recursively converts known non-serializable types in dict/list for JSON."""
        if isinstance(data, dict):
            return {k: self._sanitize_dict_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_dict_for_json(item) for item in data]
        elif isinstance(data, (datetime)): # Handle datetime objects
             return data.isoformat()
        # Check type name for Pydantic HttpUrl without direct import
        elif type(data).__name__ == 'HttpUrl':
             return str(data)
        elif isinstance(data, bytes): # Handle bytes (e.g., embeddings if accidentally included)
             return f"<bytes length={len(data)}>" # Represent as string placeholder
        # Add checks for numpy arrays if they might appear
        elif type(data).__module__ == 'numpy' and hasattr(data, 'tolist'):
             return data.tolist()
        # Add other types as needed
        else:
            # Check if it's a custom object that might not be serializable
            if (isinstance(data, (int, float, str, bool)) or data is None):
                 return data
            elif hasattr(data, '__dict__'): # Basic check for custom object
                 # Attempt to convert object vars to dict, sanitize recursively
                 # Be cautious with this, might expose too much or fail on complex objects
                 try:
                      return self._sanitize_dict_for_json(vars(data))
                 except TypeError: # Handle cases where vars() is not applicable or fails
                      logger.warning(f"Could not automatically sanitize object of type {type(data).__name__}, converting to string.")
                      return str(data) # Fallback to string representation
            else:
                 # If not a basic type or dict-convertible object, convert to string as last resort
                 # logger.debug(f"Data of type {type(data).__name__} not explicitly handled, returning as is or converting to string if needed by json.dump.")
                 return data # Let json.dump handle it with default=str if needed


    def _save_intermediate_results(
        self,
        results: List[Dict[str, Any]],
        stats: Dict[str, Any],
        site_id: Optional[str] = None
    ) -> None:
        """Save intermediate results to disk."""
        if not self.config.get("save_intermediate", True):
            return

        try:
            output_dir = self.config.get("output_dir", "results")
            # Ensure output_dir path is absolute or relative to project root
            project_root = os.path.join(os.path.dirname(__file__), '..', '..')
            if not os.path.isabs(output_dir):
                output_dir = os.path.join(project_root, output_dir)

            if site_id:
                output_dir = os.path.join(output_dir, site_id)
            os.makedirs(output_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"intermediate_results_{timestamp}.json"
            file_path = os.path.join(output_dir, filename)

            # Results should have string URLs; sanitize stats
            with open(file_path, 'w') as f:
                payload = {
                    "stats": self._sanitize_dict_for_json(stats),
                    "results": results # Assumes _process_single_item sanitized its output dict
                }
                json.dump(payload, f, indent=2, default=str) # Use default=str as fallback

            logger.info(f"Saved intermediate results ({len(results)} items) to {file_path}")

        except TypeError as e:
             logger.error(f"TypeError saving intermediate results to {file_path}: {e}. Data may contain non-serializable types.", exc_info=True)
        except Exception as e:
            logger.error(f"Error saving intermediate results: {str(e)}", exc_info=True)


    def _save_final_results(
        self,
        results: List[Dict[str, Any]],
        stats: Dict[str, Any],
        site_id: Optional[str] = None
    ) -> None:
        """Save final results and stats to disk."""
        try:
            output_dir = self.config.get("output_dir", "results")
             # Ensure output_dir path is absolute or relative to project root
            project_root = os.path.join(os.path.dirname(__file__), '..', '..')
            if not os.path.isabs(output_dir):
                output_dir = os.path.join(project_root, output_dir)

            if site_id:
                output_dir = os.path.join(output_dir, site_id)
            os.makedirs(output_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_filename = f"bulk_results_{timestamp}.json"
            stats_filename = f"bulk_stats_{timestamp}.json"
            results_path = os.path.join(output_dir, results_filename)
            stats_path = os.path.join(output_dir, stats_filename)

            # Save results (should be sanitized)
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)

            # Save stats (needs sanitization)
            with open(stats_path, 'w') as f:
                json.dump(self._sanitize_dict_for_json(stats), f, indent=2, default=str)

            logger.info(f"Saved final results ({len(results)} items) to {results_path}")
            logger.info(f"Saved final statistics to {stats_path}")

        except TypeError as e:
             logger.error(f"TypeError saving final results/stats: {e}. Data may contain non-serializable types.", exc_info=True)
        except Exception as e:
            logger.error(f"Error saving final results/stats: {str(e)}", exc_info=True)


    async def generate_report(
        self,
        results: List[Dict[str, Any]],
        stats: Dict[str, Any],
        report_format: str = "html",
        site_id: Optional[str] = None
    ) -> str:
        """Generate a report from processing results."""
        try:
            output_dir = self.config.get("output_dir", "results")
            # Ensure output_dir path is absolute or relative to project root
            project_root = os.path.join(os.path.dirname(__file__), '..', '..')
            if not os.path.isabs(output_dir):
                output_dir = os.path.join(project_root, output_dir)

            current_site_id = site_id if site_id else self.site_id
            if current_site_id:
                output_dir = os.path.join(output_dir, current_site_id)
            os.makedirs(output_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_base_name = f"bulk_report_{timestamp}"
            report_path = ""

            # Sanitize stats before using in report generation
            sanitized_stats = self._sanitize_dict_for_json(stats)

            if report_format.lower() == "html":
                report_path = os.path.join(output_dir, f"{report_base_name}.html")
                # Pass sanitized stats and results (assumed sanitized)
                self._generate_html_report(results, sanitized_stats, report_path)
            elif report_format.lower() == "json":
                report_path = os.path.join(output_dir, f"{report_base_name}.json")
                with open(report_path, 'w') as f:
                    json.dump({
                        "stats": sanitized_stats,
                        "results": results
                    }, f, indent=2, default=str)
            else:
                logger.error(f"Unsupported report format: {report_format}")
                return ""

            logger.info(f"Generated {report_format.upper()} report at {report_path}")
            return report_path

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}", exc_info=True)
            return ""


    def _generate_html_report(
        self,
        results: List[Dict[str, Any]],
        stats: Dict[str, Any], # Expect sanitized stats
        output_path: str
    ) -> None:
        """Generate an HTML report."""
        # Basic HTML report template (consider using a templating engine like Jinja2 for more complex reports)
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Bulk Processing Report - Site: {site_id}</title>
            <style>
                body {{ font-family: sans-serif; line-height: 1.5; margin: 20px; }}
                .container {{ max-width: 1400px; margin: auto; }}
                h1, h2 {{ color: #333; border-bottom: 1px solid #eee; padding-bottom: 5px;}}
                .stats-box {{ background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 20px; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }}
                .stat {{ background-color: #fff; border: 1px solid #e0e0e0; border-radius: 4px; padding: 10px; text-align: center; }}
                .stat-value {{ font-size: 20px; font-weight: bold; color: #007bff; }}
                .stat-label {{ font-size: 12px; color: #666; margin-top: 5px;}}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px; table-layout: fixed; }}
                th, td {{ padding: 8px 10px; border: 1px solid #ddd; text-align: left; word-wrap: break-word; }}
                th {{ background-color: #f2f2f2; font-weight: bold; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .status-success {{ color: #28a745; font-weight: bold; }}
                .status-error {{ color: #dc3545; font-weight: bold; }}
                .error-message {{ color: #dc3545; font-size: 0.9em; max-height: 100px; overflow-y: auto; display: block;}}
                .suggestions-list {{ list-style: none; padding-left: 0; margin: 0; font-size: 0.9em; max-height: 100px; overflow-y: auto; display: block;}}
                .analysis-details {{ font-size: 0.8em; color: #555; max-height: 100px; overflow-y: auto; display: block; white-space: pre-wrap;}}
                .date-info {{ margin-top: 20px; color: #777; font-size: 12px; text-align: right; }}
                td:nth-child(1) {{ width: 10%; }} /* ID */
                td:nth-child(2) {{ width: 25%; }} /* Title */
                td:nth-child(3) {{ width: 10%; }} /* Status */
                td:nth-child(4) {{ width: 30%; }} /* Suggestions/Error */
                td:nth-child(5) {{ width: 15%; }} /* Analysis */
                td:nth-child(6) {{ width: 10%; }} /* Time */

            </style>
        </head>
        <body>
            <div class="container">
                <h1>Bulk Content Analysis Report</h1>
                <h2>Site: {site_id}</h2>

                <div class="stats-box">
                    <h3>Processing Statistics</h3>
                    <div class="stats-grid">
                        <div class="stat"><div class="stat-value">{total_items}</div><div class="stat-label">Total Items</div></div>
                        <div class="stat"><div class="stat-value">{processed_items}</div><div class="stat-label">Processed Items</div></div>
                        <div class="stat"><div class="stat-value">{successful_items}</div><div class="stat-label">Successful</div></div>
                        <div class="stat"><div class="stat-value">{failed_items}</div><div class="stat-label">Failed</div></div>
                        <div class="stat"><div class="stat-value">{total_suggestions}</div><div class="stat-label">Total Suggestions</div></div>
                        <div class="stat"><div class="stat-value">{avg_suggestions:.1f}</div><div class="stat-label">Avg Suggestions</div></div>
                        <div class="stat"><div class="stat-value">{kb_initial} &rarr; {kb_final}</div><div class="stat-label">KB Items</div></div>
                        <div class="stat"><div class="stat-value">{duration_formatted}</div><div class="stat-label">Duration</div></div>
                    </div>
                    <p style="margin-top: 10px;"><strong>Overall Status:</strong> {status}</p>
                    <p><strong>Knowledge Building Mode:</strong> {kb_mode}</p>
                </div>

                <h2>Results Summary</h2>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Title / URL</th>
                            <th>Status</th>
                            <th>Suggestions / Error</th>
                            <th>Analysis Snippet</th>
                            <th>Time (s)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>

                <div class="date-info">
                    Report generated: {generation_time}<br>
                    Processing started: {start_time}<br>
                    Processing ended: {end_time}
                </div>
            </div>
        </body>
        </html>
        """

        # Format table rows
        table_rows = ""
        for result in results:
            status = result.get("status", "error")
            status_class = "status-success" if status == "success" else "status-error"
            error_msg = result.get("error") or result.get("suggestion_error") or ""
            suggestions = result.get("link_suggestions", [])
            # Ensure analysis is serializable before dumping
            analysis_safe = self._sanitize_dict_for_json(result.get("analysis", {}))
            analysis_snippet = json.dumps(analysis_safe, indent=2) # Pretty print analysis

            # Display suggestions or error message
            suggestions_or_error_html = ""
            if status == "success":
                if suggestions:
                    suggestions_html = "".join([f"<li><a href='{s.get('target_url', '#')}' target='_blank'>{s.get('anchor_text', 'N/A')}</a> (Rel: {s.get('relevance', 0):.2f})</li>" for s in suggestions])
                    suggestions_or_error_html = f"<span class='suggestions-count'>({len(suggestions)})</span><ul class='suggestions-list'>{suggestions_html}</ul>"
                else:
                     suggestions_or_error_html = "<span>(0 suggestions)</span>"
                     if result.get("suggestion_error"): # Show suggestion error even if main status is success
                         suggestions_or_error_html += f"<br><span class='error-message'>Suggestion Error: {error_msg}</span>"
            else:
                suggestions_or_error_html = f"<span class='error-message'>{error_msg}</span>"

            table_rows += f"""
            <tr>
                <td>{result.get('id', '')}</td>
                <td>
                    <strong>{result.get('title', '')}</strong><br>
                    <small><a href='{result.get('url', '#')}' target='_blank'>{result.get('url', '')}</a></small>
                 </td>
                <td class="{status_class}">{status.upper()}</td>
                <td>{suggestions_or_error_html}</td>
                <td><pre class='analysis-details'>{analysis_snippet[:300]}{'...' if len(analysis_snippet) > 300 else ''}</pre></td>
                <td>{result.get('processing_time', 0):.3f}</td>
            </tr>
            """

        # Format duration
        duration = stats.get("duration_seconds", 0)
        hours, rem = divmod(duration, 3600)
        mins, secs = divmod(rem, 60)
        duration_formatted = f"{int(hours):02d}:{int(mins):02d}:{secs:05.2f}"

        # Calculate average suggestions per successful item
        successful_items = stats.get("successful_items", 0)
        total_suggestions = stats.get("total_suggestions", 0)
        avg_suggestions = total_suggestions / successful_items if successful_items > 0 else 0

        # Fill template
        html_content = html_template.format(
            site_id=stats.get("site_id", "N/A"),
            total_items=stats.get("total_items", 0),
            processed_items=stats.get("processed_items", 0),
            successful_items=successful_items,
            failed_items=stats.get("failed_items", 0),
            total_suggestions=total_suggestions,
            avg_suggestions=avg_suggestions,
            kb_initial=stats.get("knowledge_db_initial_items", "N/A"),
            kb_final=stats.get("knowledge_db_final_items", "N/A"),
            duration_formatted=duration_formatted,
            status=stats.get("status", "").upper(),
            kb_mode=stats.get("knowledge_building_mode", False),
            table_rows=table_rows,
            generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            start_time=stats.get("start_time", "N/A"),
            end_time=stats.get("end_time", "N/A")
        )

        # Write to file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Successfully generated HTML report at {output_path}")
        except Exception as write_err:
             logger.error(f"Error writing HTML report to {output_path}: {write_err}", exc_info=True)