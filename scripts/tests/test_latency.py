#!/usr/bin/env python3
"""
Test component and total latency in Freibot.
Measures individual component timings up to TTFT and total response time.
"""

import pytest
import time
import statistics
from typing import Dict, List, Tuple
from .test_utils import (
    client, TEST_QUERIES, 
    measure_response_time, get_response_time_stats,
    skip_if_api_unavailable, assert_valid_response
)

class TestInfrastructureLatency:
    """Test basic infrastructure response times."""

    @skip_if_api_unavailable
    def test_health_endpoint_latency(self, client):
        """Test health check response time (infrastructure baseline)."""
        times = []
        for _ in range(5):
            start = time.time()
            health = client.health()
            elapsed = time.time() - start
            times.append(elapsed)
            
            assert "freibot_api" in health, "Health check should return API status"
            time.sleep(0.1)  # Small delay between requests
        
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
        
        # Health check should be very fast
        assert avg_time < 2.0, f"Health check avg {avg_time:.3f}s exceeds 2s"
        assert p95_time < 5.0, f"Health check p95 {p95_time:.3f}s exceeds 5s"
        
        print(f"Health latency: avg {avg_time:.3f}s, p95 {p95_time:.3f}s")

    @skip_if_api_unavailable  
    def test_stats_endpoint_latency(self, client):
        """Test stats endpoint response time (vectorstore access baseline)."""
        times = []
        for _ in range(5):
            start = time.time()
            stats = client.stats()
            elapsed = time.time() - start
            times.append(elapsed)
            
            assert "chunk_count" in stats, "Stats should return chunk count"
            time.sleep(0.1)
        
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]
        
        # Stats should be faster than full queries but may access vectorstore
        assert avg_time < 3.0, f"Stats avg {avg_time:.3f}s exceeds 3s"
        assert p95_time < 8.0, f"Stats p95 {p95_time:.3f}s exceeds 8s"
        
        print(f"Stats latency: avg {avg_time:.3f}s, p95 {p95_time:.3f}s")

class TestComponentLatency:
    """Test estimated component latencies by query type."""

    @skip_if_api_unavailable
    def test_llm_only_latency(self, client):
        """Test LLM-only latency using no-retrieval queries."""
        no_retrieval_queries = TEST_QUERIES["no_retrieval"][:5]
        times = []
        
        for query in no_retrieval_queries:
            result = client.timed_ask(query)
            assert_valid_response(result, require_answer=False)
            
            # Should have no sources (no retrieval)
            sources = result.get("sources", [])
            assert len(sources) == 0, f"No-retrieval query '{query}' returned {len(sources)} sources"
            
            latency = result.get("latency", 0)
            times.append(latency)
            time.sleep(0.2)
        
        avg_llm_time = statistics.mean(times)
        p95_llm_time = statistics.quantiles(times, n=20)[18]
        
        # LLM-only should be faster than retrieval queries
        assert avg_llm_time < 8.0, f"LLM-only avg {avg_llm_time:.3f}s exceeds 8s"
        assert p95_llm_time < 15.0, f"LLM-only p95 {p95_llm_time:.3f}s exceeds 15s"
        
        print(f"LLM-only latency: avg {avg_llm_time:.3f}s, p95 {p95_llm_time:.3f}s")
        return avg_llm_time, p95_llm_time

    @skip_if_api_unavailable
    def test_light_retrieval_latency(self, client):
        """Test light retrieval latency (embedding + limited search + LLM)."""
        light_queries = TEST_QUERIES["light_retrieval"][:5]
        times = []
        
        for query in light_queries:
            result = client.timed_ask(query)
            assert_valid_response(result)
            
            # Should have 1-2 sources
            sources = result.get("sources", [])
            assert 1 <= len(sources) <= 2, f"Light retrieval query '{query}' returned {len(sources)} sources"
            
            latency = result.get("latency", 0)
            times.append(latency)
            time.sleep(0.2)
        
        avg_light_time = statistics.mean(times)
        p95_light_time = statistics.quantiles(times, n=20)[18]
        
        # Light retrieval should be moderate
        assert avg_light_time < 12.0, f"Light retrieval avg {avg_light_time:.3f}s exceeds 12s"
        assert p95_light_time < 20.0, f"Light retrieval p95 {p95_light_time:.3f}s exceeds 20s"
        
        print(f"Light retrieval latency: avg {avg_light_time:.3f}s, p95 {p95_light_time:.3f}s")
        return avg_light_time, p95_light_time

    @skip_if_api_unavailable
    def test_full_retrieval_latency(self, client):
        """Test full retrieval latency (embedding + full search + LLM)."""
        full_queries = TEST_QUERIES["full_retrieval"][:5]
        times = []
        
        for query in full_queries:
            result = client.timed_ask(query)
            assert_valid_response(result)
            
            # Should have 3+ sources
            sources = result.get("sources", [])
            assert len(sources) >= 3, f"Full retrieval query '{query}' returned only {len(sources)} sources"
            
            latency = result.get("latency", 0)
            times.append(latency)
            time.sleep(0.2)
        
        avg_full_time = statistics.mean(times)
        p95_full_time = statistics.quantiles(times, n=20)[18]
        
        # Full retrieval will be slowest
        assert avg_full_time < 25.0, f"Full retrieval avg {avg_full_time:.3f}s exceeds 25s"
        assert p95_full_time < 45.0, f"Full retrieval p95 {p95_full_time:.3f}s exceeds 45s"
        
        print(f"Full retrieval latency: avg {avg_full_time:.3f}s, p95 {p95_full_time:.3f}s")
        return avg_full_time, p95_full_time

