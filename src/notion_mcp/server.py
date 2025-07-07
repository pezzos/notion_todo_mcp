from mcp.server import Server
from mcp.types import (
    Resource, 
    Tool,
    TextContent,
    EmbeddedResource
)
from pydantic import AnyUrl
import os
import json
from datetime import datetime
import httpx
from typing import Any, Sequence
from dotenv import load_dotenv
from pathlib import Path
import logging
import asyncio

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('notion_mcp')

# Find and load .env file from project root
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
if not env_path.exists():
    raise FileNotFoundError(f"No .env file found at {env_path}")
load_dotenv(env_path)

# Initialize server
server = Server("notion-todo")

# Configuration with validation
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

if not NOTION_API_KEY:
    raise ValueError("NOTION_API_KEY not found in .env file")
if not DATABASE_ID:
    raise ValueError("NOTION_DATABASE_ID not found in .env file")

NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

# Notion API headers
headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION
}

# Global variable to track if database exists
_database_exists = None

async def fetch_todos(filters: dict = None) -> dict:
    """Fetch todos from Notion database with optional filters"""
    query = {
        "sorts": [
            {
                "timestamp": "created_time",
                "direction": "descending"
            }
        ]
    }
    
    if filters:
        query["filter"] = filters
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTION_BASE_URL}/databases/{DATABASE_ID}/query",
            headers=headers,
            json=query
        )
        response.raise_for_status()
        return response.json()

async def create_todo(task: str, tags: list = None, priority: str = "Moderate", status: str = "To do") -> dict:
    """Create a new todo in Notion with enhanced properties"""
    properties = {
        "Task": {
            "type": "title",
            "title": [{"type": "text", "text": {"content": task}}]
        },
        "Status": {
            "type": "status",
            "status": {"name": status}
        },
        "Priority": {
            "type": "select",
            "select": {"name": priority}
        }
    }
    
    if tags:
        properties["Tags"] = {
            "type": "multi_select",
            "multi_select": [{"name": tag} for tag in tags]
        }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTION_BASE_URL}/pages",
            headers=headers,
            json={
                "parent": {"database_id": DATABASE_ID},
                "properties": properties
            }
        )
        response.raise_for_status()
        return response.json()

async def update_todo_status(page_id: str, status: str) -> dict:
    """Update todo status in Notion"""
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{NOTION_BASE_URL}/pages/{page_id}",
            headers=headers,
            json={
                "properties": {
                    "Status": {
                        "type": "status",
                        "status": {"name": status}
                    }
                }
            }
        )
        response.raise_for_status()
        return response.json()

