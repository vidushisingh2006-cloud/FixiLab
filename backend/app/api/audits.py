from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import re
import json
from pathlib import Path

from app.database import get_db, Audit, Finding, SessionLocal
from app.schemas import (
    AuditDetailResponse,
    FindingUpdate,
    FindingResponse,
    ExtractionResult,
)
from app.services.pdf_reader import verify_file_integrity
from app.services.extraction import extract_document
from app.services.validation import validate_document
from app.services.reports import generate_report

router = APIRouter()

# Resolve backend root directory reliably
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BACKEND_DIR / "uploads"
REPORTS_DIR = BACKEND_DIR / "reports"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/pjpeg",
    "application/octet-stream",
}
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
EXT_TO_MIME = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


def sanitize_filename(filename: str) -> str:
    """Remove potentially dangerous characters from filename."""
    filename = filename.replace("..", "").replace("/", "").replace("\\", "")
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[: 255 - len(ext)] + ext
    return filename


def normalize_and_validate_file_type(filename: str, mime_type: Optional[str]) -> Optional[str]:
    """Validate file extension and MIME type, returning canonical MIME type or None."""
    ext = os.path.splitext((filename or "").lower())[1]
    if ext not in ALLOWED_EXTENSIONS:
        return None
    canonical = EXT_TO_MIME[ext]
    if not mime_type or mime_type.strip() == "" or mime_type in ("application/octet-stream", "application/x-pdf", "image/pjpeg"):
        return canonical
    if mime_type.lower() not in ALLOWED_MIME_TYPES:
        return None
    return mime_type.lower()


def _serialize_finding(f: Finding) -> FindingResponse:
    """Convert SQLAlchemy Finding instance into FindingResponse safely on Pydantic v1 & v2."""
    return FindingResponse(
        id=f.id,
        audit_id=f.audit_id,
        category=f.category,
        severity=f.severity,
        description=f.description,
        extracted_value=f.extracted_value,
        expected_value=f.expected_value,
        page_number=f.page_number,
        evidence=f.evidence,
        validation_rule=f.validation_rule,
        confidence=f.confidence,
        reviewer_comments=f.reviewer_comments,
        review_status=f.review_status or "open",
        created_at=f.created_at,
    )


def _build_audit_detail(audit: Audit, db: Session) -> AuditDetailResponse:
    """Construct a complete AuditDetailResponse with serialized findings and extracted fields."""
    findings_orm = db.query(Finding).filter(Finding.audit_id == audit.id).all()
    findings_list = [_serialize_finding(f) for f in findings_orm]

    extraction_list: List[ExtractionResult] = []
    if audit.extraction_data:
        try:
            raw_items = json.loads(audit.extraction_data)
            extraction_list = [ExtractionResult(**item) for item in raw_items]
        except Exception:
            extraction_list = []
    elif audit.file_path and os.path.exists(audit.file_path):
        # Fallback for old records or if background task hasn't finished yet
        try:
            raw_items = extract_document(audit.file_path, audit.mime_type)
            extraction_list = [ExtractionResult(**item) for item in raw_items]
        except Exception:
            extraction_list = []

    return AuditDetailResponse(
        id=audit.id,
        filename=audit.filename,
        file_size=audit.file_size,
        mime_type=audit.mime_type,
        status=audit.status,
        created_at=audit.created_at,
        updated_at=audit.updated_at,
        findings=findings_list,
        extraction_results=extraction_list,
    )


def run_audit_validation_task(audit_id: str):
    """Background task to run extraction and validation without blocking the request."""
    db = SessionLocal()
    try:
        audit = db.query(Audit).filter(Audit.id == audit_id).first()
        if not audit:
            return

        audit.status = "validating"
        db.commit()

        # Clear previous findings if any
        db.query(Finding).filter(Finding.audit_id == audit_id).delete()
        db.commit()

        findings_data = validate_document(audit.id, audit.file_path, db, audit.mime_type)
        for finding in findings_data:
            db.add(Finding(**finding))

        extraction_items = extract_document(audit.file_path, audit.mime_type)
        audit.extraction_data = json.dumps(extraction_items)
        audit.status = "completed"
        db.commit()
    except Exception as e:
        print(f"Background validation failed for {audit_id}: {e}")
        audit = db.query(Audit).filter(Audit.id == audit_id).first()
        if audit:
            audit.status = "failed"
            db.commit()
    finally:
        db.close()


@router.get("", response_model=List[AuditDetailResponse])
async def list_audits(db: Session = Depends(get_db)):
    audits = db.query(Audit).order_by(Audit.created_at.desc()).all()
    return [_build_audit_detail(a, db) for a in audits]


