#!/usr/bin/env python3
"""
Test answer quality and regression testing in Freibot.
Implements three-tier quality strategy: structural → content → semantic/regression.
"""

import pytest
import re
import time
import statistics
from typing import Dict, List, Set, Tuple
from .test_utils import (
    client, TEST_QUERIES, 
    assert_valid_response, assert_has_sources, assert_german_content,
    skip_if_api_unavailable, skip_if_no_docs
)

class TestStructuralQuality:
    """Tier 1: Fast, deterministic structural quality checks."""

    @pytest.mark.parametrize("query_type,min_length", [
        ("light_retrieval", 50),    # Simple questions need substantial answers
        ("full_retrieval", 150),    # Complex questions need comprehensive answers
        ("german_compounds", 100),  # Compound terms need detailed explanations
    ])
    @skip_if_api_unavailable
    def test_answer_length_appropriateness(self, client, query_type: str, min_length: int):
        """Test that answer length matches query complexity."""
        queries = TEST_QUERIES.get(query_type, [])[:3]  # Test first 3 of each type
        
        for query in queries:
            result = client.ask(query)
            assert_valid_response(result)
            
            answer = result["answer"]
            actual_length = len(answer)
            
            assert actual_length >= min_length, (
                f"Answer too short for {query_type} query '{query}': "
                f"{actual_length} chars < {min_length} minimum"
            )

    @skip_if_api_unavailable
    @pytest.mark.parametrize("query_type,expected_sources", [
        ("no_retrieval", (0, 0)),      # Should have no sources
        ("light_retrieval", (1, 2)),   # Should have 1-2 sources
        ("full_retrieval", (3, 5)),    # Should have 3+ sources
    ])
    def test_source_citation_quality(self, client, query_type: str, expected_sources: Tuple[int, int]):
        """Test that source count matches query type appropriateness."""
        queries = TEST_QUERIES.get(query_type, [])[:3]
        min_sources, max_sources = expected_sources
        
        for query in queries:
            result = client.ask(query, privacy_mode=True)
            assert_valid_response(result, require_answer=False)
            
            sources = result.get("sources", [])
            source_count = len(sources)
            
            if max_sources == 0:  # No retrieval expected
                assert source_count == 0, (
                    f"No-retrieval query '{query}' returned {source_count} sources"
                )
            else:
                assert min_sources <= source_count <= max_sources or source_count >= max_sources, (
                    f"{query_type} query '{query}' returned {source_count} sources, "
                    f"expected {min_sources}-{max_sources}"
                )

    @skip_if_api_unavailable
    def test_response_completeness(self, client):
        """Test that responses contain substantive content, not generic rejections."""
        queries = TEST_QUERIES["light_retrieval"][:5] + TEST_QUERIES["full_retrieval"][:3]
        
        # Patterns that indicate non-substantive responses
        weak_patterns = [
            r"ich weiß nicht",
            r"kann ich nicht beantworten",
            r"keine information",
            r"sorry",
            r"entschuldigung",
            r"leider kann ich"
        ]
        
        for query in queries:
            result = client.ask(query)
            assert_valid_response(result)
            
            answer = result["answer"].lower()
            
            # Should not be dominated by weak response patterns
            weak_matches = sum(1 for pattern in weak_patterns if re.search(pattern, answer))
            
            # Allow some uncertainty expressions, but answer should be primarily substantive
            assert weak_matches <= 1, (
                f"Answer for '{query}' appears non-substantive with {weak_matches} weak patterns: "
                f"{answer[:200]}..."
            )
            
            # Should contain some factual content indicators
            factual_indicators = ["freiburg", "prozent", "anzahl", "jahr", "stadt", "bezirk", "einwohner"]
            has_factual_content = any(indicator in answer for indicator in factual_indicators)
            
            assert has_factual_content, f"Answer for '{query}' lacks factual content indicators"

    @skip_if_api_unavailable
    def test_german_language_quality(self, client):
        """Test German language indicators and basic structure."""
        queries = TEST_QUERIES["light_retrieval"][:3] + TEST_QUERIES["full_retrieval"][:2]
        
        # German language indicators
        german_chars = set("äöüß")
        german_words = {"der", "die", "das", "und", "ist", "sind", "hat", "haben", "ein", "eine", "von", "in", "mit"}
        
        for query in queries:
            result = client.ask(query)
            assert_valid_response(result)
            
            answer = result["answer"].lower()
            
            # Should contain German characters or words
            has_german_chars = any(char in answer for char in german_chars)
            has_german_words = any(word in answer.split() for word in german_words)
            
            assert has_german_chars or has_german_words, (
                f"Answer for '{query}' lacks German language indicators: {answer[:100]}..."
            )

    @skip_if_api_unavailable
    def test_basic_sentence_structure(self, client):
        """Test basic German sentence structure patterns."""
        queries = TEST_QUERIES["light_retrieval"][:3]
        
        for query in queries:
            result = client.ask(query)
            assert_valid_response(result)
            
            answer = result["answer"]
            
            # Should contain proper sentences (capital letters, periods)
            has_capitals = any(char.isupper() for char in answer)
            has_periods = "." in answer
            
            assert has_capitals, f"Answer lacks proper capitalization: {answer[:100]}..."
            assert has_periods, f"Answer lacks sentence structure (periods): {answer[:100]}..."
            
            # Should not be a single very long sentence (readability)
            sentence_count = answer.count(".") + answer.count("!") + answer.count("?")
            word_count = len(answer.split())
            
            if word_count > 50:  # Only check for longer answers
                avg_words_per_sentence = word_count / max(sentence_count, 1)
                assert avg_words_per_sentence < 40, (
                    f"Answer has overly long sentences (avg {avg_words_per_sentence:.1f} words/sentence)"
                )

