#!/usr/bin/env python3
"""Test simple of the check_setup command"""

import json
import urllib.request
from urllib.error import HTTPError

def test_check_setup():
    """Test the check_setup functionality via the direct API"""
    
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
    
    print("🔍 TEST CHECK SETUP")
    print("=" * 30)
    print(f"🔑 API Key: {api_key[:15]}...")
    print(f"🗃️  Database ID: {db_id}")
    
    try:
        # Test if the database exists
        url = f"https://api.notion.com/v1/databases/{db_id}"
        req = urllib.request.Request(url, headers=headers, method='GET')
        
        with urllib.request.urlopen(req) as response:
            db_info = json.loads(response.read().decode('utf-8'))
        
        print("\n✅ Database found !")
        
        # Verify the title
        title = "Unknown"
        if db_info.get('title') and len(db_info['title']) > 0:
            title = db_info['title'][0].get('text', {}).get('content', 'Unknown')
        print(f"📊 Name: {title}")
        
        # Verify the properties
        properties = db_info.get('properties', {})
        required_props = ['Tâche', 'Tags', 'Status', 'Priorité']
        
        print(f"\n🔧 Properties ({len(properties)}):")
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get('type', 'unknown')
            status = "✅" if prop_name in required_props else "ℹ️"
            print(f"  {status} {prop_name}: {prop_type}")
        
        # Verify the missing properties
        missing_props = [prop for prop in required_props if prop not in properties]
        
        if missing_props:
            print(f"\n❌ Missing properties: {', '.join(missing_props)}")
            print("💡 This database is not compatible with the MCP TODO")
            return False
        else:
            print("\n🎉 PERFECT CONFIGURATION !")
            print("✅ All required properties are present")
            print("✅ MCP TODO is ready to work")
            
            # Tester une requête simple
            query_url = f"https://api.notion.com/v1/databases/{db_id}/query"
            query_data = json.dumps({
                "page_size": 1
            }).encode('utf-8')
            
            query_req = urllib.request.Request(query_url, data=query_data, headers=headers, method='POST')
            
            with urllib.request.urlopen(query_req) as response:
                query_result = json.loads(response.read().decode('utf-8'))
            
            total_items = len(query_result.get("results", []))
            print(f"📋 Test query: {total_items} task(s) accessible")
            
            return True
        
    except HTTPError as e:
        if e.code == 404:
            print("❌ Database not found")
            print("💡 Options:")
            print("  1. Check the ID in .env")
            print("  2. Run 'setup_todo_database' to create one")
            print("  3. Check the integration permissions")
        elif e.code == 401:
            print("❌ Authentication failed")
            print("💡 Check your API key")
        else:
            print(f"❌ HTTP Error {e.code}: {e.reason}")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_check_setup()
    print(f"\n{'🎯 READY' if success else '🔧 SETUP REQUIRED'}")
    
    if not success:
        print("\n🚀 NEXT STEPS:")
        print("1. Run 'setup_todo_database' from the MCP")
        print("2. Or create a database manually with the right properties")
        print("3. Then run this test again")