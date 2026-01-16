import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, 
    DateTime, Date, Text, JSON, Numeric, Enum, ARRAY, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base

# Enums
class UserRole(str, enum.Enum):
    patient = 'patient'
    clinician = 'clinician'
    admin = 'admin'

class MetricCategory(str, enum.Enum):
    Blood = 'Blood'
    DNA = 'DNA'
    Vitals = 'Vitals'
    Functional = 'Functional'
    Fitness = 'Fitness'
    Microbiome = 'Microbiome'

class FileCategory(str, enum.Enum):
    LabReport = 'LabReport'
    Scan = 'Scan'
    UserUpload = 'UserUpload'
    FunctionalTestVideo = 'FunctionalTestVideo'
    AudioNote = 'AudioNote'

class MedType(str, enum.Enum):
    Prescription = 'Prescription'
    Supplement = 'Supplement'
    Nootropic = 'Nootropic'
    Peptide = 'Peptide'

# Tables

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    auth0_sub = Column(String(255), unique=True)
    role = Column(Enum(UserRole), default=UserRole.patient)
    first_name = Column(String(100))
    last_name = Column(String(100))
    dob = Column(Date)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class DataSource(Base):
    __tablename__ = "data_sources"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    api_key_hash = Column(String(255))
    is_trusted = Column(Boolean, default=False)

class MetricDefinition(Base):
    __tablename__ = "metric_definitions"
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    category = Column(Enum(MetricCategory), nullable=False)
    unit = Column(String(20))
    description = Column(Text)
    ref_min = Column(Numeric(10, 4))
    ref_max = Column(Numeric(10, 4))

class HealthObservation(Base):
    __tablename__ = "health_observations"
    id = Column(Integer, primary_key=True, autoincrement=True) # BigSerial logic handled by DB
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    metric_id = Column(Integer, ForeignKey("metric_definitions.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("data_sources.id"))
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    ingested_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    value_numeric = Column(Numeric(18, 6), nullable=True)
    value_text = Column(Text, nullable=True)
    raw_metadata = Column(JSON, nullable=True)

    __table_args__ = (
        CheckConstraint('value_numeric IS NOT NULL OR value_text IS NOT NULL', name='check_has_value'),
    )

class Medication(Base):
    __tablename__ = "medications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(Enum(MedType), default=MedType.Supplement)
    dosage = Column(String(100))
    frequency = Column(String(100))
    is_active = Column(Boolean, default=True)
    start_date = Column(Date)
    end_date = Column(Date)

class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    entry_date = Column(Date, nullable=False)
    content_markdown = Column(Text)
    mood_score = Column(Integer)
    tags = Column(ARRAY(Text))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint('mood_score BETWEEN 1 AND 10', name='check_mood_score'),
    )

class MediaFile(Base):
    __tablename__ = "media_files"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category = Column(Enum(FileCategory), nullable=False)
    s3_bucket = Column(String(100), nullable=False) # Maps to Firebase bucket name
    s3_key = Column(String(500), nullable=False) # Maps to Firebase Storage Path
    filename = Column(String(255))
    mime_type = Column(String(100))
    size_bytes = Column(Integer)
    is_processed = Column(Boolean, default=False)
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow)
