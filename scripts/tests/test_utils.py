#!/usr/bin/env python3
"""
Shared utilities and test data for Freibot test suite.
Provides common fixtures, test queries, and helper functions.

This version runs tests in-process using FastAPI's TestClient.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

import pytest
from dotenv import load_dotenv

# Ensure .env is loaded for tests (keys used by the app if present)
load_dotenv()

# Make repo root importable so we can import api.py from anywhere
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import FastAPI app and local TestClient
try:
    import api  # FastAPI app module at repo root
    from fastapi.testclient import TestClient as FastAPITestClient
    APP_IMPORT_OK = True
except Exception:
    api = None  # type: ignore
    FastAPITestClient = None  # type: ignore
    APP_IMPORT_OK = False


class APITestClient:
    """Thin wrapper exposing ask(), health(), stats(), timed_ask()."""
    def __init__(self, client: "FastAPITestClient"):
        self._client = client

    def ask(self, question: str, session_id: str | None = None, privacy_mode: bool = False, top_k: int | None = None) -> Dict[str, Any]:
        payload = {"question": question}
        if session_id is not None:
            payload["session_id"] = session_id
        if privacy_mode:
            payload["privacy_mode"] = True
        if top_k is not None:
            payload["top_k"] = top_k
        resp = self._client.post("/ask", json=payload)
        # Return JSON even on non-200 if possible, else raise
        try:
            data = resp.json()
        except Exception:
            resp.raise_for_status()
            data = {}
        return data

    def timed_ask(self, question: str, **kwargs) -> Dict[str, Any]:
        start = time.perf_counter()
        data = self.ask(question, **kwargs)
        data["latency"] = time.perf_counter() - start
        return data

    def health(self) -> Dict[str, Any]:
        """Composite health similar to CLI health_check, built in-process.
        Does not make any external network calls.
        """
        try:
            api_health = self._client.get("/health").json()
        except Exception:
            api_health = {}
        try:
            stats = self._client.get("/stats").json()
        except Exception:
            stats = {}

        # freibot_api block
        freibot = {
            "status": api_health.get("status", "unknown"),
            "details": {
                "documents": api_health.get("documents", 0),
                "pipeline_ready": api_health.get("pipeline_ready", False),
            },
        }

        # vectorstore block
        chunk_count = stats.get("chunk_count", 0)
        vectorstore = {
            "status": "healthy" if chunk_count > 0 else ("degraded" if api_health.get("vectorstore_available") else "offline"),
            "details": {
                "chunks": chunk_count,
                "pdfs": stats.get("pdf_count", 0),
            },
        }

        # openrouter block from env only (no network)
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        openrouter = {
            "status": "healthy" if openrouter_key else "no_key",
            "details": {},
        }

        # voyage block from env only (no network)
        voyage_key = os.getenv("VOYAGE_API_KEY")
        voyage = {
            "status": "healthy" if voyage_key else "no_key",
            "details": {},
        }

        return {
            "freibot_api": freibot,
            "vectorstore": vectorstore,
            "openrouter": openrouter,
            "voyage": voyage,
        }

    def stats(self) -> Dict[str, Any]:
        resp = self._client.get("/stats")
        return resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}


# ---------- Availability checks without network I/O at import time ----------

def _check_api_availability() -> bool:
    return APP_IMPORT_OK and getattr(api, "app", None) is not None


def _check_docs_availability() -> bool:
    if not _check_api_availability():
        return False
    try:
        store_available = bool(getattr(api, "STORE_AVAILABLE", False))
        if not store_available:
            return False
        store = getattr(api, "store", None)
        if store is None:
            return False
        if hasattr(store, "count_documents"):
            n = store.count_documents()
        elif hasattr(store, "count"):
            n = store.count()
        elif hasattr(store, "__len__"):
            n = len(store)  # type: ignore
        else:
            n = 0
        return (n or 0) > 0
    except Exception:
        return False


def _check_embeddings_available() -> bool:
    # Environment-based check
    return bool(os.getenv("VOYAGE_API_KEY"))


def _probe_retrieval_working() -> bool:
    # Conservative: only declare working if store and embeddings are present
    return _check_docs_availability() and _check_embeddings_available()


skip_if_api_unavailable = pytest.mark.skipif(
    not _check_api_availability(),
    reason="FastAPI app not importable (api.py)"
)

skip_if_no_docs = pytest.mark.skipif(
    not _check_docs_availability(),
    reason="No documents loaded in vectorstore"
)

skip_if_no_embeddings = pytest.mark.skipif(
    not _check_embeddings_available(),
    reason="Embeddings not available (VOYAGE_API_KEY missing or invalid)"
)

skip_if_retrieval_inactive = pytest.mark.skipif(
    not _probe_retrieval_working(),
    reason="Retrieval appears inactive (no docs or no embeddings)"
)


def wait_for_api(client: "APITestClient", timeout: int = 30) -> bool:
    """Wait for the in-process FastAPI app to report healthy.

    This performs in-process GET /health calls (no external network).
    Returns True on success within timeout, False otherwise.
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            health = client.health()
            if health.get("status") == "healthy":
                return True
            time.sleep(0.5)
        except Exception:
            time.sleep(0.5)
    return False

# --------- Pytest fixture: session-scoped APITestClient ----------

@pytest.fixture(scope="session")
def client():
    if not _check_api_availability():
        pytest.skip("FastAPI app (api.py) not importable; skipping in-process tests.")
    app = getattr(api, "app", None)
    if app is None:
        pytest.skip("api.app not found; cannot run in-process tests.")
    with FastAPITestClient(app) as fast_client:
        yield APITestClient(fast_client)


# ----------------------- Existing helpers below -----------------------

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


def classify_query_result(sources_count: int) -> str:
    """Classify query result based on number of sources returned."""
    if sources_count == 0:
        return "no_retrieval"
    elif sources_count <= 2:
        return "light_retrieval"
    else:
        return "full_retrieval"


def measure_response_time(client: APITestClient, query: str, **kwargs) -> Dict[str, Any]:
    """Measure response time for a query."""
    start_time = time.time()
    result = client.ask(query, **kwargs)
    end_time = time.time()
    result['response_time'] = end_time - start_time
    result['query'] = query
    return result


def calculate_success_rate(results: List[Dict]) -> float:
    """Calculate success rate from test results."""
    if not results:
        return 0.0
    passed = sum(1 for r in results if r.get("success", False))
    return (passed / len(results)) * 100.0


def get_response_time_stats(results: List[Dict]) -> Dict[str, float]:
    """Calculate response time statistics."""
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
    """Format a test summary string."""
    total = len(results)
    passed = sum(1 for r in results if r.get("success", False))
    failed = total - passed
    success_rate = (passed / total * 100) if total > 0 else 0
    summary = f"{test_name} Summary:\n"
    summary += f"  Total: {total}\n"
    summary += f"  Passed: {passed}\n"
    summary += f"  Failed: {failed}\n"
    summary += f"  Success Rate: {success_rate:.1f}%"
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
    german_indicators = ["ä", "ö", "ü", "ß", "der", "die", "das", "und", "ist", "eine", "ein"]
    has_german = any(indicator in answer.lower() for indicator in german_indicators)
    assert has_german, "Answer does not appear to contain German content"