class TestContentQuality:
    """Tier 2: Medium-cost content quality validation."""

    @skip_if_api_unavailable
    def test_numerical_reasonableness(self, client):
        """Test that numbers in answers are reasonable for Freiburg context."""
        queries = [
            "Wie viele Einwohner hat Freiburg?",
            "Was ist die Arbeitslosenquote?",
            "Wie groß ist Freiburg?",
        ]
        
        for query in queries:
            result = client.ask(query)
            assert_valid_response(result)
            
            answer = result["answer"]
            
            # Extract numbers from answer
            numbers = re.findall(r'\b\d+\.?\d*\b', answer)
            
            if numbers:  # If answer contains numbers
                for num_str in numbers:
                    try:
                        num = float(num_str.replace('.', ''))
                        
                        # Basic sanity checks for Freiburg context
                        if "einwohner" in query.lower():
                            # Population should be reasonable (100k-500k range)
                            assert 50000 <= num <= 1000000, (
                                f"Population number {num} seems unreasonable in: {answer[:200]}..."
                            )
                        
                        elif "arbeitslos" in query.lower():
                            # Unemployment should be percentage (0-20%)
                            if num <= 100:  # Likely a percentage
                                assert 0 <= num <= 25, (
                                    f"Unemployment rate {num}% seems unreasonable in: {answer[:200]}..."
                                )
                    
                    except (ValueError, AssertionError):
                        # Skip numbers that can't be parsed or fail validation
                        continue

    @skip_if_api_unavailable
    def test_query_keyword_presence(self, client):
        """Test that answers contain relevant keywords from the question."""
        test_cases = [
            ("Wie viele Einwohner hat Freiburg?", ["einwohner", "freiburg"]),
            ("Was ist die Arbeitslosenquote?", ["arbeitslos"]),
            ("Welche Stadtteile gibt es?", ["stadtteil"]),
            ("Wie ist die Verkehrssituation?", ["verkehr"]),
        ]
        
        for query, expected_keywords in test_cases:
            result = client.ask(query)
            assert_valid_response(result)
            
            answer = result["answer"].lower()
            
            # At least one expected keyword should appear
            found_keywords = [kw for kw in expected_keywords if kw in answer]
            
            assert len(found_keywords) > 0, (
                f"Answer for '{query}' missing expected keywords {expected_keywords}. "
                f"Answer: {answer[:200]}..."
            )

    @skip_if_api_unavailable  
    def test_freiburg_context_relevance(self, client):
        """Test that Freiburg-specific queries mention Freiburg appropriately."""
        freiburg_queries = [
            "Wie viele Einwohner hat Freiburg?",
            "Welche Stadtteile gibt es in Freiburg?",
            "Was ist typisch für Freiburg?",
        ]
        
        for query in freiburg_queries:
            result = client.ask(query)
            assert_valid_response(result)
            
            answer = result["answer"].lower()
            
            # Should mention Freiburg (unless it's very obvious from context)
            mentions_freiburg = "freiburg" in answer
            
            # For explicit Freiburg questions, answer should mention Freiburg
            if "freiburg" in query.lower():
                assert mentions_freiburg, (
                    f"Freiburg query '{query}' answer should mention Freiburg: {answer[:200]}..."
                )

    @skip_if_api_unavailable
    def test_topic_coherence(self, client):
        """Test that answers stay on topic and don't drift to unrelated subjects."""
        topic_test_cases = [
            ("Wie ist die Wohnsituation in Freiburg?", ["wohn", "miete", "immobilien"], ["wetter", "sport"]),
            ("Was ist die Verkehrssituation?", ["verkehr", "straße", "öffentlich"], ["wohnen", "kultur"]),
            ("Welche kulturellen Angebote gibt es?", ["kultur", "veranstaltung", "museum"], ["verkehr", "wirtschaft"]),
        ]
        
        for query, relevant_terms, irrelevant_terms in topic_test_cases:
            result = client.ask(query)
            assert_valid_response(result)
            
            answer = result["answer"].lower()
            
            # Should contain some relevant terms
            relevant_found = sum(1 for term in relevant_terms if term in answer)
            assert relevant_found > 0, (
                f"Answer for '{query}' lacks relevant terms {relevant_terms}: {answer[:200]}..."
            )
            
            # Should not be dominated by irrelevant terms  
            irrelevant_found = sum(1 for term in irrelevant_terms if term in answer)
            assert irrelevant_found <= relevant_found, (
                f"Answer for '{query}' contains more irrelevant terms ({irrelevant_found}) "
                f"than relevant ones ({relevant_found})"
            )

