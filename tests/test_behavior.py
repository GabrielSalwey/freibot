#!/usr/bin/env python3
"""
Test system behavior and API functionality in Freibot.
Migrated from scripts/test_api.py with pytest integration.
"""

import pytest
import time
from typing import Dict, List
from .test_utils import (
    client, TEST_QUERIES, wait_for_api,
    assert_valid_response, assert_has_sources, assert_response_time, assert_german_content,
    skip_if_api_unavailable, skip_if_no_docs, format_test_summary
)

class TestBasicFunctionality:
    """Test basic API functionality."""

    @skip_if_api_unavailable
    def test_health_check(self, client):
        """Test API health endpoint."""
        health = client.health()
        
        # Should have all required components
        required_components = ["freibot_api", "vectorstore", "openrouter", "voyage"]
        for component in required_components:
            assert component in health, f"Missing health component: {component}"
        
        # Freibot API should be healthy
        freibot_status = health["freibot_api"]["status"]
        assert freibot_status == "healthy", f"Freibot API status: {freibot_status}"
        
        # Should report document count
        details = health["freibot_api"].get("details", {})
        doc_count = details.get("documents", 0)
        assert doc_count > 0, "No documents reported in health check"

    @skip_if_api_unavailable
    def test_stats_endpoint(self, client):
        """Test system stats endpoint."""
        stats = client.stats()
        assert "error" not in stats, f"Stats endpoint error: {stats.get('error')}"
        
        # Should have chunk and PDF counts
        chunk_count = stats.get("chunk_count", 0)
        pdf_count = stats.get("pdf_count", 0)
        
        assert chunk_count > 0, "No chunks reported in stats"
        assert pdf_count > 0, "No PDFs reported in stats"
        
        print(f"System stats: {chunk_count} chunks from {pdf_count} PDFs")

class TestQueryHandling:
    """Test different types of query handling."""

    @skip_if_api_unavailable 
    @skip_if_no_docs
    def test_simple_german_query(self, client):
        """Test a simple German query."""
        result = client.ask("Wie viele Einwohner hat Freiburg?")
        assert_valid_response(result)
        assert_has_sources(result)
        assert_german_content(result)

    @skip_if_api_unavailable
    @pytest.mark.parametrize("query", TEST_QUERIES["german_compounds"][:3])
    def test_german_compound_words(self, client, query):
        """Test German compound word handling."""
        result = client.ask(query)
        assert_valid_response(result)
        
        # Compound word queries about Freiburg should retrieve sources
        if "Freiburg" in query:
            assert_has_sources(result)
        
        # Answer should be substantial
        answer = result["answer"]
        assert len(answer) > 50, f"Answer too short for compound query '{query}'"

    @skip_if_api_unavailable
    def test_source_citations(self, client):
        """Test that sources are returned with answers."""
        result = client.ask("Welche Stadtteile gibt es in Freiburg?")
        assert_valid_response(result)
        
        sources = result.get("sources", [])
        assert len(sources) > 0, "Should return source documents"
        
        # Sources should be a list of dictionaries or strings
        for source in sources:
            assert source, "Source should not be empty"
            
        print(f"Retrieved {len(sources)} source documents")

    @skip_if_api_unavailable
    def test_no_retrieval_queries(self, client):
        """Test queries that shouldn't trigger retrieval."""
        no_retrieval_queries = TEST_QUERIES["no_retrieval"][:3]
        
        for query in no_retrieval_queries:
            result = client.ask(query)
            assert_valid_response(result, require_answer=False)  # May have generic answers
            
            sources = result.get("sources", [])
            assert len(sources) == 0, f"Query '{query}' should not retrieve sources but got {len(sources)}"

class TestSessionManagement:
    """Test conversation session handling."""

    @skip_if_api_unavailable
    def test_session_persistence(self, client):
        """Test that conversation context is maintained."""
        session_id = f"test_session_{int(time.time())}"
        
        # First question
        result1 = client.ask("Wie viele Einwohner hat Freiburg?", session_id=session_id)
        assert_valid_response(result1)
        
        # Follow-up question using context
        result2 = client.ask("Und wie viele davon sind Studenten?", session_id=session_id)
        assert_valid_response(result2)
        
        # Follow-up answer should be contextually relevant
        answer2 = result2["answer"]
        student_indicators = ["Student", "Universität", "Hochschule", "studieren"]
        has_student_context = any(indicator in answer2 for indicator in student_indicators)
        assert has_student_context, "Follow-up answer should contain student-related context"

    @skip_if_api_unavailable
    def test_multiple_sessions(self, client):
        """Test that different sessions are isolated."""
        session1 = f"test_session_1_{int(time.time())}"
        session2 = f"test_session_2_{int(time.time())}"
        
        # Different questions in different sessions
        result1 = client.ask("Wie ist das Wetter in Freiburg?", session_id=session1)
        result2 = client.ask("Wie viele Einwohner hat Freiburg?", session_id=session2)
        
        # Both should work independently
        assert_valid_response(result1, require_answer=False)
        assert_valid_response(result2)

