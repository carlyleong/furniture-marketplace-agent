#!/usr/bin/env python3
"""
Docker health check script for the Furniture Classifier backend
"""
import sys
import requests
import time

def health_check():
    """Check if the backend is healthy"""
    try:
        response = requests.get('http://localhost:8000/api/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend healthy: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Backend unhealthy: status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend unreachable: {e}")
        return False

if __name__ == "__main__":
    # Give the backend time to start
    time.sleep(2)
    
    if health_check():
        sys.exit(0)
    else:
        sys.exit(1)
