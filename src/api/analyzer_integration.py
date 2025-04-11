from src.core.analyzer import ContentAnalyzer
from typing import List, Dict, Any, Optional
import logging
import time
from pydantic import HttpUrl # Added for type hint consistency

logger = logging.getLogger("web_analyzer_api.integration")

# Initialize analyzer
# Assuming ContentAnalyzer uses default config path relative to project root
# Or adjust if it needs specific path relative to this file
try:
    # Assuming config.json is at project root
    analyzer = ContentAnalyzer(config_path="config.json")
    logger.info("ContentAnalyzer instance created for integration.")
except Exception as e:
    logger.error(f"Failed to initialize ContentAnalyzer in integration module: {e}", exc_info=True)
    analyzer = None # Set to None to indicate failure

async def analyze_content_task(content: str, title: str, site_id: str = None, url: Optional[HttpUrl] = None) -> Dict[str, Any]:
    """
    Process content analysis using the simple ContentAnalyzer.

    Args:
        content: The content text.
        title: The content title.
        site_id: Identifier for the site (currently unused by simple analyzer).
        url: URL of the content being analyzed (currently unused by simple analyzer).

    Returns:
        A dictionary containing the analysis results or an error.
    """
    start_time = time.time()
    logger.info(f"Starting SIMPLE content analysis for: {title} (site: {site_id})")

    if analyzer is None:
        logger.error("ContentAnalyzer failed to initialize. Cannot process request.")
        return {
                "analysis": {}, "link_suggestions": [], "processing_time": 0,
                "status": "error", "error": "Simple Analyzer initialization failed"
            }

    try:
        # Run the analysis - Simple analyzer doesn't technically need target URLs for its logic,
        # but the current method signature requires it. Pass an empty list.
        opportunities = analyzer.analyze_content(content, title, [])

        # Convert to API response format
        link_suggestions = []

        # The simple analyzer's output format for `opportunities` needs confirmation.
        # Based on ContentAnalyzer code, it returns a list of dicts like:
        # { 'paragraph_index': int, 'target_url': str, 'target_title': str, 'relevance': float,
        #   'anchor_text': str, 'anchor_context': str, 'anchor_confidence': float }
        for opp in opportunities:
            # Validate required fields exist before appending
            if all(k in opp for k in ["anchor_text", "target_url", "anchor_confidence", "paragraph_index"]):
                 # Convert target_url back to HttpUrl for schema consistency if needed,
                 # but schema expects str? Let's check schema.
                 # LinkSuggestion expects HttpUrl. Need conversion.
                 target_url_obj = None
                 try:
                      target_url_obj = HttpUrl(opp["target_url"])
                 except Exception:
                      logger.warning(f"Could not validate target URL: {opp['target_url']}. Skipping suggestion.")
                      continue

                 link_suggestions.append({
                    "anchor_text": opp["anchor_text"],
                    "target_url": target_url_obj,
                    "context": opp.get("anchor_context", ""), # Use .get() for optional field
                    "confidence": opp["anchor_confidence"],
                    "paragraph_index": opp["paragraph_index"],
                    "relevance": opp.get("relevance") # Include relevance if available
                 })
            else:
                logger.warning(f"Opportunity found with missing required fields: {opp}")


        processing_time = time.time() - start_time
        logger.info(f"Simple Analysis completed in {processing_time:.2f} seconds. Found {len(link_suggestions)} suggestions.")

        # Construct response matching AnalysisResponse schema
        # Simple analyzer doesn't produce the detailed 'analysis' dict like Enhanced one.
        return {
            "analysis": {}, # Return empty analysis dict
            "link_suggestions": link_suggestions,
            "processing_time": round(processing_time, 3),
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error in simple analysis task: {str(e)}", exc_info=True)
        # Return error structure consistent with AnalysisResponse schema
        return {
            "analysis": {},
            "link_suggestions": [],
            "processing_time": round(time.time() - start_time, 3),
            "status": "error",
            "error": str(e)
        }