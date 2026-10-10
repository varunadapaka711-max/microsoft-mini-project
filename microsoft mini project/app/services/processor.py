import os
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import GenerationJob, CertificateItem, JobStatus, CertificateStatus
from app.config import settings
from app.services.generator import generate_certificate_pdf

logger = logging.getLogger("certificate_processor")

def process_generation_job(job_id: str, db: Session = None):
    """
    Background worker task to process all certificate generation items in a job.
    Processes items sequentially/resiliently. A failure in one item will not block others.
    """
    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True

    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found for background processing.")
            return

        job.status = JobStatus.PROCESSING
        job.updated_at = datetime.now(timezone.utc)
        db.commit()

        items = db.query(CertificateItem).filter(CertificateItem.job_id == job_id).all()
        
        successes = 0
        failures = 0

        for item in items:
            # If item was already marked failed during initial schema validation
            if item.status == CertificateStatus.FAILED:
                failures += 1
                continue

            try:
                output_pdf_path = os.path.join(settings.STORAGE_DIR, f"{item.id}.pdf")
                
                # Render PDF
                generate_certificate_pdf(
                    file_path=output_pdf_path,
                    recipient_name=item.recipient_name,
                    course_name=item.course_name,
                    issue_date=item.issue_date,
                    issuer_name=item.issuer_name or "Organization Admin",
                    certificate_id=item.id
                )
                
                item.status = CertificateStatus.SUCCESS
                item.file_path = output_pdf_path
                item.updated_at = datetime.now(timezone.utc)
                successes += 1

            except Exception as e:
                logger.exception(f"Failed to generate certificate for item {item.id} ({item.recipient_name}): {e}")
                item.status = CertificateStatus.FAILED
                item.error_message = f"Generation Error: {str(e)}"
                item.updated_at = datetime.now(timezone.utc)
                failures += 1

            db.commit()

        # Update final job metrics and status
        job.success_count = successes
        job.failure_count = failures
        job.updated_at = datetime.now(timezone.utc)

        if successes == job.total_count:
            job.status = JobStatus.COMPLETED
        elif failures == job.total_count:
            job.status = JobStatus.FAILED
        else:
            job.status = JobStatus.PARTIALLY_COMPLETED

        db.commit()
        logger.info(f"Job {job_id} processing completed. Status: {job.status} (Success: {successes}, Failures: {failures})")

    except Exception as exc:
        logger.exception(f"Fatal error processing job {job_id}: {exc}")
        db.rollback()
        if 'job' in locals() and job:
            job.status = JobStatus.FAILED
            db.commit()
    finally:
        if should_close_db:
            db.close()
