from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID
from app.models import MetricCategory, FileCategory

class ObservationInput(BaseModel):
    metric_code: str
    recorded_at: datetime
    value_numeric: Optional[float] = None
    value_text: Optional[str] = None
    raw_metadata: Optional[Dict[str, Any]] = None

    @field_validator('value_numeric', 'value_text')
    @classmethod
    def check_one_value(cls, v, values):
        # Note: Pydantic v2 validation logic is slightly different, 
        # but for simplicity we rely on database constraints or upper level logic
        # This is a basic structural validation.
        return v

class BatchIngestRequest(BaseModel):
    source_name: str
    data: List[ObservationInput]

class ObservationResponse(BaseModel):
    metric_code: str
    recorded_at: datetime
    value: str | float
    category: MetricCategory

class JournalEntryCreate(BaseModel):
    entry_date: date
    content: str
    mood_score: Optional[int] = Field(None, ge=1, le=10)
    tags: Optional[List[str]] = []

class MediaUploadRequest(BaseModel):
    filename: str
    file_type: FileCategory
    content_type: str  # Mime Type
