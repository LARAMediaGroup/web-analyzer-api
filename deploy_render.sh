#!/bin/bash
# Deployment script for Web Analyzer Service to Render

echo "Starting Web Analyzer Service deployment to Render..."

# Check if render-cli is installed
if ! command -v render &> /dev/null; then
    echo "Render CLI not found. Installing..."
    npm install -g @renderinc/cli
fi

# Check if we have Render API key set
if [ -z "$RENDER_API_KEY" ]; then
    echo "RENDER_API_KEY environment variable not set"
    echo "Please set it with: export RENDER_API_KEY=your_api_key"
    exit 1
fi

# Check if service ID is provided
if [ -z "$RENDER_SERVICE_ID" ]; then
    echo "RENDER_SERVICE_ID environment variable not set"
    echo "Please set it with: export RENDER_SERVICE_ID=your_service_id"
    exit 1
fi

# Validate requirements.txt to make sure numpy is included
if ! grep -q "^numpy" requirements.txt; then
    echo "ERROR: numpy not found in requirements.txt"
    echo "Please add numpy to requirements.txt"
    exit 1
fi

# Validate Dockerfile has NLTK data download
if ! grep -q "download_nltk.py" Dockerfile; then
    echo "ERROR: NLTK download step not found in Dockerfile"
    echo "Please update the Dockerfile to run download_nltk.py"
    exit 1
fi

# Verify download_nltk.py exists
if [ ! -f "download_nltk.py" ]; then
    echo "ERROR: download_nltk.py not found"
    echo "Please create the NLTK download script"
    exit 1
fi

echo "All pre-deployment checks passed!"

# Run NLTK download script locally to verify it works
echo "Testing NLTK download script locally..."
python3 download_nltk.py

# Trigger a deploy on Render
echo "Triggering deployment on Render..."
curl -X POST "https://api.render.com/v1/services/$RENDER_SERVICE_ID/deploys" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json"

echo "Deployment triggered on Render!"
echo "Monitor the deployment status in the Render dashboard."

# Check deployment status
echo "Waiting for deployment to complete..."
sleep 10

# Query deployment status
echo "Checking deployment status..."
curl -X GET "https://api.render.com/v1/services/$RENDER_SERVICE_ID" \
  -H "Authorization: Bearer $RENDER_API_KEY"

echo "Deployment script completed!"
echo "Once the deployment is complete, verify the API at:"
echo "https://your-service-name.onrender.com/health"