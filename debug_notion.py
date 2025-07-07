#!/usr/bin/env python3
"""Debug script to analyze the Notion configuration"""

import json
import urllib.request
import urllib.parse
from urllib.error import HTTPError

def test_notion_config():
    """Test the Notion configuration"""
    
    print("🔧 DIAGNOSTIC NOTION MCP")
    print("=" * 40)
    
    # Read the token from .env
    try:
        with open('.env', 'r') as f:
            env_content = f.read()
        print("✅ .env found")
        
        # Extract the values
        api_key = None
        db_id = None
        
        for line in env_content.split('\n'):
            if line.startswith('NOTION_API_KEY='):
                api_key = line.split('=', 1)[1]
            elif line.startswith('NOTION_DATABASE_ID='):
                db_id = line.split('=', 1)[1]
        
        print(f"🔑 API Key format: {api_key[:10] if api_key else 'None'}...{api_key[-10:] if api_key and len(api_key) > 20 else ''}")
        print(f"🗃️  Database ID: {db_id}")
        
        # Validation format (accept new tokens ntn_ and old secret_)
        if not api_key or not (api_key.startswith('secret_') or api_key.startswith('ntn_')):
            print("❌ The API key must start with 'secret_' or 'ntn_'")
            return False
            
        if not db_id or len(db_id) not in [32, 36]:
            print("❌ The database ID must be 32 or 36 characters")
            return False
            
        print("✅ Credentials seem correct")
        
        # Test simple - retrieve database info
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": "2022-06-28"
        }
        
        url = f"https://api.notion.com/v1/databases/{db_id}"
        req = urllib.request.Request(url, headers=headers, method='GET')
        
        print("\n🔍 Testing connection...")
        
        with urllib.request.urlopen(req) as response:
            db_info = json.loads(response.read().decode('utf-8'))
            
        print("✅ Connection successful !")
        print(f"📊 Database: {db_info.get('title', [{}])[0].get('text', {}).get('content', 'No title')}")
        
        # Analyze the properties
        properties = db_info.get('properties', {})
        print(f"\n🏷️  Properties found ({len(properties)}):")
        
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get('type', 'unknown')
            print(f"  - {prop_name}: {prop_type}")
            
            # For multi_select, show options
            if prop_type == 'multi_select':
                options = prop_info.get('multi_select', {}).get('options', [])
                if options:
                    option_names = [opt['name'] for opt in options]
                    print(f"    Options: {', '.join(option_names)}")
            
            # For select, show options  
            elif prop_type == 'select':
                options = prop_info.get('select', {}).get('options', [])
                if options:
                    option_names = [opt['name'] for opt in options]
                    print(f"    Options: {', '.join(option_names)}")
        
        return True
        
    except FileNotFoundError:
        print("❌ .env file not found")
        return False
    except HTTPError as e:
        print(f"❌ Erreur HTTP {e.code}: {e.reason}")
        if e.code == 401:
            print("🔑 Invalid or expired token")
        elif e.code == 404:
            print("🗃️  Database not found or no access")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    test_notion_config()