#!/usr/bin/env python3
"""
Minimal test to verify core functionality without full dependencies
"""
import os
import sys
from pathlib import Path

# Test environment setup
def test_environment():
    """Test if basic environment is set up correctly"""
    print("Testing environment...")
    
    # Check API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    print(f"OpenAI API Key: {'OK' if openai_key else 'MISSING'}")
    print(f"Anthropic API Key: {'OK' if anthropic_key else 'MISSING'}")
    
    # Check data directory
    data_dir = Path("data")
    pdfs_dir = data_dir / "pdfs"
    vectorstore_dir = data_dir / "vectorstore"
    
    print(f"Data directory: {'OK' if data_dir.exists() else 'MISSING'}")
    print(f"PDFs directory: {'OK' if pdfs_dir.exists() else 'MISSING'}")
    print(f"Vectorstore: {'OK' if vectorstore_dir.exists() else 'MISSING'}")
    
    if pdfs_dir.exists():
        pdf_count = len(list(pdfs_dir.glob("*.pdf")))
        print(f"PDF files: {pdf_count} found")
    
    return openai_key and anthropic_key and data_dir.exists()

def test_imports():
    """Test if core dependencies can be imported"""
    print("\nTesting imports...")
    
    try:
        import anthropic
        print("OK anthropic")
    except ImportError as e:
        print(f"FAIL anthropic: {e}")
        return False
    
    try:
        from langchain_community.embeddings import OpenAIEmbeddings
        print("OK langchain_community")
    except ImportError as e:
        print(f"FAIL langchain_community: {e}")
        return False
        
    try:
        from langchain_community.vectorstores import Chroma
        print("OK vectorstores (Chroma)")
    except ImportError as e:
        print(f"FAIL vectorstores: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("FrAIbot Minimal Test\n")
    
    # Load environment
    from pathlib import Path
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    env_ok = test_environment()
    imports_ok = test_imports()
    
    print(f"\nResults:")
    print(f"Environment: {'READY' if env_ok else 'ISSUES'}")
    print(f"Dependencies: {'READY' if imports_ok else 'ISSUES'}")
    
    if env_ok and imports_ok:
        print("\nCore system ready for containerization!")
    else:
        print("\nFix issues before proceeding")
