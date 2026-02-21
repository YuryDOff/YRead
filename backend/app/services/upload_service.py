"""File upload service for manuscript uploads (.txt, .docx, .pdf)."""
import logging
import os
import time
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Maximum file size: 20MB
MAX_FILE_SIZE = 20 * 1024 * 1024

# Supported file extensions
SUPPORTED_EXTENSIONS = {".txt", ".docx", ".pdf"}


class UploadError(Exception):
    """Custom exception for upload-related errors."""
    pass


def validate_file(filename: str, file_size: int) -> None:
    """
    Validate uploaded file extension and size.
    
    Args:
        filename: Original filename from upload
        file_size: File size in bytes
        
    Raises:
        UploadError: If validation fails
    """
    # Check file extension
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise UploadError(
            f"Invalid file type. Please upload {', '.join(SUPPORTED_EXTENSIONS)} files only."
        )
    
    # Check file size
    if file_size > MAX_FILE_SIZE:
        size_mb = file_size / (1024 * 1024)
        raise UploadError(
            f"File too large ({size_mb:.1f}MB). Maximum size is {MAX_FILE_SIZE / (1024 * 1024):.0f}MB."
        )
    
    logger.info(f"File validation passed: {filename} ({file_size} bytes)")


def extract_text_from_txt(file_path: str) -> str:
    """Extract text from .txt file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        if not text.strip():
            raise UploadError("Text file is empty.")
        return text
    except UnicodeDecodeError:
        # Try with different encodings
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                text = f.read()
            if not text.strip():
                raise UploadError("Text file is empty.")
            return text
        except Exception as e:
            raise UploadError(f"Unable to read text file: {str(e)}")
    except Exception as e:
        raise UploadError(f"Unable to read text file: {str(e)}")


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from .docx file using python-docx."""
    try:
        from docx import Document
    except ImportError:
        raise UploadError(
            "DOCX support not available. Please contact administrator."
        )
    
    try:
        doc = Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs]
        text = '\n'.join(paragraphs)
        
        if not text.strip():
            raise UploadError("DOCX file contains no readable text.")
        
        return text
    except Exception as e:
        raise UploadError(f"Unable to read DOCX file: {str(e)}")


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using PyPDF2."""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        raise UploadError(
            "PDF support not available. Please contact administrator."
        )
    
    try:
        reader = PdfReader(file_path)
        
        if len(reader.pages) == 0:
            raise UploadError("PDF file has no pages.")
        
        # Extract text from all pages
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        
        text = '\n'.join(text_parts)
        
        # Check if we extracted meaningful text
        if not text.strip() or len(text.strip()) < 100:
            raise UploadError(
                "PDF must contain extractable text, not scanned images. "
                "Please upload a text-based PDF or convert to .txt/.docx."
            )
        
        return text
    except UploadError:
        raise
    except Exception as e:
        raise UploadError(f"Unable to read PDF file: {str(e)}")


def extract_text_from_file(file_path: str, extension: str) -> str:
    """
    Extract text from uploaded file based on extension.
    
    Args:
        file_path: Path to the uploaded file
        extension: File extension (with dot, e.g., '.txt')
        
    Returns:
        Extracted text content
        
    Raises:
        UploadError: If extraction fails
    """
    extension = extension.lower()
    
    if extension == '.txt':
        return extract_text_from_txt(file_path)
    elif extension == '.docx':
        return extract_text_from_docx(file_path)
    elif extension == '.pdf':
        return extract_text_from_pdf(file_path)
    else:
        raise UploadError(f"Unsupported file extension: {extension}")


def guess_title_from_text(text: str, filename: str) -> str:
    """
    Guess book title from text content or filename.
    
    Args:
        text: Book text content
        filename: Original filename
        
    Returns:
        Guessed title
    """
    # Try to extract from first line (common in manuscripts)
    lines = text.strip().split('\n')
    if lines:
        first_line = lines[0].strip()
        # If first line is short and looks like a title
        if 1 < len(first_line) < 100 and not first_line.endswith('.'):
            return first_line
    
    # Fallback to filename without extension
    title = Path(filename).stem
    # Clean up common patterns
    title = title.replace('_', ' ').replace('-', ' ')
    return title


def compute_word_count(text: str) -> int:
    """Compute word count from text."""
    words = text.split()
    return len(words)


def estimate_page_count(word_count: int, words_per_page: int = 250) -> int:
    """
    Estimate page count based on word count.
    
    Args:
        word_count: Total number of words
        words_per_page: Average words per page (default 250 for typical books)
        
    Returns:
        Estimated page count
    """
    return max(1, word_count // words_per_page)


def save_uploaded_file(
    file_content: bytes,
    filename: str,
    upload_dir: str
) -> str:
    """
    Save uploaded file to disk.
    
    Args:
        file_content: File content as bytes
        filename: Original filename
        upload_dir: Directory to save file
        
    Returns:
        Path to saved file
        
    Raises:
        UploadError: If save fails
    """
    try:
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate safe filename (use original name but ensure uniqueness later)
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"Saved uploaded file to: {file_path}")
        return file_path
        
    except Exception as e:
        raise UploadError(f"Failed to save file: {str(e)}")


def process_manuscript_upload(
    file_content: bytes,
    filename: str,
    upload_dir: str
) -> Tuple[str, dict]:
    """
    Process uploaded manuscript file: validate, extract text, compute metadata.
    
    Args:
        file_content: File content as bytes
        filename: Original filename
        upload_dir: Directory to save temporary file
        
    Returns:
        Tuple of (extracted_text, metadata_dict)
        metadata_dict contains: title, word_count, estimated_pages, original_filename
        
    Raises:
        UploadError: If processing fails
    """
    t0 = time.perf_counter()
    file_size = len(file_content)
    validate_file(filename, file_size)
    logger.info("[upload_service] validate_file done in %.2fs", time.perf_counter() - t0)

    t1 = time.perf_counter()
    temp_file_path = save_uploaded_file(file_content, filename, upload_dir)
    logger.info("[upload_service] save_uploaded_file done in %.2fs", time.perf_counter() - t1)

    try:
        t2 = time.perf_counter()
        extension = Path(filename).suffix.lower()
        text = extract_text_from_file(temp_file_path, extension)
        logger.info("[upload_service] extract_text_from_file (%s) done in %.2fs, text_len=%d", extension, time.perf_counter() - t2, len(text))

        t3 = time.perf_counter()
        word_count = compute_word_count(text)
        estimated_pages = estimate_page_count(word_count)
        title = guess_title_from_text(text, filename)
        logger.info("[upload_service] metadata (word_count, pages, title) done in %.2fs", time.perf_counter() - t3)
        
        metadata = {
            'title': title,
            'word_count': word_count,
            'estimated_pages': estimated_pages,
            'original_filename': filename,
        }
        
        logger.info(
            f"Processed manuscript: {filename} -> {word_count} words, "
            f"~{estimated_pages} pages, title='{title}'"
        )
        
        return text, metadata
        
    except UploadError:
        # Clean up temp file on error
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise UploadError(f"Failed to process manuscript: {str(e)}")
