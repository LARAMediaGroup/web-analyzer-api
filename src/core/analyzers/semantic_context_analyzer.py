"""
Semantic Context Analyzer Module

This module analyzes the semantic context of content to understand:
- Primary topic and subtopics
- Content structure and hierarchy
- Relevance between paragraphs
- Semantic similarity between texts
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Set
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag
import numpy as np
from collections import Counter

# Configure logging
logger = logging.getLogger("web_analyzer.semantic_context_analyzer")

class SemanticContextAnalyzer:
    """
    Analyzer for understanding semantic context of content.
    
    This class analyzes the semantic structure of text, identifying topics,
    subtopics, and the relationships between different parts of the content.
    """
    
    def __init__(self):
        """Initialize the semantic context analyzer."""
        # Initialize NLTK components
        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            nltk.download('stopwords')
            self.stop_words = set(stopwords.words('english'))
            
        try:
            self.lemmatizer = WordNetLemmatizer()
        except LookupError:
            nltk.download('wordnet')
            self.lemmatizer = WordNetLemmatizer()
        
        # Extended stop words for fashion context
        self.fashion_stop_words = {
            "wear", "wearing", "wore", "worn", "looks", "looking", 
            "style", "styled", "styling", "fashion", "fashionable",
            "dress", "dressed", "dressing", "outfit", "outfits",
            "clothes", "clothing", "garment", "garments", "item", "items",
            "piece", "pieces", "accessory", "accessories", "collection",
            "look", "trend", "trendy", "choose", "choosing", "chose",
            "makes", "making", "made", "want", "wants", "wanted",
            "need", "needs", "needed", "like", "likes", "liked",
            "good", "great", "best", "better", "nice", "perfect",
            "way", "ways", "thing", "things"
        }
        
        # Combine stop words
        self.stop_words.update(self.fashion_stop_words)
        
        # Topic transition phrases
        self.transition_phrases = {
            "another important aspect", "additionally", "furthermore",
            "moreover", "in addition", "also", "besides", "apart from",
            "on the other hand", "conversely", "however", "but", "yet",
            "nevertheless", "nonetheless", "still", "instead", "rather",
            "consequently", "as a result", "therefore", "thus", "hence",
            "for this reason", "because of this", "first", "firstly",
            "second", "secondly", "third", "thirdly", "finally", "lastly",
            "to conclude", "in conclusion", "to sum up", "in summary"
        }
    
    def analyze_content(self, content: str, title: str = "") -> Dict[str, Any]:
        """
        Analyze the semantic context of content.
        
        Args:
            content (str): The content to analyze
            title (str): Optional title to include in analysis
            
        Returns:
            Dict[str, Any]: Analysis results including topics and structure
        """
        # Basic data validation
        if not content or not isinstance(content, str):
            return {
                "primary_topic": None,
                "subtopics": [],
                "structure": {},
                "keyword_density": {},
                "paragraph_relevance": {}
            }
        
        # Preprocess content
        preprocessed_content = self._preprocess_text(content)
        
        # Split into paragraphs
        paragraphs = self._split_into_paragraphs(content)
        preprocessed_paragraphs = [self._preprocess_text(p) for p in paragraphs]
        
        # Extract topics
        primary_topic, subtopics = self._extract_topics(preprocessed_content, title)
        
        # Analyze paragraph structure and relationships
        paragraph_topics = self._analyze_paragraph_topics(preprocessed_paragraphs)
        
        # Calculate keyword density
        keyword_density = self._calculate_keyword_density(preprocessed_content)
        
        # Calculate relevance between paragraphs
        paragraph_relevance = self._calculate_paragraph_relevance(preprocessed_paragraphs)
        
        # Identify content structure
        structure = self._identify_content_structure(paragraphs, paragraph_topics)
        
        # Build final analysis
        return {
            "primary_topic": primary_topic,
            "subtopics": subtopics,
            "structure": structure,
            "keyword_density": keyword_density,
            "paragraph_relevance": paragraph_relevance,
            "paragraph_topics": paragraph_topics
        }
    
    def _preprocess_text(self, text: str) -> List[str]:
        """
        Preprocess text for analysis.
        
        Args:
            text (str): Text to preprocess
            
        Returns:
            List[str]: List of preprocessed tokens
        """
        # Convert to lowercase
        text = text.lower()
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stop words and short words
        tokens = [t for t in tokens if t not in self.stop_words and len(t) > 2]
        
        # Remove non-alphabetic tokens
        tokens = [t for t in tokens if t.isalpha()]
        
        # Lemmatize
        tokens = [self.lemmatizer.lemmatize(t) for t in tokens]
        
        return tokens
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split by double newlines or single newlines
        paragraphs = re.split(r'\n\n|\n', text)
        
        # Remove empty paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def _extract_topics(
        self, 
        preprocessed_text: List[str], 
        title: str = ""
    ) -> Tuple[str, List[str]]:
        """
        Extract primary topic and subtopics from preprocessed text.
        
        Args:
            preprocessed_text: List of preprocessed tokens
            title: Optional title to aid topic extraction
            
        Returns:
            Tuple of primary topic and list of subtopics
        """
        # Get word frequencies
        word_freq = Counter(preprocessed_text)
        
        # Extract most common words as topic candidates
        most_common = word_freq.most_common(20)
        
        # If title is provided, use it to identify the primary topic
        primary_topic = None
        if title:
            # Preprocess title
            title_tokens = self._preprocess_text(title)
            
            # Find the most frequent word from the title in the content
            title_words_in_content = [w for w in title_tokens if w in word_freq]
            
            if title_words_in_content:
                # Sort by frequency in content
                title_words_in_content.sort(key=lambda w: word_freq[w], reverse=True)
                primary_topic = title_words_in_content[0]
        
        # If no primary topic from title, use most frequent word
        if not primary_topic and most_common:
            primary_topic = most_common[0][0]
        
        # Extract subtopics (excluding primary topic)
        subtopics = [word for word, _ in most_common if word != primary_topic][:5]
        
        return primary_topic, subtopics
    
    def _analyze_paragraph_topics(self, preprocessed_paragraphs: List[List[str]]) -> List[Dict[str, Any]]:
        """
        Analyze the topic of each paragraph.
        
        Args:
            preprocessed_paragraphs: List of preprocessed paragraph tokens
            
        Returns:
            List of dictionaries with paragraph topic information
        """
        paragraph_topics = []
        
        for i, para_tokens in enumerate(preprocessed_paragraphs):
            if not para_tokens:
                paragraph_topics.append({
                    "paragraph_index": i,
                    "main_topic": None,
                    "keywords": []
                })
                continue
            
            # Get word frequencies for this paragraph
            word_freq = Counter(para_tokens)
            
            # Extract most common words as keywords
            most_common = word_freq.most_common(5)
            keywords = [word for word, _ in most_common]
            
            # Main topic is the most frequent keyword
            main_topic = keywords[0] if keywords else None
            
            paragraph_topics.append({
                "paragraph_index": i,
                "main_topic": main_topic,
                "keywords": keywords
            })
        
        return paragraph_topics
    
    def _calculate_keyword_density(self, preprocessed_text: List[str]) -> Dict[str, float]:
        """
        Calculate keyword density in the content.
        
        Args:
            preprocessed_text: List of preprocessed tokens
            
        Returns:
            Dictionary of keywords and their density percentages
        """
        # Get word frequencies
        word_freq = Counter(preprocessed_text)
        
        # Calculate total word count
        total_words = len(preprocessed_text)
        
        # Calculate density for top keywords
        density = {}
        top_keywords = word_freq.most_common(20)
        
        for word, count in top_keywords:
            density[word] = round((count / total_words) * 100, 2) if total_words > 0 else 0
        
        return density
    
    def _calculate_paragraph_relevance(self, preprocessed_paragraphs: List[List[str]]) -> Dict[str, List[int]]:
        """
        Calculate relevance between paragraphs.
        
        Args:
            preprocessed_paragraphs: List of preprocessed paragraph tokens
            
        Returns:
            Dictionary of paragraph indices and their related paragraphs
        """
        num_paragraphs = len(preprocessed_paragraphs)
        relevance = {}
        
        # Create sets of unique words for each paragraph
        paragraph_sets = [set(tokens) for tokens in preprocessed_paragraphs]
        
        # Calculate Jaccard similarity between paragraphs
        for i in range(num_paragraphs):
            related_paragraphs = []
            
            for j in range(num_paragraphs):
                if i == j:
                    continue
                
                # Jaccard similarity = size of intersection / size of union
                intersection = len(paragraph_sets[i] & paragraph_sets[j])
                union = len(paragraph_sets[i] | paragraph_sets[j])
                
                similarity = intersection / union if union > 0 else 0
                
                # Consider paragraphs with similarity > 0.2 as related
                if similarity > 0.2:
                    related_paragraphs.append(j)
            
            relevance[str(i)] = related_paragraphs
        
        return relevance
    
    def _identify_content_structure(
        self, 
        paragraphs: List[str], 
        paragraph_topics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Identify the structure of the content.
        
        Args:
            paragraphs: List of paragraphs
            paragraph_topics: List of paragraph topic dictionaries
            
        Returns:
            Dictionary describing the content structure
        """
        # Initialize structure
        structure = {
            "introduction": None,
            "body": [],
            "conclusion": None,
            "sections": []
        }
        
        num_paragraphs = len(paragraphs)
        
        # Analyze first paragraph as potential introduction
        if num_paragraphs > 0:
            intro_markers = ["introduction", "introduce", "begin", "start", "first"]
            if any(marker in paragraphs[0].lower() for marker in intro_markers) or len(paragraphs[0]) < 300:
                structure["introduction"] = 0
        
        # Analyze last paragraph as potential conclusion
        if num_paragraphs > 1:
            conclusion_markers = ["conclusion", "conclude", "finally", "summary", "summing up", "to sum up", "in summary"]
            if any(marker in paragraphs[-1].lower() for marker in conclusion_markers) or len(paragraphs[-1]) < 300:
                structure["conclusion"] = num_paragraphs - 1
        
        # Identify body paragraphs
        body_start = 1 if structure["introduction"] is not None else 0
        body_end = num_paragraphs - 1 if structure["conclusion"] is not None else num_paragraphs
        
        structure["body"] = list(range(body_start, body_end))
        
        # Identify sections by looking for topic transitions
        current_section = {"start": body_start, "topic": None, "paragraphs": []}
        current_topic = None
        
        for i in range(body_start, body_end):
            para = paragraphs[i].lower()
            topics = paragraph_topics[i]
            
            # Check for section transitions
            is_transition = False
            
            # Check for transition phrases
            if any(phrase in para for phrase in self.transition_phrases):
                is_transition = True
            
            # Check for topic change
            if topics["main_topic"] != current_topic and current_topic is not None:
                is_transition = True
            
            # If this is a transition, close the current section and start a new one
            if is_transition and i > body_start:
                current_section["end"] = i - 1
                structure["sections"].append(current_section)
                
                current_section = {
                    "start": i, 
                    "topic": topics["main_topic"],
                    "paragraphs": []
                }
            
            # Update current topic and add paragraph to current section
            current_topic = topics["main_topic"]
            current_section["paragraphs"].append(i)
        
        # Add the last section
        if current_section["paragraphs"]:
            current_section["end"] = body_end - 1
            structure["sections"].append(current_section)
        
        return structure
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Float similarity score between 0 and 1
        """
        # Preprocess both texts
        tokens1 = self._preprocess_text(text1)
        tokens2 = self._preprocess_text(text2)
        
        # Create sets of unique tokens
        set1 = set(tokens1)
        set2 = set(tokens2)
        
        # Calculate Jaccard similarity
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        similarity = intersection / union if union > 0 else 0
        
        return similarity
    
    def find_relevant_paragraphs(
        self, 
        paragraphs: List[str], 
        query: str, 
        top_n: int = 3
    ) -> List[Tuple[int, float]]:
        """
        Find paragraphs most relevant to a query.
        
        Args:
            paragraphs: List of paragraphs
            query: Query text
            top_n: Number of top relevant paragraphs to return
            
        Returns:
            List of tuples with paragraph index and similarity score
        """
        # Preprocess query
        query_tokens = self._preprocess_text(query)
        query_set = set(query_tokens)
        
        # Calculate relevance for each paragraph
        relevance_scores = []
        
        for i, para in enumerate(paragraphs):
            # Preprocess paragraph
            para_tokens = self._preprocess_text(para)
            para_set = set(para_tokens)
            
            # Calculate Jaccard similarity
            intersection = len(query_set & para_set)
            union = len(query_set | para_set)
            
            similarity = intersection / union if union > 0 else 0
            
            relevance_scores.append((i, similarity))
        
        # Sort by similarity score (descending)
        relevance_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N most relevant paragraphs
        return relevance_scores[:top_n]