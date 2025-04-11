"""
Knowledge Database Module

This module provides a persistent storage mechanism for analyzed content,
allowing for effective internal linking suggestions between content items.
"""

import os
import json
import logging
import time
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
import threading
import sqlite3
import hashlib
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pickle # Import pickle for embedding serialization

# Configure logging
logger = logging.getLogger("web_analyzer.knowledge_db")

# --- Model Loading ---
# Load the sentence transformer model globally once when the class is loaded.
# Choose a model suitable for semantic search (e.g., all-MiniLM-L6-v2 is fast and good)
# Wrap in a try-except block in case model loading fails on import.
try:
    # Define model name (can be made configurable later if needed)
    MODEL_NAME = 'all-MiniLM-L6-v2'
    logger.info(f"Loading sentence transformer model: {MODEL_NAME}...")
    global_embedding_model = SentenceTransformer(MODEL_NAME) # Use a distinct global name
    logger.info(f"Sentence transformer model '{MODEL_NAME}' loaded successfully.")
except Exception as e:
    logger.error(f"CRITICAL: Failed to load sentence transformer model '{MODEL_NAME}'. Embeddings will not be generated. Error: {e}", exc_info=True)
    global_embedding_model = None # Set model to None if loading fails

# Helper function (can be outside class or static method)
def _calculate_cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """Calculates cosine similarity between two numpy embedding vectors."""
    if embedding1 is None or embedding2 is None or embedding1.ndim == 0 or embedding2.ndim == 0:
        return 0.0
    # Reshape to 2D arrays as expected by cosine_similarity
    if embedding1.ndim == 1: embedding1 = embedding1.reshape(1, -1)
    if embedding2.ndim == 1: embedding2 = embedding2.reshape(1, -1)
    try:
        similarity = cosine_similarity(embedding1, embedding2)[0][0]
        return float(similarity) # Ensure result is float
    except Exception as e:
        logger.warning(f"Could not calculate cosine similarity: {e}")
        return 0.0

