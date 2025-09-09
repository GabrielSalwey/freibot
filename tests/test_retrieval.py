#!/usr/bin/env python3
"""
Test retrieval effectiveness and dynamic k selection in Freibot.
Migrated from scripts/test_dynamic_k.py with pytest integration.
"""

import pytest
import time
from typing import Dict, List, Tuple
from .test_utils import (
    client, TEST_QUERIES, QUERY_CLASSIFICATIONS, 
    classify_query_result, assert_valid_response,
    skip_if_api_unavailable, format_test_summary
)

@pytest.mark.parametrize("query,expected", [
    # No retrieval cases (k=0)
    ("Hallo", ("no_retrieval", 0)),
    ("Was ist 2+2?", ("no_retrieval", 0)),
    ("Wie funktioniert Python?", ("no_retrieval", 0)),
    ("Erkläre mir Quantenphysik", ("no_retrieval", 0)),
    ("Danke", ("no_retrieval", 0)),
    
    # Light retrieval cases (k=2) 
    ("Wie viele Einwohner hat Freiburg?", ("light_retrieval", 2)),
    ("Wer ist der Bürgermeister von Freiburg?", ("light_retrieval", 2)),
    ("Wie groß ist Freiburg?", ("light_retrieval", 2)),
    
    # Full retrieval cases (k=3)
    ("Welche Stadtteile gibt es in Freiburg?", ("full_retrieval", 3)),
    ("Wie ist die Entwicklung der Arbeitslosigkeit in Freiburg?", ("full_retrieval", 3)),
    ("Vergleiche die verschiedenen Bezirke in Freiburg", ("full_retrieval", 3)),
    ("Was sagt der Sozialbericht über die Zufriedenheit?", ("full_retrieval", 3)),
])
@skip_if_api_unavailable
def test_dynamic_k_selection(client, query: str, expected: Tuple[str, int]):
    """Test that dynamic k selection works correctly for different query types."""
    expected_classification, expected_k = expected
    
    # Use privacy mode for testing to avoid logging
    result = client.ask(query, privacy_mode=True)
    assert_valid_response(result, require_answer=False)  # Some no_retrieval queries may have generic answers
    
    # Analyze retrieval behavior
    actual_sources = len(result.get("sources", []))
    actual_classification = classify_query_result(actual_sources)
    
    # Assert classification matches expectation
    assert actual_classification == expected_classification, (
        f"Query '{query}' classified as {actual_classification}, expected {expected_classification}"
    )
    
    # Assert k value matches expectation
    assert actual_sources == expected_k, (
        f"Query '{query}' retrieved {actual_sources} sources, expected {expected_k}"
    )

@pytest.mark.parametrize("query_type", ["light_retrieval", "full_retrieval"])
@skip_if_api_unavailable
def test_retrieval_quality(client, query_type: str):
    """Test that retrieved documents are relevant for different query types."""
    queries = TEST_QUERIES[query_type][:3]  # Test first 3 queries of each type
    
    for query in queries:
        result = client.ask(query, privacy_mode=True)
        assert_valid_response(result)
        
        sources = result.get("sources", [])
        assert len(sources) > 0, f"Query '{query}' should retrieve sources"
        
        # Check that answer contains substantive content
        answer = result["answer"]
        assert len(answer) > 50, f"Answer too short for query '{query}'"
        
        # For Freiburg-specific queries, answer should mention Freiburg
        if "Freiburg" in query:
            assert "Freiburg" in answer, f"Answer should mention Freiburg for query '{query}'"

