# 🚀 Auto-Setup TODO Database

## ✨ New Feature: Automatic Database Creation

The MCP TODO can now **automatically create** a perfectly configured TODO database! No more complicated manual setup.

## 🎯 Auto-Setup Commands

### `check_setup`
Checks if your TODO database is correctly configured.

**Usage:**
```bash
# In Claude or via the MCP
check_setup
```

**Possible Results:**
-  ✅ **Database OK**: All required properties are present
-  ❌ **Database missing**: The ID in .env does not exist or is not accessible
-  ⚠️ **Incomplete Database**: Exists but is missing required properties

### `setup_todo_database`
Creates a new TODO database with the complete schema.

**Usage:**
```bash
# Creation with default name
setup_todo_database

# Or with a custom name
setup_todo_database database_name="My Personal TODO"
```

**What is created automatically:**

#### 🏷️ **Tags** (multi_select)
-  Administrative (red)
-  Family (green)
-  IT (blue)  
-  Productivity (purple)
-  Project (orange)
-  Quick to finish (yellow)
-  Pro (gray)
-  Work (brown)

#### 📊 **Status** (status)
-  To describe (gray)
-  To validate (yellow)
-  To do (red)
-  Blocked (orange)
-  In progress (blue)
-  Done (green)
-  Killed (default)

#### ⚡ **Priority** (select)
-  Critical (red)
-  Important (orange)
-  Moderate (yellow)
-  Non-essential (gray)

#### 📅 **Other fields**
-  **Task** (title) - Main title
-  **Due date** (date) - Optional deadline
-  **Assignee** (people) - Responsible person

## 🔄 Complete Installation Workflow

### For New Users

1. **Create the Notion integration** (see SETUP_NOTION.md)
2. **Configure the API key** in .env
3. **Launch the auto-setup**:
   ```bash
   setup_todo_database database_name="TODO MCP"
   ```
4. **Update .env** with the new ID
5. **Check**: `check_setup`

### For Existing Users

If you already have a TODO database but it is missing properties:

1. **Check the status**: `check_setup`
2. **Option A**: Manually add the missing properties
3. **Option B**: Create a new database: `setup_todo_database`

## 🧪 Tests and Validation

### Included Test Script
```bash
# Tests your current configuration
python test_check_setup.py
```

**Example output:**
```
🔍 TEST CHECK SETUP
==============================
🔑 API Key: ntn_119236...
🗃️  Database ID: 689e7bcb-b1b9-4fc3-bdae-2c1e38a0f845

✅ Database found!
📊 Name: Personal: Todo

🔧 Properties (8):
  ✅ Task: title
  ✅ Tags: multi_select  
  ✅ Status: status
  ✅ Priority: select
  ℹ️ Due date: date
  ℹ️ Assignee: people

🎉 PERFECT CONFIGURATION!
```

## 🚨 Troubleshooting

### Database not found (404)
```bash
❌ Database not found
💡 Options:
  1. Check the ID in .env
  2. Run 'setup_todo_database' to create one
  3. Check the integration permissions
```

**Solution:** `setup_todo_database`

### Insufficient permissions
```bash
❌ Authentication failed
💡 Check your API key
```

**Solution:** Check SETUP_NOTION.md for configuration

### Incomplete database
```bash
❌ Missing properties: Status, Priority
💡 This database is not compatible with MCP TODO
```

**Solution:** `setup_todo_database` to create a new one

## 🎯 Benefits of Auto-Setup

### ✅ **Simplicity**
-  A single command to configure everything
-  No more manual configuration errors
-  Standardized and tested schema

### ✅ **Robustness** 
-  Automatic validation of properties
-  Complete error management
-  Detailed feedback at each step

### ✅ **Portability**
-  Anyone can use the MCP
-  No need to know the Notion structure
-  Auto-generated documentation

## 🚀 Complete Usage Example

```bash
# 1. Check the current status
check_setup
# ❌ Database not found

# 2. Create the database
setup_todo_database database_name="TODO MCP Demo"
# 🎉 Successfully created TODO database 'TODO MCP Demo'!
# 📋 Database ID: 12345678-1234-1234-1234-123456789abc

# 3. Update .env
# NOTION_DATABASE_ID=12345678-1234-1234-1234-123456789abc

# 4. Check that everything works
check_setup
# ✅ TODO database 'TODO MCP Demo' is properly configured!

# 5. Test the commands
show_family_tasks
add_todo task="Test MCP" tags=["IT"] priority="Important"
```

---

**🎉 With auto-setup, the MCP TODO truly becomes plug-and-play!**