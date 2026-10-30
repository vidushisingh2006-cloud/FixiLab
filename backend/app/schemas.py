from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AuditCreate(BaseModel):
    filename: str
    file_size: int
    mime_type: str


class ExtractionResult(BaseModel):
    field_name: str
    value: str
    page_number: int = 1
    confidence: Optional[float] = 1.0
    source: Optional[str] = "document"

    class Config:
        orm_mode = True
        from_attributes = True


class FindingCreate(BaseModel):
    category: str
    severity: str
    description: str
    extracted_value: Optional[str] = None
    expected_value: Optional[str] = None
    page_number: Optional[int] = None
    evidence: Optional[str] = None
    validation_rule: Optional[str] = None
    confidence: Optional[float] = None


class FindingUpdate(BaseModel):
    reviewer_comments: Optional[str] = None
    review_status: Optional[str] = None


class FindingResponse(BaseModel):
    id: str
    audit_id: str
    category: str
    severity: str
    description: str
    extracted_value: Optional[str] = None
    expected_value: Optional[str] = None
    page_number: Optional[int] = None
    evidence: Optional[str] = None
    validation_rule: Optional[str] = None
    confidence: Optional[float] = None
    reviewer_comments: Optional[str] = None
    review_status: str = "open"
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class AuditResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    mime_type: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class AuditDetailResponse(AuditResponse):
    findings: List[FindingResponse] = []
    extraction_results: List[ExtractionResult] = []

    class Config:
        orm_mode = True
        from_attributes = True
