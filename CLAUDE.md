# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Single-file CLI tool for OCR (optical character recognition) using Tesseract. Extracts text from images and PDFs, with optional searchable PDF output.

## Commands

```bash
# Install dependencies
uv pip install --system -e .

# Run the CLI
python3 ocr.py <file>

# Lint/format with ruff
ruff check ocr.py
ruff format ocr.py
```

Always use `python3` (not `python`).

## System Requirements

- tesseract: `brew install tesseract`
- For Polish and other non-English languages: `brew install tesseract-lang`

## Architecture

**Single file:** All code lives in `ocr.py` (~200 lines).

**Key flow:**
1. `main()` → parses args, validates inputs, processes files in batch
2. `ocr_file()` → dispatches to `process_pdf()` or `process_image()`, writes output
3. `process_pdf()` → renders each page with pypdfium2 at scale=2, OCRs with tesseract
4. `process_image()` → opens with Pillow, OCRs with tesseract
5. Output written as txt, json (with page metadata), or searchable PDF

**External dependencies:**
- `pytesseract` - Python wrapper for Tesseract OCR engine
- `Pillow` - Image loading and processing
- `pypdfium2` - PDF page rendering to PIL images
- `pypdf` - PDF merging for searchable PDF output
- `tesseract` - System binary (must be installed separately)

**Constants:**
- `DEFAULT_LANG = "pol+eng"` - default OCR language(s)
- `PDF_RENDER_SCALE = 2` - scale factor for PDF rendering (~300 DPI)

**Output naming:**
- `document.pdf` → `document.txt` (txt format)
- `document.pdf` → `document.json` (json format)
- `document.pdf` → `document_ocr.pdf` (pdf format, avoids collision with input)
