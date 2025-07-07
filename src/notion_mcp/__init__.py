import asyncio
import sys

def main():
    """Main entry point for the package."""
    try:
        from . import server
        asyncio.run(server.main())
    except ImportError as e:
        # Fallback to simple server if MCP is not available
        print(f"MCP library not available (Python {sys.version_info.major}.{sys.version_info.minor}), using simple test server...", file=sys.stderr)
        from . import simple_server
        asyncio.run(simple_server.main())