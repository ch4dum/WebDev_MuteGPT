#!/usr/bin/env python3
"""Extract tarot card images from a PDF deck.

Default usage from the repository root:

    python scripts/extract_tarot_cards.py Tarot-Card-Deck.pdf

The script prefers PyMuPDF when installed. If PyMuPDF is not available, it
falls back to Poppler's `pdfimages` command.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract card-sized images from a tarot deck PDF."
    )
    parser.add_argument("pdf", type=Path, help="Path to the source PDF.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("frontend/assets/tarot-cards"),
        help="Output directory for extracted card images.",
    )
    parser.add_argument(
        "--skip-pages",
        type=int,
        default=1,
        help="Number of leading pages to skip. Default skips the cover page.",
    )
    parser.add_argument(
        "--min-width",
        type=int,
        default=500,
        help="Minimum image width to keep.",
    )
    parser.add_argument(
        "--min-height",
        type=int,
        default=800,
        help="Minimum image height to keep.",
    )
    parser.add_argument(
        "--png",
        action="store_true",
        help="Convert kept images to PNG instead of preserving PDF image format.",
    )
    return parser.parse_args()


def should_keep(image_path: Path, min_width: int, min_height: int) -> bool:
    try:
        with Image.open(image_path) as image:
            width, height = image.size
        return width >= min_width and height >= min_height
    except Exception:
        return False


def maybe_convert_to_png(image_path: Path) -> Path:
    target = image_path.with_suffix(".png")
    if image_path.suffix.lower() == ".png":
        return image_path

    with Image.open(image_path) as image:
        image.save(target)
    image_path.unlink()
    return target


def extract_with_pymupdf(
    pdf_path: Path,
    output_dir: Path,
    skip_pages: int,
    min_width: int,
    min_height: int,
    as_png: bool,
) -> list[Path]:
    import fitz  # type: ignore

    extracted: list[Path] = []
    doc = fitz.open(pdf_path)
    image_index = 1

    for page_index in range(skip_pages, len(doc)):
        page = doc[page_index]
        for image_info in page.get_images(full=True):
            xref = image_info[0]
            image_data = doc.extract_image(xref)
            width = image_data.get("width", 0)
            height = image_data.get("height", 0)

            if width < min_width or height < min_height:
                continue

            ext = image_data.get("ext", "bin")
            image_path = output_dir / f"card_{image_index:03d}_p{page_index + 1:02d}.{ext}"
            image_path.write_bytes(image_data["image"])

            if as_png:
                image_path = maybe_convert_to_png(image_path)

            extracted.append(image_path)
            image_index += 1

    return extracted


def extract_with_pdfimages(
    pdf_path: Path,
    output_dir: Path,
    skip_pages: int,
    min_width: int,
    min_height: int,
    as_png: bool,
) -> list[Path]:
    pdfimages = shutil.which("pdfimages")
    if not pdfimages:
        raise RuntimeError(
            "PyMuPDF is not installed and `pdfimages` was not found in PATH."
        )

    raw_dir = output_dir / "_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    prefix = raw_dir / "raw"

    command = [
        pdfimages,
        "-j",
        "-p",
        "-f",
        str(skip_pages + 1),
        str(pdf_path),
        str(prefix),
    ]
    subprocess.run(command, check=True)

    extracted: list[Path] = []
    image_index = 1
    for raw_image in sorted(raw_dir.iterdir()):
        if not raw_image.is_file():
            continue
        if not should_keep(raw_image, min_width, min_height):
            raw_image.unlink(missing_ok=True)
            continue

        suffix = ".png" if as_png else raw_image.suffix.lower()
        target = output_dir / f"card_{image_index:03d}{suffix}"
        if as_png:
            with Image.open(raw_image) as image:
                image.save(target)
            raw_image.unlink(missing_ok=True)
        else:
            raw_image.replace(target)
        extracted.append(target)
        image_index += 1

    shutil.rmtree(raw_dir, ignore_errors=True)
    return extracted


def main() -> int:
    args = parse_args()
    pdf_path = args.pdf.resolve()
    output_dir = args.output.resolve()

    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        import fitz  # noqa: F401

        images = extract_with_pymupdf(
            pdf_path,
            output_dir,
            args.skip_pages,
            args.min_width,
            args.min_height,
            args.png,
        )
        engine = "PyMuPDF"
    except ImportError:
        images = extract_with_pdfimages(
            pdf_path,
            output_dir,
            args.skip_pages,
            args.min_width,
            args.min_height,
            args.png,
        )
        engine = "pdfimages"

    print(f"Extracted {len(images)} images with {engine}.")
    print(f"Output: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
