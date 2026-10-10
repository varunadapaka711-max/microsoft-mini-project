import os
import zipfile
import tempfile
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.database import get_db
from app.models import GenerationJob, CertificateItem, JobStatus, CertificateStatus
from app.schemas import (
    BulkJobCreateRequest,
    JobResponse,
    JobDetailResponse,
    RecipientInput
)
from app.services.processor import process_generation_job

router = APIRouter(prefix="/api/v1/certificates", tags=["Certificates"])

def build_certificate_response(item: CertificateItem) -> dict:
    download_url = None
    if item.status == CertificateStatus.SUCCESS and item.file_path:
        download_url = f"/api/v1/certificates/{item.id}"
    
    return {
        "id": item.id,
        "job_id": item.job_id,
        "recipient_name": item.recipient_name,
        "recipient_email": item.recipient_email,
        "course_name": item.course_name,
        "issue_date": item.issue_date,
        "issuer_name": item.issuer_name,
        "status": item.status,
        "error_message": item.error_message,
        "download_url": download_url,
        "created_at": item.created_at,
        "updated_at": item.updated_at
    }


@router.post(
    "/jobs",
    response_model=JobDetailResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit bulk certificate generation request"
)
def create_bulk_generation_job(
    request: BulkJobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    if not request.recipients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipient list cannot be empty."
        )

    job = GenerationJob(
        title=request.title or "Bulk Certificate Batch",
        status=JobStatus.PENDING,
        total_count=len(request.recipients)
    )
    db.add(job)
    db.flush()

    certificate_items = []
    
    for idx, raw_data in enumerate(request.recipients):
        try:
            validated = RecipientInput(**raw_data)
            item = CertificateItem(
                job_id=job.id,
                recipient_name=validated.recipient_name,
                recipient_email=validated.recipient_email,
                course_name=validated.course_name,
                issue_date=validated.issue_date,
                issuer_name=validated.issuer_name,
                status=CertificateStatus.PENDING
            )
        except ValidationError as val_err:
            errors = [f"{e['loc'][0]}: {e['msg']}" for e in val_err.errors()]
            error_str = "Validation Error: " + "; ".join(errors)
            
            item = CertificateItem(
                job_id=job.id,
                recipient_name=raw_data.get("recipient_name") or f"Invalid Recipient #{idx+1}",
                recipient_email=raw_data.get("recipient_email") or "invalid@unknown",
                course_name=raw_data.get("course_name") or "Unknown",
                issue_date=raw_data.get("issue_date") or "N/A",
                issuer_name=raw_data.get("issuer_name") or "Organization Admin",
                status=CertificateStatus.FAILED,
                error_message=error_str
            )

        db.add(item)
        certificate_items.append(item)

    db.commit()
    db.refresh(job)

    background_tasks.add_task(process_generation_job, job.id)

    job_dict = JobResponse.model_validate(job).model_dump()
    job_dict["certificates"] = [build_certificate_response(item) for item in certificate_items]
    return job_dict


@router.get(
    "/jobs/{job_id}",
    response_model=JobDetailResponse,
    summary="Get job progress and certificate details"
)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation job '{job_id}' not found."
        )
    
    items = db.query(CertificateItem).filter(CertificateItem.job_id == job_id).all()
    job_dict = JobResponse.model_validate(job).model_dump()
    job_dict["certificates"] = [build_certificate_response(item) for item in items]
    return job_dict


@router.get(
    "/jobs",
    response_model=List[JobResponse],
    summary="List all certificate generation jobs"
)
def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    jobs = db.query(GenerationJob).order_by(GenerationJob.created_at.desc()).offset(skip).limit(limit).all()
    return jobs


@router.get(
    "/{certificate_id}",
    summary="Retrieve generated certificate PDF"
)
def get_certificate_pdf(certificate_id: str, db: Session = Depends(get_db)):
    item = db.query(CertificateItem).filter(CertificateItem.id == certificate_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{certificate_id}' not found."
        )
    
    if item.status != CertificateStatus.SUCCESS or not item.file_path or not os.path.exists(item.file_path):
        error_msg = item.error_message or "Certificate PDF is unavailable."
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot download certificate. Status: {item.status}. Details: {error_msg}"
        )
    
    filename = f"Certificate_{item.recipient_name.replace(' ', '_')}.pdf"
    return FileResponse(
        path=item.file_path,
        media_type="application/pdf",
        filename=filename
    )


@router.get(
    "/jobs/{job_id}/zip",
    summary="Download all generated certificates as a ZIP archive"
)
def download_job_certificates_zip(job_id: str, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation job '{job_id}' not found."
        )
    
    successful_items = db.query(CertificateItem).filter(
        CertificateItem.job_id == job_id,
        CertificateItem.status == CertificateStatus.SUCCESS
    ).all()
    
    if not successful_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No successfully generated certificates found for this job."
        )

    zip_filename = f"job_{job_id[:8]}_certificates.zip"
    temp_zip_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_zip_dir, zip_filename)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for item in successful_items:
            if item.file_path and os.path.exists(item.file_path):
                arcname = f"Certificate_{item.recipient_name.replace(' ', '_')}_{item.id[:6]}.pdf"
                zip_file.write(item.file_path, arcname=arcname)

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=zip_filename
    )
