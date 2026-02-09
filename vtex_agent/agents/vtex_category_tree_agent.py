"""VTEX Category Tree Agent - Creates and manages VTEX category hierarchy."""
from typing import Dict, Any, List, Optional
import time

from ..tools.vtex_catalog_tools import (
    list_categories,
    list_brands,
    create_department,
    create_category,
    create_brand,
)
from ..utils.state_manager import save_state, load_state
from ..utils.logger import get_agent_logger
from ..utils.validation import normalize_category_name, normalize_brand_name
from ..utils.error_handler import retry_with_exponential_backoff


class VTEXCategoryTreeAgent:
    """Agent responsible for creating VTEX category tree and brands."""

    def __init__(self):
        self.logger = get_agent_logger("vtex_category_tree_agent")
        
        # Track created entities
        self.departments = {}
        self.categories = {}
        self.brands = {}
    
    def create_category_tree(self, legacy_site_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create VTEX category tree from legacy site data.
        
        Args:
            legacy_site_data: Output from Legacy Site Agent
            
        Returns:
            Dictionary with VTEX category structure (departments, categories, brands)
        """
        self.logger.info("Starting category tree creation")
        
        # Try to load from state
        state = load_state("vtex_category_tree")
        if state and state.get("departments"):
            self.logger.info("Loaded category tree from state")
            self.departments = state.get("departments", {})
            self.categories = state.get("categories", {})
            self.brands = state.get("brands", {})
            return self._format_output()
        
        products = legacy_site_data.get("products", [])
        self.logger.info(f"Processing {len(products)} products for category tree")
        
        # Evaluate existing VTEX structure
        existing_categories = self._evaluate_existing_categories()
        existing_brands = self._evaluate_existing_brands()
        
        # Process all products to build category tree
        for product in products:
            self._process_product_categories(product, existing_categories)
            self._process_product_brand(product, existing_brands)
        
        # Save output
        output = self._format_output()
        save_state("vtex_category_tree", output)
        
        self.logger.info(f"Category tree creation complete. Created {len(self.departments)} departments, {len(self.categories)} categories, {len(self.brands)} brands")
        
        return output
    
    def _evaluate_existing_categories(self) -> Dict[str, Dict[str, Any]]:
        """Evaluate existing categories in VTEX."""
        self.logger.info("Evaluating existing VTEX categories")
        existing = {}
        
        try:
            categories = list_categories()
            for cat in categories:
                if isinstance(cat, dict):
                    name = cat.get("Name", "")
                    if name:
                        normalized = normalize_category_name(name)
                        existing[normalized] = cat
        except Exception as e:
            self.logger.warning(f"Error evaluating existing categories: {e}")
        
        self.logger.info(f"Found {len(existing)} existing categories")
        return existing
    
    def _evaluate_existing_brands(self) -> Dict[str, Dict[str, Any]]:
        """Evaluate existing brands in VTEX."""
        self.logger.info("Evaluating existing VTEX brands")
        existing = {}
        
        try:
            brands = list_brands()
            for brand in brands:
                if isinstance(brand, dict):
                    name = brand.get("Name", "")
                    if name:
                        normalized = normalize_brand_name(name)
                        existing[normalized] = brand
        except Exception as e:
            self.logger.warning(f"Error evaluating existing brands: {e}")
        
        self.logger.info(f"Found {len(existing)} existing brands")
        return existing
    
    def _process_product_categories(
        self,
        product: Dict[str, Any],
        existing_categories: Dict[str, Dict[str, Any]]
    ):
        """Process categories for a single product."""
        categories_list = product.get("categories", [])
        
        if not categories_list:
            # Try old format
            category = product.get("category", {})
            if category:
                categories_list = [category]
            else:
                return
        
        if not categories_list:
            return
        
        # First category becomes department
        dept_info = categories_list[0]
        dept_name = normalize_category_name(dept_info.get("Name", "Default"))
        
        # Create/get department
        if dept_name not in self.departments:
            # Check if exists in VTEX
            if dept_name in existing_categories:
                dept_data = existing_categories[dept_name]
                dept_id = dept_data.get("Id")
                if dept_id:
                    self.departments[dept_name] = {
                        "id": dept_id,
                        "name": dept_name,
                        "created": False
                    }
                    self.logger.debug(f"Using existing department: {dept_name} (ID: {dept_id})")
            else:
                # Create new department
                try:
                    print(f"     📁 Creating department: {dept_name}")
                    dept = create_department(dept_name)
                    dept_id = dept.get("Id") if isinstance(dept, dict) else None
                    if dept_id:
                        self.departments[dept_name] = {
                            "id": dept_id,
                            "name": dept_name,
                            "created": True
                        }
                        self.logger.info(f"Created department: {dept_name} (ID: {dept_id})")
                    else:
                        self.logger.warning(f"Could not get department ID for: {dept_name}")
                except Exception as e:
                    self.logger.error(f"Error creating department {dept_name}: {e}")
        
        # Create category tree
        parent_id = self.departments[dept_name]["id"]
        
        # If only one category, department serves as category
        if len(categories_list) == 1:
            cat_key = f"{parent_id}::{dept_name}"
            if cat_key not in self.categories:
                self.categories[cat_key] = {
                    "id": parent_id,
                    "name": dept_name,
                    "parent_id": None,
                    "level": 1,
                    "created": False,
                    "path": dept_name
                }
        else:
            # Process remaining categories (skip first, it's the department)
            for cat_info in categories_list[1:]:
                cat_name = normalize_category_name(cat_info.get("Name", ""))
                if not cat_name:
                    continue
                
                cat_key = f"{parent_id}::{cat_name}"
                
                if cat_key not in self.categories:
                    # Check if exists in VTEX
                    existing_cat = None
                    for existing_name, existing_data in existing_categories.items():
                        if existing_name == cat_name:
                            existing_cat = existing_data
                            break
                    
                    if existing_cat:
                        cat_id = existing_cat.get("Id")
                        if cat_id:
                            self.categories[cat_key] = {
                                "id": cat_id,
                                "name": cat_name,
                                "parent_id": parent_id,
                                "level": cat_info.get("Level", 2),
                                "created": False,
                                "path": f"{dept_name} > {cat_name}"
                            }
                            parent_id = cat_id
                            continue
                    
                    # Create new category
                    try:
                        print(f"     📂 Creating category: {cat_name} (Level {cat_info.get('Level', 2)})")
                        cat = create_category(
                            cat_name,
                            father_category_id=parent_id
                        )
                        cat_id = cat.get("Id") if isinstance(cat, dict) else None
                        if cat_id:
                            self.categories[cat_key] = {
                                "id": cat_id,
                                "name": cat_name,
                                "parent_id": parent_id,
                                "level": cat_info.get("Level", 2),
                                "created": True,
                                "path": f"{dept_name} > {cat_name}"
                            }
                            parent_id = cat_id
                            self.logger.info(f"Created category: {cat_name} (ID: {cat_id})")
                        else:
                            self.logger.warning(f"Could not get category ID for: {cat_name}")
                    except Exception as e:
                        self.logger.error(f"Error creating category {cat_name}: {e}")
                else:
                    parent_id = self.categories[cat_key]["id"]
        
        time.sleep(0.2)  # Rate limiting
    
    def _process_product_brand(
        self,
        product: Dict[str, Any],
        existing_brands: Dict[str, Dict[str, Any]]
    ):
        """Process brand for a single product."""
        brand = product.get("brand", {})
        brand_name = normalize_brand_name(brand.get("Name", "Default"))
        
        if not brand_name or brand_name == "Default":
            return
        
        if brand_name not in self.brands:
            # Check if exists in VTEX
            if brand_name in existing_brands:
                brand_data = existing_brands[brand_name]
                brand_id = brand_data.get("Id")
                if brand_id:
                    self.brands[brand_name] = {
                        "id": brand_id,
                        "name": brand_name,
                        "created": False
                    }
                    self.logger.debug(f"Using existing brand: {brand_name} (ID: {brand_id})")
            else:
                # Create new brand
                try:
                    print(f"     🏷️  Creating brand: {brand_name}")
                    brand_obj = create_brand(brand_name)
                    brand_id = brand_obj.get("Id") if isinstance(brand_obj, dict) else None
                    if brand_id:
                        self.brands[brand_name] = {
                            "id": brand_id,
                            "name": brand_name,
                            "created": True
                        }
                        self.logger.info(f"Created brand: {brand_name} (ID: {brand_id})")
                    else:
                        self.logger.warning(f"Could not get brand ID for: {brand_name}")
                except Exception as e:
                    self.logger.error(f"Error creating brand {brand_name}: {e}")
        
        time.sleep(0.2)  # Rate limiting
    
    def _format_output(self) -> Dict[str, Any]:
        """Format output JSON."""
        return {
            "departments": self.departments,
            "categories": self.categories,
            "brands": self.brands,
            "summary": {
                "total_departments": len(self.departments),
                "total_categories": len(self.categories),
                "total_brands": len(self.brands),
                "departments_created": sum(1 for d in self.departments.values() if d.get("created")),
                "categories_created": sum(1 for c in self.categories.values() if c.get("created")),
                "brands_created": sum(1 for b in self.brands.values() if b.get("created"))
            }
        }
    
    def get_category_id_for_product(self, product: Dict[str, Any]) -> Optional[int]:
        """
        Get the category ID for a product based on its category hierarchy.
        
        Args:
            product: Product data from legacy site
            
        Returns:
            Category ID or None
        """
        categories_list = product.get("categories", [])
        
        if not categories_list:
            category = product.get("category", {})
            if category:
                categories_list = [category]
        
        if not categories_list:
            return None
        
        # Get department
        dept_name = normalize_category_name(categories_list[0].get("Name", "Default"))
        if dept_name not in self.departments:
            return None
        
        parent_id = self.departments[dept_name]["id"]
        
        # If only one category, return department ID
        if len(categories_list) == 1:
            return parent_id
        
        # Find the deepest category
        for cat_info in categories_list[1:]:
            cat_name = normalize_category_name(cat_info.get("Name", ""))
            if not cat_name:
                continue
            
            cat_key = f"{parent_id}::{cat_name}"
            if cat_key in self.categories:
                parent_id = self.categories[cat_key]["id"]
            else:
                break
        
        return parent_id
    
    def get_brand_id(self, brand_name: str) -> Optional[int]:
        """
        Get brand ID by name.
        
        Args:
            brand_name: Brand name
            
        Returns:
            Brand ID or None
        """
        normalized = normalize_brand_name(brand_name)
        brand_data = self.brands.get(normalized)
        if brand_data:
            return brand_data.get("id")
        return None

