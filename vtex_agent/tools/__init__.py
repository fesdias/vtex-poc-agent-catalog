"""Tools for legacy site extraction and VTEX catalog operations."""
from .sitemap_crawler import extract_sitemap_urls, recursive_crawl_pdp_patterns, crawl_categories, build_session
from .url_parser import parse_category_tree_from_url
from .gemini_mapper import extract_to_vtex_schema, analyze_structure_from_sample
from .image_manager import extract_high_res_images
from .prompt_manager_cli import main as prompt_manager_cli_main
from .vtex_catalog_tools import (
    create_department,
    create_category,
    create_brand,
    list_categories,
    list_brands,
    create_product,
    get_product,
    update_product,
    create_sku,
    get_sku,
    update_sku,
    activate_sku,
    set_sku_price,
    set_sku_inventory,
    set_sku_inventory_all_warehouses,
    associate_sku_image,
    list_specification_fields,
    set_product_specification,
)

__all__ = [
    "extract_sitemap_urls",
    "recursive_crawl_pdp_patterns",
    "crawl_categories",
    "build_session",
    "parse_category_tree_from_url",
    "extract_to_vtex_schema",
    "analyze_structure_from_sample",
    "extract_high_res_images",
    "prompt_manager_cli_main",
    "create_department",
    "create_category",
    "create_brand",
    "list_categories",
    "list_brands",
    "create_product",
    "get_product",
    "update_product",
    "create_sku",
    "get_sku",
    "update_sku",
    "activate_sku",
    "set_sku_price",
    "set_sku_inventory",
    "set_sku_inventory_all_warehouses",
    "associate_sku_image",
    "list_specification_fields",
    "set_product_specification",
]

