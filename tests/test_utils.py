#!/usr/bin/env python3
"""
Shared utilities and test data for Freibot test suite.
Provides common fixtures, test queries, and helper functions.
"""

import time
from typing import Dict, List, Any
import pytest
from dotenv import load_dotenv

# Ensure .env is loaded for tests
load_dotenv()

from scripts.cli import TestClient

# Test client fixture
@pytest.fixture
def client():
    """Reusable test client fixture."""
    return TestClient()

# Common test queries organized by category
TEST_QUERIES = {
    "no_retrieval": [
        "Hallo",
        "Was ist 2+2?",
        "Wie funktioniert Python?", 
        "Erkläre mir Quantenphysik",
        "Danke",
        "Guten Tag"
    ],
    
    "light_retrieval": [
        "Wie viele Einwohner hat Freiburg?",
        "Wer ist der Bürgermeister von Freiburg?",
        "Wie groß ist Freiburg?",
        "Was ist die Arbeitslosenquote in Freiburg?",
        "Wie alt ist Freiburg?"
    ],
    
    "full_retrieval": [
        "Welche Stadtteile gibt es in Freiburg?",
        "Wie ist die Entwicklung der Arbeitslosigkeit in Freiburg?",
        "Vergleiche die verschiedenen Bezirke in Freiburg",
        "Was sagt der Sozialbericht über die Zufriedenheit?",
        "Welche demografischen Trends gibt es in Freiburg?",
        "Wie entwickelt sich der Wohnungsmarkt in Freiburg?"
    ],
    
    "german_compounds": [
        "Lärmschutzverordnung in Freiburg",
        "Stadtentwicklungsplan Freiburg", 
        "Öffentlichkeitsarbeit der Stadt",
        "Verkehrsberuhigung in der Innenstadt"
    ],
    
    "performance_test": [
        "Wie viele Einwohner hat Freiburg?",
        "Was ist die Arbeitslosenquote?",
        "Wie viele Studenten gibt es?",
        "Welche Bezirke gibt es?",
        "Wie ist die Altersstruktur?"
    ]
}

# Expected classifications for dynamic k testing
QUERY_CLASSIFICATIONS = {
    # No retrieval (k=0)
    "Hallo": ("no_retrieval", 0),
    "Was ist 2+2?": ("no_retrieval", 0),
    "Wie funktioniert Python?": ("no_retrieval", 0),
    "Erkläre mir Quantenphysik": ("no_retrieval", 0),
    "Danke": ("no_retrieval", 0),
    
    # Light retrieval (k=2)
    "Wie viele Einwohner hat Freiburg?": ("light_retrieval", 2),
    "Wer ist der Bürgermeister von Freiburg?": ("light_retrieval", 2),
    "Wie groß ist Freiburg?": ("light_retrieval", 2),
    
    # Full retrieval (k=3)
    "Welche Stadtteile gibt es in Freiburg?": ("full_retrieval", 3),
    "Wie ist die Entwicklung der Arbeitslosigkeit in Freiburg?": ("full_retrieval", 3),
    "Vergleiche die verschiedenen Bezirke in Freiburg": ("full_retrieval", 3),
    "Was sagt der Sozialbericht über die Zufriedenheit?": ("full_retrieval", 3)
}

