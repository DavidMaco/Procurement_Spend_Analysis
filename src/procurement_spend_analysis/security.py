from __future__ import annotations

from pathlib import Path
import re


SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
ALLOWED_UPLOAD_SUFFIXES = {".csv"}


def sanitize_filename(filename: str) -> str:
    original = filename.strip()
    candidate = Path(original).name.strip()
    if candidate != original or any(separator in original for separator in ("/", "\\")):
        raise ValueError("Unsafe filename detected.")
    if not candidate or not SAFE_FILENAME_RE.match(candidate):
        raise ValueError("Unsafe filename detected.")
    if Path(candidate).suffix.lower() not in ALLOWED_UPLOAD_SUFFIXES:
        raise ValueError("Only CSV uploads are supported.")
    return candidate


def validate_text_payload(text: str, max_chars: int = 5_000_000) -> None:
    if len(text) > max_chars:
        raise ValueError("Payload exceeds allowed text size.")
    if "\x00" in text:
        raise ValueError("Payload contains null bytes.")
