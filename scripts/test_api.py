#!/usr/bin/env python3
"""
Test script for Freibot API
Tests basic functionality and German language retrieval
"""

import sys
import time
import json
import requests
from typing import List, Dict, Any
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8001"
TIMEOUT = 30

class TestResult:
    """Simple test result tracking."""
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.message = ""
        self.duration = 0.0
    
    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"{status} [{self.duration:.2f}s] {self.name}: {self.message}"

def test_health_check() -> TestResult:
    """Test API health endpoint."""
    result = TestResult("Health Check")
    start = time.time()
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        result.duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            result.passed = data.get("status") == "healthy"
            result.message = f"API status: {data.get('status')}, Documents: {data.get('documents', 0)}"
        else:
            result.message = f"HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        result.message = "Cannot connect to API. Is freibot.py running?"
    except Exception as e:
        result.message = str(e)
    
    return result

def test_simple_query() -> TestResult:
    """Test a simple German query."""
    result = TestResult("Simple Query")
    start = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE}/ask",
            json={"question": "Wie viele Einwohner hat Freiburg?"},
            timeout=TIMEOUT
        )
        result.duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            if data.get("answer"):
                result.passed = True
                result.message = f"Got answer ({len(data['answer'])} chars)"
            else:
                result.message = "Empty answer"
        else:
            result.message = f"HTTP {response.status_code}"
    except Exception as e:
        result.message = str(e)
    
    return result

def test_german_compounds() -> TestResult:
    """Test German compound word handling."""
    result = TestResult("German Compounds")
    start = time.time()
    
    compound_queries = [
        "Lärmschutzverordnung",
        "Stadtentwicklungsplan",
        "Öffentlichkeitsarbeit"
    ]
    
    try:
        passed = 0
        for query in compound_queries:
            response = requests.post(
                f"{API_BASE}/ask",
                json={"question": f"Was ist die {query} in Freiburg?"},
                timeout=TIMEOUT
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("answer") and len(data["answer"]) > 50:
                    passed += 1
        
        result.duration = time.time() - start
        result.passed = passed >= 2  # At least 2 out of 3 should work
        result.message = f"{passed}/{len(compound_queries)} compound words handled"
    except Exception as e:
        result.message = str(e)
    
    return result

def test_source_citation() -> TestResult:
    """Test that sources are returned with answers."""
    result = TestResult("Source Citations")
    start = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE}/ask",
            json={"question": "Welche Stadtteile gibt es in Freiburg?"},
            timeout=TIMEOUT
        )
        result.duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            sources = data.get("sources", [])
            if sources and len(sources) > 0:
                result.passed = True
                result.message = f"Retrieved {len(sources)} source documents"
            else:
                result.message = "No sources returned"
        else:
            result.message = f"HTTP {response.status_code}"
    except Exception as e:
        result.message = str(e)
    
    return result

def test_response_time() -> TestResult:
    """Test that responses are reasonably fast."""
    result = TestResult("Response Time")
    
    queries = [
        "Wie viele Einwohner hat Freiburg?",
        "Was ist die Arbeitslosenquote?",
        "Wie viele Studenten gibt es?"
    ]
    
    times = []
    try:
        for query in queries:
            start = time.time()
            response = requests.post(
                f"{API_BASE}/ask",
                json={"question": query},
                timeout=TIMEOUT
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                times.append(elapsed)
        
        if times:
            avg_time = sum(times) / len(times)
            result.duration = avg_time
            result.passed = avg_time < 5.0  # Should respond within 5 seconds
            result.message = f"Avg: {avg_time:.2f}s, Max: {max(times):.2f}s"
        else:
            result.message = "No successful queries"
    except Exception as e:
        result.message = str(e)
    
    return result

def test_session_persistence() -> TestResult:
    """Test that conversation context is maintained."""
    result = TestResult("Session Context")
    start = time.time()
    
    try:
        session_id = f"test_{int(time.time())}"
        
        # First question
        response1 = requests.post(
            f"{API_BASE}/ask",
            json={
                "question": "Wie viele Einwohner hat Freiburg?",
                "session_id": session_id
            },
            timeout=TIMEOUT
        )
        
        # Follow-up question
        response2 = requests.post(
            f"{API_BASE}/ask",
            json={
                "question": "Und wie viele davon sind Studenten?",
                "session_id": session_id
            },
            timeout=TIMEOUT
        )
        
        result.duration = time.time() - start
        
        if response1.status_code == 200 and response2.status_code == 200:
            data2 = response2.json()
            # Check if the follow-up answer makes sense
            answer = data2.get("answer", "")
            if "Student" in answer or "Universität" in answer:
                result.passed = True
                result.message = "Context maintained across queries"
            else:
                result.message = "Context may not be maintained"
        else:
            result.message = "Failed to complete session test"
    except Exception as e:
        result.message = str(e)
    
    return result

def test_error_handling() -> TestResult:
    """Test that errors are handled gracefully."""
    result = TestResult("Error Handling")
    start = time.time()
    
    try:
        # Test with empty question
        response = requests.post(
            f"{API_BASE}/ask",
            json={"question": ""},
            timeout=TIMEOUT
        )
        result.duration = time.time() - start
        
        # Should handle empty question gracefully
        if response.status_code in [200, 400, 422]:
            result.passed = True
            result.message = "Handles invalid input gracefully"
        else:
            result.message = f"Unexpected status: {response.status_code}"
    except Exception as e:
        result.message = str(e)
    
    return result

def run_all_tests():
    """Run all tests and print summary."""
    print("Freibot API Test Suite")
    print("=" * 50)
    
    tests = [
        test_health_check,
        test_simple_query,
        test_german_compounds,
        test_source_citation,
        test_response_time,
        test_session_persistence,
        test_error_handling
    ]
    
    results = []
    for test_func in tests:
        print(f"\nRunning: {test_func.__name__}")
        result = test_func()
        results.append(result)
        print(result)
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\nAll tests passed!")
        return 0
    else:
        print(f"\n{total - passed} test(s) failed")
        return 1

def main():
    """Main entry point."""
    # Check if API is running first
    try:
        response = requests.get(f"{API_BASE}/health", timeout=2)
        if response.status_code != 200:
            print("WARNING: API returned non-200 status")
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to Freibot API")
        print("Please start the API first: python freibot.py")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return 1
    
    # Run tests
    return run_all_tests()

if __name__ == "__main__":
    sys.exit(main())