class TestErrorHandling:
    """Test error handling and edge cases."""

    @skip_if_api_unavailable
    def test_empty_question(self, client):
        """Test handling of empty questions."""
        result = client.ask("")
        
        # Should handle gracefully - either return error or generic response
        if "error" in result:
            # Error response is acceptable
            assert "error" in result
        else:
            # Or should return some kind of response
            assert "answer" in result

    @skip_if_api_unavailable
    def test_very_long_question(self, client):
        """Test handling of very long questions."""
        long_question = "Was ist " + "sehr " * 100 + "lang und kompliziert in Freiburg?"
        result = client.ask(long_question)
        
        # Should handle without crashing
        assert "error" not in result or "timeout" in result.get("error", "").lower()

    @skip_if_api_unavailable 
    def test_special_characters(self, client):
        """Test handling of special characters."""
        special_queries = [
            "Wie ist die Situation in Freiburg? 🏛️",
            "Freiburg's Bevölkerung?",
            "Was kostet 1m² in Freiburg?",
            "Lärmschutz & Umwelt in Freiburg"
        ]
        
        for query in special_queries:
            result = client.ask(query)
            # Should not crash, may return valid answer or handle gracefully
            assert isinstance(result, dict), f"Should return dict for query '{query}'"

class TestPerformance:
    """Test response time and performance characteristics."""

    @skip_if_api_unavailable
    def test_response_time_limits(self, client):
        """Test that responses are reasonably fast."""
        queries = TEST_QUERIES["performance_test"][:3]
        
        times = []
        for query in queries:
            result = client.timed_ask(query)
            assert_valid_response(result)
            
            response_time = result.get("latency", 0)
            times.append(response_time)
            
            # Individual query should complete within timeout
            assert_response_time(result, max_time=30.0)
        
        # Average should be reasonable
        avg_time = sum(times) / len(times)
        assert avg_time < 15.0, f"Average response time {avg_time:.2f}s exceeds 15s"
        
        print(f"Performance: Avg {avg_time:.2f}s, Max {max(times):.2f}s")

    @skip_if_api_unavailable
    def test_concurrent_requests(self, client):
        """Test handling of multiple concurrent requests."""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request(query, session_id):
            try:
                result = client.ask(query, session_id=session_id)
                results.put(("success", result))
            except Exception as e:
                results.put(("error", str(e)))
        
        # Start 3 concurrent requests
        threads = []
        queries = ["Wie viele Einwohner hat Freiburg?", 
                  "Was ist die Arbeitslosenquote?",
                  "Wie groß ist Freiburg?"]
        
        for i, query in enumerate(queries):
            session_id = f"concurrent_test_{i}_{int(time.time())}"
            thread = threading.Thread(target=make_request, args=(query, session_id))
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join(timeout=60)  # 60 second timeout
        
        # Check results
        successful = 0
        while not results.empty():
            status, result = results.get()
            if status == "success" and "error" not in result:
                successful += 1
        
        assert successful >= 2, f"Only {successful}/3 concurrent requests succeeded"

class TestPrivacyMode:
    """Test privacy mode functionality."""

    @skip_if_api_unavailable
    def test_privacy_mode(self, client):
        """Test that privacy mode works."""
        query = "Wie viele Einwohner hat Freiburg?"
        
        # Regular request
        result1 = client.ask(query, privacy_mode=False)
        assert_valid_response(result1)
        
        # Privacy mode request  
        result2 = client.ask(query, privacy_mode=True)
        assert_valid_response(result2)
        
        # Both should return valid answers
        assert len(result1["answer"]) > 0
        assert len(result2["answer"]) > 0

if __name__ == "__main__":
    # Allow running this file directly for development
    pytest.main([__file__, "-v"])