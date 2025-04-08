import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import re
from datetime import datetime
import yaml

# Configure logging
logger = logging.getLogger("web_analyzer.analyzer")

# Define config directory relative to this file's location (assuming analyzer.py is in src/core)
CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'config')

class ContentAnalyzer:
    """
    Core content analysis engine that processes text and identifies link opportunities.
    This is a simplified version of our consolidated sitemap_anchor_generator.
    Relies on weighted topic categories loaded from external configuration.
    NOTE: This analyzer might be superseded by EnhancedContentAnalyzer for main API use.
    """

    def __init__(self, config_path: str = "config.json", config_dir: str = CONFIG_DIR):
        logger.info("Initializing ContentAnalyzer...") # Log start
        self.config = self._load_app_config(config_path)
        self.config_dir = config_dir
        # Load topic categories from YAML during initialization
        self.topic_categories = self._init_topic_categories()
        if not self.topic_categories:
             logger.error("Failed to load topic categories. Analyzer may not function correctly.")
             # Provide default empty structure to avoid NoneType errors later
             self.topic_categories = {}
        logger.info("ContentAnalyzer initialized.") # Log completion

    def _load_app_config(self, config_path: str) -> Dict[str, Any]:
        """Load main application configuration from JSON file."""
        try:
            # Adjust path relative to project root if needed, assuming config.json is at the root
            project_root = os.path.dirname(self.config_dir) # Get parent of config dir
            json_config_path = os.path.join(project_root, config_path)
            if os.path.exists(json_config_path):
                with open(json_config_path, 'r') as f:
                    logger.info(f"Loading app config from: {json_config_path}")
                    config_data = json.load(f)
                    logger.debug(f"App config loaded: {config_data}") # Log loaded data at debug level
                    return config_data
            else:
                logger.warning(f"App config file {json_config_path} not found, using defaults.")
                # Define essential defaults here
                return {
                    "min_confidence": 0.6,
                    "max_links_per_paragraph": 2,
                    "min_paragraph_length": 50,
                    "min_relevance": 0.4, # Add defaults expected later
                    "max_suggestions": 15
                }
        except Exception as e:
            logger.error(f"Error loading app config from {config_path}: {str(e)}")
            # Return essential defaults on error
            return {
                    "min_confidence": 0.6,
                    "max_links_per_paragraph": 2,
                    "min_paragraph_length": 50,
                    "min_relevance": 0.4,
                    "max_suggestions": 15
            }

    def _init_topic_categories(self) -> Dict[str, Dict[str, Any]]:
        """Initialize topic categories by loading from YAML file."""
        filepath = os.path.join(self.config_dir, "topic_weights.yaml")
        logger.debug(f"Attempting to load topic categories from: {filepath}") # Add log
        try:
            with open(filepath, 'r') as f:
                categories = yaml.safe_load(f)
                if isinstance(categories, dict):
                    logger.info(f"Successfully loaded {len(categories)} topic categories from {filepath}") # Changed level
                    # Basic validation of structure (optional but recommended)
                    valid_categories = {}
                    for key, value in categories.items():
                        if isinstance(value, dict) and 'terms' in value and isinstance(value['terms'], list) and 'weight' in value and isinstance(value['weight'], (int, float)):
                            valid_categories[key] = value
                            # Convert terms to lowercase once during loading
                            valid_categories[key]['terms_lower'] = {str(t).lower() for t in value['terms'] if t}
                        else:
                            logger.warning(f"Invalid structure or missing keys/types for category '{key}' in {filepath}. Skipping.")
                    return valid_categories
                else:
                    logger.error(f"Expected a dictionary in {filepath}, but got {type(categories)}. Returning empty dict.")
                    return {}
        except FileNotFoundError:
            logger.error(f"Topic weights file not found: {filepath}. Returning empty dict.")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {filepath}: {e}. Returning empty dict.")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error loading {filepath}: {e}. Returning empty dict.")
            return {}

    def analyze_content(self, content: str, title: str, target_urls: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Analyze content and find link opportunities to target URLs.
        
        Args:
            content: The content to analyze
            title: The title of the content
            target_urls: List of dictionaries with target URLs and titles
            
        Returns:
            List of link opportunities
        """
        logger.info(f"Starting content analysis for title: '{title}', {len(target_urls)} target URLs.")
        start_time = datetime.now()

        if not self.topic_categories:
             logger.warning("Topic categories not loaded, analysis results might be empty or inaccurate.")
             # Return empty list if config is essential and missing
             return []

        # Split content into paragraphs
        paragraphs = self._split_into_paragraphs(content)
        logger.info(f"Split content into {len(paragraphs)} paragraphs.")

        # Extract main topics from content - using the loaded categories
        # This seems less relevant if we analyze paragraph by paragraph vs targets
        # main_content_topics = self._extract_topics(content, title)
        # logger.debug(f"Main content topics: {main_content_topics[:5]}...")

        opportunities = []
        processed_opportunities = 0 # Counter for logging

        min_para_len = self.config.get("min_paragraph_length", 50)
        min_relevance_threshold = self.config.get("min_relevance", 0.4) # Get threshold from config
        logger.debug(f"Using min_paragraph_length: {min_para_len}, min_relevance: {min_relevance_threshold}")

        for para_idx, paragraph in enumerate(paragraphs):
            if len(paragraph) < min_para_len:
                logger.debug(f"Skipping paragraph {para_idx}: too short ({len(paragraph)} chars).")
                continue

            logger.debug(f"Analyzing paragraph {para_idx}...")
            # Find opportunities for each target URL within this paragraph
            links_in_para = 0 # Track links per paragraph if needed for limits
            max_links_per_para = self.config.get("max_links_per_paragraph", 2)

            for target in target_urls:
                target_title = target.get("title", "")
                target_url = target.get("url", "")
                if not target_url or not target_title:
                    logger.debug(f"Skipping target with missing URL or title: {target}")
                    continue

                # Extract topics for the target - using the loaded categories
                # Pass empty content, only use title
                target_topics = self._extract_topics("", target_title)
                if not target_topics:
                    logger.debug(f"No topics extracted for target title: '{target_title}'. Skipping relevance check.")
                    continue

                # Calculate relevance - using the loaded categories
                relevance = self._calculate_relevance(paragraph, target_topics, target_title)

                # Skip if not relevant enough
                if relevance < min_relevance_threshold:
                    logger.debug(f"Paragraph {para_idx} -> Target '{target_title}' relevance {relevance:.3f} < {min_relevance_threshold}. Skipping.")
                    continue

                logger.info(f"Paragraph {para_idx} -> Target '{target_title}' relevance {relevance:.3f} >= {min_relevance_threshold}. Finding anchors.")

                # Find potential anchor text - using the loaded categories
                anchor_options = self._find_anchor_options(paragraph, target_topics, target_title)

                if anchor_options:
                    # Select best anchor based on confidence/score if multiple options exist
                    # Simple selection for now: take the first one if available
                    # TODO: Refine anchor selection logic if needed
                    best_anchor = anchor_options[0] # Assuming sorted by confidence
                    min_anchor_confidence = self.config.get("min_confidence", 0.6)

                    if best_anchor.get("confidence", 0.0) >= min_anchor_confidence:
                        logger.info(f"  Found suitable anchor: '{best_anchor['text']}' (Conf: {best_anchor['confidence']:.2f})")
                        opportunities.append({
                            "paragraph_index": para_idx,
                            # "paragraph": paragraph, # Optionally exclude full paragraph for brevity
                            "target_url": target_url,
                            "target_title": target_title,
                            "relevance": round(relevance, 3), # Round for cleaner output
                            "anchor_text": best_anchor["text"],
                            "anchor_context": best_anchor.get("context", ""), # Ensure context exists
                            "anchor_confidence": round(best_anchor.get("confidence", 0.0), 2) # Round for output
                        })
                        processed_opportunities += 1
                        links_in_para += 1
                        if links_in_para >= max_links_per_para:
                            logger.debug(f"Reached max links ({max_links_per_para}) for paragraph {para_idx}. Moving to next paragraph.")
                            break # Stop checking targets for this paragraph
                    else:
                         logger.debug(f"  Anchor '{best_anchor['text']}' confidence {best_anchor.get('confidence', 0.0):.2f} < {min_anchor_confidence}. Skipping.")

                else:
                    logger.debug(f"  No suitable anchor options found for target '{target_title}' in paragraph {para_idx}.")

        logger.info(f"Found {processed_opportunities} raw link opportunities for title: '{title}'.")

        # Sort by relevance primarily, then confidence
        opportunities.sort(key=lambda x: (x["relevance"], x["anchor_confidence"]), reverse=True)

        # Apply limits (e.g., max suggestions per article)
        max_suggestions = self.config.get("max_suggestions", 15) # Example limit
        final_opportunities = opportunities[:max_suggestions]
        logger.info(f"Returning {len(final_opportunities)} link opportunities after applying limits (max={max_suggestions}).")

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Content analysis completed in {duration:.3f} seconds for title: '{title}'")
        return final_opportunities # Return the limited list

    def _split_into_paragraphs(self, content: str) -> List[str]:
        """Split content into paragraphs."""
        if not content: return [] # Handle empty content
        paragraphs = re.split(r'\n\n|\n{2,}', content) # Split on 2+ newlines first
        # If minimal splitting, try single newline (less reliable)
        if len(paragraphs) <= 1 and '\n' in content:
             paragraphs = re.split(r'\n', content)
        return [p.strip() for p in paragraphs if p.strip()] # Ensure no empty strings

    def _extract_topics(self, content: str, title: str) -> List[str]:
        """Extract main topics from content and title with priority on multi-word specifics."""
        topic_scores = {}  # Track topic scores for sorting
        # Combine content and title for searching terms
        search_text = ((content + " " + title) if content else title).lower()

        if not search_text:
            logger.debug("Cannot extract topics: search text is empty.")
            return []

        # Use the loaded self.topic_categories
        if not self.topic_categories:
            # Warning logged in caller
            return []

        # Collect all matching topics with their category weights
        for category, data in self.topic_categories.items():
            # Use pre-lowercased terms for matching
            terms_lower = data.get('terms_lower', set())
            weight = data.get('weight', 1.0)

            for term_lower in terms_lower:
                # Simple substring check (consider word boundaries if needed: r'\b' + re.escape(term_lower) + r'\b')
                if term_lower in search_text:
                    # Use original term case for scoring if available (better for length calc)
                    # Find the original term that matches the lowercased one
                    original_term = term_lower # Default to lower if original not found easily
                    for t in data.get("terms", []):
                         if str(t).lower() == term_lower:
                              original_term = str(t)
                              break

                    term_length_score = min(1.0, len(original_term) / 25.0)
                    word_count = len(original_term.split())
                    word_count_score = min(1.0, word_count / 5.0)

                    score = (
                        weight * 0.6 +
                        word_count_score * 0.3 +
                        term_length_score * 0.1
                    )
                    topic_scores[original_term] = max(score, topic_scores.get(original_term, 0))

        # Sort topics by score (highest first)
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)

        # Take top N topics (e.g., 15)
        topics = [term for term, score in sorted_topics[:15]]

        logger.debug(f"Extracted topics (top {len(topics)}): {topics}")
        return topics

    def _calculate_relevance(self, paragraph: str, target_topics: List[str], target_title: str) -> float:
        """Calculate relevance between paragraph and target based on shared topics and title overlap."""
        # Check if topics can be loaded before proceeding
        if not self.topic_categories:
             logger.warning("Cannot calculate relevance: topic categories not loaded.")
             return 0.0

        paragraph_lower = paragraph.lower()
        target_title_lower = target_title.lower()

        # 1. Score direct topic matches found in the paragraph
        paragraph_topics = self._extract_topics(paragraph, "") # Extract topics from paragraph only
        # Ensure topics are lowercased for set intersection
        shared_topics = set(topic.lower() for topic in paragraph_topics) & set(topic.lower() for topic in target_topics)
        logger.debug(f"Shared topics between paragraph and target '{target_title}': {shared_topics}")

        topic_relevance_score = 0.0
        for topic_lower in shared_topics:
             score = 0.1 # Base score
             word_count = len(topic_lower.split())
             score += min(0.1, (word_count -1) * 0.05) # Bonus for multi-word

             # Find category weight for bonus
             for category, data in self.topic_categories.items():
                  # Use pre-lowercased terms set for efficient check
                  if topic_lower in data.get("terms_lower", set()):
                       category_bonus = max(0, (data.get("weight", 1.0) - 1.0) * 0.1) # Bonus for weight > 1.0
                       score += category_bonus
                       logger.debug(f"  Topic '{topic_lower}' bonus from category '{category}' weight {data.get('weight', 1.0)}: +{category_bonus:.2f}")
                       break # Assume topic belongs to only one category
             topic_relevance_score += score

        # Normalize topic relevance
        topic_relevance_score = min(topic_relevance_score, 0.6) # Cap contribution

        # 2. Score title phrase overlap (Improved)
        title_overlap_score = 0.0
        # Consider phrases of 2-4 words from the title
        title_phrases = set()
        words = [w for w in target_title_lower.split() if len(w) > 2] # Basic word filter
        for n in range(2, 5): # Phrase lengths 2, 3, 4
             for i in range(len(words) - n + 1):
                  phrase = " ".join(words[i:i+n])
                  title_phrases.add(phrase)

        matched_phrase_score = 0.0
        for phrase in title_phrases:
             # Use regex for word boundary matching
             if re.search(r'\b' + re.escape(phrase) + r'\b', paragraph_lower):
                  # Score longer phrases higher
                  phrase_score = 0.1 + min(0.15, (len(phrase.split()) - 1) * 0.05)
                  matched_phrase_score += phrase_score
                  logger.debug(f"  Found title phrase match: '{phrase}', adding score: {phrase_score:.2f}")

        title_overlap_score = min(matched_phrase_score, 0.4) # Cap contribution

        # Combine scores
        relevance = topic_relevance_score + title_overlap_score
        logger.debug(f"Paragraph -> Target '{target_title}': Final Relevance = {relevance:.3f} (Topic Score: {topic_relevance_score:.3f}, Title Overlap: {title_overlap_score:.3f})")
        return min(relevance, 1.0) # Ensure score is capped at 1.0

    def _find_anchor_options(self, paragraph: str, target_topics: List[str], target_title: str) -> List[Dict[str, Any]]:
        """
        Find potential anchor text options in the paragraph.
        Focuses on matching target topics found within the paragraph text.
        """
        logger.debug(f"Finding anchor options for target '{target_title}' in paragraph snippet: '{paragraph[:100]}...'")
        anchor_options = []
        seen_texts_lower = set() # Avoid duplicates based on lowercase text

        # Prioritize longer, more specific target topics found in the paragraph
        # Sort target topics by length descending
        sorted_target_topics = sorted(target_topics, key=len, reverse=True)

        for topic in sorted_target_topics:
            topic_lower = topic.lower()
            # Use regex to find topic with word boundaries in the paragraph
            # Need to escape potential regex characters in the topic itself
            try:
                # Find all occurrences to potentially choose the best context later
                matches = list(re.finditer(r'\b' + re.escape(topic_lower) + r'\b', paragraph.lower()))
            except re.error:
                 logger.warning(f"Regex error finding anchor for topic: '{topic}'. Skipping.")
                 continue # Skip this topic if regex fails

            if matches:
                # Use the original casing from the topic list as the primary anchor text
                original_case_topic = topic
                if original_case_topic.lower() not in seen_texts_lower:
                    # Calculate confidence (higher for longer topics, maybe add category weight bonus?)
                    confidence = 0.5 + min(0.4, len(original_case_topic.split()) * 0.08) # Adjusted scoring

                    # Find category weight bonus
                    for category, data in self.topic_categories.items():
                        if topic_lower in data.get("terms_lower", set()):
                             confidence += max(0, (data.get("weight", 1.0) - 1.0) * 0.05) # Small weight bonus
                             break

                    confidence = min(confidence, 1.0) # Cap confidence

                    # Extract context around the first match found
                    first_match_span = matches[0].span()
                    context = self._extract_context_span(paragraph, first_match_span, original_case_topic)

                    anchor_options.append({
                        "text": original_case_topic,
                        "confidence": round(confidence, 2),
                        "context": context,
                        "position": first_match_span[0] # Store position of first match
                    })
                    seen_texts_lower.add(original_case_topic.lower())
                    logger.debug(f"  Found anchor option: '{original_case_topic}' (Confidence: {confidence:.2f})")

        # Sort options by confidence primarily, then position (earlier preferred)
        anchor_options.sort(key=lambda x: (x["confidence"], -x["position"]), reverse=True)

        logger.debug(f"Found {len(anchor_options)} anchor options for target '{target_title}'.")
        return anchor_options[:5] # Return top 5 options

    def _extract_context_span(self, paragraph: str, span: Tuple[int, int], anchor_text: str) -> str:
         """Extract context around a given character span, highlighting the anchor."""
         try:
              start, end = span
              # Try to find sentence boundaries containing the span
              sentence_start = paragraph.rfind('.', 0, start) + 1
              sentence_end = paragraph.find('.', end)
              if sentence_end == -1: # If no period found after
                   sentence_end = len(paragraph)

              # Adjust sentence start if the period was part of e.g., "Dr."
              if sentence_start > 0 and paragraph[sentence_start-2].isalpha() and paragraph[sentence_start-1] == '.':
                   prev_period = paragraph.rfind('.', 0, sentence_start - 2)
                   if prev_period != -1:
                        sentence_start = prev_period + 1

              context = paragraph[sentence_start:sentence_end].strip()

              # Highlight the anchor text within this context sentence
              # Find the anchor's position relative to the sentence start
              highlight_start = start - sentence_start
              highlight_end = end - sentence_start

              # Ensure calculated indices are within the extracted context bounds
              if 0 <= highlight_start < highlight_end <= len(context):
                    # Use original anchor text casing for highlighting if possible
                    highlighted_context = (
                         context[:highlight_start] +
                         "**" + context[highlight_start:highlight_end] + "**" +
                         context[highlight_end:]
                    )
                    return highlighted_context
              else:
                    # Fallback if index calculation is off, return context without highlight
                    logger.warning(f"Could not accurately highlight anchor '{anchor_text}' in context. Span: {span}, Sentence Start: {sentence_start}")
                    return context

         except Exception as e:
              logger.warning(f"Error extracting context for span {span}, anchor '{anchor_text}': {e}")
              # Fallback to simple snippet
              snippet_start = max(0, span[0] - 50)
              snippet_end = min(len(paragraph), span[1] + 50)
              return "..." + paragraph[snippet_start:snippet_end].strip() + "..."