class TestSemanticQualityAndRegression:
    """Tier 3: Higher-cost semantic quality and regression testing."""

    @skip_if_api_unavailable
    def test_answer_consistency_repeated_queries(self, client):
        """Test that same questions get similar answers (consistency)."""
        critical_queries = [
            "Wie viele Einwohner hat Freiburg?",
            "Was ist die Arbeitslosenquote in Freiburg?",
            "Welche Stadtteile gibt es in Freiburg?",
        ]
        
        for query in critical_queries:
            # Ask same question twice with different session IDs
            result1 = client.ask(query, session_id=f"consistency_test_1_{int(time.time())}")
            time.sleep(0.5)
            result2 = client.ask(query, session_id=f"consistency_test_2_{int(time.time())}")
            
            assert_valid_response(result1)
            assert_valid_response(result2)
            
            answer1 = result1["answer"].lower()
            answer2 = result2["answer"].lower()
            
            # Basic consistency check: answers should share some common words
            words1 = set(answer1.split())
            words2 = set(answer2.split())
            
            # Remove very common words for better comparison
            stop_words = {"der", "die", "das", "und", "ist", "sind", "hat", "haben", "ein", "eine", "von", "in", "mit", "zu", "auf", "für", "als", "auch", "oder", "aber"}
            words1 -= stop_words
            words2 -= stop_words
            
            if len(words1) > 5 and len(words2) > 5:  # Only check substantial answers
                common_words = words1 & words2
                union_words = words1 | words2
                
                # Should have reasonable overlap (Jaccard similarity)
                if len(union_words) > 0:
                    similarity = len(common_words) / len(union_words)
                    assert similarity >= 0.2, (
                        f"Inconsistent answers for '{query}' (similarity {similarity:.3f}):\n"
                        f"Answer 1: {result1['answer'][:150]}...\n"
                        f"Answer 2: {result2['answer'][:150]}..."
                    )

    @skip_if_api_unavailable
    def test_critical_query_regression(self, client):
        """Test known good responses for critical queries (regression protection)."""
        # Define critical queries with expected characteristics
        regression_tests = [
            {
                "query": "Wie viele Einwohner hat Freiburg?",
                "must_contain": ["freiburg", "einwohner"],
                "should_contain_number": True,
                "min_length": 80,
                "max_sources": 3
            },
            {
                "query": "Welche Stadtteile gibt es in Freiburg?",
                "must_contain": ["stadtteil", "freiburg"],
                "should_contain_number": False,
                "min_length": 150,
                "max_sources": 5
            },
            {
                "query": "Was ist die Arbeitslosenquote?",
                "must_contain": ["arbeitslos"],
                "should_contain_number": True,
                "min_length": 60,
                "max_sources": 3
            }
        ]
        
        for test_case in regression_tests:
            query = test_case["query"]
            result = client.ask(query)
            assert_valid_response(result)
            
            answer = result["answer"].lower()
            sources = result.get("sources", [])
            
            # Must contain keywords
            for keyword in test_case["must_contain"]:
                assert keyword in answer, (
                    f"Regression: '{query}' missing required keyword '{keyword}': {answer[:200]}..."
                )
            
            # Number presence check
            has_number = bool(re.search(r'\d+', answer))
            if test_case["should_contain_number"]:
                assert has_number, f"Regression: '{query}' should contain numbers: {answer[:200]}..."
            
            # Length check
            assert len(answer) >= test_case["min_length"], (
                f"Regression: '{query}' answer too short ({len(answer)} < {test_case['min_length']})"
            )
            
            # Source count check
            assert len(sources) <= test_case["max_sources"], (
                f"Regression: '{query}' returned too many sources ({len(sources)} > {test_case['max_sources']})"
            )

    @skip_if_api_unavailable
    def test_performance_regression(self, client):
        """Test that response times haven't regressed significantly."""
        benchmark_queries = [
            "Wie viele Einwohner hat Freiburg?",
            "Was ist die Arbeitslosenquote?", 
            "Welche Stadtteile gibt es?",
        ]
        
        times = []
        for query in benchmark_queries:
            result = client.timed_ask(query)
            assert_valid_response(result)
            times.append(result.get("latency", 0))
            time.sleep(0.2)
        
        avg_time = statistics.mean(times)
        max_time = max(times)
        
        # Performance regression thresholds
        assert avg_time < 20.0, f"Performance regression: avg time {avg_time:.3f}s > 20s threshold"
        assert max_time < 35.0, f"Performance regression: max time {max_time:.3f}s > 35s threshold"
        
        print(f"Performance benchmark: avg {avg_time:.3f}s, max {max_time:.3f}s")

    @skip_if_api_unavailable
    def test_quality_score_tracking(self, client):
        """Calculate and track overall quality score for monitoring."""
        test_queries = TEST_QUERIES["light_retrieval"][:5] + TEST_QUERIES["full_retrieval"][:3]
        
        quality_scores = []
        
        for query in test_queries:
            result = client.ask(query)
            
            if "error" in result:
                quality_scores.append(0)  # Failed queries get 0 score
                continue
            
            score = 0
            answer = result.get("answer", "")
            sources = result.get("sources", [])
            
            # Scoring criteria (0-10 scale per criterion)
            
            # 1. Answer length appropriateness (0-2 points)
            if len(answer) >= 50:
                score += 1
            if len(answer) >= 150:
                score += 1
            
            # 2. German language quality (0-2 points)
            german_chars = any(char in answer.lower() for char in "äöüß")
            german_words = any(word in answer.lower() for word in ["der", "die", "das", "und", "ist"])
            if german_chars or german_words:
                score += 2
            
            # 3. Source appropriateness (0-2 points)  
            if "freiburg" in query.lower() and len(sources) > 0:
                score += 2
            elif "freiburg" not in query.lower() and len(sources) == 0:
                score += 2
            elif len(sources) > 0:  # At least some sources for other queries
                score += 1
            
            # 4. Content substantiveness (0-2 points)
            if not any(pattern in answer.lower() for pattern in ["weiß nicht", "kann nicht"]):
                score += 1
                if len(answer) > 100:
                    score += 1
            
            # 5. Query relevance (0-2 points)
            query_words = query.lower().split()
            answer_words = answer.lower().split()
            relevant_words = [w for w in query_words if w in answer_words and len(w) > 3]
            if len(relevant_words) > 0:
                score += 1
                if len(relevant_words) > 1:
                    score += 1
            
            quality_scores.append(score)
        
        # Calculate overall quality metrics
        if quality_scores:
            avg_quality = statistics.mean(quality_scores)
            min_quality = min(quality_scores)
            
            print(f"Quality Score: avg {avg_quality:.1f}/10, min {min_quality}/10")
            
            # Quality regression thresholds
            assert avg_quality >= 6.0, f"Quality regression: avg score {avg_quality:.1f} < 6.0 threshold"
            assert min_quality >= 3, f"Quality regression: min score {min_quality} < 3 threshold"

if __name__ == "__main__":
    # Allow running this file directly for development
    pytest.main([__file__, "-v"])