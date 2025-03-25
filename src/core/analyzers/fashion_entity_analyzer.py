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

# Configure logging
logger = logging.getLogger("web_analyzer.fashion_entity_analyzer")

class FashionEntityAnalyzer:
    """
    Analyzer for fashion-specific entities in content.
    
    This class extracts fashion-specific entities from text using a combination
    of pattern matching, NLP techniques, and domain-specific knowledge.
    """
    
    def __init__(self):
        """Initialize the analyzer with fashion-specific entity patterns."""
        # Load entity dictionaries
        self.clothing_items = self._load_clothing_items()
        self.fashion_brands = self._load_fashion_brands()
        self.style_categories = self._load_style_categories()
        self.materials = self._load_materials()
        self.body_shapes = self._load_body_shapes()
        self.colours = self._load_colours()
        self.seasonal_terms = self._load_seasonal_terms()
        
        # Compile regex patterns
        self.clothing_pattern = self._compile_pattern(self.clothing_items)
        self.brand_pattern = self._compile_pattern(self.fashion_brands)
        self.style_pattern = self._compile_pattern(self.style_categories)
        self.material_pattern = self._compile_pattern(self.materials)
        self.body_shape_pattern = self._compile_pattern(self.body_shapes)
        self.colour_pattern = self._compile_pattern(self.colours)
        self.seasonal_pattern = self._compile_pattern(self.seasonal_terms)
    
    def _load_clothing_items(self) -> Set[str]:
        """Load dictionary of clothing items."""
        return {
            # Tops
            "oxford shirt", "dress shirt", "button-down shirt", "polo shirt", "t-shirt", "tee",
            "henley shirt", "sweater", "jumper", "cardigan", "pullover", "sweatshirt", "hoodie",
            "tank top", "vest", "waistcoat", "navy blazer", "sport coat", "suit jacket", "dinner jacket",
            "double breasted suit jacket", "single breasted suit jacket", "tweed jacket", "harrington jacket",
            "field jacket", "safari jacket", "gilet", "puffer vest",
            
            # Bottoms
            "khaki trousers", "dress trousers", "chinos", "preppy chinos", "jeans", "denim jeans",
            "corduroy trousers", "joggers", "sweatpants", "shorts", "bermuda shorts", "swim shorts",
            "formal trousers", "casual trousers", "pleated trousers", "flat front trousers",
            
            # Outerwear
            "overcoat", "topcoat", "trench coat", "raincoat", "mac", "parka", "anorak",
            "windbreaker", "peacoat", "duffle coat", "leather jacket", "bomber jacket", 
            "harrington jacket", "field jacket", "safari jacket", "gilet", "puffer vest",
            
            # Footwear
            "oxford shoes", "derby shoes", "brogues", "penny loafers", "boat shoes",
            "deck shoes", "driving shoes", "monk strap shoes", "chelsea boots", "desert boots",
            "chukka boots", "wingtip shoes", "moccasins", "sneakers", "trainers", "sandals",
            "espadrilles", "slippers", "dress shoes", "formal shoes", "casual shoes",
            
            # Accessories
            "necktie", "tie", "bow tie", "pocket square", "cufflinks", "tie bar", "tie clip",
            "belt", "suspenders", "braces", "watch", "scarf", "gloves", "hat", "cap", "beanie",
            "sunglasses", "wallet", "briefcase", "messenger bag", "backpack", "umbrella", "socks",
            
            # Full outfits
            "suit", "tuxedo", "dinner suit", "three-piece suit", "two-piece suit", "ensemble",
            "outfit", "look", "attire", "formal attire", "business attire", "casual attire"
        }
    
    def _load_fashion_brands(self) -> Set[str]:
        """Load dictionary of fashion brands."""
        return {
            # Luxury/high-end brands
            "ralph lauren", "polo ralph lauren", "brooks brothers", "j.press", "drakes",
            "barbour", "burberry", "lacoste", "hugo boss", "vineyard vines", "j.crew",
            "sperry", "loro piana", "brunello cucinelli", "zegna", "tom ford", "gucci",
            "prada", "louis vuitton", "hermes", "armani", "versace", "charles tyrwhitt",
            "thomas pink", "hackett london", "turnbull & asser", "brioni",
            
            # Old money associated brands
            "lululemon", "l.l.bean", "bean boots", "duck boots", "patagonia", "north face",
            "orvis", "filson", "pendleton", "woolrich", "hunter boots", "belstaff", 
            "gant", "johnston & murphy", "allen edmonds", "tricker's", "crockett & jones",
            "church's", "alden", "new balance", "keds", "sebago", "sperrys", "quoddy",
            
            # Fast fashion brands
            "uniqlo", "h&m", "zara", "massimo dutti", "mango", "topman", "cos", "arket",
            "gap", "banana republic", "old navy", "express", "asos", "everlane", "reiss",
            "sandro", "maje", "club monaco", "suitsupply"
        }
    
    def _load_style_categories(self) -> Set[str]:
        """Load dictionary of style categories."""
        return {
            # Traditional/conservative styles
            "old money style", "old money fashion", "ivy league style", "preppy style",
            "trad style", "traditional style", "conservative style", "classic style",
            "heritage style", "vintage style", "retro style", "smart style", "formal style",
            "business casual", "casual style", "smart casual", "business formal",
            "black tie", "white tie", "cocktail attire", "evening wear",
            
            # Regional styles
            "american traditional", "british style", "italian style", "french style",
            "scandinavian style", "japanese style", "korean style", "nautical style",
            "coastal style", "country style", "rural style", "urban style",
            "ivy style", "british countryside", "english country", "scottish highland",
            "italian sprezzatura", "parisian style", "riviera style", "mediterranean style",
            "alpine style", "cape cod style", "nantucket style", "hamptons style",
            "upper east side", "roppongi hills", "sloane ranger", "kensington style",
            "chelsea style", "mayfair style",
            
            # Contemporary styles
            "minimalist style", "capsule wardrobe", "streetwear", "athleisure",
            "techwear", "workwear", "utility style", "avant-garde", "contemporary style",
            "modern style", "clean-cut style", "smart style", "sharp style",
            "polished style", "refined style", "new money style", "luxury style",
            "high-end style", "punk style", "goth style", "boho chic", "bcbg style"
        }
    
    def _load_materials(self) -> Set[str]:
        """Load dictionary of clothing materials."""
        return {
            # Natural fibers
            "cotton", "pima cotton", "sea island cotton", "egyptian cotton", "supima",
            "wool", "merino wool", "lambswool", "shetland wool", "cashmere", "tweed",
            "houndstooth", "herringbone", "linen", "flax", "silk", "mohair", "alpaca",
            "camel hair", "vicuña", "leather", "suede", "nubuck", "calfskin", "cordovan",
            "sheepskin", "deerskin", "pigskin", "sharkskin", "alligator", "crocodile", 
            
            # Synthetic and mixed fibers
            "polyester", "nylon", "acrylic", "rayon", "viscose", "tencel", "lycra", 
            "spandex", "elastane", "gore-tex", "performance fabric", "tech fabric",
            "microfiber", "fleece", "down", "goose down", "duck down", "synthetic down",
            
            # Weaves and treatments
            "oxford cloth", "broadcloth", "poplin", "twill", "pinpoint", "chambray",
            "denim", "seersucker", "corduroy", "madras", "flannel", "gabardine", "canvas",
            "velvet", "velour", "waxed", "weatherproof", "waterproof", "breathable"
        }
    
    def _load_body_shapes(self) -> Set[str]:
        """Load dictionary of body shapes."""
        return {
            # Male body shapes
            "triangle body shape", "triangle shape", "pear shape", "inverted triangle", 
            "inverted triangle body shape", "v-shape", "athletic", "athletic build",
            "rectangle", "rectangle body shape", "straight", "oval", "oval body shape",
            "round", "apple shape", "apple body shape", "trapezoid", "trapezoid body shape",
            
            # Body features
            "broad shoulders", "narrow shoulders", "muscular chest", "muscular build",
            "slim waist", "narrow waist", "wide waist", "full waist", "slim hips",
            "narrow hips", "wide hips", "full hips", "short legs", "long legs",
            "slim legs", "muscular legs", "long torso", "short torso"
        }
    
    def _load_colours(self) -> Set[str]:
        """Load dictionary of colours and colour palettes."""
        return {
            # Basic colours
            "navy", "navy blue", "blue", "light blue", "sky blue", "cobalt blue", "royal blue",
            "white", "off-white", "cream", "ivory", "eggshell", "grey", "gray", "charcoal", 
            "silver", "black", "red", "burgundy", "maroon", "green", "olive", "forest green",
            "khaki", "beige", "tan", "brown", "chocolate brown", "camel", "pink", "purple",
            "lavender", "orange", "coral", "yellow", "gold", "mustard",
            
            # Seasonal colour analysis terms
            "spring colours", "summer colours", "autumn colours", "winter colours", 
            "warm colours", "cool colours", "clear colours", "muted colours", "deep colours",
            "light colours", "dark colours", "bright colours", "soft colours", "neutral colours",
            "earthy colours", "pastel colours", "jewel tones", "monochrome", "tonal",
            
            # Specific seasonal palettes
            "true spring", "light spring", "bright spring", "warm spring", 
            "true summer", "light summer", "soft summer", "cool summer",
            "true autumn", "soft autumn", "deep autumn", "warm autumn",
            "true winter", "deep winter", "clear winter", "cool winter",
            
            # Old money colours
            "old money colours", "heritage colours", "traditional colours", "preppy colours",
            "ivy league colours", "collegiate colours", "nautical colours"
        }
    
    def _load_seasonal_terms(self) -> Set[str]:
        """Load dictionary of seasonal references."""
        return {
            # Seasons
            "spring", "summer", "autumn", "fall", "winter", "seasonal", "year-round",
            "trans-seasonal", "resort", "vacation", "holiday", 
            
            # Weather conditions
            "warm weather", "cold weather", "hot weather", "cool weather", "rainy", 
            "wet weather", "sunny", "windy", "humid", "dry", "temperate", 
            
            # Seasonal activities
            "beach", "coastal", "skiing", "winter sports", "summer sports", "outdoor",
            "indoor", "layering", "temperature regulation", "weather-appropriate"
        }
    
    def _compile_pattern(self, terms: Set[str]) -> re.Pattern:
        """Compile regex pattern from a set of terms."""
        # Sort by length (longest first) to ensure we match the longest terms
        sorted_terms = sorted(terms, key=len, reverse=True)
        # Escape special regex characters and join with OR
        pattern_string = "|".join(re.escape(term) for term in sorted_terms)
        # Compile pattern with word boundaries and case insensitivity
        return re.compile(r'\b(' + pattern_string + r')\b', re.IGNORECASE)
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract fashion entities from text.
        
        Args:
            text (str): The text to analyze
            
        Returns:
            Dict[str, List[str]]: Dictionary of entity types and extracted entities
        """
        # Basic data validation
        if not text or not isinstance(text, str):
            return {
                "clothing_items": [],
                "brands": [],
                "styles": [],
                "materials": [],
                "body_shapes": [],
                "colours": [],
                "seasonal": []
            }
        
        # Find all matches using regex patterns
        clothing_matches = self._find_matches(self.clothing_pattern, text)
        brand_matches = self._find_matches(self.brand_pattern, text)
        style_matches = self._find_matches(self.style_pattern, text)
        material_matches = self._find_matches(self.material_pattern, text)
        body_shape_matches = self._find_matches(self.body_shape_pattern, text)
        colour_matches = self._find_matches(self.colour_pattern, text)
        seasonal_matches = self._find_matches(self.seasonal_pattern, text)
        
        # Look for compound terms using NLP
        compound_terms = self._extract_compound_terms(text)
        
        # Add compound terms to appropriate categories
        for term in compound_terms:
            term_lower = term.lower()
            
            # Check if the term contains known entities
            if any(item in term_lower for item in self.clothing_items):
                clothing_matches.append(term)
            elif any(brand in term_lower for brand in self.fashion_brands):
                brand_matches.append(term)
            elif any(style in term_lower for style in self.style_categories):
                style_matches.append(term)
            elif any(material in term_lower for material in self.materials):
                material_matches.append(term)
            elif any(shape in term_lower for shape in self.body_shapes):
                body_shape_matches.append(term)
            elif any(colour in term_lower for colour in self.colours):
                colour_matches.append(term)
            elif any(season in term_lower for season in self.seasonal_terms):
                seasonal_matches.append(term)
        
        # Return all extracted entities
        return {
            "clothing_items": clothing_matches,
            "brands": brand_matches,
            "styles": style_matches,
            "materials": material_matches,
            "body_shapes": body_shape_matches,
            "colours": colour_matches,
            "seasonal": seasonal_matches
        }
    
    def _find_matches(self, pattern: re.Pattern, text: str) -> List[str]:
        """Find all matches using a regex pattern."""
        matches = pattern.findall(text)
        # Remove duplicates while preserving order
        seen = set()
        return [x for x in matches if not (x.lower() in seen or seen.add(x.lower()))]
    
    def _extract_compound_terms(self, text: str) -> List[str]:
        """
        Extract compound fashion terms using NLP techniques.
        
        This looks for phrases like "navy blue oxford shirt" that combine
        colour + material + clothing item.
        """
        compound_terms = []
        
        try:
            # Tokenize and tag parts of speech
            tokens = word_tokenize(text)
            tagged = pos_tag(tokens)
            
            # Look for noun phrases
            i = 0
            while i < len(tagged):
                # If we find an adjective, look for a sequence of adjectives and nouns
                if tagged[i][1].startswith('JJ'):
                    start = i
                    while i < len(tagged) and (tagged[i][1].startswith('JJ') or 
                                              tagged[i][1].startswith('NN') or 
                                              tagged[i][1] == 'IN' or  # Include prepositions
                                              tagged[i][1] == 'CC'):  # Include conjunctions
                        i += 1
                    
                    # If the phrase is at least 2 words and ends with a noun
                    if i - start >= 2 and tagged[i-1][1].startswith('NN'):
                        phrase = ' '.join(tokens[start:i])
                        
                        # Only include if it contains a fashion-related term
                        fashion_related = any(
                            term in phrase.lower() for term_set in 
                            [self.clothing_items, self.materials, self.fashion_brands, 
                             self.style_categories, self.colours]
                            for term in term_set
                        )
                        
                        if fashion_related:
                            compound_terms.append(phrase)
                    continue
                
                i += 1
        except Exception as e:
            logger.warning(f"Error in NLP processing: {str(e)}")
        
        return compound_terms
    
    def analyze_content(self, content: str, title: str = "") -> Dict[str, Any]:
        """
        Analyze content and extract all fashion entities.
        
        Args:
            content (str): The main content to analyze
            title (str): Optional title to include in analysis
            
        Returns:
            Dict[str, Any]: Comprehensive analysis results
        """
        # Combine title and content with higher weight for title
        full_text = f"{title} {title} {content}" if title else content
        
        # Extract entities from the full text
        entities = self.extract_entities(full_text)
        
        # Calculate entity frequencies and importance
        entity_scores = self._calculate_entity_scores(entities, content, title)
        
        # Identify primary and secondary themes
        themes = self._identify_themes(entities, entity_scores)
        
        # Build final analysis result
        return {
            "entities": entities,
            "entity_scores": entity_scores,
            "themes": themes,
            "primary_theme": themes[0] if themes else None,
            "entity_count": sum(len(entities[key]) for key in entities)
        }
    
    def _calculate_entity_scores(
        self, 
        entities: Dict[str, List[str]], 
        content: str, 
        title: str
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate importance scores for each entity.
        
        Args:
            entities: Dictionary of extracted entities
            content: The content text
            title: The title text
            
        Returns:
            Dictionary of entity types with scores for each entity
        """
        entity_scores = {}
        content_lower = content.lower()
        title_lower = title.lower()
        
        # Calculate scores for each entity type
        for entity_type, entity_list in entities.items():
            entity_scores[entity_type] = {}
            
            for entity in entity_list:
                entity_lower = entity.lower()
                
                # Base score 
                score = 1.0
                
                # Boost for presence in title
                if entity_lower in title_lower:
                    score += 2.0
                
                # Boost for frequency in content
                frequency = content_lower.count(entity_lower)
                score += min(frequency / 5, 1.0)  # Cap at 1.0 additional points
                
                # Boost for entity length (multi-word entities are more specific)
                word_count = len(entity_lower.split())
                score += min(word_count / 3, 1.0)  # Cap at 1.0 additional points
                
                # Type-specific boosts
                if entity_type == "styles" and entity_lower in title_lower:
                    score += 1.0  # Style in title is very important
                elif entity_type == "body_shapes" and entity_lower in title_lower:
                    score += 1.5  # Body shape in title is extremely important
                
                entity_scores[entity_type][entity] = round(score, 2)
        
        return entity_scores
    
    def _identify_themes(
        self, 
        entities: Dict[str, List[str]], 
        entity_scores: Dict[str, Dict[str, float]]
    ) -> List[str]:
        """
        Identify primary and secondary themes from the entities.
        
        Args:
            entities: Dictionary of extracted entities
            entity_scores: Dictionary of entity scores
            
        Returns:
            List of identified themes, in order of importance
        """
        # Flatten all entities with their scores into a single list
        all_entities = []
        for entity_type, entities_dict in entity_scores.items():
            for entity, score in entities_dict.items():
                all_entities.append((entity, entity_type, score))
        
        # Sort by score (highest first)
        all_entities.sort(key=lambda x: x[2], reverse=True)
        
        # Take top entities as themes (up to 5)
        themes = [entity[0] for entity in all_entities[:5]]
        
        return themes
    
    def _analyze_fashion_entities(self, text: str) -> Dict[str, List[str]]:
        """Analyze fashion entities with improved context handling."""
        # Initialize results
        results = {
            "clothing_items": [],
            "brands": [],
            "styles": [],
            "materials": [],
            "body_shapes": [],
            "colours": [],
            "seasonal": []
        }
        
        # Find compound terms and their relationships
        compound_patterns = {
            "clothing_items": [
                r'\b(?:navy|khaki|oxford)\s+(?:blazer|trousers|shirt|suit)\b',
                r'\b(?:penny|cable-knit)\s+(?:loafers|sweaters)\b',
                r'\b(?:well-tailored|double-breasted)\s+(?:pieces|suit)\b'
            ],
            "styles": [
                r'\b(?:old money|ivy league|prep school)\s+(?:fashion|style)\b',
                r'\b(?:timeless|classic|luxury|understated)\s+(?:elegance|style|fashion)\b'
            ],
            "colours": [
                r'\b(?:navy|khaki)\s+(?:blazer|trousers|suit)\b'
            ]
        }
        
        # Extract compound terms
        for category, patterns in compound_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    term = match.group()
                    if category == "colours":
                        # For colors, extract just the color name
                        color = term.split()[0]
                        if color not in results["colours"]:
                            results["colours"].append(color)
                    else:
                        # For other categories, add the full compound term
                        if term not in results[category]:
                            results[category].append(term)
        
        # Look for context around each compound term
        for category, terms in results.items():
            if category in ["clothing_items", "styles"]:
                for term in terms:
                    context = self._get_context_around_term(text, term)
                    if context:
                        # Add any additional attributes found in context
                        self._extract_attributes_from_context(context, results)
        
        return results
    
    def _get_context_around_term(self, text: str, term: str, window: int = 5) -> Optional[str]:
        """Get context around a specific term."""
        words = text.split()
        try:
            idx = words.index(term.split()[0])
            start = max(0, idx - window)
            end = min(len(words), idx + len(term.split()) + window)
            return " ".join(words[start:end])
        except ValueError:
            return None
    
    def _extract_attributes_from_context(self, context: str, results: Dict[str, List[str]]) -> None:
        """Extract additional attributes from context around a term."""
        # Look for material attributes
        material_patterns = [
            r'\b(?:cable-knit|wool|cotton|silk|linen)\b'
        ]
        for pattern in material_patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                material = match.group()
                if material not in results["materials"]:
                    results["materials"].append(material)
        
        # Look for quality attributes
        quality_patterns = [
            r'\b(?:well-tailored|quality|luxury|timeless)\b'
        ]
        for pattern in quality_patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                quality = match.group()
                if quality not in results["materials"]:  # Store quality attributes in materials for now
                    results["materials"].append(quality)