#!/usr/bin/env python3
"""Test PDF text extraction directly without running the server."""

import asyncio
import base64
import sys

async def test_with_file(pdf_path: str):
    """Test extracting text from a real PDF file."""
    from lexedge.web.file_processor import process_uploaded_file, format_document_context
    
    print(f"\n=== Testing PDF: {pdf_path} ===")
    
    with open(pdf_path, "rb") as f:
        file_content = f.read()
    
    print(f"File size: {len(file_content)} bytes")
    print(f"First 10 bytes (hex): {file_content[:10].hex()}")
    print(f"Is valid PDF header: {file_content[:5] == b'%PDF-'}")
    
    content_type, extracted_text = await process_uploaded_file(pdf_path.split("/")[-1], file_content)
    
    print(f"Content type: {content_type}")
    if content_type == "text":
        print(f"Extracted text length: {len(extracted_text)}")
        print(f"First 500 characters:\n{extracted_text[:500]}")
    else:
        print(f"Error: {extracted_text}")

async def test_b64_pdf(b64_data: str):
    """Test extracting from base64 encoded PDF (as the web app sends it)."""
    from lexedge.web.file_processor import process_uploaded_file
    import base64
    
    print(f"\n=== Testing Base64 PDF ===")
    print(f"Base64 length: {len(b64_data)}")
    
    # Handle data URI format
    if b64_data.startswith("data:"):
        header, encoded = b64_data.split(",", 1)
        print(f"MIME type from header: {header.split(':')[1].split(';')[0]}")
        file_bytes = base64.b64decode(encoded)
    else:
        file_bytes = base64.b64decode(b64_data)
    
    print(f"Decoded bytes: {len(file_bytes)}")
    print(f"First 10 bytes (hex): {file_bytes[:10].hex()}")
    print(f"Is valid PDF header: {file_bytes[:5] == b'%PDF-'}")
    
    content_type, extracted_text = await process_uploaded_file("test.pdf", file_bytes)
    print(f"Content type: {content_type}")
    if content_type == "text":
        print(f"Extracted text length: {len(extracted_text)}")
        print(f"First 500 characters:\n{extracted_text[:500]}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        asyncio.run(test_with_file(pdf_path))
    else:
        print("Usage: python3 test_pdf_extract.py /path/to/your.pdf")
        print("\nNo PDF path given - searching for sample PDFs...")
        import glob
        pdfs = glob.glob("**/*.pdf", recursive=True)
        if pdfs:
            print(f"Found: {pdfs[0]}")
            asyncio.run(test_with_file(pdfs[0]))
        else:
            print("No PDFs found in current directory. Please provide a path.")
