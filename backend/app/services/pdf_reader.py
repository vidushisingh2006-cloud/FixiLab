"""
Document reader module for FixiLab.
Supports PDF and image (PNG, JPG, JPEG) documents using a multi-strategy
extraction pipeline:
1. PyMuPDF (fitz) if installed
2. pypdf / pdfplumber if installed
3. Pure-Python standard-library PDF stream parser (/ASCII85Decode + /FlateDecode)
   so extraction works out-of-the-box on any Python version (including Python 3.15)
   without requiring native C extensions.
4. Pillow / pytesseract or pure-Python binary header inspection for images.
"""

from typing import List, Dict, Any, Tuple
import base64
import os
import re
import struct
import zlib


def verify_file_integrity(file_path: str, mime_type: str = "") -> Dict[str, Any]:
    """
    Verify that the uploaded file exists, is non-empty, and has a valid
    format header matching PDF, PNG, or JPEG.
    """
    if not file_path or not os.path.exists(file_path):
        return {"valid": False, "reason": "Uploaded file not found on disk", "format": "missing"}

    size = os.path.getsize(file_path)
    if size == 0:
        return {"valid": False, "reason": "Uploaded file is empty (0 bytes)", "format": "empty"}

    with open(file_path, "rb") as f:
        header = f.read(1024)

    ext = os.path.splitext(file_path.lower())[1]

    if ext == ".pdf" or "pdf" in (mime_type or "").lower():
        if b"%PDF-" not in header:
            return {
                "valid": False,
                "reason": "File has .pdf extension/MIME type but lacks a valid %PDF- header",
                "format": "invalid_pdf",
            }
        return {"valid": True, "reason": "Valid PDF document", "format": "pdf", "size": size}

    if ext == ".png" or "png" in (mime_type or "").lower():
        if not header.startswith(b"\x89PNG\r\n\x1a\n"):
            return {
                "valid": False,
                "reason": "File has .png extension/MIME type but lacks a valid PNG signature",
                "format": "invalid_png",
            }
        return {"valid": True, "reason": "Valid PNG image", "format": "png", "size": size}

    if ext in (".jpg", ".jpeg") or "jpeg" in (mime_type or "").lower() or "jpg" in (mime_type or "").lower():
        if not header.startswith(b"\xff\xd8\xff"):
            return {
                "valid": False,
                "reason": "File has JPEG extension/MIME type but lacks a valid SOI marker",
                "format": "invalid_jpeg",
            }
        return {"valid": True, "reason": "Valid JPEG image", "format": "jpeg", "size": size}

    return {"valid": False, "reason": f"Unsupported file format ({ext})", "format": "unsupported"}


def _unescape_pdf_string(raw: str) -> str:
    """Unescape PDF literal string escapes."""
    out = []
    i = 0
    n = len(raw)
    while i < n:
        ch = raw[i]
        if ch == "\\" and i + 1 < n:
            nxt = raw[i + 1]
            if nxt in ("(", ")", "\\"):
                out.append(nxt)
                i += 2
                continue
            if nxt == "n":
                out.append("\n")
                i += 2
                continue
            if nxt == "r":
                out.append("\r")
                i += 2
                continue
            if nxt == "t":
                out.append("\t")
                i += 2
                continue
            if nxt.isdigit():
                octal = nxt
                j = i + 2
                while j < n and j < i + 4 and raw[j].isdigit():
                    octal += raw[j]
                    j += 1
                try:
                    out.append(chr(int(octal, 8)))
                except ValueError:
                    pass
                i = j
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def _extract_pdf_stdlib(file_path: str) -> Tuple[List[str], Dict[str, str]]:
    """
    Pure-Python standard-library PDF text and metadata extractor.
    Handles /ASCII85Decode, /FlateDecode, and uncompressed PDF content streams.
    """
    with open(file_path, "rb") as f:
        data = f.read()

    metadata: Dict[str, str] = {}
    for key in ("Title", "Author", "Subject", "Creator", "Producer", "CreationDate"):
        m = re.search(rf"/{key}\s*\(((?:\\.|[^\\)])*)\)".encode("ascii"), data)
        if m:
            metadata[key.lower()] = _unescape_pdf_string(m.group(1).decode("latin1", errors="ignore"))

    pages: List[str] = []
    stream_pattern = re.compile(rb"<<(.*?)>>\s*stream\r?\n(.*?)\s*endstream", re.DOTALL)

    for match in stream_pattern.finditer(data):
        header = match.group(1)
        raw_stream = match.group(2)
        if b"/Subtype /Image" in header or b"/Type /XRef" in header or b"/Type /ObjStm" in header:
            continue

        buf = raw_stream.strip()
        try:
            if b"ASCII85Decode" in header or b"A85" in header:
                if buf.endswith(b"~>"):
                    buf = buf[:-2]
                buf = base64.a85decode(buf, adobe=False)
            if b"FlateDecode" in header or b"Fl" in header:
                try:
                    buf = zlib.decompress(buf)
                except zlib.error:
                    buf = zlib.decompress(buf, -zlib.MAX_WBITS)
        except Exception:
            continue

        content = buf.decode("latin1", errors="ignore")
        if "BT" not in content and "Tj" not in content and "TJ" not in content:
            continue

        # Parse text positioning and string literals inside content stream
        lines: List[str] = []
        current_line: List[str] = []

        token_re = re.compile(
            r"\[(?:\\.|[^\]])*\]\s*TJ"
            r"|\((?:\\.|[^\\)])*\)\s*(?:Tj|'|\"|)"
            r"|-?\d+(?:\.\d+)?\s+(-?\d+(?:\.\d+)?)\s+Td"
            r"|-?\d+(?:\.\d+)?\s+(-?\d+(?:\.\d+)?)\s+TD"
            r"|\bT\*\b"
            r"|\bET\b"
        )

        for tok_match in token_re.finditer(content):
            tok = tok_match.group(0)
            td_y = tok_match.group(1) or tok_match.group(2)

            if tok.endswith("TJ") and tok.startswith("["):
                parts = re.findall(r"\((?:\\.|[^\\)])*\)", tok)
                seg = "".join(_unescape_pdf_string(p[1:-1]) for p in parts)
                if seg:
                    current_line.append(seg)
            elif tok.startswith("("):
                str_m = re.match(r"\(((?:\\.|[^\\)])*)\)", tok)
                if str_m:
                    seg = _unescape_pdf_string(str_m.group(1))
                    if seg:
                        current_line.append(seg)
            elif td_y is not None:
                try:
                    if abs(float(td_y)) > 1.0 and current_line:
                        lines.append(" ".join("".join(current_line).split()))
                        current_line = []
                except ValueError:
                    pass
            elif tok in ("T*", "ET"):
                if current_line:
                    lines.append(" ".join("".join(current_line).split()))
                    current_line = []

        if current_line:
            lines.append(" ".join("".join(current_line).split()))

        page_text = "\n".join(line for line in lines if line.strip())
        if page_text.strip():
            pages.append(page_text.strip())

    return pages, metadata


