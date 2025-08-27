#!/usr/bin/env python3
"""Convert Freibot to Chroma vectorstore"""

import os
import sys
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from document_processor_claude import FreibotDocumentProcessor

def main():
    processor = FreibotDocumentProcessor()
    pdf_dir = Path("data/pdfs")
    
    if not pdf_dir.exists():
        print(f"Error: {pdf_dir} does not exist")
        return
    
    # Process all PDFs
    documents = processor.process_all_pdfs()
    print(f"Processed {len(documents)} document chunks")
    
    # Create Chroma vectorstore
    vectorstore = processor.create_vectorstore(documents, "data/vectorstore")
    print("Chroma vectorstore created successfully!")

if __name__ == "__main__":
    main()
