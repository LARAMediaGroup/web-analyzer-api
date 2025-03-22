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

# Alternative: Run with Docker Compose
docker-compose up -d
```

### Deploy to Render

1. Create a GitHub repository and push your code:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/web_analyzer_service.git
git push -u origin main
```

2. In Render Dashboard:
   - Create a new Web Service
   - Connect your GitHub repository
   - Select "Docker" as the build method
   - Set the environment variables:
     - `SECRET_KEY` (generate a secure key)
     - `DEBUG` (set to "False" for production)
     - `MAX_WORKERS` (set to 4 or appropriate value)
     - `NLTK_DATA` (set to "/app/nltk_data")
   - Deploy the service

3. GitHub Actions CI/CD (Optional):
   - CI/CD workflow is preconfigured in `.github/workflows/deploy.yml`
   - Set the required secrets in your GitHub repository:
     - `RENDER_API_KEY`: Your Render API key
     - `RENDER_SERVICE_ID`: Your Render service ID
   - Each push to main will trigger a deployment

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

1. Configure Redis for production-ready caching (currently using file-based caching)
2. Setup monitoring and logging with a service like DataDog or Prometheus
3. Create an admin dashboard for link analytics and performance metrics
4. Extend the WordPress plugin for automated link insertion
5. Add support for custom taxonomies and post types in WordPress
6. Implement A/B testing framework for link placement effectiveness
7. Develop an API client library for easier integration with other platforms