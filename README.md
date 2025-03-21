# Web Analyzer Service

A microservice API for analyzing web content and suggesting internal links for WordPress sites.

## Features

- Content analysis with NLP for finding topic relevance
- Anchor text generation with context-aware selection
- RESTful API for WordPress integration
- Optimized for fashion content
- Docker containerization for easy deployment

## Local Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/web_analyzer_service.git
cd web_analyzer_service

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python download_nltk.py
```

### Running locally

```bash
# Start the API server
python run_local.py

# Test the API (in a different terminal)
python test_api.py
```

## Docker Deployment

### Build locally

```bash
# Build the Docker image
docker build -t web_analyzer_service .

# Run with Docker
docker run -p 8000:8000 web_analyzer_service
```

### Deploy to Hostinger

1. Package the application:
```bash
tar -czvf web_analyzer_service.tar.gz .
```

2. Upload to Hostinger:
```bash
scp web_analyzer_service.tar.gz username@your-hostinger-server.com:~/
```

3. SSH to Hostinger and deploy:
```bash
ssh username@your-hostinger-server.com
mkdir -p ~/web_analyzer_service
cd ~/web_analyzer_service
tar -xzvf ~/web_analyzer_service.tar.gz
docker-compose up -d
```

## API Endpoints

### Health Check

```
GET /health
```

### Content Analysis

```
POST /analyze/content
```

Request body:
```json
{
  "content": "The content to analyze...",
  "title": "Article Title",
  "url": "https://example.com/article-url",
  "site_id": "site-identifier"
}
```

Response:
```json
{
  "link_suggestions": [
    {
      "anchor_text": "detected anchor text",
      "target_url": "https://example.com/target-url",
      "context": "surrounding context with **anchor text** highlighted",
      "confidence": 0.95,
      "paragraph_index": 3
    }
  ],
  "processing_time": 0.123,
  "status": "success"
}
```

## Next Steps

1. Implement the WordPress plugin for frontend integration
2. Create content editor integration for inline link suggestions
3. Develop link insertion engine for automated link placement
4. Implement bulk processing for existing content