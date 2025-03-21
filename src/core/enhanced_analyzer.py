"""
Enhanced Content Analyzer Module

This module combines multiple specialized analyzers to:
1. Extract fashion entities and topics
2. Understand the semantic structure of content
3. Generate high-quality anchor text
4. Find link opportunities based on relevance
"""

import os
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
import re
from datetime import datetime

# Import specialized analyzers
from src.core.analyzers.fashion_entity_analyzer import FashionEntityAnalyzer
from src.core.analyzers.semantic_context_analyzer import SemanticContextAnalyzer
from src.core.analyzers.anchor_text_generator import AnchorTextGenerator

# Configure logging
logger = logging.getLogger("web_analyzer.enhanced_analyzer")

class EnhancedContentAnalyzer:
    """
    Enhanced content analyzer that combines multiple specialized analyzers
    for comprehensive content analysis and high-quality link suggestions.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the enhanced content analyzer.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        
        # Initialize specialized analyzers
        self.fashion_analyzer = FashionEntityAnalyzer()
        self.semantic_analyzer = SemanticContextAnalyzer()
        self.anchor_generator = AnchorTextGenerator()
        
        # Relevance threshold for link suggestions
        self.min_relevance = self.config.get("min_relevance", 0.4)
        self.min_confidence = self.config.get("min_confidence", 0.6)
        self.max_links_per_paragraph = self.config.get("max_links_per_paragraph", 2)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Config file {config_path} not found, using defaults")
                return {
                    "min_relevance": 0.4,
                    "min_confidence": 0.6,
                    "max_links_per_paragraph": 2,
                    "min_paragraph_length": 50,
                    "max_suggestions": 15
                }
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return {}
    
    def _split_into_paragraphs(self, content: str) -> List[str]:
        """Split content into paragraphs."""
        paragraphs = re.split(r'\n\n|\n', content)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def analyze_content(
        self, 
        content: str, 
        title: str, 
        target_pages: List[Dict[str, str]],
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive content analysis and find link opportunities.
        
        Args:
            content: The content to analyze
            title: The title of the content
            target_pages: List of potential target pages with URL and title
            url: URL of the current content (optional)
            
        Returns:
            Dictionary with analysis results and link suggestions
        """
        start_time = datetime.now()
        logger.info(f"Starting enhanced analysis for: {title}")
        
        # Basic validation
        if not content or not title or not target_pages:
            return {
                "analysis": {},
                "link_suggestions": [],
                "processing_time": 0,
                "status": "error",
                "error": "Missing required parameters"
            }
        
        try:
            # Split content into paragraphs
            paragraphs = self._split_into_paragraphs(content)
            
            # Skip analysis if content is too short
            min_length = self.config.get("min_content_length", 100)
            if len(content) < min_length:
                return {
                    "analysis": {},
                    "link_suggestions": [],
                    "processing_time": 0,
                    "status": "error",
                    "error": f"Content too short (minimum {min_length} characters)"
                }
            
            # 1. Fashion entity analysis
            fashion_analysis = self.fashion_analyzer.analyze_content(content, title)
            
            # 2. Semantic context analysis
            semantic_analysis = self.semantic_analyzer.analyze_content(content, title)
            
            # 3. Extract target page information for linking
            target_info = self._extract_target_info(target_pages)
            
            # 4. Find link opportunities
            link_opportunities = self._find_link_opportunities(
                paragraphs, 
                fashion_analysis, 
                semantic_analysis, 
                target_info,
                title
            )
            
            # 5. Generate final link suggestions
            link_suggestions = self._generate_link_suggestions(link_opportunities, content)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Prepare complete analysis result
            return {
                "analysis": {
                    "fashion_entities": fashion_analysis["entities"],
                    "primary_theme": fashion_analysis["primary_theme"],
                    "semantic_structure": semantic_analysis["structure"],
                    "primary_topic": semantic_analysis["primary_topic"],
                    "subtopics": semantic_analysis["subtopics"]
                },
                "link_suggestions": link_suggestions,
                "processing_time": processing_time,
                "status": "success"
            }
        
        except Exception as e:
            logger.error(f"Error in enhanced analysis: {str(e)}")
            return {
                "analysis": {},
                "link_suggestions": [],
                "processing_time": 0,
                "status": "error",
                "error": str(e)
            }
    
    def _extract_target_info(self, target_pages: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
        """
        Extract and organize information about target pages.
        
        Args:
            target_pages: List of target pages with URL and title
            
        Returns:
            Dictionary with information about each target page
        """
        target_info = {}
        
        for page in target_pages:
            url = page.get("url", "")
            title = page.get("title", "")
            
            if not url or not title:
                continue
            
            # Extract keywords from title
            keywords = []
            
            # Extract style keywords
            for style in self.fashion_analyzer.style_categories:
                if style.lower() in title.lower():
                    keywords.append(style)
            
            # Extract clothing keywords
            for item in self.fashion_analyzer.clothing_items:
                if item.lower() in title.lower():
                    keywords.append(item)
            
            # Extract body shape keywords
            for shape in self.fashion_analyzer.body_shapes:
                if shape.lower() in title.lower():
                    keywords.append(shape)
            
            # Extract colour keywords
            for colour in self.fashion_analyzer.colours:
                if colour.lower() in title.lower():
                    keywords.append(colour)
            
            # If no specific keywords found, use title words
            if not keywords:
                # Split the title and use words with 4+ characters
                title_words = [word.lower() for word in title.split() if len(word) >= 4]
                keywords.extend(title_words)
            
            target_info[url] = {
                "title": title,
                "keywords": keywords
            }
        
        return target_info
    
    def _find_link_opportunities(
        self,
        paragraphs: List[str],
        fashion_analysis: Dict[str, Any],
        semantic_analysis: Dict[str, Any],
        target_info: Dict[str, Dict[str, Any]],
        source_title: str
    ) -> List[Dict[str, Any]]:
        """
        Find opportunities for internal links.
        
        Args:
            paragraphs: List of content paragraphs
            fashion_analysis: Results from fashion entity analysis
            semantic_analysis: Results from semantic context analysis
            target_info: Information about target pages
            source_title: Title of the source content
            
        Returns:
            List of link opportunities
        """
        opportunities = []
        
        # For each paragraph, find matching target pages
        for para_idx, paragraph in enumerate(paragraphs):
            # Skip paragraphs that are too short
            min_paragraph_length = self.config.get("min_paragraph_length", 50)
            if len(paragraph) < min_paragraph_length:
                continue
            
            # Count opportunities for this paragraph
            para_opportunities = 0
            
            # Check each target page for relevance to this paragraph
            for target_url, target_data in target_info.items():
                # Skip if we already have enough links for this paragraph
                if para_opportunities >= self.max_links_per_paragraph:
                    break
                
                target_title = target_data["title"]
                target_keywords = target_data["keywords"]
                
                # Calculate relevance between paragraph and target
                relevance = self._calculate_relevance(
                    paragraph, 
                    target_keywords, 
                    target_title,
                    fashion_analysis
                )
                
                # Skip if not relevant enough
                if relevance < self.min_relevance:
                    continue
                
                # Generate anchor text options
                anchor_options = self.anchor_generator.generate_anchor_options(
                    paragraph, 
                    target_keywords, 
                    target_title
                )
                
                # Filter anchor options by minimum confidence
                valid_anchors = [a for a in anchor_options if a["confidence"] >= self.min_confidence]
                
                # Skip if no valid anchor options
                if not valid_anchors:
                    continue
                
                # Add opportunity
                opportunities.append({
                    "paragraph_index": para_idx,
                    "paragraph": paragraph,
                    "target_url": target_url,
                    "target_title": target_title,
                    "relevance": relevance,
                    "anchor_options": valid_anchors
                })
                
                para_opportunities += 1
        
        # Sort opportunities by relevance (highest first)
        opportunities.sort(key=lambda x: x["relevance"], reverse=True)
        
        return opportunities
    
    def _calculate_relevance(
        self,
        paragraph: str,
        target_keywords: List[str],
        target_title: str,
        fashion_analysis: Dict[str, Any]
    ) -> float:
        """
        Calculate relevance between paragraph and target.
        
        Args:
            paragraph: The paragraph text
            target_keywords: Keywords from the target page
            target_title: Title of the target page
            fashion_analysis: Fashion entity analysis results
            
        Returns:
            Float relevance score (0.0 to 1.0)
        """
        # Start with base relevance
        relevance = 0.0
        paragraph_lower = paragraph.lower()
        target_title_lower = target_title.lower()
        
        # 1. Keyword matches in paragraph
        for keyword in target_keywords:
            if keyword.lower() in paragraph_lower:
                # Weight by keyword length (longer = more specific)
                keyword_weight = min(1.0, len(keyword) / 20)
                relevance += 0.2 * keyword_weight
        
        # 2. Title word matches
        title_words = [word.lower() for word in target_title.split() if len(word) > 3]
        for word in title_words:
            if word in paragraph_lower:
                relevance += 0.1
        
        # 3. Entity matches (fashion-specific relevance)
        entities = fashion_analysis["entities"]
        
        # Check if target has clothing items mentioned in paragraph
        for item in entities.get("clothing_items", []):
            if item.lower() in target_title_lower:
                relevance += 0.2
        
        # Check if target has style categories mentioned in paragraph
        for style in entities.get("styles", []):
            if style.lower() in target_title_lower:
                relevance += 0.3
        
        # Check if target has body shapes mentioned in paragraph
        for shape in entities.get("body_shapes", []):
            if shape.lower() in target_title_lower:
                relevance += 0.3
        
        # Check if target has colours mentioned in paragraph
        for colour in entities.get("colours", []):
            if colour.lower() in target_title_lower:
                relevance += 0.2
        
        # 4. Topic similarity
        primary_theme = fashion_analysis.get("primary_theme")
        if primary_theme and primary_theme.lower() in target_title_lower:
            relevance += 0.3
        
        # Cap relevance at 1.0
        return min(relevance, 1.0)
    
    def _generate_link_suggestions(
        self,
        opportunities: List[Dict[str, Any]],
        content: str
    ) -> List[Dict[str, Any]]:
        """
        Generate final link suggestions from opportunities.
        
        Args:
            opportunities: List of link opportunities
            content: Original content
            
        Returns:
            List of link suggestions in standardized format
        """
        # Get maximum number of suggestions
        max_suggestions = self.config.get("max_suggestions", 15)
        
        # Track URLs to avoid duplicates
        seen_urls = set()
        suggestions = []
        
        # Process opportunities
        for opp in opportunities:
            # Skip if we already suggested this URL
            target_url = opp["target_url"]
            if target_url in seen_urls:
                continue
            
            # Get best anchor option
            if opp["anchor_options"]:
                best_anchor = opp["anchor_options"][0]
                
                # Add to suggestions
                suggestions.append({
                    "anchor_text": best_anchor["text"],
                    "target_url": target_url,
                    "context": best_anchor["context"],
                    "confidence": best_anchor["confidence"],
                    "paragraph_index": opp["paragraph_index"],
                    "relevance": opp["relevance"]
                })
                
                # Track URL to avoid duplicates
                seen_urls.add(target_url)
                
                # Stop if we have enough suggestions
                if len(suggestions) >= max_suggestions:
                    break
        
        return suggestions