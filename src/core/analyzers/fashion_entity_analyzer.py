"""
Fashion Entity Analyzer Module

This module analyzes content to extract fashion-specific entities like:
- Clothing items
- Brands
- Style categories
- Materials
- Body shapes
- Seasonal references
"""

import re
import logging
from typing import List, Dict, Any, Set, Tuple, Optional
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
import yaml
import os
from datetime import datetime

# Configure logging
logger = logging.getLogger("web_analyzer.fashion_entity_analyzer")

# Define config directory relative to this file's location
CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config')

class FashionEntityAnalyzer:
    """
    Analyzer for fashion-specific entities in content.
    
    This class extracts fashion-specific entities from text using a combination
    of pattern matching, NLP techniques, and domain-specific knowledge loaded
    from configuration files.
    """
    
    def __init__(self, config_dir: str = CONFIG_DIR):
        """Initialize the analyzer with fashion-specific entity patterns."""
        self.config_dir = config_dir
        logger.info(f"Initializing FashionEntityAnalyzer...")
        logger.info(f"Loading fashion entities from: {self.config_dir}")
        
        # Load entity dictionaries from YAML files
        self.clothing_items = self._load_terms_from_yaml("clothing_items.yaml")
        self.fashion_brands = self._load_terms_from_yaml("fashion_brands.yaml")
        self.style_categories = self._load_terms_from_yaml("style_categories.yaml")
        self.materials = self._load_terms_from_yaml("materials.yaml")
        self.body_shapes = self._load_terms_from_yaml("body_shapes.yaml")
        self.colours = self._load_terms_from_yaml("colours.yaml")
        self.seasonal_terms = self._load_terms_from_yaml("seasonal_terms.yaml")
        
        # Compile regex patterns
        self.clothing_pattern = self._compile_pattern(self.clothing_items, "clothing_items")
        self.brand_pattern = self._compile_pattern(self.fashion_brands, "fashion_brands")
        self.style_pattern = self._compile_pattern(self.style_categories, "style_categories")
        self.material_pattern = self._compile_pattern(self.materials, "materials")
        self.body_shape_pattern = self._compile_pattern(self.body_shapes, "body_shapes")
        self.colour_pattern = self._compile_pattern(self.colours, "colours")
        self.seasonal_pattern = self._compile_pattern(self.seasonal_terms, "seasonal_terms")
        logger.info("FashionEntityAnalyzer initialized successfully.")
    
    def _load_terms_from_yaml(self, filename: str) -> Set[str]:
        """Load a set of terms from a YAML file in the config directory."""
        filepath = os.path.join(self.config_dir, filename)
        logger.debug(f"Attempting to load terms from: {filepath}")
        try:
            with open(filepath, 'r') as f:
                terms = yaml.safe_load(f)
                if isinstance(terms, list):
                    # Convert to lowercase set for efficient lookup and case-insensitivity
                    # Filter out None or empty strings resulting from bad YAML
                    term_set = {str(term).lower() for term in terms if term and isinstance(term, (str, int, float))}
                    logger.info(f"Successfully loaded {len(term_set)} terms from {filename}")
                    return term_set
                else:
                    logger.warning(f"Expected a list in {filename}, but got {type(terms)}. Returning empty set.")
                    return set()
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {filepath}. Returning empty set.")
            return set()
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {filepath}: {e}. Returning empty set.")
            return set()
        except Exception as e:
            logger.error(f"Unexpected error loading {filepath}: {e}. Returning empty set.")
            return set()
    
    def _compile_pattern(self, terms: Set[str], category_name: str) -> Optional[re.Pattern]:
        """Compile regex pattern from a set of terms."""
        if not terms:
            logger.warning(f"Cannot compile pattern for '{category_name}': set of terms is empty.")
            return None
        # Sort by length (longest first) to ensure we match the longest terms
        # Filter out any potential empty strings just in case
        sorted_terms = sorted([term for term in terms if term], key=len, reverse=True)
        if not sorted_terms:
            logger.warning(f"Cannot compile pattern for '{category_name}': term set contains only empty strings after filtering.")
            return None
        # Escape special regex characters and join with OR
        pattern_string = "|".join(re.escape(term) for term in sorted_terms)
        # Compile pattern with word boundaries and case insensitivity
        try:
            # Added word boundaries \\b for more precise matching
            compiled_pattern = re.compile(r'\b(' + pattern_string + r')\b', re.IGNORECASE)
            logger.debug(f"Successfully compiled regex pattern for '{category_name}'.")
            return compiled_pattern
        except re.error as e:
            logger.error(f"Regex compilation error for '{category_name}': {e}")
            return None # Return None if compilation fails
    
    def _find_matches(self, pattern: Optional[re.Pattern], text: str) -> List[str]:
        """Find unique matches for a compiled regex pattern in text."""
        if pattern is None:
            # logger.debug("Skipping match finding due to None pattern.") # Maybe too verbose
            return []
        if not text: # Added check for empty text
            return []
        try:
            # Find all matches and convert to lowercase to avoid duplicates like "Suit" and "suit"
            # Use a set for efficient uniqueness check
            matches = {match.group(1).lower() for match in pattern.finditer(text)}
            return list(matches)
        except Exception as e:
            # Log unexpected errors during regex matching
            logger.error(f"Error during regex matching: {e}")
            return []
    
    def analyze_content(self, content: str, title: str = "") -> Dict[str, Any]:
        """
        Analyze content for fashion entities and identify the primary theme.
        """
        logger.info(f"Starting entity analysis for title: '{title}'")
        start_time = datetime.now() # For timing
        
        # Basic validation
        if not content and not title:
             logger.warning("Entity analysis skipped: Both content and title are empty.")
             return {"entities": {}, "primary_theme": None}

        combined_text = (title.lower() if title else "") + " " + (content.lower() if content else "")
        
        entities = {
            "clothing_items": self._find_matches(self.clothing_pattern, combined_text),
            "brands": self._find_matches(self.brand_pattern, combined_text),
            "styles": self._find_matches(self.style_pattern, combined_text),
            "materials": self._find_matches(self.material_pattern, combined_text),
            "body_shapes": self._find_matches(self.body_shape_pattern, combined_text),
            "colours": self._find_matches(self.colour_pattern, combined_text),
            "seasonal": self._find_matches(self.seasonal_pattern, combined_text)
        }
        # Log counts for each category
        for category, items in entities.items():
            if items: # Only log if entities were found
                logger.debug(f"Found {len(items)} entities for '{category}': {items[:5]}...") # Log first few found

        # Identify primary theme based on dominant entity type (simple heuristic)
        primary_theme = self._determine_primary_theme(entities, title)
        logger.info(f"Determined primary theme: '{primary_theme}'")

        result = {
            "entities": entities,
            "primary_theme": primary_theme
        }
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Entity analysis completed in {duration:.3f} seconds for title: '{title}'")
        return result
    
    def _determine_primary_theme(self, entities: Dict[str, List[str]], title: str) -> Optional[str]:
        """Determine primary theme based on entity counts and title clues."""
        logger.debug(f"Determining primary theme for title: '{title}'")
        # Priority: Style category mentioned in title
        title_lower = title.lower() if title else ""
        if title_lower: # Check if title exists
             for style in entities.get("styles", []):
                  # Check if the exact style phrase is in the title
                  # This requires the original case potentially, let's use the loaded set
                  # Ensure self.style_categories is not None before iterating
                  if self.style_categories and any(s_case.lower() == style and s_case.lower() in title_lower for s_case in self.style_categories):
                      logger.debug(f"Primary theme identified from title (Style): {style}")
                      return style

             # Priority: Clothing item mentioned in title
             for item in entities.get("clothing_items", []):
                 # Ensure self.clothing_items is not None
                 if self.clothing_items and any(i_case.lower() == item and i_case.lower() in title_lower for i_case in self.clothing_items):
                      logger.debug(f"Primary theme identified from title (Clothing): {item}")
                      return item

        # Fallback: Most frequent category (excluding colours/materials/seasonal)
        category_counts = {
            "styles": len(entities.get("styles", [])),
            "clothing_items": len(entities.get("clothing_items", [])),
            "brands": len(entities.get("brands", [])),
            "body_shapes": len(entities.get("body_shapes", []))
        }
        
        # Find category with max count > 0
        max_count = 0
        dominant_category = None
        # Sort categories for deterministic behavior if counts are equal (optional)
        sorted_categories = sorted(category_counts.keys())
        for category in sorted_categories:
            count = category_counts[category]
            if count > max_count:
                max_count = count
                dominant_category = category
        
        if dominant_category and entities.get(dominant_category):
            # Return the most frequent specific term within that dominant category
            term_counts = {}
            for term in entities[dominant_category]:
                # Count occurrences in the original combined text for better frequency measure?
                # This is simpler for now: count unique terms identified.
                term_counts[term] = term_counts.get(term, 0) + 1 # Simple count needed here
            if term_counts: # Check if term_counts is not empty
                most_frequent_term = max(term_counts, key=term_counts.get)
                logger.debug(f"Primary theme identified by frequency in content ({dominant_category}): {most_frequent_term}")
                return most_frequent_term
            else:
                 logger.debug(f"Dominant category '{dominant_category}' found, but no specific terms counted.")

        logger.info("Could not determine a primary theme.")
        return None
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract fashion entities from text. (Consider removing if analyze_content suffices)
        
        Args:
            text (str): The text to analyze
            
        Returns:
            Dict[str, List[str]]: Dictionary of entity types and extracted entities
        """
        # Basic data validation
        if not text or not isinstance(text, str):
            # Return structure consistent with analyze_content
            logger.warning("extract_entities called with empty or invalid text.")
            return {
                "clothing_items": [], "brands": [], "styles": [], "materials": [],
                "body_shapes": [], "colours": [], "seasonal": []
            }
        
        logger.debug(f"Extracting entities from text snippet: {text[:100]}...")
        # Find all matches using regex patterns
        entities = {
             "clothing_items": self._find_matches(self.clothing_pattern, text),
             "brands": self._find_matches(self.brand_pattern, text),
             "styles": self._find_matches(self.style_pattern, text),
             "materials": self._find_matches(self.material_pattern, text),
             "body_shapes": self._find_matches(self.body_shape_pattern, text),
             "colours": self._find_matches(self.colour_pattern, text),
             "seasonal": self._find_matches(self.seasonal_pattern, text)
        }
        # Log counts here as well if this method is used independently
        for category, items in entities.items():
            if items:
                logger.debug(f"[extract_entities] Found {len(items)} for '{category}': {items[:5]}...")

        return entities