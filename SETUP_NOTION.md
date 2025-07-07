# 🔧 Setup Notion Integration - Complete Guide

## ❌ Problem Detected
Invalid or expired API token: `secret_JMg7VDrfQ5WMgJDGjYEGx3S7F9Pr81zOJpKj6Eqmy3GzUmt`

## 🛠️ Solution: Create/Renew the Notion Integration

### Step 1: Create a Notion Integration
1. Go to https://www.notion.so/my-integrations
2. Click "Create new integration"
3. Name: `Claude MCP TODO Pezzos`
4. Workspace: Select your workspace
5. Click "Submit"

### Step 2: Copy the Token
1. On the integration page
2. Section "Secrets" → "Internal Integration Token"
3. Click "Show" then "Copy"
4. The token starts with `secret_` and is approximately 50 characters long

### Step 3: Grant Access to the Database
**CORRECT METHOD:** Via the integration settings in Notion
1. Go to **Notion Settings** (gear icon)
2. **Integrations** in the left menu
3. Click on your integration **"Todo MCP"**
4. Tab **"Access"**
5. Section **"Page and database access"**
6. Click **"Edit access"**
7. Search and select your TODO database
8. Click **"Save"**

**Note:** The "Add connections" method from the database does not always work. Always use the integration settings.

### Step 4: Verify the Database ID
From the URL of your database:
`https://www.notion.so/teampezzorockette/689e7bcbb1b94fc3bdae2c1e38a0f845`

The ID is: `689e7bcbb1b94fc3bdae2c1e38a0f845` (not `1ee7ff69-6438-43b3-b016-e97d2b1b4427`)

### Step 5: Update .env
```env
NOTION_API_KEY=secret_YOUR_NEW_TOKEN_HERE
NOTION_DATABASE_ID=689e7bcbb1b94fc3bdae2c1e38a0f845
```

## 🧪 Validation Test

Once updated, run:
```bash
python debug_notion.py
```

You should see:
```
✅ Connection successful!
📊 Database: TODO Pezzos
🏷️ Found properties (X):
  - Task: title
  - Tags: multi_select
    Options: Administrative, Family, IT, Pro...
  - Status: status
  - Priority: select
    Options: Critical, Important, Moderate, Non-essential
```

## 🎯 Test Family Tasks

Then test your family tasks:
```bash
python test_famille_direct.py
```

## ⚠️ Checkpoints

1. **Token Format:** Must start with `secret_` and be approximately 50 characters long
2. **Database ID:** 32 characters without dashes (extracted from the URL)
3. **Permissions:** The integration must have access to the database
4. **Properties:** Exact names "Task", "Tags", "Status", "Priority"

## 🚀 Once Functional

You will be able to use all contextual commands:
-  `show_family_tasks` → Your family tasks
-  `show_pro_tasks` → Your professional tasks
-  `show_urgent_tasks` → Critical/Important tasks
-  And all the others!

---

**📞 Need help?** Make sure you have:
1. Created the Notion integration
2. Copied the correct token  
3. Granted access to your database
4. Used the correct database ID (from the URL)