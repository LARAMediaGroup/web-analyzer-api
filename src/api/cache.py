from typing import Any, Optional, Dict, Callable
import time
import json
import hashlib
import logging
import os
import asyncio
from functools import wraps

# Configure logging
logger = logging.getLogger("web_analyzer_api.cache")

class Cache:
    """
    Simple file-based cache implementation.
    
    In production, this would be replaced with Redis or another distributed cache.
    """
    def __init__(self, cache_dir: str = "cache", default_ttl: int = 3600):
        """
        Initialize the cache.
        
        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default time-to-live in seconds
        """
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, key: str) -> str:
        """
        Convert a key to a valid filename.
        
        Args:
            key: The cache key
            
        Returns:
            A valid filename for the cache key
        """
        # Hash the key to ensure it's a valid filename
        hashed = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hashed}.json")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value, or None if not found or expired
        """
        cache_file = self._get_cache_key(key)
        
        try:
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check if expired
            if cache_data.get("expires_at", 0) < time.time():
                # Expired, remove the file
                os.remove(cache_file)
                return None
            
            return cache_data.get("value")
        except Exception as e:
            logger.error(f"Error reading from cache: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time-to-live in seconds (optional, uses default if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        cache_file = self._get_cache_key(key)
        
        try:
            ttl = ttl if ttl is not None else self.default_ttl
            expires_at = time.time() + ttl
            
            cache_data = {
                "value": value,
                "expires_at": expires_at
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
            
            return True
        except Exception as e:
            logger.error(f"Error writing to cache: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if successful, False otherwise
        """
        cache_file = self._get_cache_key(key)
        
        try:
            if os.path.exists(cache_file):
                os.remove(cache_file)
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False

# Initialize the cache
cache = Cache()

def cache_key_builder(*args, **kwargs) -> str:
    """
    Build a cache key from function arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        A cache key string
    """
    # Convert args and kwargs to a string representation
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
    
    # Join parts and hash
    key = ":".join(key_parts)
    return key

def cached(ttl: Optional[int] = None, key_builder: Optional[Callable] = None):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time-to-live in seconds (optional)
        key_builder: Function to build cache key (optional)
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = f"{func.__module__}.{func.__name__}:{cache_key_builder(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Cache miss, call function
            logger.debug(f"Cache miss for {cache_key}")
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl)
            
            return result
            
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = f"{func.__module__}.{func.__name__}:{cache_key_builder(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Cache miss, call function
            logger.debug(f"Cache miss for {cache_key}")
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl)
            
            return result
        
        # Return appropriate wrapper based on whether function is async or not
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator