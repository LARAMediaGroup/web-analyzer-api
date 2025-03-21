import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import re
from datetime import datetime

# Configure logging
logger = logging.getLogger("web_analyzer.analyzer")

class ContentAnalyzer:
    """
    Core content analysis engine that processes text and identifies link opportunities.
    This is a simplified version of our consolidated sitemap_anchor_generator.
    """

    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.topic_categories = self._init_topic_categories()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Config file {config_path} not found, using defaults")
                return {
                    "min_confidence": 0.6,
                    "max_links_per_paragraph": 2,
                    "min_paragraph_length": 50
                }
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return {}

    def _init_topic_categories(self) -> Dict[str, Dict[str, Any]]:
        """Initialize topic categories with weighted terms."""
        return {
            "body_shape_intent": {
                "terms": ["men's body shape guide", "how to dress for body shape", "body shape styling", 
                        "inverted triangle body shape", "triangle body shape men", "athletic build styling", 
                        "rectangle body styling", "oval body shape men"],
                "weight": 1.6  # Higher weight for search intent phrases
            },
            "specific_styles": {
                "terms": ["old money style for men", "preppy fashion guide", "ivy league aesthetic", 
                         "trad style men", "nautical fashion guide", "british countryside style", 
                         "sloane ranger look", "minimalist fashion for men", "capsule wardrobe guide", 
                         "gaucho style", "southern preppy look"],
                "weight": 1.7  # Highest weight for specific styles with intent
            },
            "clothing_specific": {
                "terms": ["how to style oxford shirts", "tailored blazer guide", "navy jacket outfits", 
                          "chino trouser styling", "penny loafer outfits", "cable knit jumper", 
                          "tweed jacket combinations", "linen suit styling", "camel coat outfits", "silk tie pairings"],
                "weight": 1.5  # Higher weight for specific clothing items with context
            },
            "colour_specific": {
                "terms": ["true spring colours", "cool summer colour palette", "warm autumn colours", 
                         "seasonal colour analysis", "men's colour theory", "colour coordination guide", 
                         "navy blue styling", "burgundy colour combinations", "forest green outfits"],
                "weight": 1.5  # British English spelling
            },
            "fashion_services": {
                "terms": ["men's image consultant", "personal stylist for men", "wardrobe planning guide", 
                         "colour analysis service", "body shape analysis for men", "bespoke fashion advice", 
                         "style consultation benefits"],
                "weight": 1.4
            },
            "styling_guides": {
                "terms": ["men's style guide", "fashion tips for gentlemen", "dressing rules for men", 
                         "styling principles for body types", "fashion rules for professionals",
                         "wardrobe essentials for men", "must-have items for men", "styling secrets for men"],
                "weight": 1.6
            },
            "body_parts": {
                "terms": ["broad shoulders", "narrow waist", "muscular build", "round middle", 
                          "slim hips", "long torso", "short legs", "athletic chest"],
                "weight": 1.0  # Medium weight for body parts that need context
            },
            "clothing_items": {
                "terms": ["oxford shirt", "tailored blazer", "navy jacket", "chino trousers", "penny loafers", 
                         "cable knit", "tweed jacket", "linen suit", "camel coat", "silk tie"],
                "weight": 1.2  # Medium-high weight for clothing items 
            },
            # Very low priority generic terms - only use if nothing else matches
            "generic_terms": {
                "terms": ["style", "fashion", "look", "aesthetic", "classic", "traditional", 
                          "elegant", "sophisticated", "wardrobe", "outfit", "attire"],
                "weight": 0.3  # Even lower weight for generic terms without context
            }
        }

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
        # Split content into paragraphs
        paragraphs = self._split_into_paragraphs(content)

        # Extract main topics from content
        main_topics = self._extract_topics(content, title)

        # Find link opportunities
        opportunities = []

        for para_idx, paragraph in enumerate(paragraphs):
            if len(paragraph) < self.config.get("min_paragraph_length", 50):
                continue

            # Find opportunities for each target URL
            for target in target_urls:
                target_title = target.get("title", "")
                target_url = target.get("url", "")

                # Extract topics for the target
                target_topics = self._extract_topics("", target_title)

                # Calculate relevance
                relevance = self._calculate_relevance(paragraph, target_topics, target_title)

                # Skip if not relevant enough
                if relevance < 0.4:
                    continue

                # Find potential anchor text
                anchor_options = self._find_anchor_options(paragraph, target_topics, target_title)

                if anchor_options:
                    opportunities.append({
                        "paragraph_index": para_idx,
                        "paragraph": paragraph,
                        "target_url": target_url,
                        "target_title": target_title,
                        "relevance": relevance,
                        "anchor_options": anchor_options
                    })

        # Sort by relevance
        opportunities.sort(key=lambda x: x["relevance"], reverse=True)

        return opportunities

    def _split_into_paragraphs(self, content: str) -> List[str]:
        """Split content into paragraphs."""
        paragraphs = re.split(r'\n\n|\n', content)
        return [p.strip() for p in paragraphs if p.strip()]

    def _extract_topics(self, content: str, title: str) -> List[str]:
        """Extract main topics from content and title with priority on multi-word specifics."""
        topics = []
        topic_scores = {}  # Track topic scores for sorting
        content_lower = (content + " " + title).lower()

        # First, collect all matching topics with their category weights
        for category, data in self.topic_categories.items():
            for term in data["terms"]:
                if term.lower() in content_lower:
                    # Calculate a score based on:
                    # 1. Term length (longer terms are more specific)
                    # 2. Word count (multi-word terms are more specific)
                    # 3. Category weight (from topic_categories)
                    term_length_score = min(1.0, len(term) / 20)  # Normalize by max length
                    word_count = len(term.split())
                    word_count_score = min(1.0, word_count / 4)  # Normalize by max word count
                    
                    # Final score formula
                    score = (
                        data["weight"] * 0.5 +   # Category weight (50% influence)
                        word_count_score * 0.3 +  # Word count (30% influence)
                        term_length_score * 0.2   # Term length (20% influence)
                    )
                    
                    # Store with score for later sorting
                    topic_scores[term] = score
        
        # Sort topics by score (highest first)
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Take top 15 topics to ensure we have enough to work with
        topics = [term for term, score in sorted_topics[:15]]
        
        return topics

    def _calculate_relevance(self, paragraph: str, target_topics: List[str], target_title: str) -> float:
        """Calculate relevance between paragraph and target."""
        relevance = 0.0
        paragraph_lower = paragraph.lower()
        target_title_lower = target_title.lower()

        # Score direct topic matches based on specificity
        for topic in target_topics:
            if topic.lower() in paragraph_lower:
                # Base score
                score = 0.3
                
                # Bonus for multi-word topics (more specific)
                word_count = len(topic.split())
                if word_count >= 3:
                    score += 0.2
                elif word_count == 2:
                    score += 0.1
                
                # Check topic category and adjust based on category weight
                for category, data in self.topic_categories.items():
                    if topic.lower() in [t.lower() for t in data["terms"]]:
                        # Add bonus based on category weight
                        category_bonus = (data["weight"] - 0.5) * 0.2  # Normalize around 0.5
                        score += category_bonus
                        break
                
                relevance += score

        # Title phrase matches (prefer multi-word matches)
        title_phrases = []
        words = target_title_lower.split()
        for i in range(len(words)):
            for j in range(i+1, min(i+4, len(words)+1)):  # Consider phrases up to 3 words
                phrase = " ".join(words[i:j])
                if len(phrase) > 4:  # Only phrases with significant length
                    title_phrases.append(phrase)
        
        # Sort by length descending to prioritize longer phrases
        title_phrases.sort(key=len, reverse=True)
        
        # Check for phrase matches
        for phrase in title_phrases:
            if phrase in paragraph_lower:
                # Longer phrases get higher scores
                phrase_len_score = min(0.4, len(phrase) / 25)
                relevance += phrase_len_score
        
        return min(relevance, 1.0)

    def _find_anchor_options(self, paragraph: str, target_topics: List[str], target_title: str) -> List[Dict[str, Any]]:
        """Find potential anchor text options in the paragraph with focus on search intent phrases."""
        paragraph_lower = paragraph.lower()
        anchor_options = []
        seen_texts = set()  # Track lowercase versions to avoid duplicates

        # Group topics by word count, prioritizing longer phrases that likely contain search intent
        # 4+ words = complete search intent phrase; 2-3 words = partial intent; 1 word = specific term
        search_intent_phrases = [t for t in target_topics if len(t.split()) >= 4]
        partial_intent_phrases = [t for t in target_topics if len(t.split()) >= 2 and len(t.split()) < 4]
        specific_terms = [t for t in target_topics if len(t.split()) == 1 and len(t) >= 4]
        
        # Process topics in order of search intent priority
        for topic in search_intent_phrases + partial_intent_phrases + specific_terms:
            # Try to find exact match first
            pos = paragraph_lower.find(topic.lower())
            
            # If exact match not found, try to find a semantic match (if phrase is 3+ words)
            if pos < 0 and len(topic.split()) >= 3:
                # We'll use a more focused approach for finding natural anchor text
                # Following Google's guidelines for internal linking - concise, descriptive, natural phrases
                meaningful_words = [w for w in topic.lower().split() if len(w) > 3 and w not in ["for", "the", "and", "with"]]
                matching_words = [w for w in meaningful_words if w in paragraph_lower]
                
                # If we have enough matching words to identify the topic
                if len(matching_words) >= max(2, int(0.6 * len(meaningful_words))):
                    # Find keyword phrases in the paragraph that would make good anchor text
                    for word in sorted(matching_words, key=len, reverse=True):  # Start with longest keywords
                        word_pos = paragraph_lower.find(word)
                        if word_pos >= 0:
                            # Find natural phrase boundaries (2-4 words total)
                            # Get text around the keyword
                            text_around = paragraph[max(0, word_pos-30):min(len(paragraph), word_pos+30)]
                            
                            # Split into words while preserving positions
                            words_with_pos = []
                            for m in re.finditer(r'\b\w+\b', text_around):
                                words_with_pos.append((m.group(), m.start(), m.end()))
                            
                            # Find our keyword in this list
                            keyword_idx = next((i for i, (w, _, _) in enumerate(words_with_pos) 
                                              if word.lower() in w.lower()), -1)
                            
                            if keyword_idx >= 0:
                                # Try to build natural phrases of different lengths
                                for phrase_length in [2, 3, 4]:  # Prefer 2-4 word phrases (Google recommendation)
                                    # Get potential phrase (try different positions of the keyword in the phrase)
                                    for offset in range(min(phrase_length, keyword_idx + 1)):
                                        start_idx = max(0, keyword_idx - offset)
                                        end_idx = min(len(words_with_pos), start_idx + phrase_length)
                                        
                                        if end_idx - start_idx < 2:  # Need at least 2 words
                                            continue
                                        
                                        # Build the candidate phrase
                                        phrase_words = [w for w, _, _ in words_with_pos[start_idx:end_idx]]
                                        candidate_phrase = " ".join(phrase_words)
                                        
                                        # Check if this is a natural phrase (no partial sentences)
                                        if (len(candidate_phrase.split()) >= 2 and 
                                            not candidate_phrase.startswith("and ") and
                                            not candidate_phrase.startswith("or ") and
                                            not candidate_phrase.startswith("but ") and
                                            not candidate_phrase.startswith("that ") and
                                            not candidate_phrase.endswith(" and") and
                                            not candidate_phrase.endswith(" or") and
                                            not candidate_phrase.endswith(" but") and
                                            not candidate_phrase.endswith(" that")):
                                            
                                            # Find this exact phrase in the paragraph
                                            candidate_pos = paragraph.lower().find(candidate_phrase.lower())
                                            if candidate_pos >= 0:
                                                # We found a good, natural anchor text phrase
                                                topic = candidate_phrase
                                                pos = candidate_pos
                                                break  # Found a good phrase
                                    
                                    if pos >= 0:
                                        break  # Found a good phrase length
                                        
                            if pos >= 0:
                                break  # Found a good keyword
            
            # If we found a position (either exact or semantic match)
            if pos >= 0:
                # Extract with original capitalization
                exact_phrase = paragraph[pos:pos + len(topic)]
                lowercase_phrase = exact_phrase.lower()
                
                # Skip if we've already seen this phrase (case-insensitive comparison)
                if lowercase_phrase in seen_texts:
                    continue
                
                seen_texts.add(lowercase_phrase)
                
                # Extract context
                context = self._extract_context(paragraph, pos, len(topic))

                # Calculate confidence based on several factors
                confidence = 0.6
                word_count = len(exact_phrase.split())
                
                # Strongly prefer multi-word phrases with search intent
                if word_count >= 4:  # Complete search intent phrase
                    confidence += 0.3
                elif word_count == 3:  # Likely partial search intent
                    confidence += 0.25
                elif word_count == 2:  # Could be a specific concept
                    confidence += 0.2
                
                # Boost for phrases containing search intent indicators
                intent_indicators = ["how to", "guide", "for men", "men's", "styling", "fashion", "wardrobe"]
                for indicator in intent_indicators:
                    if indicator in lowercase_phrase:
                        confidence += 0.05
                        break
                
                # Check category and adjust based on weight
                for category, data in self.topic_categories.items():
                    for term in data["terms"]:
                        # More flexible matching for category terms
                        if (term.lower() in lowercase_phrase) or (lowercase_phrase in term.lower()):
                            # Adjust confidence based on category weight
                            category_bonus = (data["weight"] - 0.5) * 0.15  # Stronger influence
                            confidence = min(0.98, confidence + category_bonus)
                            break
                
                # Significant penalty for generic terms without context
                if lowercase_phrase in [t.lower() for t in self.topic_categories.get("generic_terms", {}).get("terms", [])]:
                    confidence -= 0.25  # Much stronger penalty
                
                # Apply Google's guidelines to validate anchor text
                # 1. Should be natural, descriptive text
                # 2. Should be concise (2-4 words ideal)
                # 3. Should avoid generic terms without context
                # 4. Should avoid partial sentences or grammatically incorrect phrases
                
                # Check if this is a valid anchor text according to Google guidelines
                word_count = len(exact_phrase.split())
                is_valid_anchor = (
                    # Length check (Google prefers 2-4 word anchor text)
                    (2 <= word_count <= 6) and
                    
                    # Avoid starting with articles, conjunctions, etc.
                    not exact_phrase.lower().startswith(("the ", "a ", "an ", "and ", "or ", "but ", "that ")) and
                    
                    # Avoid ending with articles, conjunctions, etc.
                    not exact_phrase.lower().endswith((" the", " a", " an", " and", " or", " but", " that")) and
                    
                    # Avoid partial phrases that break grammar
                    not any(exact_phrase.lower().endswith(f" {prep}") for prep in ["of", "in", "by", "with", "for", "on", "at"]) and
                    
                    # Ensure it's not just a generic single term
                    not (word_count == 1 and exact_phrase.lower() in [
                        "style", "fashion", "look", "colour", "color", "trend", "outfit",
                        "wardrobe", "clothing", "garment", "wear", "dress", "casual"
                    ])
                )
                
                # Only add valid anchor text options
                if is_valid_anchor:
                    anchor_options.append({
                        "text": exact_phrase,
                        "context": context,
                        "confidence": round(confidence, 2)
                    })

        # Sort by confidence, then by word count (prefer multi-word phrases)
        anchor_options.sort(key=lambda x: (x["confidence"], len(x["text"].split())), reverse=True)

        return anchor_options[:3]  # Return top 3

    def _extract_context(self, text: str, pos: int, length: int) -> str:
        """Extract context around an anchor text."""
        # Calculate context boundaries
        start = max(0, pos - 30)
        end = min(len(text), pos + length + 30)

        # Extract context
        context = text[start:end]

        # Highlight the anchor
        highlight_pos = pos - start
        highlighted = context[:highlight_pos] + "**" + context[highlight_pos:highlight_pos+length] + "**" + context[highlight_pos+length:]

        return highlighted