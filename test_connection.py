#!/usr/bin/env python3
"""Test script to verify Notion MCP TODO adapter connectivity"""

import asyncio
import sys
import os
sys.path.insert(0, 'src')

from notion_mcp.server import fetch_todos, create_combined_filter, format_todo

async def test_connection():
    """Test basic connection and data retrieval"""
    try:
        print("🔍 Testing connection to Notion TODO database...")
        
        # Test basic fetch
        filter_active = create_combined_filter()
        result = await fetch_todos(filter_active)
        
        todos = result.get("results", [])
        print(f"✅ Connected! Found {len(todos)} active tasks")
        
        if todos:
            print("\n📋 Sample tasks:")
            for i, todo in enumerate(todos[:3]):  # Show first 3
                formatted = format_todo(todo)
                print(f"{i+1}. {formatted['task']}")
                print(f"   Status: {formatted['status']}")
                print(f"   Priority: {formatted['priority']}")
                print(f"   Tags: {', '.join(formatted['tags'])}")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)