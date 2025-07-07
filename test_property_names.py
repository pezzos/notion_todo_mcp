#!/usr/bin/env python3
"""Test to check the actual property names in the database"""

import json
import urllib.request
from urllib.error import HTTPError

def check_property_names():
    """Check the actual property names in the database"""
    
    # Read config
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('NOTION_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
            elif line.startswith('NOTION_DATABASE_ID='):
                db_id = line.split('=', 1)[1].strip()
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28"
    }
    
    print("🔍 CHECKING PROPERTY NAMES")
    print("=" * 40)
    
    try:
        # Get database info
        url = f"https://api.notion.com/v1/databases/{db_id}"
        req = urllib.request.Request(url, headers=headers, method='GET')
        
        with urllib.request.urlopen(req) as response:
            db_info = json.loads(response.read().decode('utf-8'))
        
        properties = db_info.get('properties', {})
        
        print("📊 CURRENT PROPERTY NAMES:")
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get('type', 'unknown')
            print(f"  '{prop_name}': {prop_type}")
        
        print("\n🔧 EXPECTED BY MCP (current code):")
        expected = ['Tâche', 'Tags', 'Status', 'Priorité']
        for prop in expected:
            exists = prop in properties
            status = "✅" if exists else "❌"
            print(f"  {status} '{prop}'")
        
        print("\n💡 SUGGESTED MAPPING:")
        mapping = {}
        
        # Try to find the title property
        for prop_name, prop_info in properties.items():
            if prop_info.get('type') == 'title':
                mapping['title'] = prop_name
                print(f"  Title field: '{prop_name}'")
        
        # Try to find other properties
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get('type')
            if prop_type == 'multi_select' and 'tag' in prop_name.lower():
                mapping['tags'] = prop_name
                print(f"  Tags field: '{prop_name}'")
            elif prop_type == 'status':
                mapping['status'] = prop_name
                print(f"  Status field: '{prop_name}'")
            elif prop_type == 'select' and ('prior' in prop_name.lower() or 'priorit' in prop_name.lower()):
                mapping['priority'] = prop_name
                print(f"  Priority field: '{prop_name}'")
        
        return mapping
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {}

if __name__ == "__main__":
    mapping = check_property_names()
    
    if mapping:
        print(f"\n🚀 RECOMMENDED CODE UPDATES:")
        print("Update the server.py format_todo() function with these property names:")
        for field_type, prop_name in mapping.items():
            print(f"  {field_type}: '{prop_name}'")
    else:
        print("\n❌ Could not determine property mapping")