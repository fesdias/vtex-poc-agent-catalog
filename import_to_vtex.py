#!/usr/bin/env python3
"""
Import existing legacy_site_extraction.json directly to VTEX.

This script skips the extraction phase and imports the data from
legacy_site_extraction.json directly into VTEX.

Usage:
    python import_to_vtex.py [--skip-reporting] [--no-approval]
    
Options:
    --skip-reporting: Skip the reporting phase and go directly to execution
    --no-approval: Skip the approval prompt (useful for automation)
"""
import sys
import os
import argparse

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from vtex_agent.agents.migration_agent import MigrationAgent
from vtex_agent.utils.state_manager import load_state


def main():
    parser = argparse.ArgumentParser(
        description="Import existing legacy_site_extraction.json to VTEX",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full import with reporting and approval
  python import_to_vtex.py
  
  # Skip reporting, go directly to execution
  python import_to_vtex.py --skip-reporting
  
  # Skip approval prompt (for automation)
  python import_to_vtex.py --no-approval
        """
    )
    parser.add_argument(
        "--skip-reporting",
        action="store_true",
        help="Skip reporting phase and go directly to execution"
    )
    parser.add_argument(
        "--no-approval",
        action="store_true",
        help="Skip approval prompt (useful for automation)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🚀 VTEX DIRECT IMPORT")
    print("="*60)
    print("Loading existing extraction data...")
    
    # Load existing extraction data
    legacy_site_data = load_state("legacy_site_extraction")
    
    if not legacy_site_data:
        print("\n❌ Error: legacy_site_extraction.json not found!")
        print("   Expected location: state/legacy_site_extraction.json")
        print("\n   Please ensure the file exists or run the full workflow first.")
        sys.exit(1)
    
    products = legacy_site_data.get("products", [])
    if not products:
        print("\n❌ Error: No products found in legacy_site_extraction.json!")
        print("   The file exists but contains no product data.")
        sys.exit(1)
    
    print(f"✅ Loaded {len(products)} products from legacy_site_extraction.json")
    print(f"   Target URL: {legacy_site_data.get('target_url', 'N/A')}")
    
    # Initialize migration agent
    agent = MigrationAgent()
    
    # Optionally run reporting phase
    if not args.skip_reporting:
        print("\n" + "="*60)
        print("📄 Running reporting phase...")
        print("="*60)
        agent.reporting_phase(legacy_site_data)
        print("\n✅ Reporting complete. Review final_plan.md if needed.")
    
    # Run execution phase
    print("\n" + "="*60)
    print("🚀 Starting VTEX import...")
    print("="*60)
    
    require_approval = not args.no_approval
    agent.execution_phase(legacy_site_data, require_approval=require_approval)
    
    print("\n" + "="*60)
    print("✅ IMPORT COMPLETE")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Import interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during import: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

