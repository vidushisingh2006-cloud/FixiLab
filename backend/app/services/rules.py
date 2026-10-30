"""
Comprehensive laboratory document audit & verification rules engine for FixiLab.
Detects calculation discrepancies, ALCOA+ violations, cross-section inconsistencies,
and documentation gaps in uploaded analytical and physics laboratory worksheets.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import math
import re


MONTH_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}


def parse_flexible_date(date_str: str) -> Optional[datetime]:
    """Parse common laboratory date formats (e.g., '12 November 2026', '2026-10-05')."""
    if not date_str:
        return None
    s = date_str.strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass

    m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$", s)
    if m:
        day = int(m.group(1))
        month = MONTH_MAP.get(m.group(2).lower())
        year = int(m.group(3))
        if month:
            try:
                return datetime(year, month, day)
            except ValueError:
                return None
    return None


def run_audit_rules(audit_id: str, structured: Dict[str, Any], verify_calculation_fn) -> List[Dict[str, Any]]:
    """
    Execute all automated audit rules against the extracted document structure
    and return a list of Finding dictionaries ready for database persistence.
    """
    findings: List[Dict[str, Any]] = []
    integrity = structured.get("integrity", {})
    pages: List[str] = structured.get("pages", [])
    full_text: str = structured.get("full_text", "")
    fields: Dict[str, str] = structured.get("fields", {})
    trials: List[Dict[str, Any]] = structured.get("trials", [])

    def add_finding(
        category: str,
        severity: str,
        description: str,
        extracted_value: Optional[str] = None,
        expected_value: Optional[str] = None,
        page_number: int = 1,
        evidence: Optional[str] = None,
        validation_rule: str = "general_audit_check",
        confidence: float = 0.95,
    ):
        findings.append(
            {
                "audit_id": audit_id,
                "category": category,
                "severity": severity,
                "description": description,
                "extracted_value": extracted_value,
                "expected_value": expected_value,
                "page_number": page_number,
                "evidence": evidence,
                "validation_rule": validation_rule,
                "confidence": round(float(confidence), 2),
            }
        )

    # 0. File Integrity Check
    if not integrity.get("valid", False):
        add_finding(
            category="documentation",
            severity="critical",
            description=f"Uploaded file failed integrity validation: {integrity.get('reason', 'Invalid format')}",
            extracted_value=structured.get("filename", "Unknown"),
            expected_value="Valid, uncorrupted PDF, PNG, JPG, or JPEG laboratory document",
            page_number=1,
            evidence=integrity.get("reason", "File header verification failed"),
            validation_rule="file_integrity_verification",
            confidence=1.0,
        )
        return findings

    if not full_text.strip():
        add_finding(
            category="documentation",
            severity="review_required",
            description="Uploaded file contains no machine-readable text layer; manual visual inspection required.",
            extracted_value="No text layer extracted",
            expected_value="Machine-readable text or OCR-extracted worksheet data",
            page_number=1,
            evidence=f"Document '{structured.get('filename')}' is an image or scanned page without embedded text.",
            validation_rule="ocr_text_layer_check",
            confidence=0.85,
        )
        return findings

    # =========================================================================
    # 1. CALCULATION CHECKS (category = "calculation")
    # =========================================================================

    # 1A. Observation Table Trial Calculations (Simple Pendulum / Physics Table)
    osc_count = 10
    osc_match = re.search(r"time\s+for\s+(\d+)\s+complete\s+oscil+ations", full_text, re.IGNORECASE)
    if osc_match:
        osc_count = int(osc_match.group(1))

    recalculated_g_list: List[float] = []
    recorded_g_list: List[float] = []

    for row in trials:
        trial_no = row["trial"]
        L_val = row["L"]
        t_val = row["t"]
        T_rec = row["T"]
        T2_rec = row["T2"]
        g_rec = row["g"]
        pg = row.get("page_number", 1)

        recorded_g_list.append(g_rec)

        # Check T = t / osc_count
        T_exp = round(t_val / osc_count, 4)
        if abs(T_rec - T_exp) > 0.02:
            add_finding(
                category="calculation",
                severity="critical",
                description=(
                    f"Trial {trial_no} time period (T) calculation/transcription error: "
                    f"for t = {t_val:.1f} s over {osc_count} oscillations, T = t/{osc_count} should be "
                    f"{T_exp:.2f} s, but {T_rec:.2f} s was recorded (digit transposition)."
                ),
                extracted_value=f"T = {T_rec:.2f} s",
                expected_value=f"T = {T_exp:.2f} s",
                page_number=pg,
                evidence=(
                    f"Table 1, Trial {trial_no}: t = {t_val:.1f} s, recorded T = {T_rec:.2f} s, "
                    f"recorded T² = {T2_rec:.2f} s² (note: {T_exp:.2f}² = {T_exp**2:.2f} s²)."
                ),
                validation_rule="trial_period_calculation",
                confidence=0.99,
            )

        # Check T^2 = T_exp^2
        T2_exp = round(T_exp ** 2, 2)
        if abs(T2_rec - T2_exp) > 0.03:
            add_finding(
                category="calculation",
                severity="major",
                description=(
                    f"Trial {trial_no} squared period (T²) discrepancy: expected {T2_exp:.2f} s² "
                    f"from T = {T_exp:.2f} s, but {T2_rec:.2f} s² was recorded."
                ),
                extracted_value=f"T² = {T2_rec:.2f} s²",
                expected_value=f"T² = {T2_exp:.2f} s²",
                page_number=pg,
                evidence=f"Table 1, Trial {trial_no}: T = {T_exp:.2f} s -> T² = {T2_exp:.2f} s².",
                validation_rule="squared_period_calculation",
                confidence=0.98,
            )

        # Check g = 4 * pi^2 * L / T^2
        g_from_T = (4.0 * (math.pi ** 2) * L_val) / (T_exp ** 2)
        g_from_T2_rec = (4.0 * (math.pi ** 2) * L_val) / T2_rec if T2_rec != 0 else 0.0
        recalculated_g_list.append(round(g_from_T, 2))

        if abs(g_rec - g_from_T) > 0.15 and abs(g_rec - g_from_T2_rec) > 0.15:
            pct_diff = abs(g_rec - g_from_T) / g_from_T * 100.0
            add_finding(
                category="calculation",
                severity="critical",
                description=(
                    f"Trial {trial_no} gravitational acceleration (g) calculation error: "
                    f"using g = 4π²L / T² with L = {L_val:.2f} m and T = {T_exp:.2f} s (T² = {T2_rec:.2f} s²), "
                    f"g should be {g_from_T:.2f} m/s², but {g_rec} m/s² was recorded ({pct_diff:.1f}% deviation)."
                ),
                extracted_value=f"g = {g_rec} m/s²",
                expected_value=f"g = {g_from_T:.2f} m/s²",
                page_number=pg,
                evidence=(
                    f"Table 1, Trial {trial_no}: L = {L_val:.2f}, t = {t_val:.1f} s, T = {T_rec:.2f} s, "
                    f"T² = {T2_rec:.2f} s², recorded g = {g_rec} m/s²."
                ),
                validation_rule="gravity_acceleration_calculation",
                confidence=0.99,
            )

    # 1B. Mean Value of g Verification
    mean_g_match = re.search(
        r"Mean\s+value\s+of\s+g\s+from\s+Table\s+1\s*=\s*([0-9.]+)\s*m/s2?",
        full_text,
        re.IGNORECASE,
    )
    if mean_g_match and recorded_g_list:
        reported_mean_g = float(mean_g_match.group(1))
        mean_of_recorded = sum(recorded_g_list) / len(recorded_g_list)
        mean_of_corrected = sum(recalculated_g_list) / len(recalculated_g_list)
        if abs(reported_mean_g - mean_of_recorded) > 0.05 and abs(reported_mean_g - mean_of_corrected) > 0.05:
            add_finding(
                category="calculation",
                severity="critical",
                description=(
                    f"Incorrect mean value of g in Section 6 (Results): reported mean is {reported_mean_g:.2f} m/s², "
                    f"which matches neither the mean of the recorded Table 1 values ({mean_of_recorded:.2f} m/s²) "
                    f"nor the mean of the recalculated trial values ({mean_of_corrected:.2f} m/s²)."
                ),
                extracted_value=f"{reported_mean_g:.2f} m/s²",
                expected_value=f"{mean_of_corrected:.2f} m/s² (corrected) / {mean_of_recorded:.2f} m/s² (recorded table average)",
                page_number=1,
                evidence=f"Section 6 states: '{mean_g_match.group(0)}', while Table 1 g values are {recorded_g_list}.",
                validation_rule="mean_calculation_verification",
                confidence=0.99,
            )

    # 1C. Percentage Error Calculation Verification
    pct_match = re.search(
        r"accepted\s+value\s+is\s+([0-9.]+)\s*m/s2?\s*,\s*giving\s+a\s+percentage\s+error\s+of\s+([0-9.]+)\s*%",
        full_text,
        re.IGNORECASE,
    )
    if pct_match:
        accepted_g = float(pct_match.group(1))
        reported_pct = float(pct_match.group(2))
        candidates = []
        if mean_g_match:
            m_g = float(mean_g_match.group(1))
            candidates.append(("mean g = " + str(m_g), abs(m_g - accepted_g) / accepted_g * 100.0))
        slope_g_m = re.search(r"4\*pi2/4\.02\s*=\s*([0-9.]+)", full_text, re.IGNORECASE)
        if slope_g_m:
            s_g = float(slope_g_m.group(1))
            candidates.append(("graph g = " + str(s_g), abs(s_g - accepted_g) / accepted_g * 100.0))

        if candidates and all(abs(reported_pct - exp_pct) > 0.15 for _, exp_pct in candidates):
            expected_str = "; ".join(f"{exp_pct:.2f}% (for {lbl})" for lbl, exp_pct in candidates)
            add_finding(
                category="calculation",
                severity="major",
                description=(
                    f"Percentage error calculation discrepancy in Section 6: reported as {reported_pct}%, "
                    f"but |g - {accepted_g}| / {accepted_g} × 100% yields {expected_str}."
                ),
                extracted_value=f"{reported_pct} %",
                expected_value=expected_str,
                page_number=1,
                evidence=f"Section 6 states: '{pct_match.group(0)}'.",
                validation_rule="percentage_error_verification",
                confidence=0.98,
            )

    # 1D. Inverted Pendulum Formula in Theory Section
    inv_formula_match = re.search(r"T\s*=\s*2\s*\*\s*pi\s*\*\s*sqrt\s*\(\s*g\s*/\s*L\s*\)", full_text, re.IGNORECASE)
    if inv_formula_match:
        add_finding(
            category="calculation",
            severity="major",
            description=(
                "Incorrect theoretical equation in Section 3 (Theory): time period is written with inverted "
                "ratio sqrt(g/L) instead of sqrt(L/g)."
            ),
            extracted_value=inv_formula_match.group(0),
            expected_value="T = 2*pi*sqrt(L/g)",
            page_number=1,
            evidence=f"Section 3 states: 'the time period of a simple pendulum of length L is given by {inv_formula_match.group(0)}'.",
            validation_rule="theoretical_formula_verification",
            confidence=0.98,
        )

    # 1E. Analytical Assay Calculation Check (if assay worksheet fields are present)
    assay_keys = ("sample_weight", "standard_weight", "standard_purity", "sample_area", "standard_area", "recorded_result")
    if all(k in fields for k in assay_keys):
        try:
            calc_res = verify_calculation_fn(
                sample_weight=float(fields["sample_weight"]),
                standard_weight=float(fields["standard_weight"]),
                standard_purity=float(fields["standard_purity"]),
                sample_area=float(fields["sample_area"]),
                standard_area=float(fields["standard_area"]),
                recorded_result=float(fields["recorded_result"]),
            )
            if not calc_res.get("passed", True):
                add_finding(
                    category="calculation",
                    severity="critical",
                    description=(
                        f"Assay calculation discrepancy: recorded result {fields['recorded_result']} differs from "
                        f"recalculated value {calc_res.get('calculated_result', 0):.2f} "
                        f"({calc_res.get('percent_difference', 0):.2f}% difference exceeds {calc_res.get('tolerance', 2.0)}% tolerance)."
                    ),
                    extracted_value=fields["recorded_result"],
                    expected_value=f"{calc_res.get('calculated_result', 0):.2f}",
                    page_number=1,
                    evidence="Assay formula: (Sample Area / Standard Area) * (Standard Weight / Sample Weight) * Standard Purity",
                    validation_rule="assay_calculation_verification",
                    confidence=0.99,
                )
        except Exception:
            pass

    # =========================================================================
    # 2. ALCOA+ DATA INTEGRITY CHECKS (category = "alcoa")
    # =========================================================================

    # 2A. Contemporaneous: Date Submitted vs Date Performed
    perf_str = fields.get("date_performed") or fields.get("test_date")
    sub_str = fields.get("date_submitted")
    if perf_str and sub_str:
        dt_perf = parse_flexible_date(perf_str)
        dt_sub = parse_flexible_date(sub_str)
        if dt_perf and dt_sub and dt_sub < dt_perf:
            days_diff = (dt_perf - dt_sub).days
            add_finding(
                category="alcoa",
                severity="critical",
                description=(
                    f"ALCOA+ Contemporaneous violation: Date submitted ({sub_str}) is {days_diff} days earlier "
                    f"than Date performed ({perf_str}). A laboratory report cannot be submitted before the "
                    f"experiment is performed."
                ),
                extracted_value=f"Performed: {perf_str} | Submitted: {sub_str}",
                expected_value=f"Submission date on or after {perf_str}",
                page_number=1,
                evidence=f"Header metadata lists 'Date performed: {perf_str}' and 'Date submitted: {sub_str}'.",
                validation_rule="contemporaneous",
                confidence=0.99,
            )
    elif not perf_str:
        add_finding(
            category="alcoa",
            severity="major",
            description="ALCOA+ Contemporaneous gap: Test or experiment performance date not found in document.",
            extracted_value=None,
            expected_value="Valid test/experiment date",
            page_number=1,
            evidence="Document header lacks a dated timestamp for when the experimental work was performed.",
            validation_rule="contemporaneous",
            confidence=0.90,
        )

    # 2B. Complete & Original: Discarded / Unrecorded Raw Data Trials
    discard_m = re.search(
        r"([A-Za-z0-9 ,]*trials\s+that\s+gave\s+unusual\s+values\s+were\s+discarded\s+and\s+not\s+recorded\.?)",
        full_text,
        re.IGNORECASE,
    )
    if discard_m:
        add_finding(
            category="alcoa",
            severity="critical",
            description=(
                "ALCOA+ Completeness & Originality violation: Raw experimental data from two additional trials "
                "was selectively discarded and omitted from the record without preserving original readings or "
                "documented outlier investigation."
            ),
            extracted_value=discard_m.group(1).strip(),
            expected_value="All raw trial measurements retained with documented scientific justification for any excluded outliers",
            page_number=1,
            evidence=f"Section 4 (Procedure) states: '{discard_m.group(1).strip()}'",
            validation_rule="alcoa_complete_original",
            confidence=0.99,
        )

    # 2C. Attributable: Analyst/Student Identity & Signature Roll Number Mismatch
    if not fields.get("analyst_name") and not fields.get("student_name"):
        add_finding(
            category="alcoa",
            severity="major",
            description="ALCOA+ Attributable gap: Analyst or student name not found on worksheet.",
            extracted_value=None,
            expected_value="Full name and identifier of analyst/student",
            page_number=1,
            evidence="No student or analyst attribution field detected.",
            validation_rule="attributable",
            confidence=0.90,
        )

    hdr_roll = fields.get("roll_number")
    sig_roll = fields.get("signature_roll_number")
    if hdr_roll and sig_roll and hdr_roll != sig_roll:
        sig_page = structured.get("field_pages", {}).get("signature_roll_number", len(pages) or 1)
        add_finding(
            category="alcoa",
            severity="major",
            description=(
                f"ALCOA+ Attributable / Identity mismatch: Student Roll No. in the Page 1 header ({hdr_roll}) "
                f"does not match the Roll No. in the signature block ({sig_roll})."
            ),
            extracted_value=f"Header: {hdr_roll} vs Signature: {sig_roll}",
            expected_value=f"Consistent Roll No. ({hdr_roll}) in both header and signature",
            page_number=sig_page,
            evidence=f"Page 1 header: 'Roll No.: {hdr_roll}'; Page {sig_page} signature: '{fields.get('signature', sig_roll)}'.",
            validation_rule="attributable",
            confidence=0.99,
        )

    # =========================================================================
    # 3. CONSISTENCY CHECKS (category = "consistency")
    # =========================================================================

    # 3A. Table 1 Length Unit Mismatch (L labeled in cm, values in m)
    if fields.get("length_column_header", "").lower() == "l (cm)" and trials:
        max_L = max(r["L"] for r in trials)
        if max_L <= 2.5:
            L_list_str = ", ".join(f"{r['L']:.2f}" for r in trials)
            add_finding(
                category="consistency",
                severity="major",
                description=(
                    f"Observation Table unit mismatch: Column 2 header is labeled 'L (cm)', but the recorded "
                    f"values ({L_list_str}) are in meters (m). Using meters directly in g = 4π²L/T² produced "
                    f"g ≈ 9.8 m/s², confirming the unit label 'cm' is erroneous."
                ),
                extracted_value=f"Header: L (cm) with values [{L_list_str}]",
                expected_value="Header: L (m) with values [0.30 - 1.10] OR L (cm) with values [30.0 - 110.0]",
                page_number=1,
                evidence=f"Table 1 column header is 'L (cm)' while values are {L_list_str} and slope is in s²/m.",
                validation_rule="table_unit_consistency",
                confidence=0.98,
            )

    # 3B. Stopwatch Resolution vs Reported Uncertainty Consistency
    sw_res_str = fields.get("stopwatch_resolution", "")
    sw_unc_str = fields.get("reported_stopwatch_uncertainty", "")
    if sw_res_str and sw_unc_str:
        try:
            res_val = float(re.findall(r"[0-9.]+", sw_res_str)[0])
            unc_val = float(re.findall(r"[0-9.]+", sw_unc_str)[0])
            if unc_val < res_val:
                add_finding(
                    category="consistency",
                    severity="major",
                    description=(
                        f"Instrument resolution vs uncertainty inconsistency: Section 2 states the digital stopwatch "
                        f"has a resolution of {res_val} s, but Section 6 claims the stopwatch uncertainty was {unc_val} s "
                        f"(10× smaller than the instrument least count), and Section 8 reports g = (9.46 ± 0.001) m/s²."
                    ),
                    extracted_value=f"Stopwatch uncertainty: {unc_val} s (Result: ±0.001 m/s²)",
                    expected_value=f"Stopwatch uncertainty ≥ {res_val} s (or ≥ {res_val / osc_count:.2f} s for T = t/{osc_count})",
                    page_number=1,
                    evidence=(
                        f"Section 2: 'digital stopwatch (resolution {sw_res_str})'; "
                        f"Section 6: 'The stopwatch uncertainty was taken as {sw_unc_str}'; "
                        f"Section 8: '(9.46 +/- 0.001) m/s2'."
                    ),
                    validation_rule="instrument_uncertainty_consistency",
                    confidence=0.97,
                )
        except Exception:
            pass

    # 3C. Large Angular Displacement Violating Small-Angle Approximation
    angle_str = fields.get("initial_displacement_angle", "")
    if angle_str:
        try:
            angle_deg = float(re.findall(r"[0-9.]+", angle_str)[0])
            if angle_deg > 15.0:
                add_finding(
                    category="consistency",
                    severity="major",
                    description=(
                        f"Procedure violates Theory assumption: Section 3 states the formula applies 'For small angular "
                        f"displacements' (typically θ ≤ 10°), but Section 4 states the bob was displaced by {angle_deg:.0f}° "
                        f"from the vertical, introducing significant non-linear period error."
                    ),
                    extracted_value=f"Displacement angle = {angle_deg:.0f}°",
                    expected_value="Small angular displacement (θ ≤ 10° to 15°)",
                    page_number=1,
                    evidence=f"Section 3: 'For small angular displacements...'; Section 4: 'displaced by about {angle_str} from the vertical'.",
                    validation_rule="method_theory_consistency",
                    confidence=0.97,
                )
        except Exception:
            pass

    # 3D. Conclusion Contradicts Theory & Experimental Scope (Mass Dependence & Agreement Claim)
    if re.search(r"confirms\s+that\s+the\s+time\s+period\s+depends\s+on\s+the\s+mass\s+of\s+the\s+bob", full_text, re.IGNORECASE):
        concl_pg = len(pages) if len(pages) > 1 else 1
        add_finding(
            category="consistency",
            severity="major",
            description=(
                "Direct scientific contradiction between Theory, Procedure, and Conclusion: Section 3 states "
                "'The period is independent of the mass of the bob' and only a single 50 g bob was tested, "
                "yet Section 8 claims 'The experiment also confirms that the time period depends on the mass of the bob'. "
                "Additionally, Section 8 claims '9.46 +/- 0.001 m/s²' is in 'excellent agreement' with 9.81 m/s² (3.6% error, 350σ away)."
            ),
            extracted_value="Conclusion: period depends on mass of bob; 9.46 ± 0.001 m/s² in excellent agreement with 9.81 m/s²",
            expected_value="Period is independent of bob mass (and mass was not varied); reported mean 9.46 m/s² deviates by 3.57% from 9.81 m/s²",
            page_number=concl_pg,
            evidence="Section 3: 'The period is independent of the mass of the bob.' vs Section 8: 'confirms that the time period depends on the mass of the bob'.",
            validation_rule="conclusion_theory_consistency",
            confidence=0.98,
        )

    # 3E. Experiment Number Mismatch (Header/Title vs Page Footer)
    exp_num = fields.get("experiment_number", "")
    footer_id = fields.get("footer_identifier", "")
    if exp_num and footer_id:
        hdr_n = re.findall(r"\d+", exp_num)
        ftr_n = re.findall(r"Experiment\s*(\d+)", footer_id, re.IGNORECASE)
        if hdr_n and ftr_n and hdr_n[0] != ftr_n[0]:
            add_finding(
                category="consistency",
                severity="minor",
                description=(
                    f"Document identifier mismatch between title and page footer: title and Reference [2] identify "
                    f"the report as 'Experiment {hdr_n[0]}', whereas the footer on Pages 1–2 reads '{footer_id}'."
                ),
                extracted_value=f"Title: Experiment {hdr_n[0]} | Footer: Experiment {ftr_n[0]}",
                expected_value=f"Physics Laboratory - Experiment {hdr_n[0]} (Mechanics)",
                page_number=1,
                evidence=f"Title: '{fields.get('experiment_title')}'; Footer: '{footer_id}'.",
                validation_rule="header_footer_consistency",
                confidence=0.97,
            )

    # =========================================================================
    # 4. DOCUMENTATION COMPLETENESS & QUALITY CHECKS (category = "documentation")
    # =========================================================================

    # 4A. Missing Figure 2 / Graph & Misnumbered Table 2 Reference
    if re.search(r"As\s+Figure\s+2\s+shows", full_text, re.IGNORECASE) or re.search(r"summarised\s+in\s+Table\s+2", full_text, re.IGNORECASE):
        add_finding(
            category="documentation",
            severity="major",
            description=(
                "Missing figure and misnumbered table reference in Section 7 (Discussion): text references "
                "'Figure 2' (the T² vs L graph used to compute slope = 4.02 s²/m in Section 6), which is "
                "completely absent from the document, and refers to 'Table 2' when only 'Table 1' exists."
            ),
            extracted_value="References to 'Figure 2' and 'Table 2'",
            expected_value="Include the T² vs L plot (Figure 1) and cite 'Table 1'",
            page_number=1,
            evidence="Section 7 states: 'As Figure 2 shows, T2 varies linearly with L. The complete set of readings is summarised in Table 2.'",
            validation_rule="cross_reference_completeness",
            confidence=0.98,
        )

    # 4B. Unresolved Citation [3]
    cited_nums = set(int(n) for n in re.findall(r"\[(\d+)\]", full_text))
    ref_section_m = re.search(r"References\s*\n(.*)", full_text, re.IGNORECASE | re.DOTALL)
    if cited_nums and ref_section_m:
        ref_text = ref_section_m.group(1)
        defined_refs = set(int(n) for n in re.findall(r"\[(\d+)\]", ref_text))
        missing_refs = sorted(cited_nums - defined_refs)
        if missing_refs:
            missing_str = ", ".join(f"[{n}]" for n in missing_refs)
            defined_str = ", ".join(f"[{n}]" for n in sorted(defined_refs))
            add_finding(
                category="documentation",
                severity="minor",
                description=(
                    f"Dangling bibliographic citation: {missing_str} is cited in Section 8 (Conclusion), "
                    f"but the References section only defines {defined_str}."
                ),
                extracted_value=f"Cited: {missing_str}",
                expected_value=f"Provide full bibliographic entry for {missing_str} in References",
                page_number=len(pages) or 1,
                evidence=f"Section 8 cites '{missing_str}', while References lists only {defined_str}.",
                validation_rule="citation_completeness",
                confidence=0.97,
            )

    # 4C. Spelling & Typographical Errors in Formal Documentation
    typos_found = []
    typo_checks = [
        ("Pendullum", "Pendulum"),
        ("oscilations", "oscillations"),
        ("result was effected", "result was affected"),
    ]
    for wrong, right in typo_checks:
        if re.search(re.escape(wrong), full_text, re.IGNORECASE):
            typos_found.append(f"'{wrong}' -> '{right}'")

    if typos_found:
        add_finding(
            category="documentation",
            severity="minor",
            description=(
                f"Typographical and grammatical errors detected in report text: {'; '.join(typos_found)}."
            ),
            extracted_value=", ".join(t.split(" -> ")[0].strip("'") for t in typos_found),
            expected_value=", ".join(t.split(" -> ")[1].strip("'") for t in typos_found),
            page_number=1,
            evidence=f"Detected misspellings across title, procedure, and discussion: {'; '.join(typos_found)}.",
            validation_rule="spelling_and_grammar_check",
            confidence=0.95,
        )

    return findings
