"""Book import and text processing service."""
import os
import re
import logging
from typing import Optional

import httpx
import tiktoken

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


# ---------------------------------------------------------------------------
# Text chunking
# ---------------------------------------------------------------------------

# tiktoken encoder – cached at module level
_encoder: Optional[tiktoken.Encoding] = None


def _get_encoder() -> tiktoken.Encoding:
    global _encoder
    if _encoder is None:
        _encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
    return _encoder


def count_tokens(text: str) -> int:
    """Count tokens using the GPT-3.5-turbo tokeniser."""
    return len(_get_encoder().encode(text))


def chunk_text(
    text: str,
    *,
    target_tokens: int = 2000,
    overlap_tokens: int = 200,
) -> list[dict]:
    """
    Split *text* into overlapping chunks that respect paragraph boundaries.

    Returns a list of dicts:
        {chunk_index, text, start_page, end_page, word_count}
    """
    paragraphs = re.split(r"\n\s*\n", text)
    # Remove blanks
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    enc = _get_encoder()
    chunks: list[dict] = []
    current_paragraphs: list[str] = []
    current_tokens = 0
    word_offset = 0  # running word position in the full text

    def _flush(paras: list[str], w_offset: int) -> dict:
        chunk_text_str = "\n\n".join(paras)
        words = chunk_text_str.split()
        wc = len(words)
        start_page = max(1, w_offset // WORDS_PER_PAGE + 1)
        end_page = max(start_page, (w_offset + wc) // WORDS_PER_PAGE + 1)
        return {
            "chunk_index": len(chunks),
            "text": chunk_text_str,
            "start_page": start_page,
            "end_page": end_page,
            "word_count": wc,
        }

    for para in paragraphs:
        para_tokens = len(enc.encode(para))

        # If a single paragraph exceeds target, force-flush current then
        # split the huge paragraph by sentences.
        if para_tokens > target_tokens:
            if current_paragraphs:
                chunks.append(_flush(current_paragraphs, word_offset))
                # Overlap: keep last paragraphs that fit within overlap_tokens
                overlap_paras, overlap_tok = _pick_overlap(
                    current_paragraphs, enc, overlap_tokens
                )
                word_offset += sum(len(p.split()) for p in current_paragraphs) - sum(
                    len(p.split()) for p in overlap_paras
                )
                current_paragraphs = list(overlap_paras)
                current_tokens = overlap_tok
            # Add the huge paragraph as its own chunk(s)
            for sub in _split_large_paragraph(para, enc, target_tokens, overlap_tokens):
                sub_words = sub.split()
                start_p = max(1, word_offset // WORDS_PER_PAGE + 1)
                end_p = max(start_p, (word_offset + len(sub_words)) // WORDS_PER_PAGE + 1)
                chunks.append({
                    "chunk_index": len(chunks),
                    "text": sub,
                    "start_page": start_p,
                    "end_page": end_p,
                    "word_count": len(sub_words),
                })
                word_offset += len(sub_words)
            current_paragraphs = []
            current_tokens = 0
            continue

        if current_tokens + para_tokens > target_tokens and current_paragraphs:
            chunks.append(_flush(current_paragraphs, word_offset))
            overlap_paras, overlap_tok = _pick_overlap(
                current_paragraphs, enc, overlap_tokens
            )
            word_offset += sum(len(p.split()) for p in current_paragraphs) - sum(
                len(p.split()) for p in overlap_paras
            )
            current_paragraphs = list(overlap_paras)
            current_tokens = overlap_tok

        current_paragraphs.append(para)
        current_tokens += para_tokens

    # Remaining paragraphs
    if current_paragraphs:
        chunks.append(_flush(current_paragraphs, word_offset))

    return chunks


def _pick_overlap(
    paragraphs: list[str],
    enc: tiktoken.Encoding,
    max_tokens: int,
) -> tuple[list[str], int]:
    """Pick trailing paragraphs that fit within *max_tokens* for overlap."""
    picked: list[str] = []
    total = 0
    for para in reversed(paragraphs):
        t = len(enc.encode(para))
        if total + t > max_tokens:
            break
        picked.insert(0, para)
        total += t
    return picked, total


def _split_large_paragraph(
    text: str,
    enc: tiktoken.Encoding,
    target_tokens: int,
    overlap_tokens: int,
) -> list[str]:
    """Split an oversized paragraph into smaller pieces by sentences."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    parts: list[str] = []
    current: list[str] = []
    current_tok = 0

    for sent in sentences:
        st = len(enc.encode(sent))
        if current_tok + st > target_tokens and current:
            parts.append(" ".join(current))
            # Keep overlap worth of sentences
            overlap_sents, _ = _pick_overlap(current, enc, overlap_tokens)
            current = list(overlap_sents)
            current_tok = sum(len(enc.encode(s)) for s in current)
        current.append(sent)
        current_tok += st

    if current:
        parts.append(" ".join(current))

    return parts


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
