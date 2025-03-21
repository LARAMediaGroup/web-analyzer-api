"""
Advanced Anchor Text Generator Module

This module generates high-quality anchor text that:
- Follows Google's guidelines
- Uses natural language boundaries
- Avoids grammatical issues
- Maximizes relevance and context
- Considers search intent phrases
"""

import re
import logging
import string
from typing import List, Dict, Any, Tuple, Set, Optional
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
import random

# Configure logging
logger = logging.getLogger("web_analyzer.anchor_text_generator")

class AnchorTextGenerator:
    """
    Advanced anchor text generator that creates high-quality, 
    contextually relevant anchor text for internal links.
    """
    
    def __init__(self):
        """Initialize the anchor text generator."""
        # Anchor text quality parameters
        self.min_anchor_length = 3  # Minimum characters
        self.max_anchor_length = 60  # Maximum characters
        self.min_words = 2  # Minimum words
        self.max_words = 6  # Maximum words
        
        # Phrases to avoid using as complete anchor text
        self.weak_phrases = {
            "click here", "read more", "learn more", "find out more", "discover",
            "check out", "see here", "view this", "this page", "full article",
            "details here", "more info", "click", "here", "link", "url", "website"
        }
        
        # Words to avoid starting anchor text with
        self.weak_starters = {
            "the", "a", "an", "and", "or", "but", "because", "since", "when", "by",
            "for", "with", "about", "against", "before", "after", "above", "below",
            "to", "of", "in", "on", "at", "from", "into", "during", "until", "while"
        }
        
        # Words to avoid ending anchor text with
        self.weak_endings = {
            "the", "a", "an", "and", "or", "but", "if", "with", "of", "to", "for",
            "in", "on", "at", "by", "about", "as", "into", "like", "through", "after", 
            "over", "between", "out", "against", "during", "without", "before", "under"
        }
        
        # Part-of-speech patterns that make good anchor text
        # Each pattern is a sequence of POS tags that forms a valid phrase
        self.good_pos_patterns = [
            # Adjective + Noun(s)
            ["JJ", "NN"],  # e.g., "blue shirt"
            ["JJ", "NNS"],  # e.g., "blue shirts"
            ["JJ", "JJ", "NN"],  # e.g., "light blue shirt"
            ["JJ", "NN", "NN"],  # e.g., "blue cotton shirt"
            
            # Noun phrases
            ["NN", "NN"],  # e.g., "cotton shirt"
            ["NN", "NNS"],  # e.g., "shirt collars"
            ["NN", "NN", "NN"],  # e.g., "oxford cotton shirt"
            
            # Verb + Noun phrases (imperative)
            ["VB", "DT", "NN"],  # e.g., "choose a shirt"
            ["VB", "JJ", "NNS"],  # e.g., "find blue shirts"
            ["VBG", "JJ", "NNS"],  # e.g., "choosing blue shirts"
            
            # Phrasal patterns
            ["NN", "IN", "NN"],  # e.g., "shirts for men"
            ["JJ", "NN", "IN", "NNS"],  # e.g., "blue shirts for men"
            ["NN", "NN", "IN", "NN"],  # e.g., "oxford shirts for men"
            
            # How to patterns
            ["WRB", "TO", "VB", "NNS"],  # e.g., "how to wear shirts"
            ["WRB", "TO", "VB", "JJ", "NNS"],  # e.g., "how to wear blue shirts"
        ]
    
    def generate_anchor_options(
        self, 
        text: str, 
        target_keywords: List[str], 
        target_title: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Generate a list of anchor text options from the given text.
        
        Args:
            text: Source text to extract anchor text from
            target_keywords: Keywords relevant to the target page
            target_title: Title of the target page (optional)
            
        Returns:
            List of dictionaries containing anchor text options with scores
        """
        # Basic validation
        if not text or not target_keywords:
            return []
        
        anchor_options = []
        
        # 1. Extract natural phrases from text
        natural_phrases = self._extract_natural_phrases(text, target_keywords)
        
        # 2. Generate search intent phrases
        intent_phrases = self._generate_intent_phrases(text, target_keywords, target_title)
        
        # 3. Extract keyword-matched phrases
        keyword_phrases = self._extract_keyword_phrases(text, target_keywords)
        
        # 4. Score all candidate phrases
        all_phrases = natural_phrases + intent_phrases + keyword_phrases
        scored_phrases = self._score_anchor_candidates(all_phrases, target_keywords, target_title)
        
        # 5. Filter and sort candidates
        filtered_options = self._filter_anchor_candidates(scored_phrases)
        
        # Format results
        for option in filtered_options:
            anchor_text = option["phrase"]
            score = option["score"]
            position = option.get("position", 0)
            
            # Extract context
            context = self._extract_context(text, anchor_text, position)
            
            anchor_options.append({
                "text": anchor_text,
                "context": context,
                "confidence": round(score, 2),
                "position": position
            })
        
        return anchor_options
    
    def _extract_natural_phrases(self, text: str, target_keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Extract natural language phrases from text.
        
        This uses POS tagging to identify phrases with structure that makes good anchor text.
        """
        natural_phrases = []
        
        try:
            # Tokenize text
            sentences = sent_tokenize(text)
            
            # Process each sentence
            for sent_idx, sentence in enumerate(sentences):
                # Tokenize and tag
                tokens = word_tokenize(sentence)
                tagged = pos_tag(tokens)
                
                # Find phrases matching our good patterns
                for i in range(len(tagged)):
                    for pattern in self.good_pos_patterns:
                        # Check if there's enough tokens left
                        if i + len(pattern) > len(tagged):
                            continue
                        
                        # Check if pattern matches
                        matches_pattern = True
                        for j, pos in enumerate(pattern):
                            # Allow some flexibility in POS matching
                            if not tagged[i+j][1].startswith(pos):
                                matches_pattern = False
                                break
                        
                        if matches_pattern:
                            # Extract phrase
                            phrase_tokens = [tagged[i+j][0] for j in range(len(pattern))]
                            phrase = " ".join(phrase_tokens)
                            
                            # Calculate position in original text
                            position = text.lower().find(phrase.lower())
                            
                            # Only include phrases that contain at least one target keyword
                            if any(keyword.lower() in phrase.lower() for keyword in target_keywords):
                                natural_phrases.append({
                                    "phrase": phrase,
                                    "type": "natural",
                                    "position": position if position != -1 else 0
                                })
        except Exception as e:
            logger.warning(f"Error extracting natural phrases: {str(e)}")
        
        return natural_phrases
    
    def _generate_intent_phrases(self, text: str, target_keywords: List[str], target_title: str) -> List[Dict[str, Any]]:
        """
        Generate search intent phrases that combine target keywords with intent modifiers.
        """
        intent_phrases = []
        
        # Intent modifiers
        prefixes = ["how to", "guide to", "tips for", "best way to"]
        suffixes = ["guide", "tips", "ideas", "for men", "for women", "tutorial", "basics"]
        
        # Extract main keywords (nouns) from target title
        title_keywords = []
        if target_title:
            try:
                title_tokens = word_tokenize(target_title)
                title_tagged = pos_tag(title_tokens)
                
                # Extract nouns from title
                title_keywords = [word for word, tag in title_tagged 
                                 if tag.startswith("NN") and len(word) > 3]
            except Exception as e:
                logger.warning(f"Error processing title: {str(e)}")
        
        # Combine all keywords
        all_keywords = target_keywords + title_keywords
        
        # Generate intent phrases by combining keywords with modifiers
        for keyword in all_keywords:
            # Create prefix + keyword phrases
            for prefix in prefixes:
                phrase = f"{prefix} {keyword}"
                # Check if it exists in the text
                position = text.lower().find(phrase.lower())
                if position != -1:
                    intent_phrases.append({
                        "phrase": phrase,
                        "type": "intent",
                        "position": position
                    })
            
            # Create keyword + suffix phrases
            for suffix in suffixes:
                phrase = f"{keyword} {suffix}"
                # Check if it exists in the text
                position = text.lower().find(phrase.lower())
                if position != -1:
                    intent_phrases.append({
                        "phrase": phrase,
                        "type": "intent",
                        "position": position
                    })
        
        return intent_phrases
    
    def _extract_keyword_phrases(self, text: str, target_keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Extract phrases containing target keywords with surrounding context.
        """
        keyword_phrases = []
        
        # Extract up to 3 words around each keyword
        for keyword in target_keywords:
            # Skip very short keywords
            if len(keyword) < 4:
                continue
                
            # Find all occurrences of the keyword
            keyword_lower = keyword.lower()
            text_lower = text.lower()
            
            start_pos = 0
            while start_pos < len(text_lower):
                pos = text_lower.find(keyword_lower, start_pos)
                if pos == -1:
                    break
                
                # Extract sentence containing the keyword
                sent_start = max(0, text_lower.rfind(".", 0, pos) + 1)
                sent_end = text_lower.find(".", pos)
                if sent_end == -1:
                    sent_end = len(text_lower)
                
                sentence = text[sent_start:sent_end].strip()
                
                # Tokenize sentence
                tokens = word_tokenize(sentence)
                
                # Find keyword in tokens
                keyword_tokens = word_tokenize(keyword)
                
                for i in range(len(tokens) - len(keyword_tokens) + 1):
                    if [t.lower() for t in tokens[i:i+len(keyword_tokens)]] == [t.lower() for t in keyword_tokens]:
                        # Extract up to 3 words before and after
                        start_idx = max(0, i - 3)
                        end_idx = min(len(tokens), i + len(keyword_tokens) + 3)
                        
                        phrase_tokens = tokens[start_idx:end_idx]
                        phrase = " ".join(phrase_tokens)
                        
                        # Clean up phrase (remove punctuation at edges)
                        phrase = phrase.strip(string.punctuation + " ")
                        
                        # Check if the phrase meets length requirements
                        if len(phrase.split()) >= self.min_words and len(phrase.split()) <= self.max_words:
                            keyword_phrases.append({
                                "phrase": phrase,
                                "type": "keyword",
                                "position": pos
                            })
                
                # Move to next occurrence
                start_pos = pos + len(keyword)
        
        return keyword_phrases
    
    def _score_anchor_candidates(
        self, 
        candidates: List[Dict[str, Any]], 
        target_keywords: List[str],
        target_title: str
    ) -> List[Dict[str, Any]]:
        """
        Score anchor text candidates based on quality and relevance.
        """
        scored_candidates = []
        
        # Check if candidates list is empty
        if not candidates:
            return []
        
        # Get title keywords
        title_words = word_tokenize(target_title.lower()) if target_title else []
        
        for candidate in candidates:
            phrase = candidate["phrase"]
            phrase_lower = phrase.lower()
            phrase_words = phrase_lower.split()
            
            # Start with base score based on type
            base_score = {
                "natural": 0.6,
                "intent": 0.8,
                "keyword": 0.5
            }.get(candidate["type"], 0.5)
            
            score = base_score
            
            # Adjust score based on various factors
            
            # 1. Keyword presence and density
            keyword_matches = sum(1 for keyword in target_keywords 
                                if keyword.lower() in phrase_lower)
            keyword_score = min(0.3, 0.1 * keyword_matches)
            score += keyword_score
            
            # 2. Phrase length
            word_count = len(phrase_words)
            if word_count < self.min_words:
                score -= 0.2
            elif word_count > self.max_words:
                score -= 0.1
            elif word_count == 2:
                score += 0.05
            elif 3 <= word_count <= 4:
                score += 0.1  # Ideal length
            
            # 3. Title word matches
            title_matches = sum(1 for word in title_words if word in phrase_words)
            title_score = min(0.2, 0.05 * title_matches)
            score += title_score
            
            # 4. Search intent indicators
            intent_phrases = ["how to", "guide", "tips", "tutorial", "for men", "for women"]
            if any(intent in phrase_lower for intent in intent_phrases):
                score += 0.15
            
            # 5. Weak phrase penalty
            if phrase_lower in self.weak_phrases:
                score -= 0.5
            
            # 6. Weak start/end penalty
            if phrase_words and phrase_words[0] in self.weak_starters:
                score -= 0.1
            if phrase_words and phrase_words[-1] in self.weak_endings:
                score -= 0.1
            
            # 7. Grammar/structure penalty for incomplete phrases
            if phrase_lower.startswith(tuple(self.weak_starters)) or \
               phrase_lower.endswith(tuple(self.weak_endings)):
                score -= 0.15
            
            # 8. Bonus for quotes or proper names
            if phrase.startswith('"') and phrase.endswith('"'):
                score += 0.05
            
            # Ensure score is within bounds
            score = max(0.0, min(1.0, score))
            
            # Add scored candidate to results
            scored_candidates.append({
                "phrase": phrase,
                "type": candidate["type"],
                "score": score,
                "position": candidate.get("position", 0)
            })
        
        return scored_candidates
    
    def _filter_anchor_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter and deduplicate anchor candidates.
        """
        # Remove duplicates (case-insensitive)
        seen_phrases = set()
        unique_candidates = []
        
        for candidate in candidates:
            phrase_lower = candidate["phrase"].lower()
            
            # Skip if already seen or too short/long
            if phrase_lower in seen_phrases or \
               len(candidate["phrase"]) < self.min_anchor_length or \
               len(candidate["phrase"]) > self.max_anchor_length:
                continue
            
            seen_phrases.add(phrase_lower)
            unique_candidates.append(candidate)
        
        # Sort by score (highest first)
        unique_candidates.sort(key=lambda x: x["score"], reverse=True)
        
        # Return top candidates
        return unique_candidates[:10]
    
    def _extract_context(self, text: str, anchor_text: str, position: int, context_length: int = 60) -> str:
        """
        Extract context around an anchor text.
        
        Args:
            text: The source text
            anchor_text: The anchor text to highlight
            position: The position of the anchor text in the source
            context_length: The total length of context to extract
            
        Returns:
            String with context and highlighted anchor text
        """
        # If position is invalid, try to find the anchor text
        if position <= 0:
            position = text.lower().find(anchor_text.lower())
            if position == -1:
                # Handle case where the anchor text isn't found
                return f"...{anchor_text}..."
        
        # Calculate context boundaries
        half_length = context_length // 2
        start = max(0, position - half_length)
        end = min(len(text), position + len(anchor_text) + half_length)
        
        # Extract context
        pre_context = text[start:position]
        post_context = text[position + len(anchor_text):end]
        
        # Add ellipsis if truncated
        if start > 0:
            pre_context = "..." + pre_context
        if end < len(text):
            post_context = post_context + "..."
        
        # Combine with highlighted anchor text
        context = f"{pre_context}**{anchor_text}**{post_context}"
        
        return context