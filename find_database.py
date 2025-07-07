#!/usr/bin/env python3
"""Script to find and list all accessible databases"""

import json
import urllib.request
from urllib.error import HTTPError

def convert_id_to_uuid(id_32):
    """Convert a 32 characters ID to UUID format"""
    if len(id_32) == 32:
        return f"{id_32[:8]}-{id_32[8:12]}-{id_32[12:16]}-{id_32[16:20]}-{id_32[20:]}"
    return id_32

def find_databases():
    """Find all accessible databases"""
    
    # Read config
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('NOTION_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28"
    }
    
    print("🔍 Searching for all accessible databases...")
    
    try:
        # Try to list all databases via search
        url = "https://api.notion.com/v1/search"
        data = json.dumps({
            "filter": {
                "value": "database", 
                "property": "object"
            }
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        databases = result.get("results", [])
        print(f"✅ Found {len(databases)} accessible database(s)\n")
        
        for i, db in enumerate(databases, 1):
            title = "No title"
            if db.get('title'):
                title = db['title'][0].get('text', {}).get('content', 'No title')
            
            db_id = db['id']
            print(f"{i}. {title}")
            print(f"   ID: {db_id}")
            print(f"   URL: {db.get('url', 'N/A')}")
            
            # Search for properties that resemble a TODO
            props = db.get('properties', {})
            todo_props = []
            for prop_name in props.keys():
                if any(keyword in prop_name.lower() for keyword in ['tâche', 'task', 'todo', 'tags', 'status', 'priorité']):
                    todo_props.append(prop_name)
            
            if todo_props:
                print(f"   📋 TODO properties: {', '.join(todo_props)}")
            print()
        
        # Test with different ID formats
        test_ids = [
            "689e7bcbb1b94fc3bdae2c1e38a0f845",  # Format original
            "689e7bcb-b1b9-4fc3-bdae-2c1e38a0f845",  # Format UUID
        ]
        
        print("🧪 Testing possible IDs:")
        for test_id in test_ids:
            test_database_access(api_key, test_id)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_database_access(api_key, db_id):
    """Test the access to a specific database"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28"
    }
    
    try:
        url = f"https://api.notion.com/v1/databases/{db_id}"
        req = urllib.request.Request(url, headers=headers, method='GET')
        
        with urllib.request.urlopen(req) as response:
            db_info = json.loads(response.read().decode('utf-8'))
        
        title = "No title"
        if db_info.get('title'):
            title = db_info['title'][0].get('text', {}).get('content', 'No title')
        
        print(f"✅ {db_id}: {title}")
        
    except HTTPError as e:
        print(f"❌ {db_id}: HTTP {e.code}")

if __name__ == "__main__":
    find_databases()