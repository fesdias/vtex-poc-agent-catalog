#!/usr/bin/env python3
"""
Standalone script to run the VTEX Image Enrichment Agent.

This agent:
1. Downloads images from legacy site
2. Renames them: [SkuId]_[SequenceNumber]
3. Uploads to GitHub public repository
4. Associates images with SKUs in VTEX

Usage:
    python run_image_agent.py <legacy_site_json_path> <vtex_products_skus_json_path> [github_repo_path]

Example:
    python run_image_agent.py state/legacy_site_extraction.json state/vtex_products_skus.json
    python run_image_agent.py state/legacy_site_extraction.json state/vtex_products_skus.json images/products
"""
import sys
import os
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from vtex_agent.agents.vtex_image_agent import VTEXImageAgent


def main():
    if len(sys.argv) < 3:
        print("Usage: python run_image_agent.py <legacy_site_json_path> <vtex_products_skus_json_path> [github_repo_path]")
        print("\nExample:")
        print("  python run_image_agent.py state/legacy_site_extraction.json state/vtex_products_skus.json")
        print("  python run_image_agent.py state/legacy_site_extraction.json state/vtex_products_skus.json images/products")
        sys.exit(1)
    
    legacy_site_json_path = sys.argv[1]
    vtex_products_skus_json_path = sys.argv[2]
    github_repo_path = sys.argv[3] if len(sys.argv) > 3 else "images"
    
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


if __name__ == "__main__":
    main()