@router.post("", response_model=AuditDetailResponse)
async def create_audit(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    filename: Optional[str] = Form(None),
    file_size: Optional[int] = Form(None),
    mime_type: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    raw_filename = filename or file.filename or "uploaded_document.pdf"
    raw_mime = mime_type or file.content_type

    canonical_mime = normalize_and_validate_file_type(raw_filename, raw_mime)
    if not canonical_mime:
        raise HTTPException(
            status_code=415,
            detail="Invalid file type. Only PDF, PNG, JPG, and JPEG files are allowed",
        )

    content = await file.read()
    actual_size = len(content)

    if actual_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if actual_size > MAX_FILE_SIZE or (file_size is not None and file_size > MAX_FILE_SIZE):
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds {MAX_FILE_SIZE // (1024 * 1024)} MB limit",
        )

    safe_filename = sanitize_filename(raw_filename)
    file_id = str(uuid.uuid4())
    unique_filename = f"{file_id}_{safe_filename}"
    file_path = UPLOAD_DIR / unique_filename

    with open(file_path, "wb") as buffer:
        buffer.write(content)

    integrity = verify_file_integrity(str(file_path), canonical_mime)
    if not integrity.get("valid", False):
        try:
            os.remove(file_path)
        except OSError:
            pass
        raise HTTPException(status_code=400, detail=integrity.get("reason", "Corrupted or invalid file content"))

    audit = Audit(
        id=file_id,
        filename=safe_filename,
        file_size=actual_size,
        file_path=str(file_path),
        mime_type=canonical_mime,
        status="uploaded",
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    # Run validation in the background so the upload responds immediately
    background_tasks.add_task(run_audit_validation_task, audit.id)

    return _build_audit_detail(audit, db)


@router.get("/{audit_id}", response_model=AuditDetailResponse)
async def get_audit(audit_id: str, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    return _build_audit_detail(audit, db)


@router.get("/{audit_id}/file")
async def get_audit_file(audit_id: str, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit or not os.path.exists(audit.file_path):
        raise HTTPException(status_code=404, detail="Audit file not found")

    return FileResponse(
        audit.file_path,
        media_type=audit.mime_type,
        filename=audit.filename,
    )


@router.post("/{audit_id}/extract")
@router.get("/{audit_id}/extract")
async def extract_audit(audit_id: str, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    extraction_items = extract_document(audit.file_path, audit.mime_type)
    audit.extraction_data = json.dumps(extraction_items)
    if audit.status == "uploaded":
        audit.status = "extracted"
    db.commit()

    return {
        "status": audit.status,
        "audit_id": audit.id,
        "extraction_results": extraction_items,
    }


@router.post("/{audit_id}/validate")
@router.get("/{audit_id}/validate")
async def validate_audit(audit_id: str, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    audit.status = "validating"
    db.commit()

    db.query(Finding).filter(Finding.audit_id == audit_id).delete()
    db.commit()

    findings_data = validate_document(audit.id, audit.file_path, db, audit.mime_type)
    for finding in findings_data:
        db.add(Finding(**finding))

    extraction_items = extract_document(audit.file_path, audit.mime_type)
    audit.extraction_data = json.dumps(extraction_items)
    audit.status = "completed"
    db.commit()

    return {
        "status": "completed",
        "audit_id": audit.id,
        "findings_count": len(findings_data),
        "extraction_results": extraction_items,
    }


@router.patch("/{audit_id}/findings/{finding_id}", response_model=FindingResponse)
@router.put("/{audit_id}/findings/{finding_id}", response_model=FindingResponse)
async def update_finding(
    audit_id: str,
    finding_id: str,
    update: FindingUpdate,
    db: Session = Depends(get_db),
):
    finding = (
        db.query(Finding)
        .filter(Finding.id == finding_id, Finding.audit_id == audit_id)
        .first()
    )

    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    if update.reviewer_comments is not None:
        finding.reviewer_comments = update.reviewer_comments
    if update.review_status is not None:
        finding.review_status = update.review_status

    db.commit()
    db.refresh(finding)

    return _serialize_finding(finding)


@router.get("/{audit_id}/report")
async def get_report(audit_id: str, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    findings = db.query(Finding).filter(Finding.audit_id == audit_id).all()
    report_path = generate_report(audit, findings)
    abs_pdf_path = REPORTS_DIR / os.path.basename(report_path)

    return FileResponse(
        str(abs_pdf_path),
        media_type="application/pdf",
        filename=f"FixiLab_Audit_Report_{audit.filename}.pdf",
    )
