#!/usr/bin/env python3
"""
Simple test for the Text-to-Code Generator API
"""

import requests

API_URL = "http://localhost:8000"

def test_api():
    """Test the API with a simple request"""
    
    print("🧪 Testing Text-to-Code Generator API")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n1️⃣  Testing health check...")
    try:
        response = requests.get(f"{API_URL}/")
        if response.status_code == 200:
            print("✅ API is running")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API!")
        print("   Start it with: python api/server.py")
        print("   Or: uvicorn api.server:app --reload")
        return
    
    # Test 2: Generate code
    print("\n2️⃣  Generating code...")
    print("   Query: 'create a simple calculator with add and multiply'")
    print("   ⏳ This will take 30s-2min... please wait...")
    
    try:
        response = requests.post(
            f"{API_URL}/generate",
            json={"query": "create a simple calculator with add and multiply"},
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code == 200:
            # Save the zip file
            filename = "generated_project.zip"
            with open(filename, "wb") as f:
                f.write(response.content)
            
            print(f"✅ Success!")
            print(f"   Downloaded: {filename}")
            print(f"   Size: {len(response.content)} bytes")
            
            # Show how to extract
            print(f"\n📦 To extract:")
            print(f"   unzip {filename}")
            
        else:
            print(f"❌ Generation failed: {response.status_code}")
            print(f"   Error: {response.text}")
    
    except requests.Timeout:
        print("❌ Request timed out (took longer than 5 minutes)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_api()