def wait_for_api(client: TestClient, timeout: int = 30) -> bool:
    """
    Wait for API to be ready.
    
    Args:
        client: TestClient instance
        timeout: Maximum wait time in seconds
        
    Returns:
        bool: True if API is ready, False otherwise
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            health = client.health()
            if health.get("freibot_api", {}).get("status") == "healthy":
                return True
            time.sleep(1)
        except Exception:
            time.sleep(1)
    
    return False

def classify_query_result(sources_count: int) -> str:
    """
    Classify query result based on number of sources returned.
    
    Args:
        sources_count: Number of sources returned
        
    Returns:
        str: Classification ("no_retrieval", "light_retrieval", "full_retrieval")
    """
    if sources_count == 0:
        return "no_retrieval"
    elif sources_count <= 2:
        return "light_retrieval"
    else:
        return "full_retrieval"

def measure_response_time(client: TestClient, query: str, **kwargs) -> Dict[str, Any]:
    """
    Measure response time for a query.
    
    Args:
        client: TestClient instance
        query: Query string
        **kwargs: Additional arguments for ask method
        
    Returns:
        dict: Result with timing information
    """
    start_time = time.time()
    result = client.ask(query, **kwargs)
    end_time = time.time()
    
    result['response_time'] = end_time - start_time
    result['query'] = query
    
    return result

def calculate_success_rate(results: List[Dict]) -> float:
    """
    Calculate success rate from test results.
    
    Args:
        results: List of test result dictionaries
        
    Returns:
        float: Success rate as percentage (0-100)
    """
    if not results:
        return 0.0
    
    passed = sum(1 for r in results if r.get("success", False))
    return (passed / len(results)) * 100.0

def get_response_time_stats(results: List[Dict]) -> Dict[str, float]:
    """
    Calculate response time statistics.
    
    Args:
        results: List of test results with response_time field
        
    Returns:
        dict: Statistics (mean, min, max, p95)
    """
    times = [r.get("response_time", 0) for r in results if "response_time" in r]
    
    if not times:
        return {"mean": 0.0, "min": 0.0, "max": 0.0, "p95": 0.0}
    
    times.sort()
    n = len(times)
    p95_index = int(0.95 * n)
    
    return {
        "mean": sum(times) / n,
        "min": min(times),
        "max": max(times),
        "p95": times[p95_index] if p95_index < n else times[-1]
    }

def format_test_summary(test_name: str, results: List[Dict]) -> str:
    """
    Format a test summary string.
    
    Args:
        test_name: Name of the test
        results: List of test results
        
    Returns:
        str: Formatted summary
    """
    total = len(results)
    passed = sum(1 for r in results if r.get("success", False))
    failed = total - passed
    success_rate = (passed / total * 100) if total > 0 else 0
    
    summary = f"{test_name} Summary:\n"
    summary += f"  Total: {total}\n"
    summary += f"  Passed: {passed}\n"
    summary += f"  Failed: {failed}\n"
    summary += f"  Success Rate: {success_rate:.1f}%"
    
    # Add timing info if available
    time_stats = get_response_time_stats(results)
    if time_stats["mean"] > 0:
        summary += f"\n  Avg Response Time: {time_stats['mean']:.2f}s"
        summary += f"\n  P95 Response Time: {time_stats['p95']:.2f}s"
    
    return summary

# Common assertions for test validation
def assert_valid_response(result: Dict, require_answer: bool = True):
    """Assert that a response is valid."""
    assert "error" not in result, f"API returned error: {result.get('error')}"
    
    if require_answer:
        assert "answer" in result, "Response missing 'answer' field"
        assert result["answer"], "Answer is empty"
        assert len(result["answer"]) > 0, "Answer has no content"

def assert_has_sources(result: Dict, min_sources: int = 1):
    """Assert that response has minimum number of sources."""
    assert "sources" in result, "Response missing 'sources' field"
    sources = result["sources"]
    assert isinstance(sources, list), "Sources should be a list"
    assert len(sources) >= min_sources, f"Expected at least {min_sources} sources, got {len(sources)}"

def assert_response_time(result: Dict, max_time: float = 30.0):
    """Assert that response time is within acceptable limits."""
    response_time = result.get("response_time", result.get("latency", 0))
    assert response_time <= max_time, f"Response time {response_time:.2f}s exceeds limit {max_time}s"

def assert_german_content(result: Dict):
    """Assert that response contains German content."""
    answer = result.get("answer", "")
    # Check for common German words/characters
    german_indicators = ["ä", "ö", "ü", "ß", "der", "die", "das", "und", "ist", "eine", "ein"]
    has_german = any(indicator in answer.lower() for indicator in german_indicators)
    assert has_german, "Answer does not appear to contain German content"

# Skip decorators for different test conditions
def _check_api_availability():
    """Check if API is available."""
    try:
        client = TestClient()
        health = client.health()
        return health.get("freibot_api", {}).get("status") == "healthy"
    except Exception:
        return False

def _check_docs_availability():
    """Check if documents are loaded."""
    try:
        client = TestClient()
        stats = client.stats()
        return stats.get("chunk_count", 0) > 0
    except Exception:
        return False

skip_if_api_unavailable = pytest.mark.skipif(
    not _check_api_availability(),
    reason="Freibot API is not available"
)

skip_if_no_docs = pytest.mark.skipif(
    not _check_docs_availability(),
    reason="No documents loaded in vectorstore"
)