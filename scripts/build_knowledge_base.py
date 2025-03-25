#!/usr/bin/env python3
"""
Script to build the knowledge base by processing articles from thevou.com/blog/
"""

import os
import sys
import json
import time
import logging
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('knowledge_base_builder.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class KnowledgeBaseBuilder:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        }
    
    def fetch_articles(self, batch_size: int = 5) -> List[Dict[str, Any]]:
        """Fetch articles from thevou.com/blog/ in batches."""
        try:
            # TODO: Implement actual article fetching from thevou.com/blog/
            # For now, return dummy data
            return [
                {
                    'title': f'Test Article {i}',
                    'content': f'Test content for article {i}',
                    'url': f'https://thevou.com/blog/test-article-{i}'
                }
                for i in range(batch_size)
            ]
        except Exception as e:
            logger.error(f"Error fetching articles: {str(e)}")
            return []
    
    def process_batch(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a batch of articles through the API."""
        try:
            response = requests.post(
                f"{self.api_url}/bulk/process",
                headers=self.headers,
                json={
                    'content_items': articles,
                    'knowledge_building': True,
                    'batch_size': len(articles)
                },
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"API error: {response.text}")
                return {'success': False, 'message': 'API error'}
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def check_job_status(self, job_id: str) -> Dict[str, Any]:
        """Check the status of a processing job."""
        try:
            response = requests.get(
                f"{self.api_url}/bulk/status/{job_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"API error: {response.text}")
                return {'success': False, 'message': 'API error'}
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error checking job status: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def build_knowledge_base(self, total_articles: int = 100, batch_size: int = 5):
        """Build the knowledge base by processing articles in batches."""
        processed_count = 0
        failed_count = 0
        
        logger.info(f"Starting knowledge base build with {total_articles} articles")
        
        while processed_count < total_articles:
            # Fetch next batch of articles
            articles = self.fetch_articles(batch_size)
            if not articles:
                logger.error("No more articles to process")
                break
            
            # Process the batch
            result = self.process_batch(articles)
            if not result.get('success'):
                logger.error(f"Failed to process batch: {result.get('message')}")
                failed_count += len(articles)
                continue
            
            job_id = result.get('job_id')
            if not job_id:
                logger.error("No job ID received")
                failed_count += len(articles)
                continue
            
            # Wait for job completion
            while True:
                status = self.check_job_status(job_id)
                if not status.get('success'):
                    logger.error(f"Error checking job status: {status.get('message')}")
                    failed_count += len(articles)
                    break
                
                if status.get('status') == 'completed':
                    processed_count += len(articles)
                    logger.info(f"Processed {processed_count}/{total_articles} articles")
                    break
                elif status.get('status') == 'failed':
                    logger.error(f"Job failed: {status.get('message')}")
                    failed_count += len(articles)
                    break
                
                time.sleep(5)  # Wait 5 seconds before checking again
            
            # Add a small delay between batches
            time.sleep(2)
        
        logger.info(f"Knowledge base build complete. Processed: {processed_count}, Failed: {failed_count}")

def main():
    # Get API configuration from environment variables
    api_url = os.getenv('WEB_ANALYZER_API_URL', 'https://web-analyzer-service-v2.onrender.com')
    api_key = os.getenv('WEB_ANALYZER_API_KEY', 'p6fHDUXqGRgV4SNIXrxLG-Z01TVXVjtIk5ODiMmj6F8')
    
    # Create builder instance
    builder = KnowledgeBaseBuilder(api_url, api_key)
    
    # Build knowledge base
    builder.build_knowledge_base(total_articles=100, batch_size=5)

if __name__ == '__main__':
    main() 