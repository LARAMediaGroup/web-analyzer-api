"""
Enhanced Analyzer Integration Module

This module integrates the enhanced content analyzer with the API.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from pydantic import HttpUrl # Added for type hints

from src.core.enhanced_analyzer import EnhancedContentAnalyzer

# Configure logging
logger = logging.getLogger("web_analyzer_api.enhanced_integration")

# Initialize analyzer
try:
    # Config path relative to project root expected by analyzer's constructor logic now
    analyzer = EnhancedContentAnalyzer(config_path="config.json")
    logger.info("EnhancedContentAnalyzer instance created for integration.")
except Exception as e:
    logger.error(f"Failed to initialize EnhancedContentAnalyzer in integration module: {e}", exc_info=True)
    analyzer = None # Set to None to indicate failure

async def analyze_content_enhanced(
    content: str,
    title: str,
    site_id: str,
    url: Optional[HttpUrl] = None # Use HttpUrl type hint
) -> Dict[str, Any]:
    """
    Analyzes content using the EnhancedContentAnalyzer.

    Args:
        content: The content text.
        title: The content title.
        site_id: The identifier for the site.
        url: The URL of the content being analyzed (as HttpUrl).

    Returns:
        A dictionary containing the analysis results or an error.
    """
    url_str = str(url) if url else None # Analyzer expects string URL
    logger.info(f"Enhanced Integration: Received analysis request for site '{site_id}', title '{title}', url '{url_str}'")

    if analyzer is None:
        logger.error("EnhancedContentAnalyzer failed to initialize. Cannot process request.")
        # Return error structure consistent with analyzer's error response
        return {
                "analysis": {}, "link_suggestions": [], "processing_time": 0,
                "status": "error", "error": "Analyzer initialization failed"
            }

    try:
        # Call the analyzer's main method, passing all required parameters
        # Analyzer expects string URL
        analysis_result = await analyzer.analyze_content(
            content=content,
            title=title,
            site_id=site_id,
            url=url_str
        )
        logger.info(f"Enhanced Integration: Analysis complete for site '{site_id}', title '{title}'. Status: {analysis_result.get('status')}")

        # Convert target_url strings in suggestions back to HttpUrl for schema validation
        if "link_suggestions" in analysis_result:
            valid_suggestions = []
            for sugg in analysis_result["link_suggestions"]:
                try:
                    sugg["target_url"] = HttpUrl(sugg["target_url"])
                    valid_suggestions.append(sugg)
                except Exception as url_val_err:
                    logger.warning(f"Invalid target URL '{sugg.get('target_url')}' in suggestion. Skipping. Error: {url_val_err}")
            analysis_result["link_suggestions"] = valid_suggestions

        return analysis_result

    except Exception as e:
        logger.error(f"Exception during enhanced analysis integration for site '{site_id}', title '{title}': {e}", exc_info=True)
        # Return error structure consistent with analyzer's error response
        return {
                "analysis": {}, "link_suggestions": [], "processing_time": 0,
                "status": "error", "error": f"Internal error during enhanced analysis integration: {str(e)}"
            }
