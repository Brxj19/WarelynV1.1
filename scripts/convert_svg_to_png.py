from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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


def main() -> None:
    diagrams = [
        ("docs/diagrams/architecture.svg", "docs/diagrams/architecture.png", 1400),
        ("docs/diagrams/techstack.svg", "docs/diagrams/techstack.png", 1200),
        ("docs/diagrams/request_flow.svg", "docs/diagrams/request_flow.png", 1200),
        ("docs/diagrams/workflow_routing.svg", "docs/diagrams/workflow_routing.png", 1400),
    ]

    for svg_rel, png_rel, width in diagrams:
        svg_path = ROOT / svg_rel
        png_path = ROOT / png_rel
        if not svg_path.exists():
            print(f"SKIP: {svg_rel} not found")
            continue
        ok = convert_svg_to_png(svg_path, png_path, width=width)
        if ok:
            print(f"Converted: {png_rel}")
        else:
            print(f"WARNING: could not convert {svg_rel}")


if __name__ == "__main__":
    main()
