import sys
import os
import asyncio

# Check if we are being called by Claude Desktop (stdin/stdout mode) or standalone (test mode)
is_mcp_mode = not sys.stdin.isatty()

if is_mcp_mode:
    # MCP server mode - use stdio protocol
    try:
        # Try to import the full MCP server
        from .server import main
        print("Using full MCP server", file=sys.stderr)
        
        if __name__ == "__main__":
            asyncio.run(main())
    except ImportError as e:
        # Fallback to minimal MCP server if library not available
        print(f"MCP library not available (Python {sys.version_info.major}.{sys.version_info.minor}), using minimal MCP server...", file=sys.stderr)
        from .mcp_stdio import main
        
        if __name__ == "__main__":
            asyncio.run(main())
else:
    # Test mode - run simple server for testing
    print(f"Running in test mode (Python {sys.version_info.major}.{sys.version_info.minor})...", file=sys.stderr)
    from .simple_server import main
    
    if __name__ == "__main__":
        asyncio.run(main())