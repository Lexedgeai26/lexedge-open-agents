"""File processing utilities for document upload and analysis."""

import base64
import io
import logging
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Supported file types
SUPPORTED_EXTENSIONS = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'txt': 'text/plain',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'webp': 'image/webp',
}


def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    return Path(filename).suffix.lower().lstrip('.')


def is_supported_file(filename: str) -> bool:
    """Check if file type is supported."""
    ext = get_file_extension(filename)
    return ext in SUPPORTED_EXTENSIONS


def is_image_file(filename: str) -> bool:
    """Check if file is an image."""
    ext = get_file_extension(filename)
    return ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']


async def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file."""
    try:
        import pypdf
        
        # DEBUG: Log first bytes to check file type
        header = file_content[:10].hex()
        logger.info(f"Extracting PDF text, first 10 bytes: {header}")
        
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_content))
        text_parts = []
        for i, page in enumerate(pdf_reader.pages):
            text = page.extract_text()
            if text:
                text_parts.append(text)
            else:
                logger.warning(f"Page {i+1} extracted empty text (possibly scanned)")
        
        full_text = "\n\n".join(text_parts)
        if not full_text.strip():
            logger.warning("Empty text extracted from PDF")
            # If empty, it's likely a scanned PDF or contains only images
            # Return a specific message that the agent can understand
            return "[PDF contains no extractable text. It may be a scanned image. Please provide the text manually or use an OCR tool.]"
            
        return full_text
    except ImportError:
        logger.warning("pypdf not installed. Install with: pip install pypdf")
        return "[PDF text extraction requires pypdf library]"
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return f"[Error extracting PDF: {str(e)}]"


async def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_content))
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        return "\n\n".join(text_parts)
    except ImportError:
        logger.warning("python-docx not installed. Install with: pip install python-docx")
        return "[DOCX text extraction requires python-docx library]"
    except Exception as e:
        logger.error(f"Error extracting DOCX text: {e}")
        return f"[Error extracting DOCX: {str(e)}]"


async def process_uploaded_file(filename: str, file_content: bytes) -> Tuple[str, Optional[str]]:
    """
    Process an uploaded file and return extracted content.
    
    Returns:
        Tuple of (content_type, extracted_text_or_base64)
        - For text/documents: ("text", extracted_text)
        - For images: ("image", base64_encoded_data)
    """
    ext = get_file_extension(filename)
    
    if ext == 'pdf':
        text = await extract_text_from_pdf(file_content)
        return ("text", text)
    
    elif ext == 'docx':
        text = await extract_text_from_docx(file_content)
        return ("text", text)
    
    elif ext == 'doc':
        # Old .doc format - harder to parse without additional libraries
        return ("text", "[.doc format not fully supported. Please convert to .docx or .pdf]")
    
    elif ext == 'txt':
        try:
            text = file_content.decode('utf-8')
        except UnicodeDecodeError:
            text = file_content.decode('latin-1')
        return ("text", text)
    
    elif is_image_file(filename):
        # Encode image as base64 for vision models
        base64_data = base64.b64encode(file_content).decode('utf-8')
        mime_type = SUPPORTED_EXTENSIONS.get(ext, 'image/png')
        return ("image", f"data:{mime_type};base64,{base64_data}")
    
    else:
        return ("error", f"Unsupported file type: {ext}")


def format_document_context(filename: str, content_type: str, content: str) -> str:
    """Format extracted document content for agent context."""
    if content_type == "text":
        return f"""
=== UPLOADED DOCUMENT: {filename} ===

{content}

=== END OF DOCUMENT ===

Please analyze this document and provide your assessment.
"""
    elif content_type == "image":
        return f"""
[Image uploaded: {filename}]

Please analyze this image and provide your assessment.
"""
    else:
        return f"[File upload error: {content}]"
