#!/usr/bin/env python3
"""
Simple Notion MCP Server that works without the mcp library
This is a temporary solution for Python 3.9 compatibility
"""

import sys
import json
import asyncio
import os
import httpx
from pathlib import Path
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('notion_mcp_simple')

# Find and load .env file from project root
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"Loaded .env from {env_path}")
else:
    logger.warning(f"No .env file found at {env_path}")

# Configuration
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

if not NOTION_API_KEY:
    print("ERROR: NOTION_API_KEY not found in environment", file=sys.stderr)
    sys.exit(1)

if not DATABASE_ID:
    print("ERROR: NOTION_DATABASE_ID not found in environment", file=sys.stderr)
    sys.exit(1)

NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

# Notion API headers
headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION
}

async def test_notion_connection():
    """Test connection to Notion API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{NOTION_BASE_URL}/databases/{DATABASE_ID}",
                headers=headers
            )
            if response.status_code == 200:
                db_info = response.json()
                title = "Unknown"
                if db_info.get('title') and len(db_info['title']) > 0:
                    title = db_info['title'][0].get('text', {}).get('content', 'Unknown')
                print(f"✅ Successfully connected to Notion database: '{title}'")
                print(f"Database ID: {DATABASE_ID}")
                return True
            else:
                print(f"❌ Failed to access database: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False

async def fetch_todos():
    """Fetch all active todos from Notion"""
    try:
        query = {
            "filter": {
                "and": [
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
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NOTION_BASE_URL}/databases/{DATABASE_ID}/query",
                headers=headers,
                json=query
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"❌ Error fetching todos: {str(e)}")
        return None

def format_todo(todo):
    """Format a todo for display"""
    props = todo["properties"]
    
    # Get task name
    task = ""
    for title_prop in ["Tâche", "Task", "Name", "Title"]:
        if props.get(title_prop, {}).get("title"):
            task = props[title_prop]["title"][0]["text"]["content"]
            break
    
    # Get tags
    tags = []
    for tags_prop in ["Tags", "Labels", "Categories"]:
        if props.get(tags_prop, {}).get("multi_select"):
            tags = [tag["name"] for tag in props[tags_prop]["multi_select"]]
            break
    
    # Get status
    status = "Unknown"
    for status_prop in ["Status", "État", "State"]:
        if props.get(status_prop, {}).get("status"):
            status = props[status_prop]["status"]["name"]
            break
    
    # Get priority
    priority = "Unknown"
    for priority_prop in ["Priorité", "Priority", "Importance"]:
        if props.get(priority_prop, {}).get("select"):
            priority = props[priority_prop]["select"]["name"]
            break
    
    return {
        "id": todo["id"],
        "task": task,
        "tags": tags,
        "status": status,
        "priority": priority,
        "created": todo.get("created_time", "")
    }

async def main():
    """Test the Notion connection and fetch some todos"""
    print("🔍 Testing Notion TODO MCP Server...")
    print(f"Python version: {sys.version}")
    print(f"Project root: {project_root}")
    print("")
    
    # Test connection
    if not await test_notion_connection():
        return
    
    print("")
    print("📋 Fetching active todos...")
    
    # Fetch todos
    todos_data = await fetch_todos()
    if todos_data:
        todos = [format_todo(todo) for todo in todos_data.get("results", [])]
        print(f"Found {len(todos)} active todos:")
        for i, todo in enumerate(todos[:5], 1):  # Show first 5
            tags_str = ", ".join(todo["tags"]) if todo["tags"] else "No tags"
            print(f"{i}. {todo['task']} ({todo['status']}, {todo['priority']}) [{tags_str}]")
        
        if len(todos) > 5:
            print(f"... and {len(todos) - 5} more")
    
    print("")
    print("✅ Basic functionality test completed!")

if __name__ == "__main__":
    asyncio.run(main())