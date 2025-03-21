from src.core.analyzer import ContentAnalyzer
from typing import List, Dict, Any, Optional
import logging
import time

logger = logging.getLogger("web_analyzer_api.integration")

# Initialize analyzer
analyzer = ContentAnalyzer()

async def analyze_content_task(content: str, title: str, site_id: str = None, url: Optional[str] = None) -> Dict[str, Any]:
    """
    Process content analysis as an async task.
    
    This is where we integrate our existing analyzer logic.
    """
    start_time = time.time()
    logger.info(f"Starting content analysis for: {title} (site: {site_id})")

    try:
        # In production, we would load target URLs from the site's WordPress instance
        # For now, we'll use target URLs that vary slightly based on site ID
        
        # If site_id is 'default' or None, use default target URLs
        # Otherwise, we could customize this based on the site_id
        # In a real implementation, we'd query each site's content from their WordPress database
        
        # Common target URLs for all sites
        target_urls = [
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

        # Run the analysis
        opportunities = analyzer.analyze_content(content, title, target_urls)

        # Convert to API response format
        link_suggestions = []

        for opp in opportunities:
            # Get best anchor option
            if opp["anchor_options"]:
                best_anchor = opp["anchor_options"][0]

                link_suggestions.append({
                    "anchor_text": best_anchor["text"],
                    "target_url": opp["target_url"],
                    "context": best_anchor["context"],
                    "confidence": best_anchor["confidence"],
                    "paragraph_index": opp["paragraph_index"]
                })

        processing_time = time.time() - start_time
        logger.info(f"Analysis completed in {processing_time:.2f} seconds. Found {len(link_suggestions)} suggestions.")

        return {
            "link_suggestions": link_suggestions,
            "processing_time": processing_time,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error in analysis task: {str(e)}")
        return {
            "link_suggestions": [],
            "processing_time": time.time() - start_time,
            "status": "error",
            "error": str(e)
        }