class TestTTFTEquivalent:
    """Test Time To First Token equivalent metrics."""

    @skip_if_api_unavailable
    def test_simple_vs_complex_query_latency(self, client):
        """Test TTFT-equivalent by comparing simple vs complex queries."""
        
        # Simple queries (should be faster to start processing)
        simple_queries = [
            "Hallo",
            "Wie viele Einwohner hat Freiburg?",
            "Danke"
        ]
        
        # Complex queries (may take longer to process/understand)
        complex_queries = [
            "Vergleiche die demografische Entwicklung der verschiedenen Stadtteile in Freiburg über die letzten Jahre",
            "Wie beeinflusst die Anwesenheit der Universität die Wohn- und Arbeitssituation in verschiedenen Bezirken?",
            "Welche Zusammenhänge gibt es zwischen Lärmschutzverordnungen und der Zufriedenheit in verschiedenen Stadtteilen?"
        ]
        
        simple_times = []
        complex_times = []
        
        # Test simple queries
        for query in simple_queries:
            result = client.timed_ask(query)
            simple_times.append(result.get("latency", 0))
            time.sleep(0.1)
        
        # Test complex queries  
        for query in complex_queries:
            result = client.timed_ask(query)
            assert_valid_response(result)
            complex_times.append(result.get("latency", 0))
            time.sleep(0.3)
        
        avg_simple = statistics.mean(simple_times)
        avg_complex = statistics.mean(complex_times)
        
        print(f"TTFT-equivalent - Simple: {avg_simple:.3f}s, Complex: {avg_complex:.3f}s")
        
        # Complex queries may take longer, but not dramatically longer for TTFT
        # (most latency is in LLM generation, not query understanding)
        ratio = avg_complex / avg_simple if avg_simple > 0 else 1
        assert ratio < 3.0, f"Complex queries {ratio:.1f}x slower than simple (TTFT issue?)"

class TestLatencyBreakdown:
    """Test estimated latency breakdown and total time validation."""

    @skip_if_api_unavailable
    def test_latency_component_analysis(self, client):
        """Analyze latency components and validate total time."""
        
        # Measure baseline times
        health_times = []
        llm_only_times = []
        light_retrieval_times = []
        full_retrieval_times = []
        
        # Infrastructure baseline (3 samples)
        for _ in range(3):
            start = time.time()
            client.health()
            health_times.append(time.time() - start)
            time.sleep(0.1)
        
        # LLM-only baseline (3 samples)
        no_retrieval_queries = TEST_QUERIES["no_retrieval"][:3]
        for query in no_retrieval_queries:
            result = client.timed_ask(query)
            llm_only_times.append(result.get("latency", 0))
            time.sleep(0.1)
        
        # Light retrieval (3 samples)
        light_queries = TEST_QUERIES["light_retrieval"][:3]
        for query in light_queries:
            result = client.timed_ask(query)
            light_retrieval_times.append(result.get("latency", 0))
            time.sleep(0.1)
        
        # Full retrieval (3 samples)
        full_queries = TEST_QUERIES["full_retrieval"][:3]
        for query in full_queries:
            result = client.timed_ask(query)
            full_retrieval_times.append(result.get("latency", 0))
            time.sleep(0.1)
        
        # Calculate averages
        avg_health = statistics.mean(health_times)
        avg_llm_only = statistics.mean(llm_only_times)
        avg_light = statistics.mean(light_retrieval_times)
        avg_full = statistics.mean(full_retrieval_times)
        
        # Estimate component costs
        infrastructure_cost = avg_health
        llm_base_cost = avg_llm_only - infrastructure_cost
        light_embedding_search_cost = avg_light - avg_llm_only
        full_embedding_search_cost = avg_full - avg_llm_only
        
        # Print breakdown
        print(f"\nLatency Breakdown Analysis:")
        print(f"  Infrastructure: {infrastructure_cost:.3f}s")
        print(f"  LLM (base): {llm_base_cost:.3f}s")
        print(f"  Light retrieval overhead: {light_embedding_search_cost:.3f}s")
        print(f"  Full retrieval overhead: {full_embedding_search_cost:.3f}s")
        print(f"  Total estimated (full): {infrastructure_cost + llm_base_cost + full_embedding_search_cost:.3f}s")
        print(f"  Total measured (full): {avg_full:.3f}s")
        
        # Validate logical progression
        assert avg_llm_only <= avg_light, "LLM-only should be <= light retrieval"
        assert avg_light <= avg_full, "Light retrieval should be <= full retrieval"
        
        # Validate component costs are reasonable
        assert llm_base_cost > 0, "LLM base cost should be positive"
        assert light_embedding_search_cost >= 0, "Light retrieval overhead should be non-negative"
        assert full_embedding_search_cost >= light_embedding_search_cost, "Full retrieval should cost more than light"

