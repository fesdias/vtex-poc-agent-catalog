"""Legacy Site Agent - Extracts product data from source website."""
import os
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..tools.sitemap_crawler import extract_sitemap_urls, recursive_crawl_pdp_patterns, build_session
from ..tools.url_parser import parse_category_tree_from_url
from ..tools.gemini_mapper import extract_to_vtex_schema
from ..tools.image_manager import extract_high_res_images
from ..utils.state_manager import save_state, load_state, save_custom_prompt
from ..utils.prompt_manager import get_custom_prompt, edit_custom_prompt_interactive
from ..utils.logger import get_agent_logger
from ..utils.validation import validate_legacy_site_output


class LegacySiteAgent:
    """Agent responsible for extracting data from legacy websites."""
    
    def __init__(self):
        self.logger = get_agent_logger("legacy_site_agent")
        self.session = build_session()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        # Agent state
        self.target_url = None
        self.product_urls = []
        self.extracted_products = []
    
    def discover_target_url(self, target_url: Optional[str] = None) -> str:
        """
        Discover and set target website URL.
        
        Args:
            target_url: Optional target URL (if None, loads from state or prompts user)
            
        Returns:
            Target URL string
        """
        self.logger.info("Starting discovery phase")
        
        # Try to load from state
        state = load_state("discovery")
        if state and state.get("target_url"):
            self.target_url = state["target_url"]
            self.logger.info(f"Loaded target URL from state: {self.target_url}")
            return self.target_url
        
        # Use provided URL or prompt
        if target_url:
            self.target_url = target_url
        else:
            self.target_url = input("\n🌐 Enter the target website URL to migrate: ").strip()
        
        if not self.target_url.startswith(("http://", "https://")):
            self.target_url = f"https://{self.target_url}"
        
        save_state("discovery", {"target_url": self.target_url})
        self.logger.info(f"Target URL set: {self.target_url}")
        
        return self.target_url
    
    def map_product_urls(self, max_pages: int = 50) -> List[str]:
        """
        Map and discover product URLs from target website.
        
        Args:
            max_pages: Maximum pages to crawl if sitemap not found
            
        Returns:
            List of product URLs
        """
        self.logger.info("Starting mapping phase")
        
        if not self.target_url:
            raise ValueError("Target URL not set. Run discover_target_url() first.")
        
        # Try to load from state
        state = load_state("mapping")
        if state and state.get("product_urls"):
            self.product_urls = state["product_urls"]
            self.logger.info(f"Loaded {len(self.product_urls)} URLs from state")
            return self.product_urls
        
        # Try sitemap first
        self.logger.info(f"Extracting sitemap from: {self.target_url}")
        sitemap_urls = extract_sitemap_urls(self.target_url, self.session)
        
        if sitemap_urls:
            self.logger.info(f"Found {len(sitemap_urls)} URLs from sitemap")
            self.product_urls = sitemap_urls
        else:
            self.logger.info("No sitemap found. Using recursive crawler...")
            self.product_urls = recursive_crawl_pdp_patterns(
                self.target_url,
                self.session,
                max_pages=max_pages
            )
            self.logger.info(f"Found {len(self.product_urls)} potential product URLs")
        
        # Deduplicate
        self.product_urls = list(set(self.product_urls))
        
        save_state("mapping", {
            "target_url": self.target_url,
            "product_urls": self.product_urls,
            "url_count": len(self.product_urls)
        })
        
        self.logger.info(f"Mapping complete. Found {len(self.product_urls)} unique product URLs")
        return self.product_urls
    
    def extract_products(
        self,
        sample_size: int = 1,
        custom_instructions: Optional[str] = None,
        enable_iterative_refinement: bool = True
    ) -> Dict[str, Any]:
        """
        Extract products from URLs with optional iterative refinement.
        
        Args:
            sample_size: Number of products to extract initially
            custom_instructions: Optional custom extraction instructions
            enable_iterative_refinement: Whether to enable iterative refinement loop
            
        Returns:
            Dictionary with extracted products in standardized format
        """
        self.logger.info(f"Starting extraction phase (sample_size={sample_size})")
        
        if not self.product_urls:
            raise ValueError("No product URLs found. Run map_product_urls() first.")
        
        # Load custom prompt if not provided
        if custom_instructions is None:
            custom_instructions = get_custom_prompt()
            if custom_instructions:
                self.logger.info(f"Using custom extraction instructions ({len(custom_instructions)} chars)")
        
        # Get sample products
        sample_urls = self.product_urls[:sample_size] if sample_size > 0 else self.product_urls[:1]
        
        # Initial extraction
        extracted_samples = self._extract_products_batch(sample_urls, custom_instructions)
        
        # Iterative refinement loop
        if enable_iterative_refinement:
            extracted_samples = self._iterative_refinement_loop(
                extracted_samples,
                sample_urls,
                custom_instructions
            )
        
        self.extracted_products = extracted_samples
        
        # Convert to standardized output format
        output = self._format_output(extracted_samples)
        
        # Validate output
        is_valid, error = validate_legacy_site_output(output)
        if not is_valid:
            self.logger.warning(f"Output validation warning: {error}")
        
        # Save output
        save_state("legacy_site_extraction", output)
        self.logger.info(f"Extraction complete. Extracted {len(output['products'])} products")
        
        return output
    
    def _iterative_refinement_loop(
        self,
        extracted_samples: List[Dict[str, Any]],
        sample_urls: List[str],
        custom_instructions: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Handle iterative refinement loop for extraction."""
        iteration = 1
        iteration_history = []
        
        while True:
            # Save current state
            save_state("extraction", {
                "sample_size": len(extracted_samples),
                "extracted_products": extracted_samples,
                "custom_instructions_used": custom_instructions is not None,
                "iteration": iteration,
                "iteration_history": iteration_history
            })
            
            # Display sample for user review
            if not extracted_samples:
                print("\n⚠️  No products extracted. Exiting iteration loop.")
                break
            
            sample = extracted_samples[0]
            print("\n" + "="*60)
            print(f"📊 ITERATION {iteration} - SAMPLE PRODUCT MAPPING")
            print("="*60)
            print(json.dumps(sample["mapped_data"], indent=2, ensure_ascii=False))
            
            print("\n" + "="*60)
            print("🔄 EXTRACTION ITERATION")
            print("="*60)
            print("\nOptions:")
            print("  - Type 'done' to accept and proceed")
            print("  - Type 'refine' to edit custom prompt and re-extract")
            print("  - Type 'retry' to re-extract with current prompt")
            print("  - Type 'feedback' to provide corrections (will be added to prompt)")
            print("  - Press Enter to continue")
            
            user_action = input("\nWhat would you like to do? ").strip().lower()
            
            if user_action == "done":
                print("\n✅ Extraction approved. Proceeding with current results.")
                iteration_history.append({
                    "iteration": iteration,
                    "action": "approved",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                break
            
            elif user_action == "refine":
                print("\n⚙️  Refining extraction prompt...")
                new_instructions = edit_custom_prompt_interactive()
                if new_instructions:
                    custom_instructions = new_instructions
                    iteration_history.append({
                        "iteration": iteration,
                        "action": "prompt_refined",
                        "custom_instructions_length": len(custom_instructions)
                    })
                print("\n🔄 Re-extracting with updated prompt...")
                extracted_samples = self._extract_products_batch(sample_urls, custom_instructions)
                iteration += 1
            
            elif user_action == "retry":
                print("\n🔄 Re-extracting with current prompt...")
                extracted_samples = self._extract_products_batch(sample_urls, custom_instructions)
                iteration_history.append({
                    "iteration": iteration,
                    "action": "retried",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                iteration += 1
            
            elif user_action == "feedback":
                print("\n💬 Please provide your feedback/corrections:")
                feedback = input("Feedback: ").strip()
                
                if feedback:
                    if custom_instructions:
                        custom_instructions = f"{custom_instructions}\n\nUser Feedback (Iteration {iteration}): {feedback}"
                    else:
                        custom_instructions = f"User Feedback (Iteration {iteration}): {feedback}"
                    
                    save_custom_prompt(custom_instructions)
                    
                    iteration_history.append({
                        "iteration": iteration,
                        "action": "feedback_provided",
                        "feedback": feedback
                    })
                    
                    print("\n✅ Feedback added to prompt. Re-extracting...")
                    extracted_samples = self._extract_products_batch(sample_urls, custom_instructions)
                    iteration += 1
            
            else:
                print("\n✅ Proceeding with current extraction results.")
                break
        
        return extracted_samples
    
    def _extract_products_batch(
        self,
        urls: List[str],
        custom_instructions: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Extract a batch of products from URLs."""
        extracted_samples = []
        
        print(f"\n📥 Extracting {len(urls)} product(s)...")
        self.logger.info(f"Extracting {len(urls)} products")
        
        for i, url in enumerate(urls, 1):
            print(f"\n   [{i}/{len(urls)}] Processing: {url}")
            self.logger.debug(f"Processing URL {i}/{len(urls)}: {url}")
            
            try:
                # Fetch HTML
                r = self.session.get(url, timeout=30)
                if r.status_code != 200:
                    print(f"     ⚠️  HTTP {r.status_code}, skipping...")
                    self.logger.warning(f"HTTP {r.status_code} for URL: {url}")
                    continue
                
                html_content = r.text
                
                # Extract images from HTML
                images_from_html = extract_high_res_images(html_content, url)
                print(f"     🖼️  Found {len(images_from_html)} images from HTML")
                
                # Parse category tree from URL structure
                url_categories = parse_category_tree_from_url(url)
                if url_categories:
                    print(f"     📂 Parsed {len(url_categories)} categories from URL")
                
                # Use Gemini to map to VTEX schema
                print(f"     🤖 Mapping to VTEX schema with Gemini...")
                mapped_data = extract_to_vtex_schema(
                    html_content,
                    url,
                    self.gemini_api_key,
                    custom_instructions=custom_instructions
                )
                
                # Merge images
                gemini_images = mapped_data.get("images", [])
                all_images = list(set(images_from_html + gemini_images))
                mapped_data["images"] = all_images
                
                # Use URL-based categories if Gemini didn't extract properly
                if url_categories and (not mapped_data.get("categories") or len(mapped_data.get("categories", [])) < len(url_categories)):
                    mapped_data["categories"] = url_categories
                    if url_categories:
                        mapped_data["department"] = {"Name": url_categories[0]["Name"]}
                
                print(f"     🖼️  Total images after merge: {len(all_images)}")
                
                # Store extracted data
                extracted_samples.append({
                    "url": url,
                    "html_preview": html_content[:1000],
                    "images": all_images,
                    "mapped_data": mapped_data
                })
                
                print(f"     ✅ Extraction complete")
                self.logger.debug(f"Successfully extracted product from: {url}")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"     ⚠️  Error extracting {url}: {e}")
                self.logger.error(f"Error extracting {url}: {e}", exc_info=True)
                continue
        
        return extracted_samples
    
    def _format_output(self, extracted_products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format extracted products into standardized output JSON.
        
        Args:
            extracted_products: List of extracted product data
            
        Returns:
            Standardized output dictionary
        """
        products = []
        
        for product_data in extracted_products:
            mapped = product_data.get("mapped_data", {})
            
            # Extract product info
            product_info = mapped.get("product", {})
            categories = mapped.get("categories", [])
            brand = mapped.get("brand", {})
            skus = mapped.get("skus", [])
            specifications = mapped.get("specifications", [])
            images = product_data.get("images", [])
            
            # Format product entry (include mapped_data for backward compatibility)
            product_entry = {
                "url": product_data.get("url"),
                "product": product_info,
                "categories": categories,
                "brand": brand,
                "skus": skus,
                "specifications": specifications,
                "images": images,
                "mapped_data": mapped  # Include for reporting phase compatibility
            }
            
            products.append(product_entry)
        
        return {
            "target_url": self.target_url,
            "extracted_at": datetime.now().isoformat(),
            "products": products,
            "metadata": {
                "total_products": len(products),
                "total_urls_found": len(self.product_urls),
                "custom_prompt_used": get_custom_prompt() is not None
            }
        }
    
    def extract_all_products(self, custom_instructions: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract all products without iterative refinement (for bulk extraction).
        
        Args:
            custom_instructions: Optional custom extraction instructions
            
        Returns:
            Dictionary with all extracted products
        """
        self.logger.info("Starting bulk extraction of all products")
        return self.extract_products(
            sample_size=len(self.product_urls),
            custom_instructions=custom_instructions,
            enable_iterative_refinement=False
        )

