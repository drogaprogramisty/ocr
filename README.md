# ocr - OCR CLI tool for images and PDFs

> [!NOTE]
> Also: Optimised for agentic usage with Claude Code, Codex, Open Code and more!

## Speed

| Benchmark | Pages | Processing Time | Speed |
|-----------|-------|-----------------|-------|
| Single file (image) | 1 page (1486×1256 PNG) | 0.61s | **98 pages/min** |
| Single file (PDF) | 212 pages | 3m 10s | **67 pages/min** |

**Notes:**
- Tested on MacBook Pro M4 Max, 128GB RAM
- Default language: `pol+eng`, PDF render scale: 2× (~300 DPI)

## Supported formats

**Input:** PDF, PNG, JPG, JPEG, TIFF, BMP, GIF, WEBP
**Output:** `txt` (default), `json` (with page metadata), `pdf` (searchable PDF)

## Requirements

- Python 3.9+
- tesseract (`brew install tesseract tesseract-lang`)
- uv (`brew install uv` or [see official docs](https://docs.astral.sh/uv/getting-started/installation/))

## Installation

```bash
sudo uv pip install --system git+https://github.com/drogaprogramisty/ocr
```

> [!NOTE]
> `sudo` is required when installing into the system Python (e.g. macOS's built-in Python or Xcode's Python).

## Usage

```bash
ocr document.pdf               # Creates document.txt
ocr scan.png                   # Creates scan.txt
ocr document.pdf -f json       # Creates document.json (with page numbers)
ocr document.pdf -f pdf        # Creates document_ocr.pdf (searchable PDF)
ocr *.png -o output/           # Batch process images to directory
ocr file1.pdf file2.jpg        # Multiple files
ocr document.pdf -o result.txt # Custom output path
ocr document.pdf -q            # Quiet mode, only prints output path (for CLI/agent usage)
ocr document.pdf --lang pol+eng # Specify OCR language(s)
ocr document.pdf --lang deu    # German only
ocr -h                         # All options
```

## Output Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| `txt`  | `.txt`    | Plain text (default) |
| `json` | `.json`   | JSON with full text and per-page breakdown |
| `pdf`  | `_ocr.pdf`| Searchable PDF with embedded invisible text layer |

### JSON structure

```json
{
  "text": "full combined text...",
  "pages": [
    { "page": 1, "text": "page 1 text..." },
    { "page": 2, "text": "page 2 text..." }
  ]
}
```

## Languages

Uses Tesseract language packs. Examples:
- `pol+eng` — Polish + English (default)
- `eng` — English only
- `deu` — German
- `fra` — French

Install language packs: `brew install tesseract tesseract-lang`

## CLAUDE.md / AGENTS.md

Example plug-and-play .md paragraph so your favorite agent can use this tool:

```markdown
## ocr - OCR Tool

Extract text from images and PDF documents.

ocr document.pdf               # Creates document.txt
ocr scan.png                   # Creates scan.txt
ocr document.pdf -f json       # Creates document.json (with page numbers)
ocr document.pdf -f pdf        # Creates document_ocr.pdf (searchable PDF)
ocr *.png -o output/           # Batch process to directory
ocr file1.pdf file2.jpg        # Multiple files
ocr document.pdf -o result.txt # Custom output path
ocr document.pdf -q            # Quiet mode, only prints output path (CLI usage)
ocr document.pdf --lang pol+eng # Specify language(s)
ocr -h                         # for help / all options
```
