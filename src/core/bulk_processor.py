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
        self.analyzer = EnhancedContentAnalyzer(config_path)
        
        # Initialize knowledge database
        self.site_id = site_id or "default"
        self.knowledge_db = KnowledgeDatabase(config_path, self.site_id)
        
        # Processing parameters
        self.max_workers = self.config.get("max_workers", 4)
        self.progress_callback = None
        self.stop_signal = False
        self.knowledge_building_mode = False
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Config file {config_path} not found, using defaults")
                return {
                    "max_workers": 4,
                    "batch_size": 10,
                    "output_dir": "results",
                    "save_intermediate": True
                }
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return {}
    
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
        
        # Set knowledge building mode
        self.knowledge_building_mode = knowledge_building_mode
        
        # Check knowledge database status
        db_stats = self.knowledge_db.get_database_stats()
        db_content_count = db_stats.get("content_count", 0)
        logger.info(f"Knowledge database has {db_content_count} entries")
        
        # Use configured batch size if not specified
        if batch_size is None:
            batch_size = self.config.get("batch_size", 10)
        
        # Prepare for processing
        total_items = len(content_items)
        results = []
        stats = {
            "total_items": total_items,
            "processed_items": 0,
            "successful_items": 0,
            "failed_items": 0,
            "total_suggestions": 0,
            "knowledge_db_items": db_content_count,
            "knowledge_building_mode": knowledge_building_mode,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration_seconds": 0,
            "status": "in_progress"
        }
        
        logger.info(f"Starting bulk processing of {total_items} items (knowledge building: {knowledge_building_mode})")
        
        # Process in batches
        for batch_start in range(0, total_items, batch_size):
            # Check for stop signal
            if self.stop_signal:
                logger.info("Processing stopped by user")
                stats["status"] = "stopped"
                break
            
            batch_end = min(batch_start + batch_size, total_items)
            current_batch = content_items[batch_start:batch_end]
            logger.info(f"Processing batch {batch_start // batch_size + 1}, items {batch_start+1}-{batch_end}")
            
            # Process batch with thread pool
            try:
                batch_results = await self._process_batch(
                    current_batch,
                    site_id,
                    batch_start,
                    total_items
                )
                results.extend(batch_results)
                
                # Update stats
                stats["processed_items"] += len(batch_results)
                stats["successful_items"] += sum(1 for r in batch_results if r.get("status") == "success")
                stats["failed_items"] += sum(1 for r in batch_results if r.get("status") != "success")
                stats["total_suggestions"] += sum(len(r.get("link_suggestions", [])) for r in batch_results)
                
                # Save intermediate results if configured
                if self.config.get("save_intermediate", True):
                    self._save_intermediate_results(results, stats, site_id)
                
            except Exception as e:
                logger.error(f"Error processing batch: {str(e)}")
                traceback.print_exc()
        
        # Final stats
        end_time = time.time()
        duration = end_time - start_time
        
        stats["end_time"] = datetime.now().isoformat()
        stats["duration_seconds"] = duration
        stats["status"] = "completed" if not self.stop_signal else "stopped"
        
        logger.info(f"Bulk processing completed in {duration:.2f} seconds")
        logger.info(f"Processed {stats['processed_items']} items, {stats['successful_items']} successful, {stats['failed_items']} failed")
        logger.info(f"Generated {stats['total_suggestions']} link suggestions")
        
        # Save final results
        self._save_final_results(results, stats, site_id)
        
        return results, stats
    
    async def _process_batch(
        self,
        batch_items: List[Dict[str, Any]],
        site_id: Optional[str] = None,
        batch_start: int = 0,
        total_items: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of content items using a thread pool.
        
        Args:
            batch_items: List of items in the current batch
            site_id: Optional site identifier
            batch_start: Starting index of the batch in the overall list
            total_items: Total number of items
            
        Returns:
            List of processing results
        """
        # Create tasks for thread pool
        loop = asyncio.get_event_loop()
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for i, item in enumerate(batch_items):
                if self.stop_signal:
                    break
                
                overall_index = batch_start + i
                future = loop.run_in_executor(
                    executor, 
                    self._process_single_item,
                    item,
                    site_id,
                    overall_index,
                    total_items
                )
                futures.append(future)
            
            # Wait for all futures to complete
            for future in asyncio.as_completed(futures):
                if self.stop_signal:
                    # Cancel any remaining futures
                    for f in futures:
                        if not f.done():
                            f.cancel()
                    break
                
                result = await future
                results.append(result)
        
        return results
    
    def _process_single_item(
        self,
        item: Dict[str, Any],
        site_id: Optional[str] = None,
        current_index: int = 0,
        total_items: int = 0
    ) -> Dict[str, Any]:
        """
        Process a single content item and report progress.
        
        Args:
            item: Content item to process
            site_id: Optional site identifier
            current_index: Index of this item in the overall list
            total_items: Total number of items
            
        Returns:
            Dictionary with processing results
        """
        item_id = item.get("id", str(current_index))
        logger.debug(f"Starting processing for item_id: {item_id}")
        try:
            # Extract item data
            content = item.get("content", "")
            title = item.get("title", "")
            url = item.get("url", "")
            
            # Report progress at start
            if self.progress_callback:
                self.progress_callback(current_index, total_items, {
                    "status": "processing",
                    "item_id": item_id,
                    "title": title
                })
            
            # Skip empty content
            if not content or not title:
                result = {
                    "id": item_id,
                    "title": title,
                    "url": url,
                    "status": "error",
                    "error": "Missing content or title",
                    "link_suggestions": [],
                    "processing_time": 0
                }
                
                # Report progress at end
                if self.progress_callback:
                    self.progress_callback(current_index, total_items, {
                        "status": "completed",
                        "item_id": item_id,
                        "title": title,
                        "result": result
                    })
                
                return result
            
            # Process with analyzer
            start_time = time.time()
            
            # Perform basic analysis using EnhancedAnalyzer's components
            analysis_for_kb = self.analyzer._perform_basic_analysis(content, title)

            # Generate embedding
            embedding_bytes = None
            embedding_source_text = None
            embedding_field = self.knowledge_db.config.get("embedding_text_field", "title")
            
            if embedding_field == "content":
                embedding_source_text = content
            elif embedding_field == "title":
                embedding_source_text = title
            else:
                logger.warning(f"Invalid embedding_text_field configured: '{embedding_field}'. Defaulting to title.")
                embedding_source_text = title

            if embedding_source_text:
                embedding_bytes = self.knowledge_db._generate_embedding(embedding_source_text)
                if embedding_bytes:
                    logger.debug(f"Successfully generated embedding for item {item_id} from field '{embedding_field}'.")
                else:
                    logger.warning(f"Failed to generate embedding for item {item_id} from field '{embedding_field}'.")
            else:
                logger.warning(f"Source text for embedding ('{embedding_field}') is empty for item {item_id}. Cannot generate embedding.")

            # Prepare data for knowledge database using the basic analysis results
            knowledge_data = {
                "id": item_id,
                "title": title,
                "url": url,
                "entities": analysis_for_kb.get("fashion_entities", {}),
                "topics": {
                    "primary": [analysis_for_kb.get("primary_topic")] if analysis_for_kb.get("primary_topic") else [],
                    "sub": analysis_for_kb.get("subtopics", [])
                }
            }
            
            # Store in knowledge database, passing the generated embedding
            db_success = self.knowledge_db.add_content(knowledge_data, embedding_bytes)
            
            if db_success:
                logger.debug(f"Content/Embedding processed for item {item_id} in knowledge database.")
            else:
                logger.warning(f"KB add_content returned False for item {item_id}.")

            # Link suggestion logic
            link_suggestions = []
            analysis_result_for_suggestions = None

            if not self.knowledge_building_mode:
                # Check KB size
                db_content_count = self.knowledge_db.get_content_count()
                min_db_size = self.config.get("initial_db_size", 100)

                if db_content_count >= min_db_size:
                    logger.debug(f"KB size ({db_content_count}) >= min ({min_db_size}). Generating suggestions for item {item_id}.")
                    # Now call the full enhanced analyzer to get suggestions,
                    # using the now potentially populated KB with embeddings
                    try:
                        # This is the call that actually uses the KB and embeddings for suggestions
                        analysis_result_for_suggestions = self.analyzer.analyze_content(
                            content=content,
                            title=title,
                            site_id=self.site_id,
                            url=url
                        )
                        if analysis_result_for_suggestions and analysis_result_for_suggestions.get("status") == "success":
                            link_suggestions = analysis_result_for_suggestions.get("link_suggestions", [])
                            logger.info(f"Generated {len(link_suggestions)} suggestions for item {item_id}.")
                        elif analysis_result_for_suggestions:
                            logger.warning(f"Suggestion generation failed for item {item_id}. Analyzer status: {analysis_result_for_suggestions.get('status')}, Error: {analysis_result_for_suggestions.get('error')}")
                        else:
                            logger.warning(f"Suggestion generation returned None for item {item_id}.")

                    except Exception as suggestion_error:
                        logger.error(f"Error during suggestion generation call for item {item_id}: {suggestion_error}", exc_info=True)
                else:
                    logger.info(f"Knowledge database has only {db_content_count} items, need {min_db_size} for suggestions. Skipping suggestion generation for item {item_id}.")
            else:
                logger.info(f"Knowledge building mode is ON. Skipping suggestion generation for item {item_id}.")

            # Prepare final result
            processing_time = time.time() - start_time
            final_analysis_output = analysis_for_kb

            result = {
                "id": item_id,
                "title": title,
                "url": url,
                "status": "success",
                "link_suggestions": link_suggestions,
                "analysis": final_analysis_output,
                "processing_time": round(processing_time, 3),
                "in_knowledge_db": db_success
            }

            if analysis_result_for_suggestions and analysis_result_for_suggestions.get("status") == "error":
                result["suggestion_error"] = analysis_result_for_suggestions.get("error", "Unknown suggestion error")

            # Report progress at end
            if self.progress_callback:
                self.progress_callback(current_index, total_items, {
                    "status": "completed",
                    "item_id": item_id,
                    "title": title,
                    "result": result
                })
            
            return result
        
        except Exception as e:
            logger.error(f"Unhandled error processing item {item_id}: {str(e)}", exc_info=True)
            traceback.print_exc()
            
            # Prepare error result
            result = {
                "id": item_id,
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "status": "error",
                "error": f"Unhandled exception: {str(e)}",
                "link_suggestions": [],
                "processing_time": 0
            }
            
            # Report progress at end
            if self.progress_callback:
                self.progress_callback(current_index, total_items, {
                    "status": "error",
                    "item_id": item_id,
                    "title": item.get("title", ""),
                    "error": str(e)
                })
            
            return result
    
    def _save_intermediate_results(
        self,
        results: List[Dict[str, Any]],
        stats: Dict[str, Any],
        site_id: Optional[str] = None
    ) -> None:
        """
        Save intermediate results to disk.
        
        Args:
            results: List of processing results
            stats: Processing statistics
            site_id: Optional site identifier
        """
        try:
            # Create output directory if it doesn't exist
            output_dir = self.config.get("output_dir", "results")
            os.makedirs(output_dir, exist_ok=True)
            
            # Create site-specific subdirectory if site_id is provided
            if site_id:
                site_dir = os.path.join(output_dir, site_id)
                os.makedirs(site_dir, exist_ok=True)
                output_dir = site_dir
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"intermediate_results_{timestamp}.json"
            file_path = os.path.join(output_dir, filename)
            
            # Save data
            with open(file_path, 'w') as f:
                json.dump({
                    "results": results,
                    "stats": stats
                }, f, indent=2)
            
            logger.info(f"Saved intermediate results to {file_path}")
        
        except Exception as e:
            logger.error(f"Error saving intermediate results: {str(e)}")
    
    def _save_final_results(
        self,
        results: List[Dict[str, Any]],
        stats: Dict[str, Any],
        site_id: Optional[str] = None
    ) -> None:
        """
        Save final results to disk.
        
        Args:
            results: List of processing results
            stats: Processing statistics
            site_id: Optional site identifier
        """
        try:
            # Create output directory if it doesn't exist
            output_dir = self.config.get("output_dir", "results")
            os.makedirs(output_dir, exist_ok=True)
            
            # Create site-specific subdirectory if site_id is provided
            if site_id:
                site_dir = os.path.join(output_dir, site_id)
                os.makedirs(site_dir, exist_ok=True)
                output_dir = site_dir
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_filename = f"bulk_results_{timestamp}.json"
            stats_filename = f"bulk_stats_{timestamp}.json"
            
            results_path = os.path.join(output_dir, results_filename)
            stats_path = os.path.join(output_dir, stats_filename)
            
            # Save results
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Save stats
            with open(stats_path, 'w') as f:
                json.dump(stats, f, indent=2)
            
            logger.info(f"Saved final results to {results_path}")
            logger.info(f"Saved statistics to {stats_path}")
        
        except Exception as e:
            logger.error(f"Error saving final results: {str(e)}")
    
    async def generate_report(
        self,
        results: List[Dict[str, Any]],
        stats: Dict[str, Any],
        report_format: str = "html",
        site_id: Optional[str] = None
    ) -> str:
        """
        Generate a report from processing results.
        
        Args:
            results: List of processing results
            stats: Processing statistics
            report_format: Format of the report ("html" or "json")
            site_id: Optional site identifier
            
        Returns:
            Path to the generated report file
        """
        try:
            # Create output directory if it doesn't exist
            output_dir = self.config.get("output_dir", "results")
            os.makedirs(output_dir, exist_ok=True)
            
            # Create site-specific subdirectory if site_id is provided
            if site_id:
                site_dir = os.path.join(output_dir, site_id)
                os.makedirs(site_dir, exist_ok=True)
                output_dir = site_dir
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if report_format.lower() == "html":
                report_path = os.path.join(output_dir, f"bulk_report_{timestamp}.html")
                self._generate_html_report(results, stats, report_path)
            else:
                report_path = os.path.join(output_dir, f"bulk_report_{timestamp}.json")
                with open(report_path, 'w') as f:
                    json.dump({
                        "results": results,
                        "stats": stats
                    }, f, indent=2)
            
            logger.info(f"Generated report at {report_path}")
            return report_path
        
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return ""
    
    def _generate_html_report(
        self,
        results: List[Dict[str, Any]],
        stats: Dict[str, Any],
        output_path: str
    ) -> None:
        """
        Generate an HTML report from processing results.
        
        Args:
            results: List of processing results
            stats: Processing statistics
            output_path: Path to save the HTML report
        """
        # Basic HTML report template
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Bulk Processing Report</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    color: #333;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                }
                h1, h2, h3 {
                    color: #2c3e50;
                }
                .stats-box {
                    background-color: #f8f9fa;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 20px;
                }
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 10px;
                }
                .stat {
                    background-color: #fff;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 10px;
                    text-align: center;
                }
                .stat-value {
                    font-size: 24px;
                    font-weight: bold;
                    color: #3498db;
                }
                .stat-label {
                    font-size: 14px;
                    color: #7f8c8d;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }
                th, td {
                    padding: 10px;
                    border: 1px solid #ddd;
                    text-align: left;
                }
                th {
                    background-color: #f2f2f2;
                }
                tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
                .success {
                    color: #27ae60;
                }
                .error {
                    color: #e74c3c;
                }
                .suggestions-count {
                    font-weight: bold;
                    color: #3498db;
                }
                .date-info {
                    margin-top: 30px;
                    color: #7f8c8d;
                    font-size: 14px;
                    text-align: right;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Bulk Content Analysis Report</h1>
                
                <div class="stats-box">
                    <h2>Processing Statistics</h2>
                    <div class="stats-grid">
                        <div class="stat">
                            <div class="stat-value">{total_items}</div>
                            <div class="stat-label">Total Items</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{processed_items}</div>
                            <div class="stat-label">Processed Items</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{successful_items}</div>
                            <div class="stat-label">Successful Items</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{failed_items}</div>
                            <div class="stat-label">Failed Items</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{total_suggestions}</div>
                            <div class="stat-label">Total Suggestions</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{avg_suggestions}</div>
                            <div class="stat-label">Avg Suggestions Per Item</div>
                        </div>
                    </div>
                    <p><strong>Processing Time:</strong> {duration_formatted}</p>
                    <p><strong>Status:</strong> {status}</p>
                </div>
                
                <h2>Results Summary</h2>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Title</th>
                            <th>Status</th>
                            <th>Suggestions</th>
                            <th>Processing Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
                
                <div class="date-info">
                    <p>Report generated: {generation_time}</p>
                    <p>Processing start: {start_time}</p>
                    <p>Processing end: {end_time}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Format table rows
        table_rows = ""
        for result in results:
            status_class = "success" if result.get("status") == "success" else "error"
            table_rows += f"""
            <tr>
                <td>{result.get('id', '')}</td>
                <td>{result.get('title', '')}</td>
                <td class="{status_class}">{result.get('status', '')}</td>
                <td class="suggestions-count">{len(result.get('link_suggestions', []))}</td>
                <td>{result.get('processing_time', 0):.2f}s</td>
            </tr>
            """
        
        # Format duration
        duration = stats.get("duration_seconds", 0)
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_formatted = f"{int(hours)}h {int(minutes)}m {seconds:.2f}s"
        
        # Calculate average suggestions
        successful_items = stats.get("successful_items", 0)
        total_suggestions = stats.get("total_suggestions", 0)
        avg_suggestions = round(total_suggestions / successful_items, 1) if successful_items > 0 else 0
        
        # Fill in template
        html_content = html_template.format(
            total_items=stats.get("total_items", 0),
            processed_items=stats.get("processed_items", 0),
            successful_items=stats.get("successful_items", 0),
            failed_items=stats.get("failed_items", 0),
            total_suggestions=total_suggestions,
            avg_suggestions=avg_suggestions,
            duration_formatted=duration_formatted,
            status=stats.get("status", ""),
            table_rows=table_rows,
            generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            start_time=stats.get("start_time", ""),
            end_time=stats.get("end_time", "")
        )
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write(html_content)