class KnowledgeDatabase:
    """
    Manages a database of content knowledge for generating internal linking suggestions.

    This database stores analyzed content information including:
    - Content metadata (title, URL, etc.)
    - Extracted entities and topics
    - Semantic embeddings for relevance matching

    The database enables matching between content pieces for suggestion generation.
    """

    def __init__(self, config_path: str = "config.json", site_id: Optional[str] = None):
        """
        Initialize the knowledge database.

        Args:
            config_path: Path to the configuration file (relative to project root)
            site_id: Optional site identifier for multi-site support
        """
        logger.info(f"Initializing KnowledgeDatabase for site_id: '{site_id or 'default'}'...")
        project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..') # Navigate up from src/core/knowledge_db
        self.config = self._load_config(os.path.join(project_root, config_path))
        self.site_id = site_id or "default"

        # Set up database path
        self.db_dir = self.config.get("knowledge_db_dir", "data/knowledge_db")
        # Ensure db_dir path is absolute or relative to project root
        if not os.path.isabs(self.db_dir):
             self.db_dir = os.path.join(project_root, self.db_dir)

        os.makedirs(self.db_dir, exist_ok=True)
        logger.info(f"Knowledge base directory: {self.db_dir}")

        # Create site-specific database file
        self.db_path = os.path.join(self.db_dir, f"knowledge_{self.site_id}.db")
        logger.info(f"Knowledge base file path: {self.db_path}")

        # Initialize database
        self._init_database()

        # Thread lock for database operations
        self.db_lock = threading.Lock()
        logger.info(f"KnowledgeDatabase for site_id '{self.site_id}' initialized.")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    logger.info(f"Loading KnowledgeDatabase config from: {config_path}")
                    return json.load(f)
            else:
                logger.warning(f"KnowledgeDatabase config file {config_path} not found, using defaults.")
                # Define defaults relevant to this class
                return {
                    "knowledge_db_dir": "data/knowledge_db",
                    "max_entries": 10000, # Increased default size
                    "cleanup_threshold": 0.9,
                    "embedding_text_field": "title" # Default field to embed ('title' or 'content')
                }
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {str(e)}")
            return {
                "knowledge_db_dir": "data/knowledge_db",
                "max_entries": 10000,
                "cleanup_threshold": 0.9,
                "embedding_text_field": "title"
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
                    embedding BLOB,
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

    def add_content(self, content_data: Dict[str, Any], embedding_bytes: Optional[bytes] = None) -> bool:
        """
        Add or update content in the knowledge database, optionally including its embedding.

        Args:
            content_data: Dictionary with content data including:
                - id: Content identifier
                - title: Content title
                - url: Content URL
                - content: Full content text (optional, used if embedding_text_field='content')
                - entities: Dictionary of entity lists by type
                - topics: Dictionary of topic data
            embedding_bytes: Optional pre-generated embedding for the content (as bytes).

        Returns:
            bool: Success status
        """
        try:
            # Generate a unique hash for the content
            # Note: Hash currently based on title, entities, topics.
            # If only 'content' changes and embedding_text_field='content',
            # hash might not change, but embedding should still be updated.
            content_hash = self._generate_content_hash(content_data)

            with self.db_lock, sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                content_id = str(content_data.get("id", ""))
                url = str(content_data.get("url", ""))
                content = content_data.get("content", "") # Get content for potential use in hash? Not strictly needed now.
                title = content_data.get("title", "")
                # published_date = content_data.get("published_date") # Variable not used
                now = datetime.now().isoformat()

                # Check if content already exists
                cursor.execute("SELECT hash, embedding FROM content WHERE content_id = ?", (content_id,))
                existing = cursor.fetchone()

                embedding_updated_in_this_run = False # Flag to track if embedding was actually updated
                needs_update = False # Flag to track if update/insert is needed

                if existing:
                    existing_hash = existing[0]
                    existing_embedding = existing[1]

                    # Update if hash is different OR if we have a new embedding and the old one was missing
                    needs_update = existing_hash != content_hash or (embedding_bytes is not None and existing_embedding is None)

                    if needs_update:
                        logger.debug(f"Updating content {content_id}. Hash changed: {existing_hash != content_hash}. New embedding provided while old was missing: {embedding_bytes is not None and existing_embedding is None}")

                        update_query = """
                           UPDATE content
                           SET title = ?, url = ?, hash = ?, updated_at = ?
                           WHERE content_id = ?"""
                        params = [title, str(url), content_hash, now, content_id] # Ensure url is string for UPDATE

                        # Only update embedding if it was successfully provided
                        if embedding_bytes is not None:
                           update_query = """
                               UPDATE content
                               SET title = ?, url = ?, hash = ?, embedding = ?, updated_at = ?
                               WHERE content_id = ?"""
                           params = [title, str(url), content_hash, embedding_bytes, now, content_id] # Ensure url is string for UPDATE
                           embedding_updated_in_this_run = True # Embedding is updated/set here

                        cursor.execute(update_query, tuple(params))

                        # Delete existing entity and topic data before re-inserting
                        cursor.execute("DELETE FROM entities WHERE content_id = ?", (content_id,))
                        cursor.execute("DELETE FROM topics WHERE content_id = ?", (content_id,))

                    else:
                        logger.debug(f"Content {content_id} hash matches and embedding status is unchanged. Skipping content/embedding update, checking entities/topics.")
                        # Even if content/embedding isn't updated, we might need to update entities/topics
                        # Delete existing entity and topic data before re-inserting IF they are provided in content_data
                        if "entities" in content_data or "topics" in content_data:
                             logger.debug(f"Updating entities/topics for {content_id} as they were provided.")
                             cursor.execute("DELETE FROM entities WHERE content_id = ?", (content_id,))
                             cursor.execute("DELETE FROM topics WHERE content_id = ?", (content_id,))
                             needs_update = True # Mark that we need to add entities/topics below
                        else:
                             logger.debug(f"No entities/topics provided for {content_id}, skipping delete/re-insert.")
                             conn.commit() # Need to commit if we are returning early
                             return True # Nothing more to do for this item


                else:
                    # Insert new content record - include embedding if available
                    logger.debug(f"Inserting new content record for {content_id}. Embedding provided: {embedding_bytes is not None}")
                    cursor.execute(
                        """INSERT INTO content
                           (content_id, title, url, hash, embedding, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (content_id, title, str(url), content_hash, embedding_bytes, now, now) # Ensure url is string for INSERT
                    )
                    if embedding_bytes is not None:
                        embedding_updated_in_this_run = True # Embedding is inserted here
                    needs_update = True # We inserted, so need to add entities/topics

                # Add entity/topic data only if an insert or update occurred
                if needs_update:
                    # Add entity data (only if entities were provided)
                    entities = content_data.get("entities")
                    if entities is not None: # Check if the key exists and is not None
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

                    # Add topic data (only if topics were provided)
                    topics = content_data.get("topics")
                    if topics is not None: # Check if the key exists and is not None
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

                # Refined logging based on what actually happened
                action = "updated" if existing else "added"
                if needs_update or not existing: # If insert happened OR update needed changing content/embedding
                     if embedding_updated_in_this_run:
                          log_msg = f"Content {content_id} {action} in knowledge database (including embedding and any provided entities/topics)."
                     else:
                          log_msg = f"Content {content_id} {action} in knowledge database (embedding not included/updated, entities/topics updated if provided)."
                     logger.info(log_msg)
                elif "entities" in content_data or "topics" in content_data:
                     # This covers case where only entities/topics were updated
                     logger.info(f"Content {content_id} entities/topics updated in knowledge database.")
                else:
                     # This covers the case where nothing needed changing
                     logger.info(f"Content {content_id} already up-to-date in knowledge database.")

                # Check if cleanup is needed
                self._check_cleanup_needed(cursor)

                return True

        except Exception as e:
            logger.error(f"Error adding/updating content {content_data.get('id', 'N/A')} to knowledge database: {str(e)}", exc_info=True)
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
            max_entries = self.config.get("max_entries", 10000)
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
            max_entries = self.config.get("max_entries", 10000)
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
            ids_to_remove = [row[0] for row in cursor.fetchall()]
            logger.info(f"Removing {len(ids_to_remove)} oldest content items from knowledge database: {ids_to_remove}")

            for content_id in ids_to_remove:
                # Delete entity and topic data
                cursor.execute("DELETE FROM entities WHERE content_id = ?", (content_id,))
                cursor.execute("DELETE FROM topics WHERE content_id = ?", (content_id,))

                # Delete content record
                cursor.execute("DELETE FROM content WHERE content_id = ?", (content_id,))

            logger.info(f"Finished removing {len(ids_to_remove)} oldest content items.")

        except Exception as e:
            logger.error(f"Error performing cleanup: {str(e)}")

    def _generate_embedding(self, text: str) -> Optional[np.ndarray]:
         """Generates embedding for the given text using the global model."""
         if global_embedding_model is None:
             logger.warning("Sentence transformer model not loaded. Cannot generate embedding.")
             return None
         if not text or not isinstance(text, str):
             logger.warning(f"Cannot generate embedding for invalid text: {text}")
             return None

         try:
             logger.debug(f"Generating embedding for text snippet: '{text[:100]}...'")
             # Ensure model expects a list of sentences or single sentence
             embedding_vector = global_embedding_model.encode(text, convert_to_numpy=True)
             logger.debug(f"Generated embedding of shape {embedding_vector.shape}.")
             return embedding_vector
         except Exception as e:
             logger.error(f"Error generating embedding for text '{text[:100]}...': {e}", exc_info=True)
             return None

    # --- ADDED HELPER METHOD ---
    def _embedding_to_bytes(self, embedding: np.ndarray) -> Optional[bytes]:
         """Converts a NumPy embedding array to bytes using pickle."""
         if embedding is None:
             return None
         try:
             return pickle.dumps(embedding)
         except Exception as e:
             logger.error(f"Error serializing embedding to bytes: {e}", exc_info=True)
             return None
    # --- END ADDED HELPER METHOD ---

    def get_all_content_with_embeddings(self, exclude_url: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all content entries that have embeddings stored.

        Args:
            exclude_url (Optional[str]): A URL to exclude from the results (e.g., the current post).

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing:
                - content_id (str)
                - title (str)
                - url (str)
                - embedding (np.ndarray): Deserialized embedding vector.
        """
        logger.debug(f"Attempting to retrieve all content with embeddings, excluding URL: {exclude_url}")
        results = []
        try:
            with self.db_lock, sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row # Access columns by name
                cursor = conn.cursor()

                # Base query selects content with non-null and non-empty embeddings
                # Note: SQLite doesn't have a reliable way to check blob *length* directly in WHERE
                # So we check for non-null and filter empty ones during processing.
                query = "SELECT content_id, title, url, embedding FROM content WHERE embedding IS NOT NULL"
                params = []

                if exclude_url:
                    query += " AND url != ?"
                    params.append(str(exclude_url)) # Ensure URL is string for comparison

                cursor.execute(query, params)

                rows = cursor.fetchall()
                logger.debug(f"Retrieved {len(rows)} candidate rows with embeddings from DB.")

                for row in rows:
                    embedding_blob = row["embedding"]
                    if not embedding_blob: # Skip if blob is somehow empty despite NOT NULL check
                         logger.warning(f"Skipping content_id {row['content_id']} due to empty embedding blob.")
                         continue

                    try:
                        # Deserialize blob back to NumPy array using pickle
                        embedding_vector = pickle.loads(embedding_blob)

                        # Basic check for numpy array structure after unpickling
                        if not isinstance(embedding_vector, np.ndarray):
                             logger.warning(f"Deserialized embedding for {row['content_id']} is not a numpy array (type: {type(embedding_vector)}). Skipping.")
                             continue

                        results.append({
                            "content_id": row["content_id"],
                            "title": row["title"],
                            "url": row["url"],
                            "embedding": embedding_vector
                        })
                    except pickle.UnpicklingError as deser_error:
                         # Log error during deserialization but continue with others
                         logger.error(f"Failed to deserialize embedding for content_id {row['content_id']} using pickle: {deser_error}", exc_info=False) # Keep log concise
                    except Exception as general_deser_error:
                         logger.error(f"Unexpected error deserializing embedding for content_id {row['content_id']}: {general_deser_error}", exc_info=True)


            logger.info(f"Successfully retrieved and deserialized {len(results)} content items with embeddings.")
            return results

        except sqlite3.Error as db_error:
            logger.error(f"Database error retrieving content with embeddings: {db_error}", exc_info=True)
            return [] # Return empty list on DB error
        except Exception as e:
            logger.error(f"Unexpected error retrieving content with embeddings: {e}", exc_info=True)
            return [] # Return empty list on other errors

    # --- NEW METHOD (Option 1: Simple Semantic Search) ---
    def find_related_content_semantic(
        self,
        query_embedding: np.ndarray,
        exclude_url: Optional[str] = None,
        top_n: int = 10,
        min_similarity: float = 0.5 # Configurable threshold
    ) -> List[Dict[str, Any]]:
        """
        Find related content using semantic similarity (cosine similarity).

        Args:
            query_embedding (np.ndarray): The embedding of the content to find matches for.
            exclude_url (Optional[str]): A URL to exclude from the results.
            top_n (int): The maximum number of related items to return.
            min_similarity (float): The minimum cosine similarity score to consider an item related.

        Returns:
            List[Dict[str, Any]]: A list of related content items, sorted by similarity, including:
                - content_id (str)
                - title (str)
                - url (str)
                - similarity (float)
        """
        logger.debug(f"Starting semantic search: top_n={top_n}, min_similarity={min_similarity}, excluding_url='{exclude_url}'")

        if query_embedding is None or query_embedding.size == 0:
             logger.warning("Cannot perform semantic search with an empty query embedding.")
             return []

        # 1. Retrieve all candidates with embeddings
        all_candidates = self.get_all_content_with_embeddings(exclude_url=exclude_url)
        if not all_candidates:
            logger.info("No candidate embeddings found in KB for semantic search.")
            return []

        logger.debug(f"Comparing query embedding against {len(all_candidates)} candidates from KB.")

        # 2. Calculate similarity scores
        results_with_scores = []
        for candidate in all_candidates:
            candidate_embedding = candidate.get("embedding")
            if candidate_embedding is not None and candidate_embedding.size > 0:
                # Use the helper function for calculation
                similarity = _calculate_cosine_similarity(query_embedding, candidate_embedding)

                if similarity >= min_similarity:
                    results_with_scores.append({
                        "content_id": candidate["content_id"],
                        "title": candidate["title"],
                        "url": candidate["url"],
                        "similarity": similarity
                    })
            else:
                logger.warning(f"Candidate {candidate.get('content_id')} missing valid embedding, skipping comparison.")


        # 3. Sort by similarity (highest first)
        results_with_scores.sort(key=lambda x: x["similarity"], reverse=True)

        # 4. Return top N results
        final_results = results_with_scores[:top_n]
        logger.info(f"Semantic search found {len(final_results)} related items above threshold {min_similarity} (returning top {top_n}).")
        return final_results
    # --- END NEW METHOD ---
