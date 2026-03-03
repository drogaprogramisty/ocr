#!/usr/bin/env python3
"""OCR CLI tool - extract text from images and PDFs using Tesseract."""

from __future__ import annotations

import argparse
import glob
import io
import json
import shutil
import sys
from pathlib import Path

import pytesseract
from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdfium2 import PdfDocument

# Tesseract settings
DEFAULT_LANG = "pol+eng"
PDF_RENDER_SCALE = 2  # ~300 DPI equivalent

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif", ".webp"}
PDF_EXTENSIONS = {".pdf"}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | PDF_EXTENSIONS

EXTENSION_MAP = {
    "txt": ".txt",
    "json": ".json",
    "pdf": ".pdf",
}


def find_tesseract() -> str:
    """Find tesseract binary, checking PATH then common Homebrew locations."""
    path = shutil.which("tesseract")
    if path:
        return path
    for candidate in ["/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract"]:
        if Path(candidate).exists():
            return candidate
    return "tesseract"


def expand_paths(patterns: list[str]) -> list[Path]:
    """Expand glob patterns and return list of file paths."""
    paths = []
    for pattern in patterns:
        literal_path = Path(pattern)
        if literal_path.exists():
            paths.append(literal_path.resolve())
        elif any(c in pattern for c in "*?["):
            expanded = glob.glob(pattern)
            paths.extend(Path(p).resolve() for p in sorted(expanded))
        else:
            paths.append(literal_path.resolve())
    return paths


def get_unique_output_path(base_path: Path) -> Path:
    """Return a unique path by adding numeric suffix if file exists."""
    if not base_path.exists():
        return base_path

    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent

    counter = 1
    while True:
        new_path = parent / f"{stem}-{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def get_output_path(input_path: Path, output: str | None, fmt: str) -> Path:
    """Determine the output file path."""
    ext = EXTENSION_MAP.get(fmt, ".txt")

    # Avoid collision: document.pdf → document_ocr.pdf (not document.pdf)
    stem = input_path.stem
    if fmt == "pdf" and input_path.suffix.lower() == ".pdf":
        stem = f"{stem}_ocr"

    if output:
        output_path = Path(output)
        if output_path.is_dir():
            output_path = output_path / f"{stem}{ext}"
    else:
        output_path = input_path.parent / f"{stem}{ext}"

    return get_unique_output_path(output_path)


def ocr_image_to_text(img: Image.Image, lang: str) -> str:
    """Run OCR on a PIL image, returning plain text."""
    return pytesseract.image_to_string(img, lang=lang)


def ocr_image_to_pdf_bytes(img: Image.Image, lang: str) -> bytes:
    """Run OCR on a PIL image, returning a single-page searchable PDF as bytes."""
    return pytesseract.image_to_pdf_or_hocr(img, extension="pdf", lang=lang)


def process_pdf(pdf_path: Path, fmt: str, lang: str, quiet: bool) -> str | bytes:
    """Process all pages of a PDF and return combined output."""
    with PdfDocument(str(pdf_path)) as pdf:
        num_pages = len(pdf)
        if not quiet and num_pages > 1:
            print(f"  Processing {num_pages} pages...", file=sys.stderr)

        results = []
        for i in range(num_pages):
            if not quiet and num_pages > 1:
                print(f"  Page {i + 1}/{num_pages}...", file=sys.stderr)
            img = pdf[i].render(scale=PDF_RENDER_SCALE).to_pil()
            if fmt == "pdf":
                results.append(ocr_image_to_pdf_bytes(img, lang))
            else:
                results.append(ocr_image_to_text(img, lang))

    if fmt == "pdf":
        writer = PdfWriter()
        for page_bytes in results:
            writer.append(PdfReader(io.BytesIO(page_bytes)))
        out = io.BytesIO()
        writer.write(out)
        return out.getvalue()

    if fmt == "json":
        pages = [{"page": i + 1, "text": t.strip()} for i, t in enumerate(results)]
        full_text = "\n".join(p["text"] for p in pages)
        return json.dumps({"text": full_text, "pages": pages}, indent=2, ensure_ascii=False)

    return "\n".join(results)


def process_image(img_path: Path, fmt: str, lang: str) -> str | bytes:
    """Process an image file and return output in requested format."""
    img = Image.open(img_path)

    if fmt == "pdf":
        return ocr_image_to_pdf_bytes(img, lang)

    text = ocr_image_to_text(img, lang)

    if fmt == "json":
        return json.dumps(
            {"text": text.strip(), "pages": [{"page": 1, "text": text.strip()}]},
            indent=2,
            ensure_ascii=False,
        )

    return text


def ocr_file(input_path: Path, output_path: Path, fmt: str, lang: str, quiet: bool) -> bool:
    """OCR a single file and write the result to output_path."""
    try:
        if not quiet:
            print(f"Processing {input_path.name}...", file=sys.stderr)

        if input_path.suffix.lower() in PDF_EXTENSIONS:
            content = process_pdf(input_path, fmt, lang, quiet)
        else:
            content = process_image(input_path, fmt, lang)
    except Exception as e:
        if not quiet:
            print(f"Error: OCR failed for {input_path.name}: {e}", file=sys.stderr)
        return False

    if isinstance(content, bytes):
        output_path.write_bytes(content)
    else:
        output_path.write_text(content, encoding="utf-8")

    print(output_path)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from images and PDFs using Tesseract OCR",
    )
    parser.add_argument(
        "input",
        nargs="+",
        help="Path(s) to image/PDF file(s), supports glob patterns (e.g., *.png)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output path (file for single input, directory for multiple)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["txt", "json", "pdf"],
        default="txt",
        help="Output format (default: txt)",
    )
    parser.add_argument(
        "-l",
        "--lang",
        type=str,
        default=DEFAULT_LANG,
        help=f"Tesseract language code(s), e.g. pol+eng, deu (default: {DEFAULT_LANG})",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress all output except the output file path",
    )

    args = parser.parse_args()

    input_paths = expand_paths(args.input)

    if not input_paths:
        if not args.quiet:
            print("Error: No matching files found", file=sys.stderr)
        sys.exit(1)

    missing = [p for p in input_paths if not p.exists()]
    if missing:
        if not args.quiet:
            for p in missing:
                print(f"Error: Input file not found: {p}", file=sys.stderr)
        sys.exit(1)

    unsupported = [p for p in input_paths if p.suffix.lower() not in SUPPORTED_EXTENSIONS]
    if unsupported:
        if not args.quiet:
            for p in unsupported:
                print(f"Error: Unsupported file type: {p.suffix} ({p.name})", file=sys.stderr)
        sys.exit(1)

    if len(input_paths) > 1 and args.output and not Path(args.output).is_dir():
        if not args.quiet:
            print(
                "Error: Output must be a directory when processing multiple files",
                file=sys.stderr,
            )
        sys.exit(1)

    pytesseract.pytesseract.tesseract_cmd = find_tesseract()

    success = True
    for input_path in input_paths:
        output_path = get_output_path(input_path, args.output, args.format)
        if not ocr_file(input_path, output_path, args.format, args.lang, args.quiet):
            success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
