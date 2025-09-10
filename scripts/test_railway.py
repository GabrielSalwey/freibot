#!/usr/bin/env python3
"""
Test Railway API and monitor deployment status
"""

import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_railway_graphql():
    """Test Railway GraphQL API with different authentication methods"""
    api_token = os.getenv("RAILWAY_API_TOKEN")
    if not api_token:
        print("[ERROR] RAILWAY_API_TOKEN not found in environment")
        return False
    
    url = "https://backboard.railway.com/graphql/v2"
    headers = {"Content-Type": "application/json"}
    
    # Test different authentication methods
    auth_methods = [
        ("Authorization", f"Bearer {api_token}"),
        ("Project-Access-Token", api_token),
        ("Team-Access-Token", api_token),
    ]
    
    queries = [
        ("me", '{"query":"query { me { name email } }"}'),
        ("projectToken", '{"query":"query { projectToken { projectId environmentId } }"}'),
        ("projects", '{"query":"query { projects { edges { node { id name } } } }"}'),
    ]
    
    print(f"[INFO] Testing Railway API at {url}")
    print(f"[INFO] Token: {api_token[:8]}...")
    
    for auth_name, auth_value in auth_methods:
        print(f"\n--- Testing {auth_name} ---")
        test_headers = headers.copy()
        test_headers[auth_name] = auth_value
        
        for query_name, query_data in queries:
            try:
                response = requests.post(url, headers=test_headers, data=query_data, timeout=10)
                print(f"[{query_name}] Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    if "errors" in result:
                        print(f"[{query_name}] Error: {result['errors'][0]['message']}")
                    else:
                        print(f"[{query_name}] Success: {json.dumps(result['data'], indent=2)}")
                        return True  # Found working auth method
                else:
                    print(f"[{query_name}] HTTP Error: {response.text}")
                    
            except Exception as e:
                print(f"[{query_name}] Exception: {e}")
    
    return False

def check_deployment_via_github():
    """Check deployment status via GitHub API (fallback method)"""
    print("\n[INFO] Checking deployment via GitHub API (fallback)")
    
    try:
        # Get latest deployments
        url = "https://api.github.com/repos/GabrielSalwey/freibot/deployments"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            deployments = response.json()
            if deployments:
                latest = deployments[0]
                print(f"[GITHUB] Latest deployment: {latest['id']}")
                print(f"[GITHUB] Created: {latest['created_at']}")
                print(f"[GITHUB] SHA: {latest['sha'][:8]}")
                print(f"[GITHUB] Environment: {latest['environment']}")
                
                # Get deployment status
                status_url = latest['statuses_url']
                status_response = requests.get(status_url, timeout=10)
                
                if status_response.status_code == 200:
                    statuses = status_response.json()
                    if statuses:
                        current_status = statuses[0]
                        print(f"[GITHUB] Status: {current_status['state']}")
                        print(f"[GITHUB] Updated: {current_status['updated_at']}")
                        if current_status.get('target_url'):
                            print(f"[GITHUB] Dashboard: {current_status['target_url']}")
                        return current_status['state']
                        
    except Exception as e:
        print(f"[GITHUB] Error: {e}")
    
    return None

def test_freibot_endpoint():
    """Test if the deployed Freibot is accessible"""
    endpoints = [
        "https://freibot.de",
        "https://freibot-production.up.railway.app",  # Common Railway pattern
    ]
    
    print("\n[INFO] Testing deployed endpoints")
    
    for endpoint in endpoints:
        try:
            print(f"[TEST] Checking {endpoint}")
            response = requests.get(endpoint, timeout=10, allow_redirects=True)
            print(f"[TEST] Status: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text[:200]
                if "chainlit" in content.lower() or "freibot" in content.lower():
                    print(f"[TEST] ✅ Freibot detected at {endpoint}")
                    return endpoint
                else:
                    print(f"[TEST] ⚠️ Response doesn't look like Freibbot")
            
        except requests.exceptions.ConnectionError:
            print(f"[TEST] [X] Connection failed - {endpoint} not accessible")
        except Exception as e:
            print(f"[TEST] [X] Error: {e}")
    
    return None

def main():
    """Main monitoring function"""
    print("=" * 60)
    print(f"Railway Deployment Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test Railway API
    railway_api_works = test_railway_graphql()
    
    # Check deployment status via GitHub (fallback)
    deployment_status = check_deployment_via_github()
    
    # Test deployed endpoints
    working_endpoint = test_freibot_endpoint()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Railway API: {'[OK] Working' if railway_api_works else '[X] Failed'}")
    print(f"GitHub Deployment: {deployment_status or '[X] Unknown'}")
    print(f"Live Endpoint: {working_endpoint or '[X] Not accessible'}")
    
    if working_endpoint:
        print(f"\n[SUCCESS] Freibot is live at: {working_endpoint}")
    elif deployment_status == "in_progress":
        print(f"\n[WAIT] Deployment in progress - check again in a few minutes")
    else:
        print(f"\n[ERROR] Freibot appears to be offline")

if __name__ == "__main__":
    main()