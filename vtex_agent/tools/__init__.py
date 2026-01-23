"""Tools for legacy site extraction and processing."""
from .sitemap_crawler import extract_sitemap_urls, recursive_crawl_pdp_patterns, build_session
from .url_parser import parse_category_tree_from_url
from .gemini_mapper import extract_to_vtex_schema, analyze_structure_from_sample
from .image_manager import extract_high_res_images
from .prompt_manager_cli import main as prompt_manager_cli_main

__all__ = [
    "extract_sitemap_urls",
    "recursive_crawl_pdp_patterns",
    "build_session",
    "parse_category_tree_from_url",
    "extract_to_vtex_schema",
    "analyze_structure_from_sample",
    "extract_high_res_images",
    "prompt_manager_cli_main",
]