def create_tag_filter(tag: str) -> dict:
    """Create filter for specific tag - supports both English and French tag names"""
    # Map English to French tag names for backward compatibility
    tag_mapping = {
        "Administrative": "Administratif",
        "Family": "Famille", 
        "IT": "Informatique",
        "Productivity": "Productivité",
        "Project": "Projet",
        "Quick to finish": "Rapide à terminer",
        "Work": "Travaux"
    }
    
    # Check both English and French versions
    tags_to_check = [tag]
    if tag in tag_mapping:
        tags_to_check.append(tag_mapping[tag])
    elif tag in tag_mapping.values():
        # Find the English equivalent
        for eng, fr in tag_mapping.items():
            if fr == tag:
                tags_to_check.append(eng)
                break
    
    return {
        "and": [
            {
                "or": [
                    {
                        "property": "Tags",
                        "multi_select": {
                            "contains": tag_variant
                        }
                    } for tag_variant in tags_to_check
                ]
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
    }

def create_priority_filter(priorities: list) -> dict:
    """Create filter for specific priorities - supports both English and French property names"""
    return {
        "and": [
            {
                "or": [
                    {
                        "property": "Priority",  # Try English first
                        "select": {
                            "equals": priority
                        }
                    } for priority in priorities
                ] + [
                    {
                        "property": "Priorité",  # Fallback to French
                        "select": {
                            "equals": priority
                        }
                    } for priority in priorities
                ]
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
    }

def create_combined_filter(tags: list = None, priorities: list = None, statuses: list = None) -> dict:
    """Create combined filter for multiple criteria - supports both English and French property names"""
    filters = []
    
    if tags:
        # Map English to French tag names for backward compatibility
        tag_mapping = {
            "Administrative": "Administratif",
            "Family": "Famille", 
            "IT": "Informatique",
            "Productivity": "Productivité",
            "Project": "Projet",
            "Quick to finish": "Rapide à terminer",
            "Work": "Travaux"
        }
        
        all_tags_to_check = []
        for tag in tags:
            all_tags_to_check.append(tag)
            if tag in tag_mapping:
                all_tags_to_check.append(tag_mapping[tag])
            elif tag in tag_mapping.values():
                for eng, fr in tag_mapping.items():
                    if fr == tag:
                        all_tags_to_check.append(eng)
                        break
        
        filters.append({
            "or": [
                {
                    "property": "Tags",
                    "multi_select": {
                        "contains": tag
                    }
                } for tag in all_tags_to_check
            ]
        })
    
    if priorities:
        filters.append({
            "or": [
                {
                    "property": "Priority",  # Try English first
                    "select": {
                        "equals": priority
                    }
                } for priority in priorities
            ] + [
                {
                    "property": "Priorité",  # Fallback to French
                    "select": {
                        "equals": priority
                    }
                } for priority in priorities
            ]
        })
    
    if statuses:
        filters.append({
            "or": [
                {
                    "property": "Status",
                    "status": {
                        "equals": status
                    }
                } for status in statuses
            ]
        })
    else:
        # Default: exclude Done and Killed
        filters.extend([
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
        ])
    
    return {"and": filters}

async def check_database_exists() -> bool:
    """Check if the configured database exists and is accessible"""
    global _database_exists
    
    if _database_exists is not None:
        return _database_exists
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{NOTION_BASE_URL}/databases/{DATABASE_ID}",
                headers=headers
            )
            if response.status_code == 200:
                _database_exists = True
                return True
            else:
                _database_exists = False
                return False
    except:
        _database_exists = False
        return False

async def create_todo_database(database_name: str = "TODO Database") -> dict:
    """Create a new TODO database with the proper schema"""
    
    database_schema = {
        "parent": {
            "type": "page_id",
            "page_id": await get_default_page_id()
        },
        "title": [
            {
                "type": "text",
                "text": {
                    "content": database_name
                }
            }
        ],
        "properties": {
            "Task": {
                "title": {}
            },
            "Tags": {
                "multi_select": {
                    "options": [
                        {"name": "Administrative", "color": "red"},
                        {"name": "Family", "color": "green"},
                        {"name": "IT", "color": "blue"},
                        {"name": "Productivity", "color": "purple"},
                        {"name": "Project", "color": "orange"},
                        {"name": "Quick to finish", "color": "yellow"},
                        {"name": "Pro", "color": "gray"},
                        {"name": "Work", "color": "brown"}
                    ]
                }
            },
            "Status": {
                "status": {
                    "options": [
                        {"name": "To describe", "color": "gray"},
                        {"name": "To validate", "color": "yellow"},
                        {"name": "To do", "color": "red"},
                        {"name": "Blocked", "color": "orange"},
                        {"name": "In progress", "color": "blue"},
                        {"name": "Done", "color": "green"},
                        {"name": "Killed", "color": "default"}
                    ],
                    "groups": [
                        {
                            "name": "To do",
                            "color": "red",
                            "option_ids": []
                        },
                        {
                            "name": "In progress", 
                            "color": "blue",
                            "option_ids": []
                        },
                        {
                            "name": "Done",
                            "color": "green", 
                            "option_ids": []
                        }
                    ]
                }
            },
            "Priority": {
                "select": {
                    "options": [
                        {"name": "Critical", "color": "red"},
                        {"name": "Important", "color": "orange"},
                        {"name": "Moderate", "color": "yellow"},
                        {"name": "Non-essential", "color": "gray"}
                    ]
                }
            },
            "Due date": {
                "date": {}
            },
            "Assignee": {
                "people": {}
            },
            "Project": {
                "relation": {
                    "database_id": "",
                    "type": "dual_property",
                    "dual_property": {}
                }
            }
        }
    }
    
    # Remove empty relation for now
    del database_schema["properties"]["Projet"]
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTION_BASE_URL}/databases",
            headers=headers,
            json=database_schema
        )
        response.raise_for_status()
        return response.json()

async def get_default_page_id() -> str:
    """Get a default page ID to use as parent for the database"""
    async with httpx.AsyncClient() as client:
        # Search for any page in the workspace
        response = await client.post(
            f"{NOTION_BASE_URL}/search",
            headers=headers,
            json={
                "filter": {
                    "value": "page",
                    "property": "object"
                },
                "page_size": 10
            }
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        
        # Find a page that can serve as parent (not a database)
        for result in results:
            if result.get("object") == "page" and result.get("parent", {}).get("type") != "database_id":
                return result["id"]
        
        # If no suitable page found, try to get any available page
        if results:
            return results[0]["id"]
        
        # Last resort: fail gracefully
        raise Exception("No accessible pages found. Please create a page in your Notion workspace first, or provide a specific page ID.")

def format_todo(todo: dict) -> dict:
    """Format a todo for display - supports both English and French property names"""
    props = todo["properties"]
    
    # Get task name - try both French and English
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
    
    # Get dates
    created = todo.get("created_time", "")
    due_date = None
    for date_prop in ["Date butoire", "Due date", "Due Date", "Deadline"]:
        if props.get(date_prop, {}).get("date"):
            due_date = props[date_prop]["date"]["start"]
            break
    
    return {
        "id": todo["id"],
        "task": task,
        "tags": tags,
        "status": status,
        "priority": priority,
        "created": created,
        "due_date": due_date
    }

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available todo tools"""
    return [
        Tool(
            name="add_todo",
            description="Add a new todo item with tags and priority",
            inputSchema={
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The todo task description"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for the task (Administrative, Family, IT, Productivity, Project, Quick to finish, Pro, Work)"
                    },
                    "priority": {
                        "type": "string",
                        "description": "Priority level",
                        "enum": ["Critical", "Important", "Moderate", "Non-essential"]
                    }
                },
                "required": ["task"]
            }
        ),
        Tool(
            name="show_all_todos",
            description="Show all active todo items from Notion",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="show_pro_tasks",
            description="Show professional tasks (Pro tag)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="show_family_tasks",
            description="Show family tasks (Family tag)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="show_admin_tasks",
            description="Show administrative tasks (Administrative tag)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="show_quick_tasks",
            description="Show quick tasks (Quick to finish tag)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="show_urgent_tasks",
            description="Show urgent tasks (Critical and Important priorities)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="show_blocked_tasks",
            description="Show blocked tasks",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="show_tasks_by_tag",
            description="Show tasks filtered by specific tag",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "Tag to filter by",
                        "enum": ["Administrative", "Family", "IT", "Productivity", "Project", "Quick to finish", "Pro", "Work"]
                    }
                },
                "required": ["tag"]
            }
        ),
        Tool(
            name="show_tasks_by_priority",
            description="Show tasks filtered by priority level",
            inputSchema={
                "type": "object",
                "properties": {
                    "priority": {
                        "type": "string",
                        "description": "Priority to filter by",
                        "enum": ["Critical", "Important", "Moderate", "Non-essential"]
                    }
                },
                "required": ["priority"]
            }
        ),
        Tool(
            name="update_task_status",
            description="Update task status",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The ID of the todo task to update"
                    },
                    "status": {
                        "type": "string",
                        "description": "New status",
                        "enum": ["To describe", "To validate", "To do", "Blocked", "In progress", "Killed", "Done"]
                    }
                },
                "required": ["task_id", "status"]
            }
        ),
        Tool(
            name="setup_todo_database",
            description="Create a new TODO database with proper schema if none exists",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_name": {
                        "type": "string",
                        "description": "Name for the new TODO database",
                        "default": "TODO Database"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="check_setup",
            description="Check if the TODO database is properly configured and accessible",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | EmbeddedResource]:
    """Handle tool calls for todo management"""
    
    try:
        if name == "add_todo":
            if not isinstance(arguments, dict):
                raise ValueError("Invalid arguments")
                
            task = arguments.get("task")
            tags = arguments.get("tags", [])
            priority = arguments.get("priority", "Moderate")
            
            if not task:
                raise ValueError("Task is required")
                
            result = await create_todo(task, tags, priority)
            tags_text = f" with tags: {', '.join(tags)}" if tags else ""
            return [
                TextContent(
                    type="text",
                    text=f"Added todo: {task} (priority: {priority}){tags_text}"
                )
            ]
            
        elif name == "show_all_todos":
            todos = await fetch_todos(create_combined_filter())
            formatted_todos = [format_todo(todo) for todo in todos.get("results", [])]
            return [
                TextContent(
                    type="text",
                    text=json.dumps(formatted_todos, indent=2, ensure_ascii=False)
                )
            ]
            
        elif name == "show_pro_tasks":
            todos = await fetch_todos(create_tag_filter("Pro"))
            formatted_todos = [format_todo(todo) for todo in todos.get("results", [])]
            return [
                TextContent(
                    type="text",
                    text=json.dumps(formatted_todos, indent=2, ensure_ascii=False)
                )
            ]
            
        elif name == "show_family_tasks":
            todos = await fetch_todos(create_tag_filter("Family"))
            formatted_todos = [format_todo(todo) for todo in todos.get("results", [])]
            return [
                TextContent(
                    type="text",
                    text=json.dumps(formatted_todos, indent=2, ensure_ascii=False)
                )
            ]
            
        elif name == "show_admin_tasks":
            todos = await fetch_todos(create_tag_filter("Administrative"))
            formatted_todos = [format_todo(todo) for todo in todos.get("results", [])]
            return [
                TextContent(
                    type="text",
                    text=json.dumps(formatted_todos, indent=2, ensure_ascii=False)
                )
            ]
            
        elif name == "show_quick_tasks":
            todos = await fetch_todos(create_tag_filter("Quick to finish"))
            formatted_todos = [format_todo(todo) for todo in todos.get("results", [])]
            return [
                TextContent(
                    type="text",
                    text=json.dumps(formatted_todos, indent=2, ensure_ascii=False)
                )
            ]
            
        elif name == "show_urgent_tasks":
            todos = await fetch_todos(create_priority_filter(["Critical", "Important"]))
            formatted_todos = [format_todo(todo) for todo in todos.get("results", [])]
            return [
                TextContent(
                    type="text",
                    text=json.dumps(formatted_todos, indent=2, ensure_ascii=False)
                )
            ]
            
        elif name == "show_blocked_tasks":
            todos = await fetch_todos(create_combined_filter(statuses=["Blocked"]))
            formatted_todos = [format_todo(todo) for todo in todos.get("results", [])]
            return [
                TextContent(
                    type="text",
                    text=json.dumps(formatted_todos, indent=2, ensure_ascii=False)
                )
            ]
            
        elif name == "show_tasks_by_tag":
            if not isinstance(arguments, dict):
                raise ValueError("Invalid arguments")
            tag = arguments.get("tag")
            if not tag:
                raise ValueError("Tag is required")
                
            todos = await fetch_todos(create_tag_filter(tag))
            formatted_todos = [format_todo(todo) for todo in todos.get("results", [])]
            return [
                TextContent(
                    type="text",
                    text=json.dumps(formatted_todos, indent=2, ensure_ascii=False)
                )
            ]
            
        elif name == "show_tasks_by_priority":
            if not isinstance(arguments, dict):
                raise ValueError("Invalid arguments")
            priority = arguments.get("priority")
            if not priority:
                raise ValueError("Priority is required")
                
            todos = await fetch_todos(create_priority_filter([priority]))
            formatted_todos = [format_todo(todo) for todo in todos.get("results", [])]
            return [
                TextContent(
                    type="text",
                    text=json.dumps(formatted_todos, indent=2, ensure_ascii=False)
                )
            ]
            
        elif name == "update_task_status":
            if not isinstance(arguments, dict):
                raise ValueError("Invalid arguments")
                
            task_id = arguments.get("task_id")
            status = arguments.get("status")
            
            if not task_id:
                raise ValueError("Task ID is required")
            if not status:
                raise ValueError("Status is required")
                
            result = await update_todo_status(task_id, status)
            return [
                TextContent(
                    type="text",
                    text=f"Updated task status to: {status} (ID: {task_id})"
                )
            ]
            
        elif name == "check_setup":
            # Check if database exists and is properly configured
            exists = await check_database_exists()
            
            if exists:
                # Also verify the schema
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            f"{NOTION_BASE_URL}/databases/{DATABASE_ID}",
                            headers=headers
                        )
                        response.raise_for_status()
                        db_info = response.json()
                        
                    properties = db_info.get('properties', {})
                    
                    # Check for required properties (flexible naming)
                    required_checks = {
                        'title': ['Tâche', 'Task', 'Name', 'Title'],
                        'tags': ['Tags', 'Labels', 'Categories'], 
                        'status': ['Status', 'État', 'State'],
                        'priority': ['Priorité', 'Priority', 'Importance']
                    }
                    
                    missing_types = []
                    for prop_type, possible_names in required_checks.items():
                        found = False
                        for name in possible_names:
                            if name in properties:
                                expected_type = 'title' if prop_type == 'title' else ('multi_select' if prop_type == 'tags' else ('status' if prop_type == 'status' else 'select'))
                                if properties[name].get('type') == expected_type:
                                    found = True
                                    break
                        if not found:
                            missing_types.append(prop_type)
                    
                    missing_props = missing_types
                    
                    if missing_props:
                        return [
                            TextContent(
                                type="text",
                                text=f"❌ Database exists but missing required properties: {', '.join(missing_props)}\n\nRun 'setup_todo_database' to create a properly configured database."
                            )
                        ]
                    else:
                        title = "Unknown"
                        if db_info.get('title') and len(db_info['title']) > 0:
                            title = db_info['title'][0].get('text', {}).get('content', 'Unknown')
                        
                        return [
                            TextContent(
                                type="text",
                                text=f"✅ TODO database '{title}' is properly configured!\n\nDatabase ID: {DATABASE_ID}\nRequired properties: ✅ All present\n\nYou can now use all TODO commands like 'show_family_tasks', 'add_todo', etc."
                            )
                        ]
                        
                except Exception as e:
                    return [
                        TextContent(
                            type="text",
                            text=f"❌ Error checking database configuration: {str(e)}\n\nPlease verify your NOTION_DATABASE_ID and integration permissions."
                        )
                    ]
            else:
                return [
                    TextContent(
                        type="text",
                        text=f"❌ TODO database not found or not accessible.\n\nDatabase ID: {DATABASE_ID}\n\nOptions:\n1. Run 'setup_todo_database' to create a new database\n2. Check your NOTION_DATABASE_ID in .env\n3. Verify integration permissions in Notion settings"
                    )
                ]
                
        elif name == "setup_todo_database":
            # Create a new TODO database
            if not isinstance(arguments, dict):
                arguments = {}
                
            database_name = arguments.get("database_name", "TODO Database")
            
            try:
                # Check if database already exists
                exists = await check_database_exists()
                if exists:
                    return [
                        TextContent(
                            type="text",
                            text=f"✅ Database already exists!\n\nDatabase ID: {DATABASE_ID}\n\nRun 'check_setup' to verify the configuration."
                        )
                    ]
                
                # Create the database
                result = await create_todo_database(database_name)
                new_db_id = result["id"]
                
                return [
                    TextContent(
                        type="text",
                        text=f"🎉 Successfully created TODO database '{database_name}'!\n\n📋 Database ID: {new_db_id}\n\n🔧 Next steps:\n1. Update your .env file:\n   NOTION_DATABASE_ID={new_db_id}\n\n2. Restart the MCP server\n\n3. Run 'check_setup' to verify everything works\n\n✨ Your database includes:\n• Tags: Administratif, Famille, Informatique, Productivité, Projet, Rapide à terminer, Pro, Travaux\n• Status: To describe, To validate, To do, Blocked, In progress, Done, Killed\n• Priority: Critical, Important, Moderate, Non-essential\n• Due date and Assignee fields"
                    )
                ]
                
            except Exception as e:
                logger.error(f"Error creating database: {str(e)}")
                return [
                    TextContent(
                        type="text",
                        text=f"❌ Error creating database: {str(e)}\n\nPlease check:\n1. Your Notion integration has permission to create databases\n2. You have write access to your workspace\n3. Your API token is valid"
                    )
                ]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except httpx.HTTPError as e:
        logger.error(f"Notion API error: {str(e)}")
        return [
            TextContent(
                type="text",
                text=f"Error with Notion API: {str(e)}\nPlease make sure your Notion integration is properly set up and has access to the database."
            )
        ]
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        return [
            TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )
        ]

async def main():
    """Main entry point for the server"""
    from mcp.server.stdio import stdio_server
    
    if not NOTION_API_KEY or not DATABASE_ID:
        raise ValueError("NOTION_API_KEY and NOTION_DATABASE_ID environment variables are required")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())