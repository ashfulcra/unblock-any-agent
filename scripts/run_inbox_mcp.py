"""Explicit optional human inbox; no automatic owner fallback in worker MCP."""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unblock.human_mcp import main

if __name__=='__main__':main()
