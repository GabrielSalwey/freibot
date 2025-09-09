#!/usr/bin/env python3
"""
Test system for dynamic k selection in Freibot
Tests query classification and retrieval behavior
"""

import requests
import json
import time
from typing import Dict, List

# Configuration
API_BASE = "http://localhost:8001"
TIMEOUT = 30

class DynamicKTest:
    """Test dynamic k selection system."""
    
    def __init__(self):
        self.results = []
    
    def run_query_test(self, query: str, expected_classification: str, expected_k: int) -> Dict:
        """Run a single query test and analyze the result."""
        print(f"\nTesting: '{query}'")
        print(f"Expected: {expected_classification} (k={expected_k})")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{API_BASE}/ask",
                json={"question": query, "privacy_mode": True},  # Use privacy mode for testing
                timeout=TIMEOUT
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                actual_sources = len(data.get("sources", []))
                
                # Determine if retrieval was used based on sources
                if actual_sources == 0:
                    actual_k = 0
                    actual_classification = "no_retrieval"
                else:
                    actual_k = actual_sources
                    if actual_sources <= 2:
                        actual_classification = "light_retrieval"
                    else:
                        actual_classification = "full_retrieval"
                
                success = actual_k == expected_k
                
                result = {
                    "query": query,
                    "expected_classification": expected_classification,
                    "expected_k": expected_k,
                    "actual_classification": actual_classification, 
                    "actual_k": actual_k,
                    "success": success,
                    "response_time": elapsed,
                    "answer_length": len(data.get("answer", "")),
                    "answer_preview": data.get("answer", "")[:100] + "..." if len(data.get("answer", "")) > 100 else data.get("answer", "")
                }
                
                print(f"Actual: {actual_classification} (k={actual_k}) - {'✓' if success else '✗'}")
                print(f"Response time: {elapsed:.2f}s")
                print(f"Answer preview: {result['answer_preview']}")
                
                return result
                
            else:
                return {
                    "query": query,
                    "expected_classification": expected_classification,
                    "expected_k": expected_k,
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "response_time": elapsed
                }
                
        except Exception as e:
            return {
                "query": query,
                "expected_classification": expected_classification,
                "expected_k": expected_k,
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }
    
    def run_comprehensive_test(self):
        """Run comprehensive test suite for dynamic k selection."""
        print("Dynamic K Selection Test Suite")
        print("=" * 50)
        
        # Test cases: (query, expected_classification, expected_k)
        test_cases = [
            # No retrieval cases (k=0)
            ("Hallo", "no_retrieval", 0),
            ("Was ist 2+2?", "no_retrieval", 0),
            ("Wie funktioniert Python?", "no_retrieval", 0),
            ("Erkläre mir Quantenphysik", "no_retrieval", 0),
            ("Danke", "no_retrieval", 0),
            
            # Light retrieval cases (k=2)
            ("Wie viele Einwohner hat Freiburg?", "light_retrieval", 2),
            ("Wer ist der Bürgermeister von Freiburg?", "light_retrieval", 2),
            ("Wie groß ist Freiburg?", "light_retrieval", 2),
            
            # Full retrieval cases (k=3)
            ("Welche Stadtteile gibt es in Freiburg?", "full_retrieval", 3),
            ("Wie ist die Entwicklung der Arbeitslosigkeit in Freiburg?", "full_retrieval", 3),
            ("Vergleiche die verschiedenen Bezirke in Freiburg", "full_retrieval", 3),
            ("Was sagt der Sozialbericht über die Zufriedenheit?", "full_retrieval", 3),
            
            # Edge cases - mentions Freiburg but starts with no-retrieval pattern
            ("Was ist die Geschichte von Freiburg?", "full_retrieval", 3),  # Should override no-retrieval due to Freiburg mention
            ("Erkläre mir das Freiburger Münster", "full_retrieval", 3),  # Should override no-retrieval due to Freiburg mention
        ]
        
        # Run all tests
        for query, expected_class, expected_k in test_cases:
            result = self.run_query_test(query, expected_class, expected_k)
            self.results.append(result)
            time.sleep(0.5)  # Small delay between requests
        
        # Generate summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary and results."""
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.get("success", False))
        failed = total - passed
        
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success rate: {(passed/total)*100:.1f}%")
        
        # Response time stats
        times = [r.get("response_time", 0) for r in self.results if "response_time" in r]
        if times:
            avg_time = sum(times) / len(times)
            print(f"Average response time: {avg_time:.2f}s")
        
        # Failed tests detail
        failed_tests = [r for r in self.results if not r.get("success", False)]
        if failed_tests:
            print("\nFAILED TESTS:")
            for test in failed_tests:
                print(f"  - '{test['query']}'")
                print(f"    Expected: {test['expected_classification']} (k={test['expected_k']})")
                if 'actual_classification' in test:
                    print(f"    Actual: {test['actual_classification']} (k={test['actual_k']})")
                if 'error' in test:
                    print(f"    Error: {test['error']}")
        
        # Classification accuracy by type
        print("\nCLASSIFICATION ACCURACY:")
        for class_type in ["no_retrieval", "light_retrieval", "full_retrieval"]:
            class_tests = [r for r in self.results if r["expected_classification"] == class_type]
            if class_tests:
                class_passed = sum(1 for r in class_tests if r.get("success", False))
                print(f"  {class_type}: {class_passed}/{len(class_tests)} ({(class_passed/len(class_tests))*100:.1f}%)")

def main():
    """Main test runner."""
    # Check if API is available
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code != 200:
            print("ERROR: API is not healthy")
            return 1
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to Freibot API")
        print("Please start the API first: python freibot.py")
        return 1
    except Exception as e:
        print(f"ERROR: {e}")
        return 1
    
    # Run tests
    tester = DynamicKTest()
    tester.run_comprehensive_test()
    
    # Return success/failure code
    total = len(tester.results)
    passed = sum(1 for r in tester.results if r.get("success", False))
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit(main())