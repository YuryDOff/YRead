"""Book import and text processing service."""
import os
import re
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Google Drive helpers
# ---------------------------------------------------------------------------

_GDRIVE_PATTERN = re.compile(
    r"https?://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)"
)


def extract_file_id(google_drive_link: str) -> Optional[str]:
    """Extract the file ID from a Google Drive shareable link."""
    match = _GDRIVE_PATTERN.search(google_drive_link)
    return match.group(1) if match else None


def build_direct_download_url(file_id: str) -> str:
    """Convert a Google Drive file ID to a direct-download URL."""
    return f"https://drive.google.com/uc?export=download&id={file_id}"


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

async def download_text_from_google_drive(google_drive_link: str) -> str:
    """
    Download a plain-text file from a Google Drive shareable link.

    Raises:
        ValueError  – invalid link format
        RuntimeError – network / download error
    """
    file_id = extract_file_id(google_drive_link)
    if not file_id:
        raise ValueError(
            "Invalid Google Drive link. Expected format: "
            "https://drive.google.com/file/d/FILE_ID/view"
        )

    url = build_direct_download_url(file_id)
    logger.info("Downloading from Google Drive: %s", url)

    async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
        response = await client.get(url)

        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to download file from Google Drive "
                f"(HTTP {response.status_code})"
            )

        content_type = response.headers.get("content-type", "")
        # Google may serve HTML for files that require auth
        if "text/html" in content_type and len(response.text) < 5000:
            if "ServiceLogin" in response.text or "accounts.google.com" in response.text:
                raise RuntimeError(
                    "File is not publicly shared. Please set sharing to "
                    "'Anyone with the link'."
                )

        text = response.text

    if not text.strip():
        raise RuntimeError("Downloaded file is empty.")

    # Guard against absurdly large files (>10 MB text)
    if len(text.encode("utf-8")) > 10 * 1024 * 1024:
        raise RuntimeError("File exceeds 10 MB limit.")

    return text


# ---------------------------------------------------------------------------
# Book metadata helpers
# ---------------------------------------------------------------------------

WORDS_PER_PAGE = 300  # rough estimate used throughout the project


def compute_metadata(text: str) -> dict:
    """Return word count and estimated page count for a text."""
    words = text.split()
    total_words = len(words)
    total_pages = max(1, -(-total_words // WORDS_PER_PAGE))  # ceil division
    return {"total_words": total_words, "total_pages": total_pages}


def guess_title(text: str, filename: Optional[str] = None) -> str:
    """
    Guess book title from the file name or first non-empty line of text.
    """
    if filename:
        name = os.path.splitext(filename)[0]
        if name:
            return name.strip()

    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            # Use first meaningful line, capped at 120 chars
            return stripped[:120]

    return "Untitled Book"
