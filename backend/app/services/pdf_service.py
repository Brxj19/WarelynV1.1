from __future__ import annotations

import logging
import re
from typing import Iterable

logger = logging.getLogger(__name__)

_WEASYPRINT_AVAILABLE = False
_WEASYPRINT_IMPORT_ERROR: str | None = None
try:
    import weasyprint
    _WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as exc:
    _WEASYPRINT_IMPORT_ERROR = str(exc)
    logger.warning(f"weasyprint not available ({exc}); PDF output will use fallback renderer.")


def render_html_to_pdf(html: str, *, allow_fallback: bool = False) -> bytes:
    """Render HTML to a styled PDF using WeasyPrint.

    By default, raises if WeasyPrint is unavailable or rendering fails so that
    callers are aware of degraded output. Set allow_fallback=True to silently
    fall back to the plain-text PDF renderer (useful for non-critical previews).
    """
    if _WEASYPRINT_AVAILABLE:
        try:
            return weasyprint.HTML(string=html).write_pdf()
        except Exception as exc:
            logger.error(f"weasyprint render failed: {exc}", exc_info=True)
            if not allow_fallback:
                raise RuntimeError(
                    f"PDF rendering failed: {exc}. "
                    "Ensure system dependencies (Pango, Cairo, GDK-Pixbuf) are installed."
                ) from exc
    else:
        msg = f"WeasyPrint is not available: {_WEASYPRINT_IMPORT_ERROR}"
        logger.error(msg)
        if not allow_fallback:
            raise RuntimeError(
                f"{msg}. Install weasyprint and its system dependencies "
                "(Pango, Cairo, GDK-Pixbuf) to generate styled PDFs."
            )
    return _fallback_pdf(html)


def _fallback_pdf(html: str) -> bytes:
    title, lines = _extract_full_content(html)
    return build_simple_pdf(title, lines)


def _extract_full_content(html: str) -> tuple[str, list[str]]:
    title = "Document"
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    if title_match:
        t = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
        if t:
            title = t

    lines: list[str] = []

    header_lines = _extract_header_fields(html)
    if header_lines:
        lines.extend(header_lines)
        lines.append("")

    table_sections = _extract_all_tables(html)
    for section in table_sections:
        lines.extend(section)
        lines.append("")

    block_lines = _extract_block_text(html)
    if block_lines:
        lines.extend(block_lines)

    if not lines:
        text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        for line in text.split('\n'):
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
            if len(lines) >= 60:
                break

    return title, lines[:60]


def _extract_header_fields(html: str) -> list[str]:
    lines: list[str] = []
    style_stripped = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

    for tag in ('h1', 'h2', 'h3'):
        for m in re.finditer(rf'<{tag}[^>]*>(.*?)</{tag}>', style_stripped, re.DOTALL | re.IGNORECASE):
            text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            if text and len(text) < 200:
                lines.append(text)

    label_patterns = [
        (r'<(?:p|span|td)[^>]*class="[^"]*label[^"]*"[^>]*>(.*?)</(?:p|span|td)>', None),
        (r'<(?:p|span|td)[^>]*class="[^"]*value[^"]*"[^>]*>(.*?)</(?:p|span|td)>', None),
        (r'<strong>(.*?)</strong>\s*(.*?)(?=<)', 'pair'),
    ]
    for pattern, mode in label_patterns:
        for m in re.finditer(pattern, style_stripped, re.DOTALL | re.IGNORECASE):
            if mode == 'pair':
                label = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                value = re.sub(r'<[^>]+>', '', m.group(2)).strip()
                if label and value:
                    lines.append(f"{label} {value}")
            else:
                text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                if text:
                    lines.append(text)

    return lines[:20]


def _extract_all_tables(html: str) -> list[list[str]]:
    sections: list[list[str]] = []
    table_blocks = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
    for table_html in table_blocks:
        rows: list[str] = []
        tr_blocks = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
        for tr in tr_blocks:
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.DOTALL | re.IGNORECASE)
            row_text = []
            for cell in cells:
                cell_clean = re.sub(r'<[^>]+>', '', cell).strip()
                row_text.append(cell_clean if cell_clean else "")
            non_empty = [c for c in row_text if c]
            if non_empty:
                rows.append("  |  ".join(row_text))
        if rows:
            sections.append(rows)
    return sections


def _extract_block_text(html: str) -> list[str]:
    lines: list[str] = []
    cleaned = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'<script[^>]*>.*?</script>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'<table[^>]*>.*?</table>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)

    for m in re.finditer(r'<(?:p|h[1-6]|li|dt|dd)[^>]*>(.*?)</(?:p|h[1-6]|li|dt|dd)>', cleaned, re.DOTALL | re.IGNORECASE):
        text = re.sub(r'<[^>]+>', ' ', m.group(1)).strip()
        text = re.sub(r'\s+', ' ', text)
        if text:
            lines.append(text)

    if not lines:
        for m in re.finditer(r'<div[^>]*>((?:(?!<div).)*?)</div>', cleaned, re.DOTALL | re.IGNORECASE):
            text = re.sub(r'<[^>]+>', ' ', m.group(1)).strip()
            text = re.sub(r'\s+', ' ', text)
            if text and len(text) > 2:
                lines.append(text)

    return lines[:40]


def build_simple_pdf(title: str, lines: Iterable[str]) -> bytes:
    def _esc(v: str) -> str:
        return v.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    content_lines = ["BT", "/F1 14 Tf", "1 0 0 1 50 770 Tm", f"({_esc(title)}) Tj", "/F1 9 Tf"]
    y = 745
    for line in list(lines)[:60]:
        if y < 40:
            break
        truncated = line[:120]
        content_lines += [f"1 0 0 1 50 {y} Tm", f"({_esc(truncated)}) Tj"]
        y -= 12
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
        b"5 0 obj << /Length %d >> stream\n%s\nendstream endobj" % (len(stream), stream),
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj + b"\n")
    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF".encode())
    return bytes(pdf)
