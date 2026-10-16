"""Portable local MCP entrypoint. Credential configuration is external to source."""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unblock.mcp_bridge import main

if __name__=='__main__':main()