@skip_if_api_unavailable
def test_query_classification_accuracy(client):
    """Test overall accuracy of query classification system."""
    results = []
    
    for query, (expected_class, expected_k) in QUERY_CLASSIFICATIONS.items():
        try:
            result = client.ask(query, privacy_mode=True)
            actual_sources = len(result.get("sources", []))
            actual_class = classify_query_result(actual_sources)
            
            success = (actual_class == expected_class and actual_sources == expected_k)
            
            results.append({
                "query": query,
                "expected_class": expected_class,
                "expected_k": expected_k,
                "actual_class": actual_class,
                "actual_k": actual_sources,
                "success": success
            })
            
            # Small delay between requests
            time.sleep(0.2)
            
        except Exception as e:
            results.append({
                "query": query,
                "expected_class": expected_class,
                "expected_k": expected_k,
                "success": False,
                "error": str(e)
            })
    
    # Calculate accuracy
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    accuracy = (passed / total) * 100 if total > 0 else 0
    
    # Print summary for debugging
    print(f"\nQuery Classification Accuracy: {passed}/{total} ({accuracy:.1f}%)")
    
    # Print failed tests
    failed = [r for r in results if not r["success"]]
    if failed:
        print("\nFailed Classifications:")
        for result in failed:
            if "error" in result:
                print(f"  - '{result['query']}': Error - {result['error']}")
            else:
                print(f"  - '{result['query']}': Expected {result['expected_class']} (k={result['expected_k']}), "
                      f"Got {result['actual_class']} (k={result['actual_k']})")
    
    # Assert minimum accuracy threshold
    assert accuracy >= 70.0, f"Classification accuracy {accuracy:.1f}% below 70% threshold"

@skip_if_api_unavailable  
def test_edge_cases(client):
    """Test edge cases for query classification."""
    edge_cases = [
        # Mentions Freiburg but starts with no-retrieval pattern
        ("Was ist die Geschichte von Freiburg?", "full_retrieval"),
        ("Erkläre mir das Freiburger Münster", "full_retrieval"),
        
        # Empty or very short queries
        ("Freiburg?", "light_retrieval"),
        ("Einwohner?", "no_retrieval"),  # Too ambiguous without context
        
        # Mixed language
        ("How many people live in Freiburg?", "light_retrieval"),
    ]
    
    for query, expected_class in edge_cases:
        result = client.ask(query, privacy_mode=True) 
        actual_sources = len(result.get("sources", []))
        actual_class = classify_query_result(actual_sources)
        
        print(f"Edge case '{query}': Expected {expected_class}, Got {actual_class}")
        # Note: Edge cases are documented for observation, not strict assertion

@skip_if_api_unavailable
def test_session_context_retrieval(client):
    """Test that retrieval works with session context."""
    session_id = f"test_retrieval_{int(time.time())}"
    
    # First question establishes context
    result1 = client.ask("Wie viele Einwohner hat Freiburg?", session_id=session_id)
    assert_valid_response(result1)
    assert len(result1.get("sources", [])) > 0, "First question should retrieve sources"
    
    # Follow-up question that relies on context
    result2 = client.ask("Und wie entwickelt sich die Bevölkerung?", session_id=session_id)
    assert_valid_response(result2)
    
    # Follow-up should still retrieve sources for complex questions
    sources2 = result2.get("sources", [])
    assert len(sources2) > 0, "Follow-up question should also retrieve relevant sources"

@skip_if_api_unavailable
def test_retrieval_performance(client):
    """Test retrieval performance under different conditions."""
    performance_queries = TEST_QUERIES["performance_test"]
    
    times = []
    for query in performance_queries:
        result = client.timed_ask(query, privacy_mode=True)
        assert_valid_response(result)
        
        response_time = result.get("latency", 0)
        times.append(response_time)
        
        # Individual query performance
        assert response_time < 30.0, f"Query '{query}' took {response_time:.2f}s (>30s limit)"
    
    # Average performance
    avg_time = sum(times) / len(times)
    assert avg_time < 10.0, f"Average response time {avg_time:.2f}s exceeds 10s"
    
    print(f"\nRetrieval Performance: Avg {avg_time:.2f}s, Max {max(times):.2f}s")

@skip_if_api_unavailable
def test_german_compound_retrieval(client):
    """Test retrieval effectiveness for German compound words."""
    compound_queries = TEST_QUERIES["german_compounds"]
    
    for query in compound_queries:
        result = client.ask(query, privacy_mode=True)
        assert_valid_response(result)
        
        sources = result.get("sources", [])
        answer = result["answer"]
        
        # Should retrieve sources for Freiburg-specific compound terms
        assert len(sources) > 0, f"Should retrieve sources for compound query '{query}'"
        
        # Answer should be substantial for compound word queries
        assert len(answer) > 100, f"Answer too brief for compound query '{query}'"
        
        print(f"Compound '{query}': {len(sources)} sources, {len(answer)} chars")

if __name__ == "__main__":
    # Allow running this file directly for development
    pytest.main([__file__, "-v"])