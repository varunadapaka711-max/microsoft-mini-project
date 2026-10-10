from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from app.models import JobStatus, CertificateStatus

class RecipientInput(BaseModel):
    recipient_name: str = Field(..., description="Full name of certificate recipient")
    recipient_email: str = Field(..., description="Email address of recipient")
    course_name: str = Field(..., description="Name of the course, event, or program")
    issue_date: str = Field(..., description="Date of issuance (e.g. 2026-10-08)")
    issuer_name: Optional[str] = Field("Organization Admin", description="Name of issuer or organization")

    @field_validator("recipient_name")
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Recipient name cannot be empty")
        return v.strip()

    @field_validator("course_name")
    def validate_course(cls, v):
        if not v or not v.strip():
            raise ValueError("Course name cannot be empty")
        return v.strip()

    @field_validator("recipient_email")
    def validate_email(cls, v):
        if not v or "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v.strip().lower()


class JobCreateRequest(BaseModel):
    title: Optional[str] = Field(None, description="Optional title or tag for this generation job")
    recipients: List[RecipientInput] = Field(..., min_length=1, description="List of recipient objects")


class RawRecipientInput(BaseModel):
    """Raw input schema used when handling partial validation failures in bulk requests."""
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    course_name: Optional[str] = None
    issue_date: Optional[str] = None
    issuer_name: Optional[str] = "Organization Admin"


class BulkJobCreateRequest(BaseModel):
    title: Optional[str] = Field(None, description="Optional title or tag for this generation job")
    recipients: List[dict] = Field(..., min_length=1, description="List of recipient dicts (allows partial invalid inputs)")


class CertificateItemResponse(BaseModel):
    id: str
    job_id: str
    recipient_name: str
    recipient_email: str
    course_name: str
    issue_date: str
    issuer_name: Optional[str] = None
    status: CertificateStatus
    error_message: Optional[str] = None
    download_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobResponse(BaseModel):
    id: str
    title: Optional[str] = None
    status: JobStatus
    total_count: int
    success_count: int
    failure_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobDetailResponse(JobResponse):
    certificates: List[CertificateItemResponse] = []
