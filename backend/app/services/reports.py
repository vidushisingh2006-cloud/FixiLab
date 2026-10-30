from typing import Any, Dict, List
from pathlib import Path
import math
import textwrap

try:  # Prefer PyMuPDF so we can embed vector charts; fall back to the pure-Python writer.
    import pymupdf as _fitz
except Exception:  # pragma: no cover
    try:
        import fitz as _fitz  # type: ignore
    except Exception:
        _fitz = None

# Resolve backend/reports directory reliably
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = BACKEND_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _get_attr(obj: Any, key: str, default: Any = None) -> Any:
    """Safely read attribute or dict key from either SQLAlchemy model or dict."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


_WINANSI_REPLACEMENTS = {
    "²": "^2",
    "±": "+/-",
    "×": "x",
    "≥": ">=",
    "≤": "<=",
    "≈": "~",
    "π": "pi",
    "θ": "theta",
    "σ": "sigma",
    "—": "-",
    "–": "-",
    "’": "'",
    "‘": "'",
    "“": '"',
    "”": '"',
}


def _to_winansi(text: str) -> str:
    """Normalise text to characters representable in WinAnsi/Latin-1 encoding."""
    for k, v in _WINANSI_REPLACEMENTS.items():
        text = text.replace(k, v)
    return text.encode("latin1", errors="replace").decode("latin1")


def _pdf_escape(text: str) -> str:
    """Escape text for PDF literal strings in WinAnsi/Latin-1 encoding."""
    safe = _to_winansi(text)
    return safe.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _write_pure_python_pdf(pdf_path: Path, lines: List[str]) -> None:
    """
    Generate a valid multi-page PDF 1.4 document using only the Python standard library.
    """
    lines_per_page = 48
    pages_lines = [lines[i : i + lines_per_page] for i in range(0, max(1, len(lines)), lines_per_page)]

    objects: List[bytes] = []

    # 1: Catalog, 2: Pages, 3: Helvetica Font, 4: Helvetica-Bold Font
    page_obj_ids = []
    content_obj_ids = []
    next_id = 5
    for _ in pages_lines:
        page_obj_ids.append(next_id)
        content_obj_ids.append(next_id + 1)
        next_id += 2

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids_str = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
    objects.append(f"<< /Type /Pages /Kids [ {kids_str} ] /Count {len(page_obj_ids)} >>".encode("ascii"))
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")

    for idx, p_lines in enumerate(pages_lines):
        stream_cmds = ["BT", "/F1 10 Tf", "50 790 Td", "14 TL"]
        for line in p_lines:
            is_heading = line.startswith("===") or line.startswith("---") or line.startswith("FixiLab") or line.startswith("Finding ")
            font_cmd = "/F2 11 Tf" if is_heading else "/F1 9.5 Tf"
            escaped = _pdf_escape(line)
            stream_cmds.append(f"{font_cmd} ({escaped}) Tj T*")
        stream_cmds.append("ET")
        stream_bytes = "\n".join(stream_cmds).encode("latin1", errors="replace")

        page_dict = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
            f"/Contents {content_obj_ids[idx]} 0 R >>"
        ).encode("ascii")
        content_dict = (
            f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii")
            + stream_bytes
            + b"\nendstream"
        )
        objects.append(page_dict)
        objects.append(content_dict)

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for obj_num, obj_bytes in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{obj_num} 0 obj\n".encode("ascii"))
        out.extend(obj_bytes)
        out.extend(b"\nendobj\n")

    xref_pos = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    out.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii")
    )

    with open(pdf_path, "wb") as f:
        f.write(out)


# RGB colours approximating the FixiLab design tokens, used for the report charts.
_SEVERITY_COLORS = {
    "critical": (0.78, 0.28, 0.24),
    "major": (0.87, 0.68, 0.30),
    "minor": (0.42, 0.64, 0.54),
    "review_required": (0.60, 0.63, 0.62),
}
_STATUS_COLORS = {
    "open": (0.78, 0.28, 0.24),
    "needs_review": (0.87, 0.68, 0.30),
    "accepted": (0.42, 0.64, 0.54),
    "resolved": (0.32, 0.52, 0.44),
}
_DEFAULT_SLICE_COLOR = (0.60, 0.63, 0.62)
_SEVERITY_ORDER = ["critical", "major", "minor", "review_required"]
_STATUS_ORDER = ["open", "needs_review", "accepted", "resolved"]


def _ordered_slices(counts: Dict[str, int], colors: Dict[str, tuple], order: List[str]):
    """Return (label, count, colour) tuples in a stable, human-friendly order."""
    slices = []
    for key in order + [k for k in counts if k not in order]:
        count = counts.get(key, 0)
        if count <= 0:
            continue
        slices.append((key.replace("_", " ").title(), count, colors.get(key, _DEFAULT_SLICE_COLOR)))
    return slices


def _draw_pie(page: Any, center: Any, radius: float, slices: List[tuple], title: str) -> None:
    """Draw a pie chart with a legend at ``center`` using PyMuPDF drawing primitives."""
    heading = _to_winansi(title)
    page.insert_text(
        (center.x - radius, center.y - radius - 26),
        heading,
        fontsize=13,
        fontname="hebo",
        color=(0.19, 0.22, 0.20),
    )

    total = sum(count for _, count, _ in slices)
    if total <= 0:
        page.insert_text(
            (center.x - radius, center.y),
            "No data available",
            fontsize=11,
            fontname="helv",
            color=(0.5, 0.5, 0.5),
        )
        return

    shape = page.new_shape()
    start_angle = -math.pi / 2  # begin at 12 o'clock
    for _, count, color in slices:
        sweep = 2 * math.pi * count / total
        steps = 1 if count == total else max(3, int(sweep / (math.pi / 60)) + 1)
        arc_points = []
        for step in range(steps + 1):
            angle = start_angle + sweep * step / steps
            arc_points.append(
                _fitz.Point(
                    center.x + radius * math.cos(angle),
                    center.y + radius * math.sin(angle),
                )
            )
        # Close the wedge by returning to the first arc point (draw_polyline has no `closed`).
        points = [center] + arc_points + [arc_points[0]]
        shape.draw_polyline(points)
        shape.finish(color=(1, 1, 1), fill=color, width=0.8)
        start_angle += sweep
    shape.commit()

    swatch_x = center.x + radius + 26
    swatch_y = center.y - radius
    for label, count, color in slices:
        page.draw_rect(
            _fitz.Rect(swatch_x, swatch_y, swatch_x + 11, swatch_y + 11),
            color=None,
            fill=color,
        )
        page.insert_text(
            (swatch_x + 18, swatch_y + 10),
            _to_winansi(f"{label}: {count}"),
            fontsize=10,
            fontname="helv",
            color=(0.25, 0.28, 0.26),
        )
        swatch_y += 21


def _write_pdf_with_charts(
    pdf_path: Path,
    lines: List[str],
    severity_counts: Dict[str, int],
    status_counts: Dict[str, int],
) -> None:
    """Render the text report plus a visual summary page using PyMuPDF."""
    doc = _fitz.open()
    page_width, page_height = 595, 842
    margin = 50

    lines_per_page = 50
    chunks = [lines[i : i + lines_per_page] for i in range(0, max(1, len(lines)), lines_per_page)]
    for chunk in chunks:
        page = doc.new_page(width=page_width, height=page_height)
        text = _to_winansi("\n".join(chunk))
        page.insert_textbox(
            _fitz.Rect(margin, margin, page_width - margin, page_height - margin),
            text,
            fontsize=9.5,
            fontname="helv",
            color=(0.1, 0.1, 0.1),
            lineheight=1.35,
        )

    summary_page = doc.new_page(width=page_width, height=page_height)
    summary_page.insert_text(
        (margin, margin), "Visual Summary", fontsize=18, fontname="hebo", color=(0.16, 0.24, 0.20)
    )
    summary_page.insert_text(
        (margin, margin + 18),
        _to_winansi("Distribution of findings by severity and by review status."),
        fontsize=10,
        fontname="helv",
        color=(0.45, 0.48, 0.46),
    )

    severity_slices = _ordered_slices(severity_counts, _SEVERITY_COLORS, _SEVERITY_ORDER)
    status_slices = _ordered_slices(status_counts, _STATUS_COLORS, _STATUS_ORDER)

    _draw_pie(summary_page, _fitz.Point(180, 250), 92, severity_slices, "Severity Mix")
    _draw_pie(summary_page, _fitz.Point(180, 560), 92, status_slices, "Review Status")

    doc.save(str(pdf_path))
    doc.close()


def generate_report(audit: Any, findings: List[Any]) -> str:
    """
    Generate both a structured PDF audit report and a text report.
    Accepts either SQLAlchemy ORM instances (Audit, Finding) or dictionaries.
    Returns relative path to the generated PDF report.
    """
    audit_id = str(_get_attr(audit, "id", "unknown"))
    filename = str(_get_attr(audit, "filename", "N/A"))
    status = str(_get_attr(audit, "status", "completed"))
    created_at = str(_get_attr(audit, "created_at", "N/A"))

    pdf_filename = f"report_{audit_id}.pdf"
    txt_filename = f"report_{audit_id}.txt"
    pdf_path = REPORTS_DIR / pdf_filename
    txt_path = REPORTS_DIR / txt_filename

    severity_counts: Dict[str, int] = {}
    status_counts: Dict[str, int] = {}
    for finding in findings:
        sev = str(_get_attr(finding, "severity", "unknown"))
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        r_status = str(_get_attr(finding, "review_status", "open") or "open")
        status_counts[r_status] = status_counts.get(r_status, 0) + 1

    report_lines: List[str] = [
        "FixiLab Laboratory Documentation Audit Report",
        "=" * 68,
        f"Audit ID:   {audit_id}",
        f"Document:   {filename}",
        f"Status:     {status}",
        f"Created At: {created_at}",
        "",
        f"Findings Summary ({len(findings)} total)",
        "-" * 68,
    ]

    if severity_counts:
        for sev, count in severity_counts.items():
            report_lines.append(f"  - {sev.upper()}: {count}")
    else:
        report_lines.append("  No discrepancies or compliance gaps detected.")

    report_lines.append("")
    report_lines.append("Review Status Breakdown")
    report_lines.append("-" * 68)
    if status_counts:
        for st, count in status_counts.items():
            report_lines.append(f"  - {st.upper().replace('_', ' ')}: {count}")
    else:
        report_lines.append("  No findings awaiting review.")

    report_lines.append("")
    report_lines.append("Detailed Audit Findings")
    report_lines.append("-" * 68)

    for idx, finding in enumerate(findings, start=1):
        desc = str(_get_attr(finding, "description", "N/A"))
        sev = str(_get_attr(finding, "severity", "N/A"))
        cat = str(_get_attr(finding, "category", "N/A"))
        page_num = _get_attr(finding, "page_number", 1)
        extracted_val = _get_attr(finding, "extracted_value")
        expected_val = _get_attr(finding, "expected_value")
        evidence = _get_attr(finding, "evidence")
        rule = _get_attr(finding, "validation_rule")
        r_status = _get_attr(finding, "review_status", "open")
        r_comments = _get_attr(finding, "reviewer_comments")

        report_lines.append(f"Finding {idx}: [{sev.upper()}] ({cat.upper()}) - Page {page_num or 1}")
        for wrapped in textwrap.wrap(f"Description: {desc}", width=82):
            report_lines.append(f"  {wrapped}")
        if extracted_val:
            report_lines.append(f"  Recorded Value: {extracted_val}")
        if expected_val:
            report_lines.append(f"  Expected Value: {expected_val}")
        if evidence:
            for wrapped in textwrap.wrap(f"Evidence: {evidence}", width=82):
                report_lines.append(f"  {wrapped}")
        if rule:
            report_lines.append(f"  Validation Rule: {rule} | Review Status: {r_status}")
        if r_comments:
            report_lines.append(f"  Reviewer Comments: {r_comments}")
        report_lines.append("")

    report_lines.append("=" * 68)
    report_lines.append(
        "Disclaimer: Generated by FixiLab Documentation Audit Platform. Supports qualified human review."
    )

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")

    written_with_charts = False
    if _fitz is not None:
        try:
            _write_pdf_with_charts(pdf_path, report_lines, severity_counts, status_counts)
            written_with_charts = True
        except Exception as exc:  # pragma: no cover - defensive fallback
            print(f"[reports] PyMuPDF chart rendering failed, using text-only fallback: {exc}")

    if not written_with_charts:
        _write_pure_python_pdf(pdf_path, report_lines)

    return f"backend/reports/{pdf_filename}"
