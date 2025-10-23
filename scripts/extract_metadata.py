#!/usr/bin/env python3
"""
LLM-based metadata extraction from PDFs for Qdrant filtering.
Extracts: year, document_type, title, topics
"""
import os
import json
from pathlib import Path
from typing import Dict, Any
from haystack.components.converters import PyPDFToDocument
from haystack_integrations.components.generators.openrouter import OpenRouterChatGenerator
from haystack.dataclasses import ChatMessage
from haystack.utils.auth import Secret
from dotenv import load_dotenv

load_dotenv()

def extract_metadata_from_pdf(pdf_path: Path, llm: OpenRouterChatGenerator) -> Dict[str, Any]:
    """
    Extract structured metadata from PDF using LLM.
    Returns: {year, document_type, source, topics, title}
    """
    # Convert first 2 pages to get header/title info
    converter = PyPDFToDocument()
    docs = converter.run(sources=[pdf_path])["documents"]
    
    # Get first ~1000 chars for context
    content = ""
    for doc in docs[:2]:
        text = getattr(doc, "text", None) or getattr(doc, "content", "")
        content += text[:1000]
    
    # LLM prompt for metadata extraction
    prompt = f"""Analysiere dieses PDF-Dokument und extrahiere strukturierte Metadaten.

Dokumentinhalt (erste Seiten):
{content}

Dateiname: {pdf_path.name}

Extrahiere folgende Informationen als JSON:
{{
  "year": <Jahr als Integer, z.B. 2024>,
  "document_type": <Typ: "wahlbericht", "sozialbericht", "statistik", "studie", "sonstiges">,
  "title": <Aussagekräftiger deutscher Titel>,
  "topics": [<Liste von 2-4 Hauptthemen als Keywords>],
  "source": "fritz.freiburg.de"
}}

Antworte NUR mit gültigem JSON, keine zusätzlichen Erklärungen."""

    messages = [ChatMessage.from_user(prompt)]
    result = llm.run(messages=messages)
    response = result["replies"][0].text.strip()
    
    # Parse JSON response
    try:
        # Remove markdown code blocks if present
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        
        metadata = json.loads(response.strip())
        
        # Validate and set defaults
        metadata.setdefault("year", None)
        metadata.setdefault("document_type", "sonstiges")
        metadata.setdefault("title", pdf_path.stem.replace("_", " "))
        metadata.setdefault("topics", [])
        metadata.setdefault("source", "fritz.freiburg.de")
        metadata["file_path"] = str(pdf_path)
        
        return metadata
    except Exception as e:
        print(f"  Warning: Failed to parse metadata: {e}")
        print(f"  LLM response: {response[:200]}")
        # Fallback to filename-based extraction
        return {
            "year": None,
            "document_type": "sonstiges",
            "title": pdf_path.stem.replace("_", " "),
            "topics": [],
            "source": "fritz.freiburg.de",
            "file_path": str(pdf_path)
        }

def extract_all_metadata(pdf_dir: Path) -> Dict[str, Dict[str, Any]]:
    """Extract metadata for all PDFs in directory."""
    llm = OpenRouterChatGenerator(
        api_key=Secret.from_token(os.getenv("OPENROUTER_API_KEY")),
        model="openai/gpt-4o-mini",
        generation_kwargs={"temperature": 0.0}
    )
    
    metadata_map = {}
    pdfs = list(pdf_dir.glob("*.pdf"))
    
    print(f"Extracting metadata from {len(pdfs)} PDFs...")
    for i, pdf_path in enumerate(pdfs, 1):
        print(f"[{i}/{len(pdfs)}] {pdf_path.name}...", end=" ", flush=True)
        try:
            metadata = extract_metadata_from_pdf(pdf_path, llm)
            metadata_map[pdf_path.name] = metadata
            print(f"✓ (year={metadata.get('year')}, type={metadata.get('document_type')})")
        except Exception as e:
            print(f"✗ Error: {e}")
            metadata_map[pdf_path.name] = {
                "year": None,
                "document_type": "sonstiges",
                "title": pdf_path.stem.replace("_", " "),
                "topics": [],
                "source": "fritz.freiburg.de",
                "file_path": str(pdf_path)
            }
    
    return metadata_map

if __name__ == "__main__":
    pdf_dir = Path("data/pdfs")
    
    if not pdf_dir.exists():
        print(f"ERROR: PDF directory not found: {pdf_dir}")
        exit(1)
    
    if not os.getenv("OPENROUTER_API_KEY"):
        print("ERROR: OPENROUTER_API_KEY not set in .env file")
        exit(1)
    
    metadata_map = extract_all_metadata(pdf_dir)
    
    # Save for reference
    output_path = Path("data/metadata_cache.json")
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata_map, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Metadata saved to {output_path}")
    print(f"\nTotal: {len(metadata_map)} PDFs processed")
    
    # Show summary statistics
    years = [m.get("year") for m in metadata_map.values() if m.get("year")]
    types = [m.get("document_type") for m in metadata_map.values()]
    
    if years:
        print(f"Years found: {sorted(set(years))}")
    print(f"Document types: {dict((t, types.count(t)) for t in set(types))}")
    
    print("\nSample metadata (first 3):")
    for name, meta in list(metadata_map.items())[:3]:
        print(f"\n  {name}:")
        print(f"    Year: {meta.get('year')}")
        print(f"    Type: {meta.get('document_type')}")
        print(f"    Title: {meta.get('title')}")
        print(f"    Topics: {', '.join(meta.get('topics', []))}")
