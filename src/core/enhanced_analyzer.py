"""
Enhanced Content Analyzer Module

This module combines multiple specialized analyzers and semantic similarity
to provide comprehensive content analysis and internal linking suggestions.
"""

import os
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
import re
from datetime import datetime
import numpy as np
# REMOVE: from sklearn.metrics.pairwise import cosine_similarity # No longer needed here

# Import specialized analyzers
from src.core.analyzers.fashion_entity_analyzer import FashionEntityAnalyzer
from src.core.analyzers.semantic_context_analyzer import SemanticContextAnalyzer
from src.core.analyzers.anchor_text_generator import AnchorTextGenerator
# Import KnowledgeDatabase and the loaded model
# --- FIXED IMPORT ---
from src.core.knowledge_db.knowledge_database import KnowledgeDatabase, global_embedding_model as sentence_transformer_model
# --- END FIXED IMPORT ---


# Configure logging
logger = logging.getLogger("web_analyzer.enhanced_analyzer")

# --- REMOVE UNUSED HELPER FUNCTION ---
# def calculate_cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
#    """Calculates cosine similarity between two numpy embedding vectors."""
#    # ... (implementation removed) ...
# --- END REMOVE UNUSED HELPER FUNCTION ---


class EnhancedContentAnalyzer:
    """
    Enhanced content analyzer that combines multiple specialized analyzers
    and semantic search via embeddings for comprehensive content analysis
    and high-quality link suggestions.
    """

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the enhanced content analyzer.

        Args:
            config_path: Path to the main configuration file (relative to project root)
        """
        logger.info("Initializing EnhancedContentAnalyzer...")
        project_root = os.path.join(os.path.dirname(__file__), '..', '..') # Navigate up from src/core
        self.config = self._load_config(os.path.join(project_root, config_path))

        # Initialize specialized analyzers (consider lazy loading?)
        self.fashion_analyzer = FashionEntityAnalyzer()
        self.semantic_analyzer = SemanticContextAnalyzer()
        self.anchor_generator = AnchorTextGenerator()

        # Configuration for relevance scoring
        self.min_relevance = self.config.get("min_relevance", 0.45) # Default threshold potentially higher now
        self.semantic_weight = self.config.get("semantic_weight", 0.7) # Weight for semantic score
        self.keyword_weight = self.config.get("keyword_weight", 0.3) # Weight for keyword score
        self.min_confidence = self.config.get("min_confidence", 0.6)
        self.max_links_per_paragraph = self.config.get("max_links_per_paragraph", 2)
        self.max_suggestions = self.config.get("max_suggestions", 15)
        self.min_paragraph_length = self.config.get("min_paragraph_length", 50)

        # Check if the sentence transformer model loaded correctly
        if sentence_transformer_model is None:
             logger.error("Sentence transformer model failed to load! Semantic search will be disabled.")
             self.semantic_weight = 0.0 # Disable semantic contribution if model failed
             self.keyword_weight = 1.0

        logger.info("EnhancedContentAnalyzer initialized.")
        logger.info(f"Relevance config: min_relevance={self.min_relevance}, semantic_weight={self.semantic_weight}, keyword_weight={self.keyword_weight}")


    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    logger.info(f"Loading main config from: {config_path}")
                    return json.load(f)
            else:
                logger.warning(f"Main config file {config_path} not found, using defaults")
                # Define essential defaults here
                return {
                    "knowledge_db_dir": "data/knowledge_db", # Needed for KB init
                    "min_relevance": 0.45,
                    "semantic_weight": 0.7,
                    "keyword_weight": 0.3,
                    "min_confidence": 0.6,
                    "max_links_per_paragraph": 2,
                    "min_paragraph_length": 50,
                    "max_suggestions": 15,
                    "min_content_length": 100
                }
        except Exception as e:
            logger.error(f"Error loading main config from {config_path}: {str(e)}")
            # Return essential defaults on error
            return {
                 "knowledge_db_dir": "data/knowledge_db",
                 "min_relevance": 0.45,
                 "semantic_weight": 0.7,
                 "keyword_weight": 0.3,
                 "min_confidence": 0.6,
                 "max_links_per_paragraph": 2,
                 "min_paragraph_length": 50,
                 "max_suggestions": 15,
                 "min_content_length": 100
            }

    def _split_into_paragraphs(self, content: str) -> List[str]:
        """Split content into paragraphs."""
        if not content: return []
        paragraphs = re.split(r'\n\n|\n{2,}', content) # Split on 2+ newlines
        # Fallback to single newline if needed, but filter short lines
        if len(paragraphs) <= 1 and '\n' in content:
             paragraphs = [p for p in content.split('\n') if len(p.strip()) > 20] # Filter short lines if using single newline split
        return [p.strip() for p in paragraphs if len(p.strip()) >= self.min_paragraph_length]


    def analyze_content(
        self,
        content: str,
        title: str,
        site_id: str, # Added site_id parameter
        url: Optional[str] = None # URL of the current content being analyzed (string format)
    ) -> Dict[str, Any]:
        """
        Perform comprehensive content analysis using semantic search and find link opportunities.

        Args:
            content: The content to analyze
            title: The title of the content
            site_id: Identifier for the website (used for KnowledgeDatabase)
            url: URL of the current content (string format) (used to exclude self-links)

        Returns:
            Dictionary with analysis results and link suggestions
        """
        start_time = datetime.now()
        logger.info(f"Starting enhanced analysis for site: '{site_id}', title: '{title}' (URL: {url})")

        # Basic validation
        if not content or not title or not site_id:
            return self._format_error_response("Missing required parameters (content, title, or site_id)")

        # Skip analysis if content is too short
        min_length = self.config.get("min_content_length", 100)
        if len(content) < min_length:
             return self._format_error_response(f"Content too short (minimum {min_length} characters)")

        try:
            # Initialize Knowledge Base for this site_id
            # Ensure KB loads config correctly relative to its file location
            kb = KnowledgeDatabase(site_id=site_id)

            # Perform basic analysis on source content
            analysis_result = self._perform_basic_analysis(content, title)

            # Split source content into paragraphs
            paragraphs = self._split_into_paragraphs(content)
            logger.info(f"Analyzing {len(paragraphs)} paragraphs (min length {self.min_paragraph_length}).")

            # --- Find Link Opportunities ---
            all_opportunities = []
            processed_targets_for_paragraph = {} # Track targets linked per paragraph

            if sentence_transformer_model is None:
                logger.warning("Semantic model not available, skipping link opportunity finding.")
            else:
                for para_idx, paragraph in enumerate(paragraphs):
                    # Check if we've already added max links for this paragraph
                    if processed_targets_for_paragraph.get(para_idx, 0) >= self.max_links_per_paragraph:
                         continue

                    logger.debug(f"Processing Paragraph {para_idx}...")
                    # Generate embedding for the current paragraph
                    paragraph_embedding = self._generate_embedding(paragraph)
                    if paragraph_embedding is None:
                        logger.warning(f"Could not generate embedding for paragraph {para_idx}. Skipping.")
                        continue

                    # --- USE NEW KB SEMANTIC SEARCH ---
                    # Find top N relevant targets using semantic similarity directly from KB
                    relevant_targets = kb.find_related_content_semantic(
                         query_embedding=paragraph_embedding,
                         exclude_url=url, # Pass the string URL
                         top_n=10, # How many candidates to consider per paragraph
                         min_similarity=self.min_relevance # Use configured min relevance as threshold
                    )
                    # --- END NEW KB SEMANTIC SEARCH ---


                    if not relevant_targets:
                         logger.debug(f"  No semantically relevant targets found for paragraph {para_idx} above threshold {self.min_relevance}.")
                         continue

                    logger.info(f"  Found {len(relevant_targets)} potentially relevant targets via semantic search for paragraph {para_idx}.")

                    # --- Process Semantically Relevant Targets ---
                    # We already have relevant targets, no need to calculate relevance again here.
                    # The 'similarity' score from find_related_content_semantic is our primary relevance.
                    for target in relevant_targets:
                        # Check again if we've hit the max links for this paragraph
                        if processed_targets_for_paragraph.get(para_idx, 0) >= self.max_links_per_paragraph:
                            logger.debug(f"Reached max links ({self.max_links_per_paragraph}) for paragraph {para_idx}.")
                            break # Stop processing targets for this paragraph

                        target_title = target["title"]
                        target_url = target["url"] # This is a string from KB
                        semantic_similarity_score = target["similarity"] # Get score from KB search result

                        logger.info(f"    Considering target: '{target_title}' (Similarity: {semantic_similarity_score:.3f})")

                        # Find best anchor text for this paragraph -> target pair
                        target_keywords = self._extract_keywords_from_title(target_title)

                        anchor_options = self.anchor_generator.generate_anchor_options(
                            text=paragraph,
                            target_keywords=target_keywords,
                            target_title=target_title
                        )

                        if anchor_options:
                            # Select best anchor based on confidence
                            best_anchor = max(anchor_options, key=lambda x: x.get("confidence", 0.0))

                            if best_anchor.get("confidence", 0.0) >= self.min_confidence:
                                logger.info(f"      Found suitable anchor: '{best_anchor['text']}' (Conf: {best_anchor['confidence']:.2f})")
                                all_opportunities.append({
                                    "paragraph_index": para_idx,
                                    "target_url": target_url, # Keep as string here
                                    "target_title": target_title,
                                    # Use semantic similarity as the primary relevance score
                                    "relevance": round(semantic_similarity_score, 3),
                                    "anchor_text": best_anchor["text"],
                                    "anchor_context": best_anchor.get("context", ""),
                                    "anchor_confidence": round(best_anchor.get("confidence", 0.0), 2)
                                })
                                # Increment count of links added for this paragraph
                                processed_targets_for_paragraph[para_idx] = processed_targets_for_paragraph.get(para_idx, 0) + 1
                            else:
                                 logger.debug(f"      Anchor '{best_anchor['text']}' confidence {best_anchor.get('confidence', 0.0):.2f} < {self.min_confidence}. Skipping.")
                        else:
                            logger.debug(f"      No suitable anchor options found for target '{target_title}'.")


            # --- Post-process and Format Results ---
            # Sort opportunities primarily by relevance (semantic similarity), then confidence
            all_opportunities.sort(key=lambda x: (x["relevance"], x["anchor_confidence"]), reverse=True)

            # Apply overall suggestion limit
            final_suggestions = all_opportunities[:self.max_suggestions]
            logger.info(f"Generated {len(final_suggestions)} final link suggestions (limit: {self.max_suggestions}).")

            # Pass the list of dicts with string URLs to the success formatter
            return self._format_success_response(analysis_result, final_suggestions, start_time)

        except Exception as e:
            logger.error(f"Critical error during enhanced analysis for site '{site_id}', title '{title}': {str(e)}", exc_info=True)
            return self._format_error_response(f"Internal server error during analysis: {str(e)}")

    def _perform_basic_analysis(self, content: str, title: str) -> Dict[str, Any]:
         """Performs non-linking analysis (entities, topics)."""
         logger.debug("Performing basic analysis (fashion entities, semantic context)...")
         try:
            # 1. Fashion entity analysis
            fashion_analysis = self.fashion_analyzer.analyze_content(content, title)
            # 2. Semantic context analysis (may use NLTK, ensure data downloaded)
            semantic_analysis = self.semantic_analyzer.analyze_content(content, title)

            # Combine results safely using .get()
            return {
                    "fashion_entities": fashion_analysis.get("entities", {}),
                    "primary_theme": fashion_analysis.get("primary_theme"),
                    "semantic_structure": semantic_analysis.get("structure", {}),
                    "primary_topic": semantic_analysis.get("primary_topic"), # Check source of this
                    "subtopics": semantic_analysis.get("subtopics", []) # Check source of this
                    # Add other results from semantic_analysis if needed
                }
         except Exception as e:
              logger.error(f"Error during basic analysis sub-step: {e}", exc_info=True)
              # Return a dict consistent with expected structure but indicate error
              return {
                  "fashion_entities": {}, "primary_theme": None, "semantic_structure": {},
                  "primary_topic": None, "subtopics": [], "error": "Failed during basic analysis"
              }


    def _generate_embedding(self, text: str) -> Optional[np.ndarray]:
         """Generates embedding for the given text using the loaded global model."""
         if sentence_transformer_model is None:
             logger.warning("Cannot generate embedding: Sentence transformer model not loaded.")
             return None
         if not text or not isinstance(text, str):
             logger.warning(f"Cannot generate embedding for invalid text: {text}")
             return None
         try:
             # Models often work best on sentences or short paragraphs.
             # Consider splitting longer paragraphs? For now, embed whole paragraph.
             embedding = sentence_transformer_model.encode(text, convert_to_numpy=True)
             return embedding
         except Exception as e:
             logger.error(f"Error generating paragraph embedding: {e}", exc_info=True)
             return None

    def _extract_keywords_from_title(self, title: str) -> List[str]:
        """Extracts potential keywords from a title for anchor generation."""
        # Simple approach: split, lowercase, filter short words/stopwords
        # Could be enhanced using fashion_analyzer results if needed.
        try:
            # Use NLTK stopwords if available, otherwise basic list
            try:
                 from nltk.corpus import stopwords
                 stop_words = set(stopwords.words('english'))
            except ImportError:
                 # This should not happen if NLTK download worked in Dockerfile
                 logger.warning("NLTK stopwords not found, using basic list.")
                 stop_words = {"a", "an", "the", "in", "on", "at", "for", "to", "of", "and", "or", "is", "are", "how"}

            words = re.findall(r'\b\w+\b', title.lower())
            keywords = [word for word in words if len(word) > 2 and word not in stop_words]
            logger.debug(f"Extracted keywords from title '{title}': {keywords}")
            return keywords
        except Exception as e:
             logger.warning(f"Could not extract keywords from title '{title}': {e}")
             return title.lower().split() # Fallback

    def _format_success_response(self, analysis_result: Dict, suggestions: List[Dict], start_time: datetime) -> Dict:
         """Formats a successful analysis response. Expects suggestions with string URLs."""
         processing_time = (datetime.now() - start_time).total_seconds()
         return {
                "analysis": analysis_result,
                "link_suggestions": suggestions, # Pass suggestions with string URLs
                "processing_time": round(processing_time, 3),
                "status": "success"
            }

    def _format_error_response(self, error_message: str) -> Dict:
        """Formats an error response."""
        return {
                "analysis": {},
                "link_suggestions": [],
                "processing_time": 0,
                "status": "error",
                "error": error_message
            }

    # Remove or adapt old methods if they are no longer used or conflict
    # def _extract_target_info(...) -> No longer directly used, KB provides info
    # def _find_link_opportunities(...) -> Logic integrated into analyze_content loop