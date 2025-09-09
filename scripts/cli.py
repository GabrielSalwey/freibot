#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Freibot CLI - Command line interface for Freibot API
Simple tool for testing and interacting with the Freibot system

Usage: python scripts/cli.py ask "Your question"
       python scripts/cli.py interactive
       python scripts/cli.py health
"""

import argparse
import json
import os
import sys
import time
from typing import Optional
import requests
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fix Windows encoding issues
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# API Configuration
API_BASE = "http://localhost:8001"
TIMEOUT = 30

class TestClient:
    """Reusable test client using existing CLI functions."""
    
    def __init__(self, api_base=None, timeout=None):
        self.api_base = api_base or API_BASE
        self.timeout = timeout or TIMEOUT
    
    def ask(self, question: str, session_id: Optional[str] = None, privacy_mode: bool = False) -> dict:
        """Send a question using the existing ask_question function."""
        payload = {"question": question}
        if session_id is not None:
            payload["session_id"] = session_id
        if privacy_mode:
            payload["privacy_mode"] = privacy_mode
        
        try:
            response = requests.post(
                f"{self.api_base}/ask",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def health(self) -> dict:
        """Get health status using the existing health_check function."""
        return health_check()
    
    def timed_ask(self, question: str, **kwargs) -> dict:
        """Time the ask operation and include latency in result."""
        start = time.time()
        result = self.ask(question, **kwargs)
        result['latency'] = time.time() - start
        return result
    
    def stats(self) -> dict:
        """Get system stats."""
        try:
            response = requests.get(f"{self.api_base}/stats", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def ask_question(question: str, session_id: Optional[str] = None) -> dict:
    """Send a question to the Freibot API."""
    try:
        payload = {"question": question}
        if session_id is not None:
            payload["session_id"] = session_id
        
        response = requests.post(
            f"{API_BASE}/ask",
            json=payload,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to Freibot. Is it running? (python freibot.py)"}
    except requests.exceptions.Timeout:
        return {"error": f"Request timed out after {TIMEOUT} seconds"}
    except Exception as e:
        return {"error": str(e)}


def health_check() -> dict:
    """Comprehensive health check including API dependencies."""
    health = {
        "freibot_api": {"status": "unknown", "details": {}},
        "vectorstore": {"status": "unknown", "details": {}},
        "openrouter": {"status": "unknown", "details": {}},
        "voyage": {"status": "unknown", "details": {}}
    }
    
    # Check Freibot API
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        health["freibot_api"] = {
            "status": data.get("status", "unknown"),
            "details": {
                "documents": data.get("documents", 0),
                "pipeline_ready": data.get("pipeline_ready", False)
            }
        }
    except Exception as e:
        health["freibot_api"] = {
            "status": "offline",
            "details": {"error": str(e)}
        }
    
    # Check vectorstore (via stats endpoint)
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=5)
        response.raise_for_status()
        data = response.json()
        doc_count = data.get("chunk_count", 0)
        health["vectorstore"] = {
            "status": "healthy" if doc_count > 0 else "empty",
            "details": {
                "chunks": doc_count,
                "pdfs": data.get("pdf_count", 0)
            }
        }
    except Exception as e:
        health["vectorstore"] = {
            "status": "error",
            "details": {"error": str(e)}
        }
    
    # Check OpenRouter API (validate key)
    try:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            health["openrouter"] = {
                "status": "no_key",
                "details": {"error": "OPENROUTER_API_KEY not set"}
            }
        else:
            # Test with key validation endpoint
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(
                "https://openrouter.ai/api/v1/key",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                health["openrouter"] = {
                    "status": "healthy",
                    "details": {
                        "credits": data.get("data", {}).get("credits", "unknown"),
                        "limit": data.get("data", {}).get("rate_limit", {})
                    }
                }
            else:
                health["openrouter"] = {
                    "status": "error",
                    "details": {"error": f"HTTP {response.status_code}"}
                }
    except Exception as e:
        health["openrouter"] = {
            "status": "error",
            "details": {"error": str(e)}
        }
    
    # Check VoyageAI (test with minimal embed request)
    try:
        api_key = os.getenv("VOYAGE_API_KEY")
        if not api_key:
            health["voyage"] = {
                "status": "no_key",
                "details": {"error": "VOYAGE_API_KEY not set"}
            }
        else:
            # Test with minimal embed request
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            response = requests.post(
                "https://api.voyageai.com/v1/embeddings",
                headers=headers,
                json={"input": ["test"], "model": "voyage-3-large"},
                timeout=10
            )
            if response.status_code == 200:
                health["voyage"] = {
                    "status": "healthy",
                    "details": {"model": "voyage-3-large"}
                }
            else:
                health["voyage"] = {
                    "status": "error",
                    "details": {"error": f"HTTP {response.status_code}"}
                }
    except Exception as e:
        health["voyage"] = {
            "status": "error",
            "details": {"error": str(e)}
        }
    
    return health

def interactive_mode():
    """Run interactive question-answer session."""
    print("Freibot Interactive Mode")
    print("Type 'exit' or 'quit' to end session")
    print("-" * 40)
    
    session_id = f"cli_{int(time.time())}"
    
    while True:
        try:
            question = input("\nYour question: ").strip()
            
            if question.lower() in ['exit', 'quit', 'q']:
                print("Auf Wiedersehen!")
                break
            
            if not question:
                continue
            
            print("Searching...", end="", flush=True)
            result = ask_question(question, session_id)
            print("\r", end="")  # Clear searching message
            
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"\nAnswer:\n{result.get('answer', 'No answer provided')}")
                
                if result.get('sources'):
                    print(f"\nSources: {len(result['sources'])} documents")
                    
        except KeyboardInterrupt:
            print("\nAuf Wiedersehen!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Freibot CLI - Test and interact with Freibot API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ask a single question
  python scripts/cli.py ask "Wie viele Einwohner hat Freiburg?"
  
  # Interactive mode
  python scripts/cli.py interactive
  
  # Check comprehensive health status
  python scripts/cli.py health
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Ask command
    ask_parser = subparsers.add_parser("ask", help="Ask a single question")
    ask_parser.add_argument("question", help="Question to ask")
    ask_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # Interactive command
    subparsers.add_parser("interactive", help="Interactive Q&A mode")
    
    # Health command
    health_parser = subparsers.add_parser("health", help="Check comprehensive system health")
    health_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run test suite")
    test_parser.add_argument("type", nargs="?", default="all",
                            choices=["all", "latency", "quality", "retrieval", "behavior", "regression"],
                            help="Test type to run (default: all)")
    test_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Check if API is running (for non-health commands)
    if args.command != "health":
        basic_health = {}
        try:
            response = requests.get(f"{API_BASE}/health", timeout=5)
            basic_health = response.json() if response.status_code == 200 else {}
        except:
            pass
        
        if basic_health.get("status") != "healthy":
            print("ERROR: Freibot API is not running. Start it with: python freibot.py")
            sys.exit(1)
    
    # Execute commands
    if args.command == "ask":
        result = ask_question(args.question)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"{result.get('answer', 'No answer')}")
                
    elif args.command == "interactive":
        interactive_mode()
        
    elif args.command == "health":
        health = health_check()
        
        if args.json:
            print(json.dumps(health, indent=2, ensure_ascii=False))
        else:
            print("Freibot System Health Check")
            print("=" * 30)
            
            for component, info in health.items():
                status = info["status"]
                emoji = "✅" if status == "healthy" else "❌" if status in ["offline", "error"] else "⚠️"
                print(f"\n{emoji} {component.upper()}: {status}")
                
                if info.get("details"):
                    for key, value in info["details"].items():
                        print(f"   {key}: {value}")
            
            # Overall status
            all_healthy = all(info["status"] == "healthy" for info in health.values())
            overall = "✅ All systems operational" if all_healthy else "⚠️ Some issues detected"
            print(f"\n{overall}")
            
    elif args.command == "test":
        import subprocess
        
        # Build pytest command with Windows-compatible flags
        if args.type == "all":
            cmd = ["pytest", "tests/", "-s", "--disable-warnings"]
        else:
            cmd = ["pytest", f"tests/test_{args.type}.py", "-s", "--disable-warnings"]
        
        # Add verbosity flag
        if args.verbose:
            cmd.extend(["-v", "--tb=short"])
        else:
            cmd.append("-q")
        
        # Run pytest and exit with its return code
        try:
            result = subprocess.run(cmd, cwd=".")
            sys.exit(result.returncode)
        except FileNotFoundError:
            print("ERROR: pytest not found. Install with: pip install pytest")
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: Failed to run tests: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()