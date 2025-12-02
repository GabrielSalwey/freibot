"""
Converter module for Freibot.

**INPUTS:**
    - file_path: str - Path to file (PDF, HTML, TXT, etc.)
    - file_type: str - Type of file to convert
    
**OUTPUTS:**
    - List[ConvertedDocument] - Extracted text with page/section info

**RESPONSIBILITIES:**
    - Convert PDFs to text (PyPDF)
    - Parse HTML content
    - Handle various file formats
    - Preserve document structure metadata
    
**DEPENDENCIES:**
    - pypdf (PDF extraction)
    - beautifulsoup4 (HTML parsing)
    
**TODO:**
    - Add OCR support for scanned PDFs
    - Handle tables and images
    - Support DOCX and other formats
"""

from typing import List, Optional

from .types import ConvertedDocument


def convert_pdf(file_path: str) -> List[ConvertedDocument]:
    """
    Convert a PDF file to documents.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        List of ConvertedDocument, one per page
    """
    raise NotImplementedError


def convert_html(content: str, source_url: str) -> ConvertedDocument:
    """
    Convert HTML content to document.
    
    Args:
        content: Raw HTML string
        source_url: Source URL for metadata
        
    Returns:
        ConvertedDocument with extracted text
    """
    raise NotImplementedError


def convert_text(file_path: str) -> ConvertedDocument:
    """
    Convert plain text file to document.
    
    Args:
        file_path: Path to text file
        
    Returns:
        ConvertedDocument
    """
    raise NotImplementedError


def detect_file_type(file_path: str) -> str:
    """
    Detect the type of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        File type string ("pdf", "html", "txt", etc.)
    """
    raise NotImplementedError


def convert_file(file_path: str) -> List[ConvertedDocument]:
    """
    Auto-detect and convert any supported file.
    
    Args:
        file_path: Path to file
        
    Returns:
        List of ConvertedDocument
    """
    raise NotImplementedError
