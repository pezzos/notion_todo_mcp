#!/usr/bin/env python3
"""
Minimal MCP server implementation using only stdio
This implements the basic MCP protocol without the mcp library
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
logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
logger = logging.getLogger('notion_mcp')

# Find and load .env file from project root
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"Loaded .env from {env_path}")

# Configuration
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

if not NOTION_API_KEY:
    logger.error("NOTION_API_KEY not found in environment")
    sys.exit(1)

if not DATABASE_ID:
    logger.error("NOTION_DATABASE_ID not found in environment")
    sys.exit(1)

NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

# Notion API headers
headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION
}

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
        logger.error(f"Error fetching todos: {str(e)}")
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

class MCPServer:
    def __init__(self):
        self.tools = [
            {
                "name": "show_all_todos",
                "description": "Show all active todo items from Notion",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
    
    async def handle_initialize(self, params):
        """Handle MCP initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
            },
            "serverInfo": {
                "name": "notion-todo",
                "version": "0.1.0"
            }
        }
    
    async def handle_tools_list(self, params):
        """Handle tools/list request"""
        return {"tools": self.tools}
    
    async def handle_resources_list(self, params):
        """Handle resources/list request"""
        return {"resources": []}  # No resources for now
    
    async def handle_prompts_list(self, params):
        """Handle prompts/list request"""
        return {"prompts": []}  # No prompts for now
    
    async def handle_tools_call(self, params):
        """Handle tools/call request"""
        name = params.get("name")
        
        if name == "show_all_todos":
            todos_data = await fetch_todos()
            if todos_data:
                todos = [format_todo(todo) for todo in todos_data.get("results", [])]
                result_text = f"Found {len(todos)} active todos:\n\n"
                for i, todo in enumerate(todos[:10], 1):  # Show first 10
                    tags_str = ", ".join(todo["tags"]) if todo["tags"] else "No tags"
                    result_text += f"{i}. {todo['task']} ({todo['status']}, {todo['priority']}) [{tags_str}]\n"
                
                if len(todos) > 10:
                    result_text += f"\n... and {len(todos) - 10} more todos"
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text", 
                            "text": "Failed to fetch todos from Notion."
                        }
                    ]
                }
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def handle_request(self, request):
        """Handle incoming MCP request"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            # Handle notifications (no response required)
            if method.startswith("notifications/"):
                logger.debug(f"Received notification: {method}")
                return None  # No response for notifications
            
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_tools_list(params)
            elif method == "tools/call":
                result = await self.handle_tools_call(params)
            elif method == "resources/list":
                result = await self.handle_resources_list(params)
            elif method == "prompts/list":
                result = await self.handle_prompts_list(params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

async def main():
    """Main MCP server loop"""
    server = MCPServer()
    logger.info("Starting MCP server...")
    
    try:
        while True:
            # Read JSON-RPC message from stdin
            line = sys.stdin.readline()
            if not line:
                break
            
            try:
                request = json.loads(line.strip())
                logger.debug(f"Received request: {request}")
                
                response = await server.handle_request(request)
                
                # Only send response if it's not None (notifications don't get responses)
                if response is not None:
                    logger.debug(f"Sending response: {response}")
                    print(json.dumps(response), flush=True)
                else:
                    logger.debug("No response sent (notification)")
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                print(json.dumps(error_response), flush=True)
                
    except KeyboardInterrupt:
        logger.info("Server interrupted")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())