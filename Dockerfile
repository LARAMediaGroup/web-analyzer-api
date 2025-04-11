FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables BEFORE downloading NLTK data
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV NLTK_DATA=/app/nltk_data

# Download required NLTK data directly to the NLTK_DATA directory
RUN python -m nltk.downloader -d $NLTK_DATA --unzip punkt stopwords wordnet averaged_perceptron_tagger maxent_ne_chunker words

# Copy the application code
COPY src/ ./src/
COPY config.json ./
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p logs data cache

# Expose the port the app will run on
EXPOSE 8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application - Reduced workers to 1
CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "src.api.main:app", "--bind", "0.0.0.0:8000"]