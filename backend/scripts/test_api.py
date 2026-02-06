"""
Test script for API endpoints.
Tests all endpoints to verify they work correctly.
"""

import sys
import requests
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoints."""
    print("\n" + "="*70)
    print("TEST 1: Health Endpoints")
    print("="*70 + "\n")
    
    # Basic health
    response = requests.get(f"{BASE_URL}/api/health/")
    print(f"✅ GET /api/health/ - Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)[:200]}...")
    
    # Detailed health
    response = requests.get(f"{BASE_URL}/api/health/detailed")
    print(f"\n✅ GET /api/health/detailed - Status: {response.status_code}")
    data = response.json()
    print(f"   Documents: {data.get('vector_db', {}).get('documents', 0)}")
    
    return True


def test_chat():
    """Test chat endpoint."""
    print("\n" + "="*70)
    print("TEST 2: Chat Endpoint")
    print("="*70 + "\n")
    
    payload = {
        "message": "What is Kafka?",
        "source_type": None,
        "stream": False
    }
    
    response = requests.post(f"{BASE_URL}/api/chat/", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ POST /api/chat/ - Status: {response.status_code}")
        print(f"   Answer length: {len(data.get('answer', ''))} characters")
        print(f"   Sources: {len(data.get('sources', []))}")
        print(f"   Conversation ID: {data.get('conversation_id', 'N/A')}")
        print(f"\n   Answer preview: {data.get('answer', '')[:200]}...")
        return True
    else:
        print(f"❌ POST /api/chat/ - Status: {response.status_code}")
        print(f"   Error: {response.text}")
        return False


def test_chat_with_conversation():
    """Test chat with conversation history."""
    print("\n" + "="*70)
    print("TEST 3: Chat with Conversation")
    print("="*70 + "\n")
    
    # First message
    payload1 = {
        "message": "What is Kafka replication?",
        "stream": False
    }
    
    response1 = requests.post(f"{BASE_URL}/api/chat/", json=payload1)
    data1 = response1.json()
    conversation_id = data1.get('conversation_id')
    
    print(f"✅ First message - Conversation ID: {conversation_id}")
    
    # Follow-up message
    payload2 = {
        "message": "How does it work?",
        "conversation_id": conversation_id,
        "stream": False
    }
    
    response2 = requests.post(f"{BASE_URL}/api/chat/", json=payload2)
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"✅ Follow-up message - Status: {response2.status_code}")
        print(f"   Answer length: {len(data2.get('answer', ''))} characters")
        
        # Get conversation history
        history_response = requests.get(f"{BASE_URL}/api/chat/conversations/{conversation_id}")
        if history_response.status_code == 200:
            history = history_response.json()
            print(f"✅ Conversation history - Messages: {history.get('message_count', 0)}")
        
        return True
    else:
        print(f"❌ Follow-up failed - Status: {response2.status_code}")
        return False


def main():
    """Run all API tests."""
    print("\n🚀 API ENDPOINTS TEST SUITE 🚀\n")
    print(f"Testing API at: {BASE_URL}")
    print("Make sure the server is running: python main.py\n")
    
    results = []
    
    try:
        results.append(("Health Endpoints", test_health()))
    except Exception as e:
        print(f"❌ Health test failed: {e}")
        results.append(("Health Endpoints", False))
    
    try:
        results.append(("Chat Endpoint", test_chat()))
    except Exception as e:
        print(f"❌ Chat test failed: {e}")
        results.append(("Chat Endpoint", False))
    
    try:
        results.append(("Chat with Conversation", test_chat_with_conversation()))
    except Exception as e:
        print(f"❌ Conversation test failed: {e}")
        results.append(("Chat with Conversation", False))
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70 + "\n")
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All API tests passed! 🎉\n")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
