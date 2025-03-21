from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional, Dict
import json
import os
import time
import logging
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger("web_analyzer_api.auth")

# Define API key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# In-memory cache for site credentials
# In production, consider using Redis or another distributed cache
_sites_cache = {}
_sites_cache_timestamp = 0
_CACHE_TTL = 300  # 5 minutes

def load_site_credentials() -> Dict[str, str]:
    """
    Load site credentials from config file.
    
    In a production environment, these would be stored in a database.
    For local development, we use a simple JSON file.
    """
    global _sites_cache, _sites_cache_timestamp
    
    # Check if cache is still valid
    current_time = time.time()
    if current_time - _sites_cache_timestamp < _CACHE_TTL and _sites_cache:
        return _sites_cache
    
    # Cache expired or empty, reload
    try:
        # In production, this would be a database query
        credentials_path = os.path.join(os.getcwd(), "config", "site_credentials.json")
        
        # If file doesn't exist, create it with default credentials
        if not os.path.exists(credentials_path):
            os.makedirs(os.path.dirname(credentials_path), exist_ok=True)
            default_credentials = {
                "default": {
                    "api_key": "development_key_only_for_testing",
                    "name": "Default Development Site",
                    "url": "https://example.com",
                    "rate_limit": 100  # requests per hour
                }
            }
            with open(credentials_path, 'w') as f:
                json.dump(default_credentials, f, indent=2)
            
            _sites_cache = default_credentials
        else:
            with open(credentials_path, 'r') as f:
                _sites_cache = json.load(f)
        
        _sites_cache_timestamp = current_time
        return _sites_cache
    except Exception as e:
        logger.error(f"Error loading site credentials: {str(e)}")
        # Return empty dict if there was an error
        return {}

async def get_site_from_api_key(api_key: Optional[str] = Depends(API_KEY_HEADER)) -> Dict:
    """
    Validate API key and return site details.
    
    This is used as a FastAPI dependency to protect routes.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing"
        )
    
    # Load credentials
    sites = load_site_credentials()
    
    # Check API key against all sites
    for site_id, site_data in sites.items():
        if site_data.get("api_key") == api_key:
            # Add site_id to the data
            site_info = {**site_data, "site_id": site_id}
            return site_info
    
    # API key not found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key"
    )

class RateLimiter:
    """
    Simple in-memory rate limiter.
    
    In production, this would use Redis or another shared cache.
    """
    def __init__(self):
        self.requests = {}  # site_id -> list of timestamps
    
    def is_rate_limited(self, site_id: str, max_requests: int, time_window: int = 3600) -> bool:
        """
        Check if a site is rate limited.
        
        Args:
            site_id: The site identifier
            max_requests: Maximum number of requests allowed in the time window
            time_window: Time window in seconds (default: 1 hour)
            
        Returns:
            True if rate limited, False otherwise
        """
        now = datetime.now()
        
        # Initialize if site_id not in requests
        if site_id not in self.requests:
            self.requests[site_id] = []
        
        # Filter out old requests
        self.requests[site_id] = [
            ts for ts in self.requests[site_id] 
            if now - ts < timedelta(seconds=time_window)
        ]
        
        # Check if over limit
        if len(self.requests[site_id]) >= max_requests:
            return True
        
        # Not rate limited, add request
        self.requests[site_id].append(now)
        return False

# Initialize rate limiter
rate_limiter = RateLimiter()

async def check_rate_limit(site_info: Dict = Depends(get_site_from_api_key)):
    """
    Check if the site has exceeded its rate limit.
    
    This is used as a FastAPI dependency after API key validation.
    """
    site_id = site_info["site_id"]
    rate_limit = site_info.get("rate_limit", 100)  # Default to 100 requests/hour
    
    if rate_limiter.is_rate_limited(site_id, rate_limit):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {rate_limit} requests per hour"
        )
    
    return site_info