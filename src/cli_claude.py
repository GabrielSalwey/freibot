#!/usr/bin/env python3
"""
Freibot CLI - Command Line Interface for Freiburg AI Assistant (Claude Edition)
"""

import os
import sys
from pathlib import Path
import argparse
from typing import Dict, Any

# Add src to path
sys.path.append(str(Path(__file__).parent))

from document_processor_claude import FreibotRAG, FreibotDocumentProcessor

def setup_environment():
    """Setup environment variables from .env file"""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def print_banner():
    """Print Freibot banner"""
    print("""
    ╔═══════════════════════════════════════════╗
    ║              🤖 FREIBOT 🤖                ║
    ║        Your Freiburg AI Assistant         ║
    ║           Powered by Claude 🧠            ║
    ║                                           ║
    ║     Ask questions about Freiburg data     ║
    ║       from Fritz statistical reports     ║
    ╚═══════════════════════════════════════════╝
    """)

def print_sources(sources: list):
    """Print source information in a nice format"""
    if not sources:
        return
    
    print("\n📚 Sources:")
    for i, source in enumerate(sources, 1):
        print(f"  {i}. {source['title']} ({source['year']})")
        print(f"     Type: {source['document_type']}, Page: {source['page']}")

def process_documents():
    """Process PDF documents and create vector store"""
    print("🔄 Processing documents with Claude support...")
    
    processor = FreibotDocumentProcessor()
    documents = processor.process_all_pdfs()
    
    if documents:
        vectorstore = processor.create_vectorstore(documents)
        print(f"✅ Successfully processed {len(documents)} document chunks")
        return True
    else:
        print("❌ No documents processed")
        return False

def interactive_mode():
    """Run interactive Q&A mode with Claude"""
    print("🚀 Starting interactive mode with Claude...")
    print("Type 'quit' or 'exit' to stop, 'help' for commands")
    print("Pro tip: Claude is great at detailed analysis and comparisons!\n")
    
    # Initialize RAG system with Claude
    rag = FreibotRAG(claude_model="claude-3-haiku-20240307")  # Fast and cheap
    if not rag.load_vectorstore():
        print("❌ Could not load vector store. Please run document processing first.")
        print("Use: python cli_claude.py --process-docs")
        return
    
    print("✅ Claude is ready! Ask me anything about Freiburg...")
    
    while True:
        try:
            question = input("\n🤔 Your question: ").strip()
            
            if not question:
                continue
                
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Auf Wiedersehen!")
                break
                
            if question.lower() in ['help', 'h']:
                print_help()
                continue
            
            print("🧠 Claude is analyzing the documents...")
            result = rag.ask_question(question)
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"\n💡 Claude's Answer:")
                print(f"{result['answer']}")
                print_sources(result['sources'])
                
        except KeyboardInterrupt:
            print("\n👋 Auf Wiedersehen!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

def print_help():
    """Print help information"""
    print("""
    📖 Freibot Help (Claude Edition):
    
    Commands:
    - help, h         Show this help
    - quit, exit, q   Exit the program
    
    Example questions (Claude excels at these):
    - Wie viele Einwohner hat Freiburg und wie entwickelt sich die Bevölkerung?
    - Vergleiche die Wahlergebnisse zwischen verschiedenen Stadtbezirken
    - Analysiere die wichtigsten Trends im Sozialbericht
    - Welche demographischen Veränderungen zeigen die Statistiken?
    - Erkläre mir die Ergebnisse der letzten Gemeinderatswahl im Detail
    - Was sind die sozialen Herausforderungen in Freiburg laut den Daten?
    
    💡 Claude's strengths:
    - Detailed analysis and explanations
    - Comparisons across multiple documents
    - Context-aware responses
    - Better German language understanding
    """)

def single_question(question: str, model: str = "claude-3-haiku-20240307"):
    """Answer a single question using Claude"""
    rag = FreibotRAG(claude_model=model)
    if not rag.load_vectorstore():
        print("❌ Could not load vector store. Please run document processing first.")
        return
    
    print(f"🤔 Question: {question}")
    print("🧠 Claude is analyzing...")
    
    result = rag.ask_question(question)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"\n💡 Claude's Answer:")
        print(f"{result['answer']}")
        print_sources(result['sources'])

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Freibot - Freiburg AI Assistant (Claude Edition)")
    parser.add_argument("--process-docs", action="store_true", 
                       help="Process PDF documents and create vector store")
    parser.add_argument("--question", "-q", type=str, 
                       help="Ask a single question")
    parser.add_argument("--model", "-m", type=str, 
                       default="claude-3-haiku-20240307",
                       choices=["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229"],
                       help="Claude model to use (haiku=fastest/cheapest, sonnet=balanced, opus=most capable)")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Start interactive mode (default)")
    
    args = parser.parse_args()
    
    # Setup environment
    setup_environment()
    
    # Check for API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not found")
        print("Please add your Anthropic API key to the .env file:")
        print("ANTHROPIC_API_KEY=your_key_here")
        print("\nGet your key at: https://console.anthropic.com/account/keys")
        return
        
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found")
        print("We still need OpenAI for embeddings (very cheap ~$0.0001 per document)")
        print("Please add your OpenAI API key to the .env file:")
        print("OPENAI_API_KEY=your_key_here")
        return
    
    print_banner()
    print(f"🧠 Using Claude model: {args.model}")
    
    # Handle commands
    if args.process_docs:
        process_documents()
    elif args.question:
        single_question(args.question, args.model)
    else:
        # Default to interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()
