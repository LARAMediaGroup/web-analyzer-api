"""
Knowledge Database Module

This module provides a persistent storage mechanism for analyzed content,
allowing for effective internal linking suggestions between content items.
"""

import os
import json
import logging
import time
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import threading
import sqlite3
import hashlib

# Configure logging
logger = logging.getLogger("web_analyzer.knowledge_db")

class KnowledgeDatabase:
    """
    Manages a database of content knowledge for generating internal linking suggestions.
    
    This database stores analyzed content information including:
    - Content metadata (title, URL, etc.)
    - Extracted entities and topics
    - Relevance information for linking
    
    The database enables matching between content pieces for suggestion generation.
    """
    
    def __init__(self, config_path: str = "config.json", site_id: Optional[str] = None):
        """
        Initialize the knowledge database.
        
        Args:
            config_path: Path to the configuration file
            site_id: Optional site identifier for multi-site support
        """
        self.config = self._load_config(config_path)
        self.site_id = site_id or "default"
        
        # Set up database path
        self.db_dir = self.config.get("knowledge_db_dir", "data/knowledge_db")
        os.makedirs(self.db_dir, exist_ok=True)
        
        # Create site-specific database file
        self.db_path = os.path.join(self.db_dir, f"knowledge_{self.site_id}.db")
        
        # Initialize database
        self._init_database()
        
        # Thread lock for database operations
        self.db_lock = threading.Lock()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Config file {config_path} not found, using defaults")
                return {
                    "knowledge_db_dir": "data/knowledge_db",
                    "max_entries": 1000,
                    "cleanup_threshold": 0.9,  # Cleanup when 90% full
                }
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return {
                "knowledge_db_dir": "data/knowledge_db",
                "max_entries": 1000,
                "cleanup_threshold": 0.9,
            }
    
    def _init_database(self) -> None:
        """Initialize the SQLite database for content knowledge."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create content table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id TEXT UNIQUE,
                    title TEXT,
                    url TEXT,
                    hash TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
                ''')
                
                # Create entities table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id TEXT,
                    entity_type TEXT,
                    entity_value TEXT,
                    confidence REAL,
                    FOREIGN KEY (content_id) REFERENCES content(content_id)
                )
                ''')
                
                # Create topics table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id TEXT,
                    topic_type TEXT,
                    topic_value TEXT,
                    weight REAL,
                    FOREIGN KEY (content_id) REFERENCES content(content_id)
                )
                ''')
                
                # Create index on content_id for faster lookups
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_content_id ON entities(content_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_topics_content_id ON topics(content_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_type_value ON entities(entity_type, entity_value)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_topics_type_value ON topics(topic_type, topic_value)")
                
                conn.commit()
                logger.info(f"Knowledge database initialized at {self.db_path}")
        
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def add_content(self, content_data: Dict[str, Any]) -> bool:
        """
        Add or update content in the knowledge database.
        
        Args:
            content_data: Dictionary with content data including:
                - id: Content identifier
                - title: Content title
                - url: Content URL
                - entities: Dictionary of entity lists by type
                - topics: Dictionary of topic data
                
        Returns:
            bool: Success status
        """
        try:
            # Generate a unique hash for the content
            content_hash = self._generate_content_hash(content_data)
            
            with self.db_lock, sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                content_id = str(content_data.get("id", ""))
                title = content_data.get("title", "")
                url = content_data.get("url", "")
                now = datetime.now().isoformat()
                
                # Check if content already exists
                cursor.execute("SELECT hash FROM content WHERE content_id = ?", (content_id,))
                result = cursor.fetchone()
                
                if result:
                    existing_hash = result[0]
                    # If hash is the same, skip update
                    if existing_hash == content_hash:
                        logger.debug(f"Content {content_id} already exists with same hash")
                        return True
                    
                    # Update content record
                    cursor.execute(
                        "UPDATE content SET title = ?, url = ?, hash = ?, updated_at = ? WHERE content_id = ?",
                        (title, url, content_hash, now, content_id)
                    )
                    
                    # Delete existing entity and topic data
                    cursor.execute("DELETE FROM entities WHERE content_id = ?", (content_id,))
                    cursor.execute("DELETE FROM topics WHERE content_id = ?", (content_id,))
                    
                else:
                    # Insert new content record
                    cursor.execute(
                        "INSERT INTO content (content_id, title, url, hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (content_id, title, url, content_hash, now, now)
                    )
                
                # Add entity data
                entities = content_data.get("entities", {})
                for entity_type, entity_list in entities.items():
                    for entity_value in entity_list:
                        # Handle if entity is dict with confidence or just a string
                        if isinstance(entity_value, dict):
                            value = entity_value.get("value", "")
                            confidence = entity_value.get("confidence", 1.0)
                        else:
                            value = entity_value
                            confidence = 1.0
                        
                        cursor.execute(
                            "INSERT INTO entities (content_id, entity_type, entity_value, confidence) VALUES (?, ?, ?, ?)",
                            (content_id, entity_type, value, confidence)
                        )
                
                # Add topic data
                topics = content_data.get("topics", {})
                for topic_type, topic_list in topics.items():
                    for topic_data in topic_list:
                        # Handle if topic is dict with weight or just a string
                        if isinstance(topic_data, dict):
                            value = topic_data.get("value", "")
                            weight = topic_data.get("weight", 1.0)
                        else:
                            value = topic_data
                            weight = 1.0
                        
                        cursor.execute(
                            "INSERT INTO topics (content_id, topic_type, topic_value, weight) VALUES (?, ?, ?, ?)",
                            (content_id, topic_type, value, weight)
                        )
                
                conn.commit()
                logger.info(f"Content {content_id} added to knowledge database")
                
                # Check if cleanup is needed
                self._check_cleanup_needed(cursor)
                
                return True
        
        except Exception as e:
            logger.error(f"Error adding content to knowledge database: {str(e)}")
            return False
    
    def remove_content(self, content_id: str) -> bool:
        """
        Remove content from the knowledge database.
        
        Args:
            content_id: The content identifier
            
        Returns:
            bool: Success status
        """
        try:
            with self.db_lock, sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete entity and topic data
                cursor.execute("DELETE FROM entities WHERE content_id = ?", (content_id,))
                cursor.execute("DELETE FROM topics WHERE content_id = ?", (content_id,))
                
                # Delete content record
                cursor.execute("DELETE FROM content WHERE content_id = ?", (content_id,))
                
                conn.commit()
                logger.info(f"Content {content_id} removed from knowledge database")
                return True
        
        except Exception as e:
            logger.error(f"Error removing content from knowledge database: {str(e)}")
            return False
    
    def find_related_content(
        self, 
        content_data: Dict[str, Any],
        max_results: int = 15,
        min_relevance: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Find related content based on entities and topics.
        
        Args:
            content_data: Dictionary with content data
            max_results: Maximum number of results to return
            min_relevance: Minimum relevance score (0-1)
            
        Returns:
            List of related content items with relevance scores
        """
        try:
            content_id = str(content_data.get("id", ""))
            entities = content_data.get("entities", {})
            topics = content_data.get("topics", {})
            
            # Prepare entity and topic values for matching
            entity_values = []
            for entity_list in entities.values():
                for entity in entity_list:
                    if isinstance(entity, dict):
                        entity_values.append(entity.get("value", ""))
                    else:
                        entity_values.append(entity)
            
            topic_values = []
            for topic_list in topics.values():
                for topic in topic_list:
                    if isinstance(topic, dict):
                        topic_values.append(topic.get("value", ""))
                    else:
                        topic_values.append(topic)
            
            with self.db_lock, sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get all content except current
                cursor.execute("SELECT content_id, title, url FROM content WHERE content_id != ?", (content_id,))
                all_content = cursor.fetchall()
                
                results = []
                
                for content in all_content:
                    other_id = content["content_id"]
                    
                    # Get entity matches
                    entity_score = 0.0
                    for entity_value in entity_values:
                        cursor.execute(
                            "SELECT COUNT(*) FROM entities WHERE content_id = ? AND entity_value = ?",
                            (other_id, entity_value)
                        )
                        match_count = cursor.fetchone()[0]
                        entity_score += 0.1 * min(match_count, 5)  # Cap at 0.5
                    
                    # Get topic matches
                    topic_score = 0.0
                    for topic_value in topic_values:
                        cursor.execute(
                            "SELECT COUNT(*) FROM topics WHERE content_id = ? AND topic_value = ?",
                            (other_id, topic_value)
                        )
                        match_count = cursor.fetchone()[0]
                        topic_score += 0.15 * min(match_count, 4)  # Cap at 0.6
                    
                    # Calculate total relevance
                    relevance = min(entity_score + topic_score, 1.0)
                    
                    # Only include if above minimum relevance
                    if relevance >= min_relevance:
                        results.append({
                            "content_id": other_id,
                            "title": content["title"],
                            "url": content["url"],
                            "relevance": relevance
                        })
                
                # Sort by relevance (highest first) and limit results
                results.sort(key=lambda x: x["relevance"], reverse=True)
                return results[:max_results]
        
        except Exception as e:
            logger.error(f"Error finding related content: {str(e)}")
            return []
    
    def get_all_content(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all content in the knowledge database.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of content items
        """
        try:
            with self.db_lock, sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT content_id, title, url FROM content ORDER BY updated_at DESC LIMIT ?",
                    (limit,)
                )
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "content_id": row["content_id"],
                        "title": row["title"],
                        "url": row["url"]
                    })
                
                return results
        
        except Exception as e:
            logger.error(f"Error getting all content: {str(e)}")
            return []
    
    def get_content_count(self) -> int:
        """
        Get the count of content items in the database.
        
        Returns:
            int: Count of content items
        """
        try:
            with self.db_lock, sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM content")
                return cursor.fetchone()[0]
        
        except Exception as e:
            logger.error(f"Error getting content count: {str(e)}")
            return 0
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge database.
        
        Returns:
            Dictionary with database statistics
        """
        try:
            with self.db_lock, sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get content count
                cursor.execute("SELECT COUNT(*) FROM content")
                content_count = cursor.fetchone()[0]
                
                # Get entity count
                cursor.execute("SELECT COUNT(*) FROM entities")
                entity_count = cursor.fetchone()[0]
                
                # Get topic count
                cursor.execute("SELECT COUNT(*) FROM topics")
                topic_count = cursor.fetchone()[0]
                
                # Get unique entities
                cursor.execute("SELECT COUNT(DISTINCT entity_value) FROM entities")
                unique_entities = cursor.fetchone()[0]
                
                # Get unique topics
                cursor.execute("SELECT COUNT(DISTINCT topic_value) FROM topics")
                unique_topics = cursor.fetchone()[0]
                
                # Get most recent update
                cursor.execute("SELECT MAX(updated_at) FROM content")
                last_update = cursor.fetchone()[0]
                
                return {
                    "content_count": content_count,
                    "entity_count": entity_count,
                    "topic_count": topic_count,
                    "unique_entities": unique_entities,
                    "unique_topics": unique_topics,
                    "last_update": last_update,
                    "database_size_kb": self._get_database_size() // 1024
                }
        
        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
            return {}
    
    def _generate_content_hash(self, content_data: Dict[str, Any]) -> str:
        """Generate a hash for the content data."""
        data_to_hash = {
            "title": content_data.get("title", ""),
            "entities": content_data.get("entities", {}),
            "topics": content_data.get("topics", {})
        }
        
        json_str = json.dumps(data_to_hash, sort_keys=True)
        return hashlib.md5(json_str.encode()).hexdigest()
    
    def _get_database_size(self) -> int:
        """Get the size of the database file in bytes."""
        try:
            if os.path.exists(self.db_path):
                return os.path.getsize(self.db_path)
            return 0
        except Exception:
            return 0
    
    def _check_cleanup_needed(self, cursor) -> None:
        """Check if database cleanup is needed and perform it if necessary."""
        try:
            # Get content count
            cursor.execute("SELECT COUNT(*) FROM content")
            content_count = cursor.fetchone()[0]
            
            # Check if we've exceeded threshold
            max_entries = self.config.get("max_entries", 1000)
            cleanup_threshold = self.config.get("cleanup_threshold", 0.9)
            threshold_count = int(max_entries * cleanup_threshold)
            
            if content_count > threshold_count:
                logger.info(f"Content count {content_count} exceeds threshold {threshold_count}, performing cleanup")
                self._perform_cleanup(cursor)
        
        except Exception as e:
            logger.error(f"Error checking cleanup need: {str(e)}")
    
    def _perform_cleanup(self, cursor) -> None:
        """Remove oldest content to keep database size manageable."""
        try:
            # Get content count
            cursor.execute("SELECT COUNT(*) FROM content")
            content_count = cursor.fetchone()[0]
            
            # Calculate how many to remove
            max_entries = self.config.get("max_entries", 1000)
            target_count = int(max_entries * 0.8)  # Remove enough to get down to 80%
            to_remove = content_count - target_count
            
            if to_remove <= 0:
                return
            
            # Get oldest content IDs
            cursor.execute(
                "SELECT content_id FROM content ORDER BY updated_at ASC LIMIT ?",
                (to_remove,)
            )
            
            # Remove each content item
            for row in cursor.fetchall():
                content_id = row[0]
                
                # Delete entity and topic data
                cursor.execute("DELETE FROM entities WHERE content_id = ?", (content_id,))
                cursor.execute("DELETE FROM topics WHERE content_id = ?", (content_id,))
                
                # Delete content record
                cursor.execute("DELETE FROM content WHERE content_id = ?", (content_id,))
            
            logger.info(f"Removed {to_remove} oldest content items from knowledge database")
        
        except Exception as e:
            logger.error(f"Error performing cleanup: {str(e)}")