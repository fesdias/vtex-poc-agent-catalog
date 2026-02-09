#!/usr/bin/env python3
"""Main entry point for VTEX Catalog Migration Agent."""
import sys
import os
import json
import argparse

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from vtex_agent.agents.migration_agent import MigrationAgent
from vtex_agent.agents.legacy_site_agent import LegacySiteAgent
from vtex_agent.agents.vtex_image_agent import VTEXImageAgent
from vtex_agent.utils.state_manager import load_state


def run_full_workflow():
    """Run the complete migration workflow."""
    agent = MigrationAgent()
    agent.run_full_workflow()


def run_import_to_vtex_only(skip_reporting=False, no_approval=False):
    """
    Import existing legacy_site_extraction.json directly to VTEX.
    
    This skips the extraction phase and imports the data from
    legacy_site_extraction.json directly into VTEX.
    """
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
    if not skip_reporting:
        print("\n" + "="*60)
        print("📄 Running reporting phase...")
        print("="*60)
        agent.reporting_phase(legacy_site_data)
        print("\n✅ Reporting complete. Review state/final_plan.md if needed.")
    
    # Run execution phase
    print("\n" + "="*60)
    print("🚀 Starting VTEX import...")
    print("="*60)
    
    require_approval = not no_approval
    agent.execution_phase(legacy_site_data, require_approval=require_approval)
    
    print("\n" + "="*60)
    print("✅ IMPORT COMPLETE")
    print("="*60)


def run_legacy_site_agent_only(
    target_url: str = None,
    sample_size: int = 1,
    max_pages: int = 50,
    enable_iterative_refinement: bool = True
):
    """
    Run only the Legacy Site Agent phases (discovery, mapping, extraction).
    
    This runs:
    1. Discovery - Get target website URL
    2. Mapping - Find product URLs (sitemap or crawl)
    3. Extraction - Extract product data from URLs
    
    Args:
        target_url: Optional target URL (if None, will prompt or load from state)
        sample_size: Number of products to extract (default: 1)
        max_pages: Maximum pages to crawl if sitemap not found (default: 50)
        enable_iterative_refinement: Whether to enable iterative refinement loop (default: True)
    """
    print("\n" + "="*60)
    print("🌐 LEGACY SITE AGENT - EXTRACTION PHASE")
    print("="*60)
    
    # Create agent
    agent = LegacySiteAgent()
    
    # Phase 1: Discovery
    print("\n" + "="*60)
    print("📡 PHASE 1: DISCOVERY")
    print("="*60)
    agent.discover_target_url(target_url=target_url)
    print(f"✅ Target URL: {agent.target_url}")
    
    # Phase 2: Mapping
    print("\n" + "="*60)
    print("🗺️  PHASE 2: MAPPING")
    print("="*60)
    product_urls = agent.map_product_urls(max_pages=max_pages)
    print(f"✅ Found {len(product_urls)} product URLs")
    
    # Phase 3: Extraction
    print("\n" + "="*60)
    print("📥 PHASE 3: EXTRACTION")
    print("="*60)
    print("This phase will:")
    print("  1. Extract 1 sample product for validation")
    print("  2. Allow you to refine the extraction if needed")
    print("  3. Ask how many products to extract")
    print("  4. Extract the selected products")
    extracted_data = agent.extract_products(
        sample_size=1,  # Always 1 for validation, user will choose final count
        enable_iterative_refinement=enable_iterative_refinement
    )
    
    # Summary
    print("\n" + "="*60)
    print("✅ LEGACY SITE AGENT COMPLETE")
    print("="*60)
    print(f"Target URL: {agent.target_url}")
    print(f"Product URLs found: {len(product_urls)}")
    print(f"Products extracted: {len(extracted_data.get('products', []))}")
    print(f"\n💾 Results saved to: state/legacy_site_extraction.json")
    print("="*60)


