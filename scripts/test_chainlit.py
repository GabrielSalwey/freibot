#!/usr/bin/env python3
"""
Simple liveness test for Chainlit frontend and Freibot API
- Verifies Chainlit HTTP endpoint is reachable
- Verifies Freibot API health and a sample /ask call
"""

import os
import sys
import json
import time
import requests

CHAINLIT_URL = os.getenv("CHAINLIT_URL", "http://localhost:8000")
API_BASE = os.getenv("FREIBOT_API_BASE", "http://localhost:8001")

def check_chainlit():
    try:
        r = requests.get(CHAINLIT_URL, timeout=5)
        print(f"[Chainlit] GET {CHAINLIT_URL} -> {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        print(f"[Chainlit] ERROR: {e}")
        return False

def check_api_health():
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        print(f"[API] GET /health -> {r.status_code}")
        if r.ok:
            print(f"[API] {json.dumps(r.json(), ensure_ascii=False)}")
        return r.ok
    except Exception as e:
        print(f"[API] ERROR: {e}")
        return False

def sample_ask():
    try:
        payload = {"question": "Wie viele Einwohner hat Freiburg?"}
        r = requests.post(f"{API_BASE}/ask", json=payload, timeout=30)
        print(f"[API] POST /ask -> {r.status_code}")
        if r.ok:
            data = r.json()
            print(f"[API] Answer: {data.get('answer', '')[:120]}...")
        return r.ok
    except Exception as e:
        print(f"[API] ERROR (ask): {e}")
        return False

def main():
    print("=" * 60)
    print("Chainlit & API Liveness Test")
    print("=" * 60)

    ok_chainlit = check_chainlit()
    ok_health = check_api_health()
    ok_ask = sample_ask() if ok_health else False

    print("\nSummary:")
    print(f"  Chainlit: {'OK' if ok_chainlit else 'FAIL'}")
    print(f"  API /health: {'OK' if ok_health else 'FAIL'}")
    print(f"  API /ask: {'OK' if ok_ask else 'FAIL'}")

    return 0 if (ok_chainlit and ok_health and ok_ask) else 1

if __name__ == "__main__":
    sys.exit(main())
