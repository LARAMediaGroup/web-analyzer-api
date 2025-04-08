"""
Enhanced Analyzer Integration Module

This module integrates the enhanced content analyzer with the API.
"""

import logging
import time
from typing import List, Dict, Any, Optional

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
    url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes content using the EnhancedContentAnalyzer.

    Args:
        content: The content text.
        title: The content title.
        site_id: The identifier for the site.
        url: The URL of the content being analyzed.

    Returns:
        A dictionary containing the analysis results or an error.
    """
    logger.info(f"Enhanced Integration: Received analysis request for site '{site_id}', title '{title}', url '{url}'")

    if analyzer is None:
        logger.error("EnhancedContentAnalyzer failed to initialize. Cannot process request.")
        # Return error structure consistent with analyzer's error response
        return {
                "analysis": {}, "link_suggestions": [], "processing_time": 0,
                "status": "error", "error": "Analyzer initialization failed"
            }

    try:
        # Call the analyzer's main method, passing all required parameters
        analysis_result = await analyzer.analyze_content(
            content=content,
            title=title,
            site_id=site_id,
            url=url
        )
        logger.info(f"Enhanced Integration: Analysis complete for site '{site_id}', title '{title}'. Status: {analysis_result.get('status')}")
        return analysis_result

    except Exception as e:
        logger.error(f"Exception during enhanced analysis integration for site '{site_id}', title '{title}': {e}", exc_info=True)
        # Return error structure consistent with analyzer's error response
        return {
                "analysis": {}, "link_suggestions": [], "processing_time": 0,
                "status": "error", "error": f"Internal error during enhanced analysis integration: {str(e)}"
            }

def get_target_urls_for_site(site_id: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Get target URLs for a specific site.
    
    Args:
        site_id (str, optional): The site identifier
    
    Returns:
        List[Dict[str, str]]: List of target URLs with title
    """
    # Default target URLs (same as before)
    default_urls = [
        {
            "url": "https://thevou.com/blog/complete-old-money-fashion-guide-for-young-men/",
            "title": "Complete Old Money Fashion Guide for Young Men"
        },
        {
            "url": "https://thevou.com/blog/old-money-hairstyle-guide/",
            "title": "Old Money Hairstyle Guide for Gentlemen"
        },
        {
            "url": "https://thevou.com/blog/preppy-ivy-league-style-guide/",
            "title": "Preppy Ivy League Style Guide for Modern Men"
        },
        {
            "url": "https://thevou.com/blog/colour-analysis-for-men/",
            "title": "Complete Colour Analysis Guide for Men's Wardrobe"
        },
        {
            "url": "https://thevou.com/blog/true-spring-colour-palette-men/",
            "title": "True Spring Colour Palette Guide for Men's Fashion"
        },
        {
            "url": "https://thevou.com/blog/inverted-triangle-body-shape-styling/",
            "title": "How to Dress for Inverted Triangle Body Shape - Men's Guide"
        },
        {
            "url": "https://thevou.com/blog/oxford-shirts-style-guide/",
            "title": "How to Style Oxford Shirts for Every Occasion - Men's Styling Guide"
        },
        {
            "url": "https://thevou.com/blog/mens-fashion-style-tips/",
            "title": "Essential Fashion Style Tips for Men in 2025"
        },
        {
            "url": "https://thevou.com/blog/capsule-wardrobe-guide-men/",
            "title": "How to Create a Versatile Capsule Wardrobe for Men"
        },
        {
            "url": "https://thevou.com/blog/tailored-suit-guide-men/",
            "title": "Complete Guide to Tailored Suits for Gentlemen"
        }
    ]
    
    # If site_id is "thevou" or None, use default URLs
    if not site_id or site_id == "thevou":
        return default_urls
    
    # For other sites, we could implement site-specific logic
    # For now, return a subset of the default URLs as an example
    return default_urls[:5]