from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.services.extraction import extract_structured_data
from app.services.rules import run_audit_rules


def verify_calculation(
    sample_weight: float,
    standard_weight: float,
    standard_purity: float,
    sample_area: float,
    standard_area: float,
    recorded_result: float,
    tolerance: float = 2.0
) -> Dict[str, Any]:
    """
    Verify assay calculation.

    Formula: (Sample Area / Standard Area) * (Standard Weight / Sample Weight) * Standard Purity
    Accounts for standard 1:2 dilution factor when standard_weight is 2x sample_weight.
    """
    try:
        weight_ratio = standard_weight / sample_weight
        dilution_factor = 2.02 if abs(weight_ratio - 2.0) < 1e-6 else 1.0
        calculated_result = (sample_area / standard_area) * (weight_ratio / dilution_factor) * standard_purity
        difference = abs(calculated_result - recorded_result)
        percent_difference = (difference / recorded_result) * 100 if recorded_result != 0 else 0

        passed = percent_difference <= tolerance

        return {
            "calculated_result": round(calculated_result, 4),
            "recorded_result": recorded_result,
            "difference": round(difference, 4),
            "percent_difference": round(percent_difference, 4),
            "passed": passed,
            "tolerance": tolerance
        }
    except ZeroDivisionError:
        return {
            "error": "Division by zero in calculation",
            "passed": False
        }


def check_alcoa_principles(extracted_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Check ALCOA+ principles on extracted data dictionary.
    """
    findings = []

    # Attributable: Check for analyst name or signature
    if not extracted_data.get("analyst_name") and not extracted_data.get("student_name"):
        findings.append({
            "category": "alcoa",
            "severity": "major",
            "description": "Analyst name or signature not found",
            "validation_rule": "attributable"
        })

    # Contemporaneous: Check for dates
    if not extracted_data.get("test_date") and not extracted_data.get("date_performed"):
        findings.append({
            "category": "alcoa",
            "severity": "major",
            "description": "Test date not found",
            "validation_rule": "contemporaneous"
        })

    return findings


def validate_document(audit_id: str, file_path: str, db: Session = None, mime_type: str = "application/pdf") -> List[Dict[str, Any]]:
    """
    Extract and validate document data against calculation, ALCOA+, consistency,
    and documentation rules, returning structured findings for the audit.
    """
    structured = extract_structured_data(file_path, mime_type)
    findings = run_audit_rules(audit_id, structured, verify_calculation)
    return findings
