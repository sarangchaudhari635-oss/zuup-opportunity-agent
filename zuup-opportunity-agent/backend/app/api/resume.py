"""
Resume Upload API — S3 upload + async parse job trigger.
"""
import hashlib
import uuid
from datetime import datetime, timezone

import boto3
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.models import StudentProfile, User
from app.schemas.schemas import ResumeParseStatus, ResumeUploadResponse
from app.worker.tasks import parse_resume_task

router = APIRouter(prefix="/resume", tags=["resume"])

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a resume (PDF/DOCX, max 10MB).
    File is stored in S3 (AES-256 encrypted).
    An async parse job is queued; call /resume/status/{job_id} to poll.
    """
    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF and DOCX files are supported.",
        )

    # Read and validate size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size must not exceed 10MB.",
        )

    # Generate file key
    file_hash = hashlib.sha256(file_bytes).hexdigest()[:16]
    extension = "pdf" if "pdf" in file.content_type else "docx"
    
    # Check if S3 credentials are set
    use_s3 = bool(settings.aws_access_key_id and settings.s3_bucket_name and "SECRET" not in settings.aws_access_key_id and "SECRET" not in settings.s3_bucket_name)
    
    if use_s3:
        s3_key = f"{settings.s3_resume_prefix}{current_user.id}/{file_hash}.{extension}"
        # Upload to S3 with AES-256 encryption
        s3_client = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        s3_client.put_object(
            Bucket=settings.s3_bucket_name,
            Key=s3_key,
            Body=file_bytes,
            ContentType=file.content_type,
            ServerSideEncryption="AES256",
        )
        db_key = s3_key
    else:
        # Save locally
        import os
        # Put in 'storage' folder in the backend directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        storage_dir = os.path.join(base_dir, "storage", str(current_user.id))
        os.makedirs(storage_dir, exist_ok=True)
        local_path = os.path.join(storage_dir, f"{file_hash}.{extension}")
        with open(local_path, "wb") as f:
            f.write(file_bytes)
        db_key = f"local://{current_user.id}/{file_hash}.{extension}"

    # Update profile with file key
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if profile:
        profile.resume_s3_key = db_key
        db.commit()

    # Queue async parse job
    job_id = str(uuid.uuid4())
    parse_resume_task.apply_async(
        kwargs={
            "job_id": job_id,
            "user_id": str(current_user.id),
            "s3_key": s3_key,
            "content_type": file.content_type,
        },
        task_id=job_id,
    )

    return ResumeUploadResponse(
        job_id=job_id,
        message="Resume uploaded successfully. Parsing in progress.",
        status="processing",
    )


@router.get("/status/{job_id}", response_model=ResumeParseStatus)
async def get_parse_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Poll the status of a resume parse job."""
    from app.worker.celery_app import celery_app
    from celery.result import AsyncResult

    result = AsyncResult(job_id, app=celery_app)

    if result.state == "PENDING":
        return ResumeParseStatus(job_id=job_id, status="pending")
    elif result.state == "STARTED" or result.state == "PROGRESS":
        return ResumeParseStatus(job_id=job_id, status="processing")
    elif result.state == "SUCCESS":
        return ResumeParseStatus(
            job_id=job_id,
            status="done",
            profile_id=result.result.get("profile_id") if result.result else None,
        )
    else:  # FAILURE
        return ResumeParseStatus(
            job_id=job_id,
            status="failed",
            error=str(result.info) if result.info else "Parse failed.",
        )
