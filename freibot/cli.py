"""
CLI module for Freibot.

**INPUTS:**
    - Command line arguments (ask, interactive, health, benchmark, test, index)
    - Questions from stdin in interactive mode
    
**OUTPUTS:**
    - Formatted text output to stdout
    - Exit codes (0 for success, 1 for failure)

**RESPONSIBILITIES:**
    - Provide command-line interface to Freibot
    - Support single questions and interactive mode
    - Run health checks and benchmarks
    - Trigger document indexing
    - Execute test suites
    
**DEPENDENCIES:**
    - argparse (stdlib)
    - api module or direct backend access
    - document_processor.pipeline (for indexing)
    
**TODO:**
    - Add color output for better UX
    - Support JSON output mode
    - Add verbose/quiet flags
"""

from typing import Optional, List


def main():
    """
    Main CLI entry point.
    
    Parses arguments and dispatches to appropriate command.
    """
    raise NotImplementedError


def cmd_ask(question: str):
    """
    Ask a single question and print answer.
    
    Args:
        question: Question to ask
    """
    raise NotImplementedError


def cmd_interactive():
    """
    Start interactive Q&A session.
    
    Reads questions from stdin until EOF or quit command.
    """
    raise NotImplementedError


def cmd_health():
    """
    Check system health and print status.
    
    Checks API, vectorstore, and external services.
    """
    raise NotImplementedError


def cmd_benchmark(queries: Optional[List[str]] = None):
    """
    Run benchmark queries and measure performance.
    
    Args:
        queries: Optional custom queries, uses defaults if None
    """
    raise NotImplementedError


def cmd_test(categories: Optional[List[str]] = None):
    """
    Run test suite.
    
    Args:
        categories: Optional test categories (behavior, latency, quality, etc.)
    """
    raise NotImplementedError


def cmd_index(
    pdf_dir: str = "data/pdfs",
    mode: str = "full"
):
    """
    Trigger document indexing.
    
    Args:
        pdf_dir: Directory containing PDFs
        mode: "full" or "append"
    """
    raise NotImplementedError
