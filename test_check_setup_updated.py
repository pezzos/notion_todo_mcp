#!/usr/bin/env python3
"""Test the updated check_setup functionality"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from notion_mcp.server import call_tool

async def test_check_setup():
    """Test the check_setup function"""
    print("🧪 TESTING UPDATED CHECK_SETUP")
    print("=" * 40)
    
    try:
        result = await call_tool("check_setup", {})
        
        print("✅ Check setup completed!")
        for item in result:
            if hasattr(item, 'text'):
                print(f"📋 Result:\n{item.text}")
            else:
                print(f"📋 Result: {item}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during check_setup: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_check_setup())
    if success:
        print("\n🎉 Check setup test successful!")
    else:
        print("\n💥 Check setup test failed!")