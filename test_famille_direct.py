#!/usr/bin/env python3
"""Test direct family tasks via the Notion API (without MCP)"""

import json
import urllib.request
import urllib.parse
import os
from urllib.error import HTTPError

# Configuration - Read from .env
def load_config():
    config = {}
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('NOTION_API_KEY='):
                config['api_key'] = line.split('=', 1)[1].strip()
            elif line.startswith('NOTION_DATABASE_ID='):
                config['db_id'] = line.split('=', 1)[1].strip()
    return config

config = load_config()
NOTION_API_KEY = config['api_key']
DATABASE_ID = config['db_id']
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

def test_family_tasks():
    """Test direct family tasks"""
    
    # Headers for the Notion API
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    
    # Filter for family tasks (Tags contains "Famille" AND active status)
    filter_data = {
        "filter": {
            "and": [
                {
                    "property": "Tags",
                    "multi_select": {
                        "contains": "Famille"
                    }
                },
                {
                    "property": "Status",
                    "status": {
                        "does_not_equal": "Done"
                    }
                },
                {
                    "property": "Status", 
                    "status": {
                        "does_not_equal": "Killed"
                    }
                }
            ]
        },
        "sorts": [
            {
                "timestamp": "created_time",
                "direction": "descending"
            }
        ]
    }
    
    try:
        # Prepare the request
        url = f"{NOTION_BASE_URL}/databases/{DATABASE_ID}/query"
        data = json.dumps(filter_data).encode('utf-8')
        
        # Create the request
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        print("🔍 Connecting to your TODO Notion database...")
        print(f"URL: {url}")
        print(f"Filter: Tasks with tag 'Famille' not completed")
        
        # Execute the request
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        # Analyze the results
        todos = result.get("results", [])
        print(f"\n✅ Connection successful ! {len(todos)} family tasks found\n")
        
        if not todos:
            print("📝 No active family task for the moment.")
            return
            
        print("👨‍👩‍👧‍👦 YOUR FAMILY TASKS :")
        print("=" * 50)
        
        for i, todo in enumerate(todos, 1):
            props = todo["properties"]
            
            # Extract the information
            task_name = ""
            if props.get("Tâche", {}).get("title"):
                task_name = props["Tâche"]["title"][0]["text"]["content"]
            
            # Tags
            tags = []
            if props.get("Tags", {}).get("multi_select"):
                tags = [tag["name"] for tag in props["Tags"]["multi_select"]]
            
            # Status
            status = "Unknown"
            if props.get("Status", {}).get("status"):
                status = props["Status"]["status"]["name"]
            
            # Priority
            priority = "Unknown"
            if props.get("Priorité", {}).get("select"):
                priority = props["Priorité"]["select"]["name"]
            
            # Display
            print(f"{i}. {task_name}")
            print(f"   📊 Status: {status}")
            print(f"   ⚡ Priorité: {priority}")
            print(f"   🏷️  Tags: {', '.join(tags)}")
            print()
            
        return True
        
    except HTTPError as e:
        print(f"❌ Erreur HTTP {e.code}: {e.reason}")
        if e.code == 401:
            print("🔑 Check your Notion API token")
        elif e.code == 404:
            print("🗃️  Check your database ID")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_family_tasks()
    if not success:
        print("\n🔧 Debug info:")
        print(f"API Key: {NOTION_API_KEY[:20]}...")
        print(f"Database ID: {DATABASE_ID}")