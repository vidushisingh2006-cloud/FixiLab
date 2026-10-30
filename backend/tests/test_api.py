import pymupdf
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.api import audits
from app.database import Base, get_db
from app.main import app
from app.services import reports


client = TestClient(app)


@pytest.fixture
def audit_client(tmp_path, monkeypatch):
    database_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{database_path}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    uploads_dir = tmp_path / "uploads"
    reports_dir = tmp_path / "reports"
    uploads_dir.mkdir()
    reports_dir.mkdir()
    monkeypatch.setattr(audits, "UPLOAD_DIR", uploads_dir)
    monkeypatch.setattr(audits, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(reports, "REPORTS_DIR", reports_dir)
    # Background tasks open their own session; point them at the test database.
    monkeypatch.setattr(audits, "SessionLocal", test_session)
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        engine.dispose()


def _worksheet_pdf() -> bytes:
    document = pymupdf.open()
    document.new_page().insert_text(
        (72, 72),
        "Physics Laboratory - Experiment 9\n"
        "Experiment 9: Simple Pendulum\n"
        "Analyst: Jane Doe\n"
        "Roll No.: 21BT045\n"
        "Test date: 2026-10-30\n"
        "Date submitted: 2026-10-01\n",
    )
    content = document.tobytes()
    document.close()
    return content


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "FixiLab" in response.json()["message"]


def test_upload_review_and_report(audit_client):
    content = _worksheet_pdf()

    upload_response = audit_client.post(
        "/api/audits",
        data={
            "filename": "worksheet.pdf",
            "file_size": str(len(content)),
            "mime_type": "application/pdf",
        },
        files={"file": ("worksheet.pdf", content, "application/pdf")},
    )
    assert upload_response.status_code == 200
    audit_id = upload_response.json()["id"]

    # Uploading an invalid worksheet immediately produces findings.
    uploaded_detail = audit_client.get(f"/api/audits/{audit_id}").json()
    assert uploaded_detail["status"] == "completed"
    assert len(uploaded_detail["findings"]) >= 1

    preview_response = audit_client.get(f"/api/audits/{audit_id}/file")
    assert preview_response.status_code == 200
    assert preview_response.content.startswith(b"%PDF-")

    extraction_response = audit_client.post(f"/api/audits/{audit_id}/extract")
    assert extraction_response.status_code == 200
    assert len(extraction_response.json()["extraction_results"]) >= 1

    validation_response = audit_client.post(f"/api/audits/{audit_id}/validate")
    assert validation_response.status_code == 200
    assert validation_response.json()["findings_count"] >= 1

    audit = audit_client.get(f"/api/audits/{audit_id}").json()
    assert audit["status"] == "completed"
    assert any(f["review_status"] == "open" for f in audit["findings"])

    review_response = audit_client.patch(
        f"/api/audits/{audit_id}/findings/{audit['findings'][0]['id']}",
        json={"review_status": "resolved", "reviewer_comments": "Calculation checked"},
    )
    assert review_response.status_code == 200
    assert review_response.json()["review_status"] == "resolved"
    assert review_response.json()["reviewer_comments"] == "Calculation checked"

    report_response = audit_client.get(f"/api/audits/{audit_id}/report")
    assert report_response.status_code == 200
    assert report_response.headers["content-type"] == "application/pdf"
    assert report_response.content.startswith(b"%PDF-")


def test_upload_rejects_mismatched_file_content(audit_client):
    content = b"not a PDF"
    response = audit_client.post(
        "/api/audits",
        data={
            "filename": "worksheet.pdf",
            "file_size": str(len(content)),
            "mime_type": "application/pdf",
        },
        files={"file": ("worksheet.pdf", content, "application/pdf")},
    )

    assert response.status_code == 400


def test_upload_rejects_unsupported_extension(audit_client):
    content = b"plain text"
    response = audit_client.post(
        "/api/audits",
        data={
            "filename": "notes.txt",
            "file_size": str(len(content)),
            "mime_type": "text/plain",
        },
        files={"file": ("notes.txt", content, "text/plain")},
    )

    assert response.status_code == 415