def run_image_agent_only(legacy_site_json_path=None, vtex_products_skus_json_path=None, github_repo_path="images"):
    """
    Run the VTEX Image Enrichment Agent.
    
    This agent:
    1. Downloads images from legacy site
    2. Renames them: [SkuId]_[SequenceNumber]
    3. Uploads to GitHub public repository
    4. Associates images with SKUs in VTEX
    """
    # Use default paths from state/ if not provided
    if not legacy_site_json_path:
        legacy_site_json_path = "state/legacy_site_extraction.json"
    if not vtex_products_skus_json_path:
        vtex_products_skus_json_path = "state/vtex_products_skus.json"
    
    # Load JSON files
    print(f"📂 Loading legacy site data from: {legacy_site_json_path}")
    try:
        with open(legacy_site_json_path, 'r', encoding='utf-8') as f:
            legacy_site_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File not found: {legacy_site_json_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in file: {e}")
        sys.exit(1)
    
    print(f"📂 Loading VTEX products/SKUs from: {vtex_products_skus_json_path}")
    try:
        with open(vtex_products_skus_json_path, 'r', encoding='utf-8') as f:
            vtex_products_skus = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File not found: {vtex_products_skus_json_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in file: {e}")
        sys.exit(1)
    
    # Validate structure
    products = legacy_site_data.get("products", [])
    if not products:
        print("⚠️  Warning: No products found in legacy site JSON file")
        print("   Expected format: {'products': [...]}")
    
    vtex_products = vtex_products_skus.get("products", {})
    if not vtex_products:
        print("⚠️  Warning: No VTEX products found in JSON file")
        print("   Expected format: {'products': {...}}")
        print("   Make sure to run the Product/SKU Agent first!")
    
    print(f"✅ Loaded {len(products)} products from legacy site")
    print(f"✅ Loaded {len(vtex_products)} VTEX products")
    
    # Check for GitHub credentials
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO")
    
    if not github_token or not github_repo:
        print("\n⚠️  Warning: GitHub credentials not found in environment")
        print("   Please set GITHUB_TOKEN and GITHUB_REPO in your .env file")
        print("   The agent will fail if credentials are missing.")
        response = input("\n   Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    else:
        print(f"✅ GitHub credentials found (Repo: {github_repo})")
    
    # Create agent and run
    print(f"\n🚀 Starting image enrichment (GitHub path: {github_repo_path})...")
    agent = VTEXImageAgent()
    result = agent.enrich_skus_with_images(
        legacy_site_data,
        vtex_products_skus,
        github_repo_path=github_repo_path
    )
    
    # Print summary
    summary = result.get("summary", {})
    print("\n" + "="*60)
    print("📊 Image Enrichment Summary")
    print("="*60)
    print(f"Total SKUs processed: {summary.get('total_skus', 0)}")
    print(f"Total images processed: {summary.get('total_images', 0)}")
    print(f"✅ Images associated: {summary.get('total_images_associated', 0)}")
    print(f"❌ Images failed: {summary.get('total_images_failed', 0)}")
    print("="*60)
    
    # Show SKU details
    sku_associations = result.get("sku_image_associations", {})
    if sku_associations:
        print("\n🖼️  SKU Image Associations:")
        for sku_id, assoc_data in sku_associations.items():
            sku_name = assoc_data.get("sku_name", "Unknown")
            total_associated = assoc_data.get("total_associated", 0)
            total_failed = assoc_data.get("total_failed", 0)
            status_icon = "✅" if total_associated > 0 else "❌"
            print(f"  {status_icon} SKU {sku_id} ({sku_name}): {total_associated} associated, {total_failed} failed")
            
            # Show image URLs for first few
            images = assoc_data.get("images", [])
            for img in images[:3]:  # Show first 3
                if img.get("status") == "associated":
                    print(f"      • {img.get('name')}: {img.get('url', 'N/A')[:60]}...")
    
    print(f"\n💾 Results saved to: state/vtex_images.json")
    print("\n✅ Done!")


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="VTEX Catalog Migration Agent - Unified entry point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full workflow
  python main.py

  # Run only legacy site agent (discovery, mapping, extraction)
  python main.py --run-legacy-site-agent-only
  python main.py --run-legacy-site-agent-only --target-url https://example.com
  python main.py --run-legacy-site-agent-only --sample-size 5 --max-pages 100
  python main.py --run-legacy-site-agent-only --no-iterative-refinement

  # Import existing extraction data to VTEX
  python main.py --import-to-vtex-only
  python main.py --import-to-vtex-only --skip-reporting --no-approval

  # Run image enrichment agent only
  python main.py --run-image-agent-only
  python main.py --run-image-agent-only --github-repo-path images/products
  python main.py --run-image-agent-only --legacy-site-path custom/path.json --vtex-products-path custom/vtex.json
        """
    )
    
    # Mode selection flags (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--run-legacy-site-agent-only",
        action="store_true",
        help="Run only legacy site agent (discovery, mapping, extraction phases)"
    )
    mode_group.add_argument(
        "--import-to-vtex-only",
        action="store_true",
        help="Import existing legacy_site_extraction.json directly to VTEX (skips extraction phase)"
    )
    mode_group.add_argument(
        "--run-image-agent-only",
        action="store_true",
        help="Run image enrichment agent only (downloads, uploads to GitHub, associates with SKUs)"
    )
    
    # Options for --run-legacy-site-agent-only
    parser.add_argument(
        "--target-url",
        type=str,
        default=None,
        help="Target website URL (if not provided, will prompt or load from state)"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=1,
        help="Number of products to extract (default: 1)"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=50,
        help="Maximum pages to crawl if sitemap not found (default: 50)"
    )
    parser.add_argument(
        "--no-iterative-refinement",
        action="store_true",
        help="Disable iterative refinement loop (only with --run-legacy-site-agent-only)"
    )
    
    # Options for --import-to-vtex-only
    parser.add_argument(
        "--skip-reporting",
        action="store_true",
        help="Skip reporting phase and go directly to execution (only with --import-to-vtex-only)"
    )
    parser.add_argument(
        "--no-approval",
        action="store_true",
        help="Skip approval prompt (useful for automation, only with --import-to-vtex-only)"
    )
    
    # Options for --run-image-agent-only
    parser.add_argument(
        "--legacy-site-path",
        type=str,
        default=None,
        help="Path to legacy site extraction JSON file (default: state/legacy_site_extraction.json)"
    )
    parser.add_argument(
        "--vtex-products-path",
        type=str,
        default=None,
        help="Path to VTEX products/SKUs JSON file (default: state/vtex_products_skus.json)"
    )
    parser.add_argument(
        "--github-repo-path",
        type=str,
        default="images",
        help="Path within GitHub repository for images (default: images)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.run_legacy_site_agent_only:
            # Validate that legacy site agent options are only used with --run-legacy-site-agent-only
            if args.skip_reporting or args.no_approval:
                parser.error("--skip-reporting and --no-approval are only valid with --import-to-vtex-only")
            if args.legacy_site_path or args.vtex_products_path or args.github_repo_path != "images":
                parser.error("--legacy-site-path, --vtex-products-path, and --github-repo-path are only valid with --run-image-agent-only")
            run_legacy_site_agent_only(
                target_url=args.target_url,
                sample_size=args.sample_size,
                max_pages=args.max_pages,
                enable_iterative_refinement=not args.no_iterative_refinement
            )
        elif args.import_to_vtex_only:
            # Validate that skip-reporting and no-approval are only used with import-to-vtex-only
            if args.target_url or args.sample_size != 1 or args.max_pages != 50 or args.no_iterative_refinement:
                parser.error("--target-url, --sample-size, --max-pages, and --no-iterative-refinement are only valid with --run-legacy-site-agent-only")
            if args.legacy_site_path or args.vtex_products_path or args.github_repo_path != "images":
                parser.error("--legacy-site-path, --vtex-products-path, and --github-repo-path are only valid with --run-image-agent-only")
            run_import_to_vtex_only(
                skip_reporting=args.skip_reporting,
                no_approval=args.no_approval
            )
        elif args.run_image_agent_only:
            # Validate that skip-reporting and no-approval are only used with import-to-vtex-only
            if args.skip_reporting or args.no_approval:
                parser.error("--skip-reporting and --no-approval are only valid with --import-to-vtex-only")
            run_image_agent_only(
                legacy_site_json_path=args.legacy_site_path,
                vtex_products_skus_json_path=args.vtex_products_path,
                github_repo_path=args.github_repo_path
            )
        else:
            # Default: run full workflow
            if (args.target_url or args.sample_size != 1 or args.max_pages != 50 or 
                args.no_iterative_refinement or args.skip_reporting or args.no_approval or 
                args.legacy_site_path or args.vtex_products_path or args.github_repo_path != "images"):
                parser.error("Additional flags are only valid with specific mode flags (--run-legacy-site-agent-only, --import-to-vtex-only, or --run-image-agent-only)")
            run_full_workflow()
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