class TestLatencyRegression:
    """Test for latency regressions and performance monitoring."""

    @skip_if_api_unavailable
    def test_latency_percentiles(self, client):
        """Test latency percentiles for performance monitoring."""
        queries = [
            "Wie viele Einwohner hat Freiburg?",  # Standard query
            "Was ist die Arbeitslosenquote?",     # Standard query
            "Welche Stadtteile gibt es?",          # Complex query
        ]
        
        all_times = []
        for query in queries * 5:  # 15 total samples
            result = client.timed_ask(query)
            assert_valid_response(result, require_answer=False)
            all_times.append(result.get("latency", 0))
            time.sleep(0.1)
        
        # Calculate percentiles
        times_sorted = sorted(all_times)
        n = len(times_sorted)
        
        p50 = times_sorted[n // 2]
        p95 = times_sorted[int(0.95 * n)]
        p99 = times_sorted[int(0.99 * n)]
        avg_time = statistics.mean(all_times)
        max_time = max(all_times)
        
        print(f"\nLatency Percentiles:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  P50: {p50:.3f}s")
        print(f"  P95: {p95:.3f}s") 
        print(f"  P99: {p99:.3f}s")
        print(f"  Max: {max_time:.3f}s")
        
        # Performance regression thresholds
        assert avg_time < 15.0, f"Average latency {avg_time:.3f}s regression (>15s)"
        assert p95 < 30.0, f"P95 latency {p95:.3f}s regression (>30s)"
        assert p99 < 45.0, f"P99 latency {p99:.3f}s regression (>45s)"
        assert max_time < 60.0, f"Max latency {max_time:.3f}s regression (>60s)"

    @skip_if_api_unavailable
    def test_concurrent_latency_impact(self, client):
        """Test latency impact of concurrent requests."""
        import threading
        import queue
        
        results = queue.Queue()
        query = "Wie viele Einwohner hat Freiburg?"
        
        def make_timed_request(session_id):
            try:
                result = client.timed_ask(query, session_id=session_id)
                results.put(result.get("latency", 0))
            except Exception as e:
                results.put(None)
        
        # Sequential baseline
        sequential_times = []
        for i in range(3):
            result = client.timed_ask(query, session_id=f"seq_{i}")
            sequential_times.append(result.get("latency", 0))
            time.sleep(0.1)
        
        # Concurrent requests
        threads = []
        for i in range(3):
            thread = threading.Thread(target=make_timed_request, args=(f"conc_{i}",))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join(timeout=60)
        
        # Collect concurrent results
        concurrent_times = []
        while not results.empty():
            latency = results.get()
            if latency is not None:
                concurrent_times.append(latency)
        
        if concurrent_times and sequential_times:
            avg_sequential = statistics.mean(sequential_times)
            avg_concurrent = statistics.mean(concurrent_times)
            
            print(f"Concurrency impact: Sequential {avg_sequential:.3f}s, Concurrent {avg_concurrent:.3f}s")
            
            # Concurrent shouldn't be dramatically slower (some overhead expected)
            ratio = avg_concurrent / avg_sequential if avg_sequential > 0 else 1
            assert ratio < 2.5, f"Concurrent requests {ratio:.1f}x slower than sequential"

if __name__ == "__main__":
    # Allow running this file directly for development
    pytest.main([__file__, "-v"])