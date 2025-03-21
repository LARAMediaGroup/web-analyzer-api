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
enhanced_analyzer = EnhancedContentAnalyzer()

async def analyze_content_enhanced(
    content: str, 
    title: str, 
    url: Optional[str] = None,
    site_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process enhanced content analysis as an async task.
    
    Args:
        content (str): The content to analyze
        title (str): The title of the content
        url (str, optional): The URL of the content
        site_id (str, optional): The site identifier
        
    Returns:
        Dict[str, Any]: Analysis results
    """
    start_time = time.time()
    logger.info(f"Starting enhanced content analysis for: {title}")

    try:
        # We'll use the target URLs from the previous version for now
        # In production, these would come from a database or the WordPress site
        # Ideally, this would be dynamically loaded based on site_id
        
        # Site-specific configuration
        target_urls = get_target_urls_for_site(site_id)
        
        # Run the enhanced analysis
        result = enhanced_analyzer.analyze_content(
            content=content,
            title=title,
            target_pages=target_urls,
            url=url
        )
        
        # Format the response
        processing_time = time.time() - start_time
        
        response = {
            "link_suggestions": result.get("link_suggestions", []),
            "analysis": result.get("analysis", {}),
            "processing_time": processing_time,
            "status": result.get("status", "success")
        }
        
        if "error" in result:
            response["error"] = result["error"]
        
        logger.info(f"Analysis completed in {processing_time:.2f} seconds. Found {len(response['link_suggestions'])} suggestions.")
        
        return response

    except Exception as e:
        logger.error(f"Error in enhanced analysis task: {str(e)}")
        return {
            "link_suggestions": [],
            "analysis": {},
            "processing_time": time.time() - start_time,
            "status": "error",
            "error": str(e)
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