from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import svgwrite

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "diagrams"


def convert_svg_to_png(svg_path: Path, png_path: Path, width: int = 1200) -> bool:
    """Try all available SVG→PNG converters in order."""
    try:
        import cairosvg

        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=width)
        return True
    except Exception:
        pass

    converters = [
        ("inkscape", [str(svg_path), "-o", str(png_path), f"-w{width}"]),
        ("rsvg-convert", ["-w", str(width), str(svg_path), "-o", str(png_path)]),
        ("convert", ["-density", "150", "-background", "white", str(svg_path), str(png_path)]),
    ]
    for binary, args in converters:
        if shutil.which(binary) is None:
            continue
        try:
            result = subprocess.run([binary, *args], capture_output=True, check=False, timeout=60)
            if result.returncode == 0 and png_path.exists():
                return True
        except Exception:
            continue

    return False


def badge(dwg, x, y, text, icon, bg, fg):
    bw = max(int(len(text) * 7.2 + 30), 95)
    bh = 28
    dwg.add(dwg.rect((x, y), (bw, bh), fill=bg, rx=6, ry=6))
    dwg.add(dwg.text(icon, insert=(x + 9, y + bh / 2), dominant_baseline="central",
                     font_family="Arial, sans-serif", font_size="13px", fill=fg))
    dwg.add(dwg.text(text, insert=(x + 26, y + bh / 2), dominant_baseline="central",
                     font_family="Arial, sans-serif", font_size="11px",
                     font_weight="500", fill=fg))
    return bw


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    svg_path = OUT / "techstack.svg"
    png_path = OUT / "techstack.png"

    W, H = 1200, 800
    dwg = svgwrite.Drawing(str(svg_path), size=(f"{W}px", f"{H}px"), viewBox=f"0 0 {W} {H}")

    DARK_BLUE = "#1F3A5F"
    MID_BLUE = "#2E6DA4"
    EMERALD = "#1A7F5A"
    LIGHT_BLUE = "#D6E4F0"
    LIGHT_GREEN = "#D4EDDA"
    AMBER_FILL = "#FEF3C7"
    AMBER_BORDER = "#F59E0B"
    GRAY_FILL = "#F1F5F9"
    TEXT_DARK = "#1E293B"
    TEXT_MID = "#475569"
    PURPLE_FILL = "#F3E8FF"
    PURPLE = "#7C3AED"
    WHITE = "#FFFFFF"

    dwg.add(dwg.rect((0, 0), (W, H), fill="#F8FAFC"))

    dwg.add(dwg.text(
        "Warelyn Inventory — Technology Stack",
        insert=(W / 2, 40), text_anchor="middle",
        font_family="Arial, sans-serif", font_size="22px",
        font_weight="bold", fill=DARK_BLUE
    ))
    dwg.add(dwg.text(
        "FastAPI · React 18 · MySQL · MongoDB · Google Gemini",
        insert=(W / 2, 64), text_anchor="middle",
        font_family="Arial, sans-serif", font_size="13px", fill=TEXT_MID
    ))
    dwg.add(dwg.line((40, 78), (W - 40, 78), stroke=MID_BLUE, stroke_width=2))

    layers = [
        {
            "label": "PRESENTATION",
            "sublabel": "Client Layer",
            "fill": LIGHT_BLUE, "border": MID_BLUE, "lc": DARK_BLUE,
            "badges": [
                ("React 18", "⚛", "#0EA5E9", WHITE),
                ("Vite", "⚡", "#646CFF", WHITE),
                ("Tailwind CSS 3.4", "🎨", "#06B6D4", WHITE),
                ("Recharts 2.15", "📊", MID_BLUE, WHITE),
                ("Lucide React", "✦", GRAY_FILL, TEXT_DARK),
                ("React Router", "🔀", GRAY_FILL, TEXT_DARK),
            ],
        },
        {
            "label": "API GATEWAY",
            "sublabel": "FastAPI Layer",
            "fill": "#E8F0FA", "border": DARK_BLUE, "lc": DARK_BLUE,
            "badges": [
                ("FastAPI 0.115", "🚀", DARK_BLUE, WHITE),
                ("Uvicorn", "🦄", "#4C566A", WHITE),
                ("JWT — PyJWT 2.10", "🔐", PURPLE, WHITE),
                ("bcrypt 5.0", "🔑", "#374151", WHITE),
                ("SlowAPI Rate Limit", "🛡", AMBER_FILL, "#92400E"),
                ("Pydantic V2", "✅", "#E11D48", WHITE),
            ],
        },
        {
            "label": "BUSINESS LOGIC",
            "sublabel": "Services Layer",
            "fill": LIGHT_GREEN, "border": EMERALD, "lc": EMERALD,
            "badges": [
                ("Inventory Engine", "📦", EMERALD, WHITE),
                ("Workflow Engine", "⚙️", "#065F46", WHITE),
                ("Notification Service", "🔔", DARK_BLUE, WHITE),
                ("AI/RAG Service", "🤖", PURPLE, WHITE),
                ("WeasyPrint 68.1", "📄", "#6B7280", WHITE),
                ("Jinja2 3.1", "📝", "#DC2626", WHITE),
            ],
        },
        {
            "label": "DATA ACCESS",
            "sublabel": "ORM & Repository",
            "fill": "#F0FDF4", "border": "#86EFAC", "lc": "#166534",
            "badges": [
                ("SQLAlchemy 2.0", "🗃", "#A52A2A", WHITE),
                ("Alembic 1.13", "🔄", "#6B7280", WHITE),
                ("PyMySQL 1.1", "🐬", "#00618A", WHITE),
                ("pymongo 4.10", "🍃", "#116149", WHITE),
                ("TenantScopedRepo", "🏢", DARK_BLUE, WHITE),
                ("pydantic-settings", "⚙", "#E11D48", WHITE),
            ],
        },
        {
            "label": "DATA STORES",
            "sublabel": "Persistence Layer",
            "fill": AMBER_FILL, "border": AMBER_BORDER, "lc": "#92400E",
            "badges": [
                ("MySQL (PyMySQL)", "🐬", "#00618A", WHITE),
                ("MongoDB", "🍃", "#116149", WHITE),
                ("SMTP / Mailhog", "📧", "#374151", WHITE),
                ("openpyxl 3.1", "📊", "#166534", WHITE),
            ],
        },
        {
            "label": "INFRASTRUCTURE",
            "sublabel": "DevOps & AI",
            "fill": PURPLE_FILL, "border": PURPLE, "lc": "#5B21B6",
            "badges": [
                ("Docker Compose", "🐳", "#1D63ED", WHITE),
                ("Google Gemini 2.5", "✨", "#4285F4", WHITE),
                ("Gemini Embeddings", "🧠", "#0F9D58", WHITE),
                ("pytest 8.3", "🧪", "#0A9EDC", WHITE),
                ("Graphify", "🕸", DARK_BLUE, WHITE),
                ("Mailhog (dev)", "📬", "#6B7280", WHITE),
            ],
        },
    ]

    layer_start_y = 90
    layer_height = 92
    layer_gap = 6
    label_w = 152

    for idx, layer in enumerate(layers):
        y = layer_start_y + idx * (layer_height + layer_gap)

        dwg.add(dwg.rect((20, y), (W - 40, layer_height),
                         fill=layer["fill"], stroke=layer["border"],
                         stroke_width=1.5, rx=10, ry=10))
        dwg.add(dwg.rect((20, y), (label_w, layer_height),
                         fill=layer["border"], opacity=0.22, rx=10, ry=10))
        dwg.add(dwg.rect((label_w, y), (20, layer_height),
                         fill=layer["border"], opacity=0.22))
        dwg.add(dwg.line((label_w + 8, y + 12), (label_w + 8, y + layer_height - 12),
                         stroke=layer["border"], stroke_width=1, opacity=0.35))
        dwg.add(dwg.text(layer["label"],
                         insert=(20 + label_w / 2, y + layer_height / 2 - 9),
                         text_anchor="middle", font_family="Arial,sans-serif",
                         font_size="11px", font_weight="bold", fill=layer["lc"]))
        dwg.add(dwg.text(layer["sublabel"],
                         insert=(20 + label_w / 2, y + layer_height / 2 + 9),
                         text_anchor="middle", font_family="Arial,sans-serif",
                         font_size="9.5px", fill=layer["lc"], opacity=0.7))

        bx = label_w + 28
        by = y + 14
        bh = 28
        for name, icon, bg, fg in layer["badges"]:
            bw = max(int(len(name) * 7.2 + 30), 95)
            if bx + bw > W - 25:
                bx = label_w + 28
                by += bh + 7

            dwg.add(dwg.rect((bx, by), (bw, bh), fill=bg, rx=6, ry=6))
            dwg.add(dwg.text(icon, insert=(bx + 9, by + bh / 2),
                             dominant_baseline="central",
                             font_family="Arial,sans-serif", font_size="13px", fill=fg))
            dwg.add(dwg.text(name, insert=(bx + 26, by + bh / 2),
                             dominant_baseline="central",
                             font_family="Arial,sans-serif", font_size="11px",
                             font_weight="500", fill=fg))
            bx += bw + 7

    dwg.add(dwg.text(
        "Warelyn Inventory V1.1  ·  Multi-Tenant SaaS  ·  FastAPI + React  ·  2025",
        insert=(W / 2, H - 14), text_anchor="middle",
        font_family="Arial,sans-serif", font_size="11px", fill=TEXT_MID
    ))

    dwg.save()
    if convert_svg_to_png(svg_path, png_path):
        print(f"Generated: {svg_path}")
        print(f"Generated: {png_path}")
    else:
        print(f"Generated: {svg_path}")
        print("WARNING: PNG conversion skipped; no converter available.")


if __name__ == "__main__":
    main()