def read_pdf_document(file_path: str) -> Dict[str, Any]:
    """
    Read a PDF document and return its page texts, page count, and metadata.
    Tries PyMuPDF (fitz), then pypdf, then pure-Python stdlib extraction.
    """
    pages: List[str] = []
    metadata: Dict[str, str] = {}
    engine_used = "stdlib_pdf"

    # Strategy 1: PyMuPDF (fitz)
    try:
        import fitz  # type: ignore

        doc = fitz.open(file_path)
        if doc.metadata:
            for k, v in doc.metadata.items():
                if v:
                    metadata[k.lower()] = str(v)
        for page in doc:
            pages.append(page.get_text("text") or "")
        doc.close()
        if any(p.strip() for p in pages):
            engine_used = "pymupdf"
    except Exception:
        pages = []

    # Strategy 2: pypdf
    if not any(p.strip() for p in pages):
        try:
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(file_path)
            if reader.metadata:
                for k, v in reader.metadata.items():
                    if v:
                        metadata[str(k).lstrip("/").lower()] = str(v)
            for page in reader.pages:
                pages.append(page.extract_text() or "")
            if any(p.strip() for p in pages):
                engine_used = "pypdf"
        except Exception:
            pages = []

    # Strategy 3: Pure-Python stdlib stream parser (also enriches metadata)
    std_pages, std_meta = _extract_pdf_stdlib(file_path)
    for k, v in std_meta.items():
        if k not in metadata and v:
            metadata[k] = v

    if not any(p.strip() for p in pages) and std_pages:
        pages = std_pages
        engine_used = "stdlib_pdf"
    elif std_pages and len(std_pages) > len(pages):
        pages = std_pages

    return {
        "pages": pages,
        "page_count": len(pages) if pages else 1,
        "full_text": "\n\n".join(pages),
        "metadata": metadata,
        "engine": engine_used,
    }


def read_image_document(file_path: str) -> Dict[str, Any]:
    """
    Read a PNG/JPG/JPEG image and extract OCR text (if available) and image properties.
    """
    info: Dict[str, Any] = {
        "width": None,
        "height": None,
        "format": None,
        "ocr_text": "",
        "embedded_text": [],
    }

    with open(file_path, "rb") as f:
        data = f.read()

    # Pure-Python PNG header & text chunk parser
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        info["format"] = "PNG"
        width, height = struct.unpack(">II", data[16:24])
        info["width"] = width
        info["height"] = height
        pos = 8
        while pos + 8 <= len(data):
            length, chunk_type = struct.unpack(">I4s", data[pos : pos + 8])
            chunk_data = data[pos + 8 : pos + 8 + length]
            if chunk_type == b"tEXt":
                txt = chunk_data.replace(b"\x00", b": ").decode("latin1", errors="ignore")
                if txt.strip():
                    info["embedded_text"].append(txt.strip())
            elif chunk_type == b"IEND":
                break
            pos += 12 + length

    # Pure-Python JPEG SOF parser
    elif data.startswith(b"\xff\xd8"):
        info["format"] = "JPEG"
        pos = 2
        while pos + 4 <= len(data):
            if data[pos] != 0xFF:
                pos += 1
                continue
            marker = data[pos + 1]
            if marker in (0xD8, 0xD9):
                pos += 2
                continue
            seg_len = struct.unpack(">H", data[pos + 2 : pos + 4])[0]
            if marker in (0xC0, 0xC1, 0xC2) and pos + 9 <= len(data):
                height, width = struct.unpack(">HH", data[pos + 5 : pos + 9])
                info["width"] = width
                info["height"] = height
                break
            pos += 2 + seg_len

    # Try Pillow + pytesseract if available
    try:
        from PIL import Image  # type: ignore

        with Image.open(file_path) as img:
            info["width"], info["height"] = img.size
            info["format"] = img.format or info["format"]
            try:
                import pytesseract  # type: ignore

                ocr = pytesseract.image_to_string(img)
                if ocr and ocr.strip():
                    info["ocr_text"] = ocr.strip()
            except Exception:
                pass
    except Exception:
        pass

    return info
