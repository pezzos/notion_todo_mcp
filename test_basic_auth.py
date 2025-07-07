#!/usr/bin/env python3
"""Basic test of the Notion API authentication"""

import json
import urllib.request
from urllib.error import HTTPError

def test_basic_auth():
    """Basic test: retrieve user info"""
    
    # Read the API key
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('NOTION_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28"
    }
    
    print("🔐 Test de l'authentification Notion API")
    print("=" * 45)
    print(f"🔑 Token: {api_key[:15]}...")
    
    try:
        # Test 1: Retrieve user info
        print("\n📋 Test 1: GET /v1/users/me")
        url = "https://api.notion.com/v1/users/me"
        req = urllib.request.Request(url, headers=headers, method='GET')
        
        with urllib.request.urlopen(req) as response:
            user_info = json.loads(response.read().decode('utf-8'))
        
        print("✅ Authentication successful !")
        print(f"👤 User: {user_info.get('name', 'N/A')}")
        print(f"📧 Email: {user_info.get('person', {}).get('email', 'N/A')}")
        print(f"🆔 ID: {user_info.get('id', 'N/A')}")
        
        # Test 2: General search
        print("\n📋 Test 2: POST /v1/search")
        url = "https://api.notion.com/v1/search"
        data = json.dumps({
            "query": "",
            "page_size": 5
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        with urllib.request.urlopen(req) as response:
            search_result = json.loads(response.read().decode('utf-8'))
        
        results = search_result.get("results", [])
        print(f"✅ Search successful ! {len(results)} elements found")
        
        # List the found databases
        databases = [r for r in results if r.get('object') == 'database']
        pages = [r for r in results if r.get('object') == 'page']
        
        print(f"🗃️  Accessible databases: {len(databases)}")
        print(f"📄 Accessible pages: {len(pages)}")
        
        if databases:
            print("\n📊 Found databases:")
            for i, db in enumerate(databases[:3], 1):  # Show the 3 first
                title = "No title"
                if db.get('title') and len(db['title']) > 0:
                    title = db['title'][0].get('text', {}).get('content', 'No title')
                
                print(f"  {i}. {title}")
                print(f"     ID: {db['id']}")
                
                # Check if it's our TODO database
                if 'todo' in title.lower() or 'tâche' in title.lower():
                    print("     🎯 This database seems to be your TODO !")
        
        return True
        
    except HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        if e.code == 401:
            print("🔑 Invalid or expired token")
        elif e.code == 403:
            print("🚫 Insufficient permissions")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_auth()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAIL'} - Authentication test")