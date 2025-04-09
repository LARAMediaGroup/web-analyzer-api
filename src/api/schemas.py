# src/api/schemas.py

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Basic Status ---

class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: datetime

# --- Analysis Schemas ---

class LinkSuggestion(BaseModel):
    anchor_text: str
    target_url: HttpUrl # Validate URL format
    context: Optional[str] = None
    confidence: float
    paragraph_index: int
    relevance: Optional[float] = None # Added based on enhanced analyzer output

# Analysis sub-model (can be more specific if needed)
# Using Dict[str, Any] for flexibility for now
class AnalysisResult(BaseModel):
    fashion_entities: Optional[Dict[str, Any]] = None
    primary_theme: Optional[str] = None
    semantic_structure: Optional[Dict[str, Any]] = None
    primary_topic: Optional[str] = None
    subtopics: Optional[List[str]] = None
    # Allow other fields if analyzers add more
    class Config:
        extra = 'allow'

class AnalysisResponse(BaseModel):
    analysis: Optional[AnalysisResult] = None # Make analysis optional
    link_suggestions: List[LinkSuggestion] = []
    processing_time: float
    status: str
    error: Optional[str] = None
    suggestion_error: Optional[str] = None # Added based on bulk processor output

class AnalysisRequest(BaseModel):
    content: str = Field(..., min_length=1) # Ensure content is not empty
    title: str = Field(..., min_length=1)  # Ensure title is not empty
    url: Optional[HttpUrl] = None # Optional URL of the content being analyzed

# --- Bulk Processing Schemas ---

class ContentItem(BaseModel):
    id: str # Unique identifier (e.g., post ID)
    title: str
    content: str
    url: Optional[HttpUrl] = None

class BulkAnalysisRequest(BaseModel):
    content_items: List[ContentItem]
    knowledge_building: bool = False
    batch_size: Optional[int] = Field(None, ge=1) # Optional batch size, must be positive if provided

class JobSubmissionResponse(BaseModel):
    job_id: str
    status: str # e.g., "queued"
    total_items: int
    site_id: Optional[str] = None
    knowledge_building: bool

class JobStatusKnowledgeDBInfo(BaseModel):
    current: Optional[Dict[str, Any]] = None
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    site_id: Optional[str] = None
    total_items: int
    processed_items: int
    progress: float
    elapsed_seconds: float
    report_path: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None # Processing stats
    error: Optional[str] = None
    knowledge_building: bool
    knowledge_db: Optional[JobStatusKnowledgeDBInfo] = None # Add KB stats if available
    last_update: datetime

class JobControlResponse(BaseModel):
    status: str
    message: Optional[str] = None
    error: Optional[str] = None

class JobListInfo(BaseModel):
    job_id: str
    status: str
    site_id: Optional[str] = None
    total_items: int
    processed_items: int
    start_time: datetime
    knowledge_building: bool

# --- Knowledge Base Schemas ---

# Using Dict for flexibility, can be made stricter later
class KnowledgeBaseStats(BaseModel):
    content_count: int
    entity_count: int
    topic_count: int
    unique_entities: int
    unique_topics: int
    last_update: Optional[datetime] = None
    database_size_kb: int
    # Allow any other stats fields
    class Config:
        extra = 'allow'
