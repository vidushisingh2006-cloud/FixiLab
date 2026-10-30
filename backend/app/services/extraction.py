from typing import List, Dict, Any
import os
import re

from app.services.pdf_reader import (
    verify_file_integrity,
    read_pdf_document,
    read_image_document,
)


def _clean_original_filename(file_path: str) -> str:
    """Strip the internal '<uuid>_' prefix added during upload."""
    basename = os.path.basename(file_path)
    return re.sub(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}_",
        "",
        basename,
    )


def _find_page_for_snippet(pages: List[str], snippet: str) -> int:
    """Return 1-indexed page number containing snippet, defaulting to 1."""
    needle = " ".join(snippet.lower().split())
    for idx, page_text in enumerate(pages, start=1):
        norm_page = " ".join(page_text.lower().split())
        if needle and needle in norm_page:
            return idx
    return 1


def extract_structured_data(file_path: str, mime_type: str = "application/pdf") -> Dict[str, Any]:
    """
    Parse the uploaded laboratory document into structured fields, observation
    table rows, and per-page text used by both the Extraction API and the
    Validation Engine.
    """
    integrity = verify_file_integrity(file_path, mime_type)
    clean_name = _clean_original_filename(file_path)

    result: Dict[str, Any] = {
        "integrity": integrity,
        "filename": clean_name,
        "pages": [],
        "full_text": "",
        "fields": {},
        "field_pages": {},
        "trials": [],
        "extraction_items": [],
    }

    def add_item(
        field_name: str,
        value: Any,
        page_number: int = 1,
        confidence: float = 0.95,
        source: str = "pdf_text",
    ):
        val_str = " ".join(str(value).split()).strip()
        if not val_str:
            return
        result["fields"][field_name] = val_str
        result["field_pages"][field_name] = page_number
        result["extraction_items"].append(
            {
                "field_name": field_name,
                "value": val_str,
                "page_number": page_number,
                "confidence": round(float(confidence), 2),
                "source": source,
            }
        )

    add_item("filename", clean_name, page_number=1, confidence=1.0, source="file_metadata")

    if not integrity.get("valid"):
        add_item(
            "file_integrity_status",
            f"Invalid file: {integrity.get('reason', 'Unknown error')}",
            page_number=1,
            confidence=1.0,
            source="file_validator",
        )
        return result

    fmt = integrity.get("format", "")
    if fmt in ("png", "jpeg"):
        img_info = read_image_document(file_path)
        dims = (
            f"{img_info['width']}x{img_info['height']} px"
            if img_info.get("width") and img_info.get("height")
            else "Unknown dimensions"
        )
        add_item("image_format", f"{img_info.get('format', fmt.upper())} ({dims})", 1, 1.0, "image_header")
        if img_info.get("ocr_text"):
            result["pages"] = [img_info["ocr_text"]]
            result["full_text"] = img_info["ocr_text"]
        elif img_info.get("embedded_text"):
            joined = "\n".join(img_info["embedded_text"])
            result["pages"] = [joined]
            result["full_text"] = joined
        else:
            add_item(
                "ocr_status",
                "Image uploaded without embedded text layer; manual visual verification required.",
                1,
                0.75,
                "image_inspector",
            )
            return result
    else:
        pdf_data = read_pdf_document(file_path)
        result["pages"] = pdf_data.get("pages", [])
        result["full_text"] = pdf_data.get("full_text", "")
        result["pdf_metadata"] = pdf_data.get("metadata", {})
        add_item("page_count", str(pdf_data.get("page_count", 1)), 1, 1.0, "pdf_metadata")

    pages: List[str] = result["pages"]
    full_text: str = result["full_text"]
    if not full_text.strip():
        add_item(
            "extraction_warning",
            "No extractable text layer found in document (scanned page or blank document).",
            1,
            0.8,
            "pdf_parser",
        )
        return result

    # 1. Experiment Title & Experiment Number
    title_match = re.search(r"(Experiment\s*\d+\s*:\s*[^\n]+)", full_text, re.IGNORECASE)
    if title_match:
        title_val = title_match.group(1).strip()
        add_item("experiment_title", title_val, _find_page_for_snippet(pages, title_val), 0.98, "header_parser")
        exp_num_m = re.search(r"Experiment\s*(\d+)", title_val, re.IGNORECASE)
        if exp_num_m:
            add_item("experiment_number", f"Experiment {exp_num_m.group(1)}", 1, 0.98, "header_parser")

    # Footer Experiment Identifier
    footer_match = re.search(r"(Physics Laboratory\s*-\s*Experiment\s*\d+[^\n]*)", full_text, re.IGNORECASE)
    if footer_match:
        footer_val = footer_match.group(1).strip()
        add_item("footer_identifier", footer_val, _find_page_for_snippet(pages, footer_val), 0.96, "footer_parser")

    # 2. Student / Analyst Name
    student_match = re.search(
        r"(?:Student|Analyst|Prepared by)\s*:\s*\n?\s*([A-Za-z][A-Za-z .'-]{1,60}?)(?=\s*(?:\n|Roll\s*No|Date|Lab|Instructor|$))",
        full_text,
        re.IGNORECASE,
    )
    if student_match:
        student_name = student_match.group(1).strip()
        pg = _find_page_for_snippet(pages, student_name)
        add_item("analyst_name", student_name, pg, 0.97, "header_parser")
        add_item("student_name", student_name, pg, 0.97, "header_parser")

    # 3. Roll Number (Header) & Signature Roll Number
    roll_match = re.search(r"Roll\s*No\.?\s*:\s*\n?\s*([A-Za-z0-9-]+)", full_text, re.IGNORECASE)
    if roll_match:
        roll_no = roll_match.group(1).strip()
        add_item("roll_number", roll_no, _find_page_for_snippet(pages, roll_no), 0.98, "header_parser")

    sig_match = re.search(r"Signed\s*:\s*([^\n]+)", full_text, re.IGNORECASE)
    if sig_match:
        sig_val = sig_match.group(1).strip()
        pg = _find_page_for_snippet(pages, sig_val)
        add_item("signature", sig_val, pg, 0.96, "signature_parser")
        sig_roll_m = re.search(r"Roll\s*No\.?\s*([A-Za-z0-9-]+)", sig_val, re.IGNORECASE)
        if sig_roll_m:
            add_item("signature_roll_number", sig_roll_m.group(1).strip(), pg, 0.96, "signature_parser")

    # 4. Dates (Date performed / Test date & Date submitted)
    perf_match = re.search(
        r"(?:Date\s*performed|Test\s*date|Analysis\s*date)\s*:\s*\n?\s*([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}|[0-9]{4}-[0-9]{2}-[0-9]{2})",
        full_text,
        re.IGNORECASE,
    )
    if perf_match:
        perf_date = perf_match.group(1).strip()
        pg = _find_page_for_snippet(pages, perf_date)
        add_item("test_date", perf_date, pg, 0.98, "header_parser")
        add_item("date_performed", perf_date, pg, 0.98, "header_parser")

    sub_match = re.search(
        r"Date\s*submitted\s*:\s*\n?\s*([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}|[0-9]{4}-[0-9]{2}-[0-9]{2})",
        full_text,
        re.IGNORECASE,
    )
    if sub_match:
        sub_date = sub_match.group(1).strip()
        add_item("date_submitted", sub_date, _find_page_for_snippet(pages, sub_date), 0.98, "header_parser")

    # 5. Lab Partner & Instructor
    partner_match = re.search(
        r"Lab\s*partner\s*:\s*\n?\s*([A-Za-z][A-Za-z .'-]{1,60}?)(?=\s*(?:\n|Instructor|$))",
        full_text,
        re.IGNORECASE,
    )
    if partner_match:
        add_item("lab_partner", partner_match.group(1).strip(), 1, 0.95, "header_parser")

    inst_match = re.search(
        r"Instructor\s*:\s*\n?\s*([A-Za-z][A-Za-z .'-]{1,60}?)(?=\s*(?:\n|1\.|$))",
        full_text,
        re.IGNORECASE,
    )
    if inst_match:
        add_item("instructor", inst_match.group(1).strip(), 1, 0.95, "header_parser")

    # 6. Apparatus & Instrument Specifications
    sw_res_match = re.search(r"stopwatch\s*\(\s*resolution\s*([0-9.]+\s*s)\s*\)", full_text, re.IGNORECASE)
    if sw_res_match:
        add_item("stopwatch_resolution", sw_res_match.group(1).strip(), 1, 0.96, "apparatus_parser")

    scale_match = re.search(r"metre\s*scale\s*\(\s*least\s*count\s*([0-9.]+\s*mm)\s*\)", full_text, re.IGNORECASE)
    if scale_match:
        add_item("metre_scale_least_count", scale_match.group(1).strip(), 1, 0.96, "apparatus_parser")

    # 7. Theory Formula & Procedure Parameters
    formula_match = re.search(r"(T\s*=\s*2\s*\*\s*pi\s*\*\s*sqrt\s*\([^)]+\))", full_text, re.IGNORECASE)
    if formula_match:
        add_item("theory_period_formula", formula_match.group(1).strip(), 1, 0.95, "theory_parser")

    angle_match = re.search(r"displaced\s+by\s+about\s+(\d+\s*degrees)", full_text, re.IGNORECASE)
    if angle_match:
        add_item("initial_displacement_angle", angle_match.group(1).strip(), 1, 0.95, "procedure_parser")

    discard_match = re.search(r"([A-Za-z0-9 ,]+trials[^.]*discarded\s+and\s+not\s+recorded\.)", full_text, re.IGNORECASE)
    if discard_match:
        add_item("discarded_trials_statement", discard_match.group(1).strip(), 1, 0.96, "procedure_parser")

    # 8. Observation Table Column Header & Trials
    unit_hdr_match = re.search(r"Trial\s+(L\s*\([^)]+\))", full_text, re.IGNORECASE)
    if unit_hdr_match:
        add_item("length_column_header", unit_hdr_match.group(1).strip(), 1, 0.97, "table_parser")

    trial_pattern = re.compile(
        r"(?:^|\n)\s*([1-9])\s+(0\.\d+|1\.\d+|\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)(?=\s*(?:\n|$))"
    )
    for tm in trial_pattern.finditer(full_text):
        t_num = int(tm.group(1))
        L_val = float(tm.group(2))
        t_10 = float(tm.group(3))
        T_val = float(tm.group(4))
        T2_val = float(tm.group(5))
        g_val = float(tm.group(6))
        trial_row = {
            "trial": t_num,
            "L": L_val,
            "t": t_10,
            "T": T_val,
            "T2": T2_val,
            "g": g_val,
            "page_number": _find_page_for_snippet(pages, tm.group(0)),
        }
        result["trials"].append(trial_row)
        add_item(
            f"trial_{t_num}_observation",
            f"L={L_val:.2f}, t={t_10:.1f}s, T={T_val:.2f}s, T²={T2_val:.2f}s², g={g_val} m/s²",
            trial_row["page_number"],
            0.98,
            "table_parser",
        )

    # 9. Results, Uncertainties & Conclusion Claims
    mean_g_match = re.search(r"Mean\s+value\s+of\s+g\s+from\s+Table\s+1\s*=\s*([0-9.]+\s*m/s2?)", full_text, re.IGNORECASE)
    if mean_g_match:
        add_item("reported_mean_g", mean_g_match.group(1).strip(), 1, 0.97, "results_parser")

    slope_g_match = re.search(r"slope\s*=\s*([0-9.]+)\s*s2?/m\s*\)\s*,\s*g\s*=\s*[^=]+=\s*([0-9.]+)\s*m/s2?", full_text, re.IGNORECASE)
    if slope_g_match:
        add_item("graph_slope", f"{slope_g_match.group(1)} s²/m", 1, 0.96, "results_parser")
        add_item("graph_calculated_g", f"{slope_g_match.group(2)} m/s²", 1, 0.96, "results_parser")

    pct_err_match = re.search(r"percentage\s+error\s+of\s+([0-9.]+\s*%)", full_text, re.IGNORECASE)
    if pct_err_match:
        add_item("reported_percentage_error", pct_err_match.group(1).strip(), 1, 0.97, "results_parser")

    sw_unc_match = re.search(r"stopwatch\s+uncertainty\s+was\s+taken\s+as\s+([0-9.]+\s*s)", full_text, re.IGNORECASE)
    if sw_unc_match:
        add_item("reported_stopwatch_uncertainty", sw_unc_match.group(1).strip(), 1, 0.96, "results_parser")

    concl_g_match = re.search(r"value\s+of\s+g\s+was\s+found\s+to\s+be\s*\(([^)]+)\)\s*m/s2?", full_text, re.IGNORECASE)
    if concl_g_match:
        pg = _find_page_for_snippet(pages, concl_g_match.group(1))
        add_item("conclusion_reported_g", f"({concl_g_match.group(1).strip()}) m/s²", pg, 0.96, "conclusion_parser")

    # 10. Analytical Chemistry / Assay Worksheet Fields (if present in document)
    assay_patterns = {
        "sample_id": r"(?:Sample\s*ID|Sample\s*No\.?)\s*:\s*([A-Za-z0-9_-]+)",
        "batch_number": r"(?:Batch\s*No\.?|Lot\s*No\.?)\s*:\s*([A-Za-z0-9_-]+)",
        "sample_weight": r"Sample\s*Weight\s*:\s*([0-9.]+)",
        "standard_weight": r"Standard\s*Weight\s*:\s*([0-9.]+)",
        "standard_purity": r"Standard\s*Purity\s*:\s*([0-9.]+)",
        "sample_area": r"Sample\s*Area\s*:\s*([0-9.]+)",
        "standard_area": r"Standard\s*Area\s*:\s*([0-9.]+)",
        "recorded_result": r"(?:Recorded\s*Result|Assay\s*Result)\s*:\s*([0-9.]+)",
    }
    for key, pat in assay_patterns.items():
        m = re.search(pat, full_text, re.IGNORECASE)
        if m and key not in result["fields"]:
            add_item(key, m.group(1).strip(), _find_page_for_snippet(pages, m.group(0)), 0.95, "worksheet_parser")

    return result


def extract_document(file_path: str, mime_type: str) -> List[Dict[str, Any]]:
    """
    Extract text and structured laboratory fields from an uploaded document.
    Returns a list of ExtractionResult-compatible dictionaries.
    """
    structured = extract_structured_data(file_path, mime_type)
    return structured["extraction_items"]
