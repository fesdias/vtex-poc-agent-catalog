#!/usr/bin/env python3
"""Main entry point for VTEX Catalog Migration Agent."""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from vtex_agent.agents.migration_agent import MigrationAgent

if __name__ == "__main__":
    agent = MigrationAgent()
    agent.run_full_workflow()

