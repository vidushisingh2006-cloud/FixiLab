import pymupdf

from app.services.pdf_reader import verify_file_integrity
from app.services.validation import (
    check_alcoa_principles,
    validate_document,
    verify_calculation,
)


def _write_pdf(tmp_path, text: str):
    path = tmp_path / "worksheet.pdf"
    document = pymupdf.open()
    document.new_page().insert_text((72, 72), text)
    document.save(path)
    document.close()
    return path


def test_verify_calculation_correct():
    """Test calculation verification with correct values."""
    result = verify_calculation(
        sample_weight=50.0,
        standard_weight=100.0,
        standard_purity=99.8,
        sample_area=10051,
        standard_area=10234,
        recorded_result=98.04,
        tolerance=2.0,
    )

    assert result["passed"] is True
    assert result["percent_difference"] <= 2.0


def test_verify_calculation_incorrect():
    """Test calculation verification with incorrect values."""
    result = verify_calculation(
        sample_weight=50.0,
        standard_weight=100.0,
        standard_purity=99.8,
        sample_area=10051,
        standard_area=10234,
        recorded_result=99.12,  # Incorrect value
        tolerance=2.0,
    )

    assert result["passed"] is False
    assert result["percent_difference"] > 2.0


def test_verify_calculation_zero_division():
    """Test calculation verification handles zero division."""
    result = verify_calculation(
        sample_weight=0,
        standard_weight=100.0,
        standard_purity=99.8,
        sample_area=10051,
        standard_area=10234,
        recorded_result=98.04,
        tolerance=2.0,
    )

    assert "error" in result
    assert result["passed"] is False


def test_check_alcoa_principles_missing_data():
    """Test ALCOA+ checks with missing required fields."""
    findings = check_alcoa_principles({})

    assert any(f["validation_rule"] == "attributable" for f in findings)
    assert any(f["validation_rule"] == "contemporaneous" for f in findings)


def test_check_alcoa_principles_complete_data():
    """Test ALCOA+ checks with complete data."""
    findings = check_alcoa_principles(
        {"analyst_name": "John Doe", "test_date": "2026-01-30"}
    )

    assert findings == []


def test_verify_file_integrity_accepts_valid_pdf(tmp_path):
    path = _write_pdf(tmp_path, "Analyst: Jane Doe")
    result = verify_file_integrity(str(path), "application/pdf")

    assert result["valid"] is True


def test_verify_file_integrity_rejects_fake_pdf(tmp_path):
    path = tmp_path / "fake.pdf"
    path.write_bytes(b"not a pdf")
    result = verify_file_integrity(str(path), "application/pdf")

    assert result["valid"] is False


def test_validate_document_flags_documentation_gap(tmp_path):
    """A worksheet submitted before the experiment is performed is flagged."""
    path = _write_pdf(
        tmp_path,
        "Analyst: Jane Doe\n"
        "Test date: 2026-10-30\n"
        "Date submitted: 2026-10-01",
    )

    findings = validate_document("audit-1", str(path), None, "application/pdf")

    assert findings
    assert all(finding["audit_id"] == "audit-1" for finding in findings)
    assert any(
        finding["validation_rule"] == "contemporaneous" for finding in findings
    )
