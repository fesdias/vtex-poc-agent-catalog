"""VTEX Catalog tools - callable functions for creating and managing catalog entities in VTEX.

These tools can be invoked by agents to perform VTEX operations.
"""
import os
import requests
from typing import Dict, Any, List, Optional

from .vtex_api import _get_api


# ========== CATEGORY / DEPARTMENT TOOLS ==========


def create_department(name: str, active: bool = True) -> Dict[str, Any]:
    """Create a department."""
    api = _get_api()
    endpoint = "pvt/category"
    data = {
        "Name": name,
        "AdWordsRemarketingCode": None,
        "Description": None,
        "Active": active,
        "MenuHome": True,
    }
    response = api.catalog_request("POST", endpoint, data=data)
    if response.status_code == 200:
        return response.json()
    if response.status_code == 400 and "already exists" in (response.text or "").lower():
        existing = get_category_by_name(name)
        if existing:
            return existing
    response.raise_for_status()
    return {}


def get_category_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get category by name (searches all categories)."""
    categories = list_categories()
    if not categories:
        return None
    for cat in categories:
        if isinstance(cat, dict) and cat.get("Name") == name:
            return cat
    return None


def create_category(
    name: str,
    father_category_id: Optional[int] = None,
    title: Optional[str] = None,
    active: bool = True,
) -> Dict[str, Any]:
    """Create a category."""
    api = _get_api()
    endpoint = "pvt/category"
    data = {
        "Name": name,
        "FatherCategoryId": father_category_id,
        "Title": title or name,
        "Description": None,
        "Keywords": None,
        "Active": active,
    }
    response = api.catalog_request("POST", endpoint, data=data)
    if response.status_code == 200:
        return response.json()
    if response.status_code == 400 and "already exists" in (response.text or "").lower():
        return get_category_by_name(name) or {}
    response.raise_for_status()
    return {}


def list_categories() -> List[Dict[str, Any]]:
    """List all categories."""
    api = _get_api()
    response = api.catalog_request("GET", "pvt/category")
    if response.status_code == 200:
        return response.json()
    return []


# ========== BRAND TOOLS ==========


def create_brand(
    name: str,
    active: bool = True,
    site_title: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a brand."""
    api = _get_api()
    endpoint = "pvt/brand"
    data = {
        "Name": name,
        "Active": active,
        "Text": None,
        "Keywords": None,
        "SiteTitle": site_title or name,
    }
    response = api.catalog_request("POST", endpoint, data=data)
    if response.status_code == 200:
        return response.json()
    if response.status_code == 400 and "already exists" in (response.text or "").lower():
        brands = list_brands()
        for brand in brands:
            if isinstance(brand, dict) and brand.get("Name") == name:
                return brand
    response.raise_for_status()
    return {}


def list_brands() -> List[Dict[str, Any]]:
    """List all brands."""
    api = _get_api()
    response = api.catalog_request("GET", "pvt/brand")
    if response.status_code == 200:
        return response.json()
    return []


# ========== SPECIFICATION TOOLS ==========


def _get_field_type_id(field_type: str) -> int:
    """Map field type string to VTEX field type ID."""
    mapping = {
        "Text": 1, "Number": 2, "Toggle": 3, "Combo": 4,
        "Radio": 5, "Color": 6, "Date": 7,
    }
    return mapping.get(field_type, 1)


def list_specification_groups(category_id: int) -> List[Dict[str, Any]]:
    """List all specification groups for a category."""
    api = _get_api()
    for endpoint, params in [
        ("pvt/specification/group", {"CategoryId": category_id}),
        (f"pvt/specification/group/{category_id}", None),
        (f"pvt/category/{category_id}/specification/group", None),
    ]:
        response = api.catalog_request("GET", endpoint, params=params)
        if response.status_code == 200:
            result = response.json()
            return result if isinstance(result, list) else []
    return []


def create_specification_group(group_name: str, category_id: int) -> Dict[str, Any]:
    """Create a specification group."""
    api = _get_api()
    existing = list_specification_groups(category_id)
    for group in existing:
        if isinstance(group, dict) and group.get("Name") == group_name:
            print(f"         ℹ️  Specification group '{group_name}' already exists")
            return group

    data = {"Name": group_name, "CategoryId": category_id}
    for endpoint in ["pvt/specification/group", f"pvt/specification/group/{category_id}"]:
        response = api.catalog_request("POST", endpoint, data=data)
        if response.status_code == 200:
            return response.json()
    print(f"         ⚠️  Could not create specification group '{group_name}'")
    return {}


def list_specification_fields(category_id: int) -> List[Dict[str, Any]]:
    """List all specification fields for a category."""
    api = _get_api()
    for endpoint, params in [
        ("pvt/specification/field", {"CategoryId": category_id}),
        (f"pvt/specification/field/{category_id}", None),
        (f"pvt/category/{category_id}/specification/field", None),
    ]:
        response = api.catalog_request("GET", endpoint, params=params)
        if response.status_code == 200:
            result = response.json()
            return result if isinstance(result, list) else []
    return []


def create_specification_field(
    field_name: str,
    category_id: int,
    field_type: str = "Text",
    is_required: bool = False,
    group_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Create a specification field."""
    api = _get_api()
    existing = list_specification_fields(category_id)
    for field in existing:
        if isinstance(field, dict) and field.get("Name") == field_name:
            print(f"         ℹ️  Specification field '{field_name}' already exists")
            return field

    data = {
        "Name": field_name,
        "CategoryId": category_id,
        "FieldTypeId": _get_field_type_id(field_type),
        "IsRequired": is_required,
        "IsStockKeepingUnit": False,
        "IsFilter": True,
        "IsOnProductDetails": True,
    }
    if group_id:
        data["GroupId"] = group_id

    for method, endpoint in [("PUT", "pvt/specification/field"), ("POST", "pvt/specification/field")]:
        response = api.catalog_request(method, endpoint, data=data)
        if response.status_code == 200:
            return response.json()
    return {}


def set_product_specification(
    product_id: int,
    field_id: int,
    field_value: str,
    field_type: str = "Text",
) -> Dict[str, Any]:
    """Set a specification value for a product."""
    api = _get_api()
    endpoint = f"pvt/products/{product_id}/specification"
    data = {
        "FieldId": field_id,
        "FieldValueId": None,
        "Text": str(field_value),
    }
    response = api.catalog_request("PUT", endpoint, data=data)
    if response.status_code == 200:
        return response.json()
    return {}


# ========== PRODUCT TOOLS ==========


def create_product(
    name: str,
    category_id: int,
    brand_id: int,
    description: Optional[str] = None,
    short_description: Optional[str] = None,
    is_active: bool = True,
    show_without_stock: bool = True,
    product_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Create a product."""
    api = _get_api()
    endpoint = "pvt/product"
    data = {
        "Name": name,
        "CategoryId": category_id,
        "BrandId": brand_id,
        "Description": description or "",
        "ShortDescription": short_description or (description[:200] if description else ""),
        "ReleaseDate": None,
        "KeyWords": None,
        "Title": name,
        "IsVisible": True,
        "IsActive": is_active,
        "ShowWithoutStock": show_without_stock,
        "Score": None,
    }
    if product_id is not None:
        data["Id"] = product_id

    response = api.catalog_request("POST", endpoint, data=data)
    if response.status_code == 200:
        return response.json()
    if response.status_code == 409 and product_id is not None:
        existing = get_product(product_id)
        if existing:
            print(f"   ℹ️  Product already exists, using existing product (ID: {product_id})")
            if is_active and not existing.get("IsActive", False):
                try:
                    update_product(product_id, is_active=True)
                    print(f"   ✓ Updated product IsActive flag to True")
                except Exception as update_error:
                    print(f"   ⚠️  Could not update IsActive flag: {update_error}")
            return existing
        return {"Id": product_id, "Name": "Existing Product"}
    if response.status_code != 409:
        response.raise_for_status()
    return {}


def get_product(product_id: int) -> Optional[Dict[str, Any]]:
    """Get a product by ID."""
    api = _get_api()
    response = api.catalog_request("GET", f"pvt/product/{product_id}")
    if response.status_code == 200:
        return response.json()
    return None


def update_product(
    product_id: int,
    is_active: Optional[bool] = None,
    show_without_stock: Optional[bool] = None,
) -> Dict[str, Any]:
    """Update a product's IsActive and ShowWithoutStock flags."""
    current = get_product(product_id)
    if not current:
        raise ValueError(f"Product {product_id} not found")
    if is_active is not None:
        current["IsActive"] = is_active
    if show_without_stock is not None:
        current["ShowWithoutStock"] = show_without_stock

    api = _get_api()
    response = api.catalog_request("PUT", f"pvt/product/{product_id}", data=current)
    if response.status_code == 200:
        return response.json()
    response.raise_for_status()
    return {}


# ========== SKU TOOLS ==========


def get_sku(sku_id: int) -> Optional[Dict[str, Any]]:
    """Get a SKU by ID."""
    api = _get_api()
    response = api.catalog_request("GET", f"pvt/stockkeepingunit/{sku_id}")
    if response.status_code == 200:
        return response.json()
    return None


def update_sku(sku_id: int, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update a SKU using the full payload from GET."""
    api = _get_api()
    response = api.catalog_request("PUT", f"pvt/stockkeepingunit/{sku_id}", data=payload)
    if response.status_code == 200:
        return response.json()
    return None


def activate_sku(sku_id: int) -> bool:
    """Activate a SKU: GET current data, then PUT with IsActive=true."""
    sku = get_sku(sku_id)
    if not sku:
        return False
    sku["IsActive"] = True
    return update_sku(sku_id, sku) is not None


def create_sku(
    product_id: int,
    name: str,
    ean: str,
    is_active: bool = True,
    ref_id: Optional[str] = None,
    package_height: Optional[float] = None,
    package_width: Optional[float] = None,
    package_length: Optional[float] = None,
    package_weight: Optional[float] = None,
    height: Optional[float] = None,
    width: Optional[float] = None,
    length: Optional[float] = None,
    weight: Optional[float] = None,
    sku_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Create a SKU."""
    api = _get_api()
    endpoint = "pvt/stockkeepingunit"
    data = {
        "ProductId": product_id,
        "Name": name,
        "EAN": ean,
        "IsActive": is_active,
        "RefId": ref_id,
    }
    if package_height is not None:
        data["PackagedHeight"] = package_height
    if package_width is not None:
        data["PackagedWidth"] = package_width
    if package_length is not None:
        data["PackagedLength"] = package_length
    if package_weight is not None:
        data["PackagedWeightKg"] = package_weight
    if height is not None:
        data["Height"] = height
    if width is not None:
        data["Width"] = width
    if length is not None:
        data["Length"] = length
    if weight is not None:
        data["WeightKg"] = weight
    if sku_id is not None:
        data["Id"] = sku_id

    response = api.catalog_request("POST", endpoint, data=data)
    if response.status_code == 200:
        return response.json()
    if response.status_code == 409 and sku_id is not None:
        existing = get_sku(sku_id)
        if existing:
            print(f"   ℹ️  SKU already exists, using existing SKU (ID: {sku_id})")
            return existing
        return {"Id": sku_id, "Name": name, "ProductId": product_id}
    if response.status_code != 409:
        response.raise_for_status()
    return {}


def set_sku_price(
    sku_id: int,
    price: float,
    list_price: Optional[float] = None,
) -> Dict[str, Any]:
    """Set SKU pricing using VTEX Pricing API."""
    api = _get_api()
    url = f"https://api.vtex.com/{api.account_name}/pricing/prices/{sku_id}"
    data = {"markup": 0, "costPrice": price}
    try:
        response = requests.put(url, json=data, headers=api.headers, timeout=30)
        if response.status_code in [200, 201, 204]:
            return response.json() if response.text else {"status": "success"}
        if response.status_code != 200:
            print(f"         ⚠️  Failed to set price for SKU {sku_id}. Status: {response.status_code}")
        response.raise_for_status()
    except Exception as e:
        print(f"         ⚠️  Error setting price for SKU {sku_id}: {e}")
        raise
    return {}


def list_warehouses() -> List[Dict[str, Any]]:
    """List all available warehouses."""
    api = _get_api()
    url = f"{api.base_url}/api/logistics/pvt/configuration/warehouses"
    try:
        response = requests.get(url, headers=api.headers, timeout=30)
        if response.status_code == 200:
            warehouses = response.json()
            return warehouses if isinstance(warehouses, list) else []
    except Exception as e:
        print(f"         ⚠️  Error listing warehouses: {e}")
    return []


def set_sku_inventory(
    sku_id: int,
    warehouse_id: Optional[str] = None,
    quantity: int = 0,
    unlimited_quantity: bool = False,
) -> Dict[str, Any]:
    """Set SKU inventory for a specific warehouse."""
    api = _get_api()
    warehouse_id = warehouse_id or os.getenv("VTEX_WAREHOUSE_ID", "1_1")
    url = f"{api.base_url}/api/logistics/pvt/inventory/skus/{sku_id}/warehouses/{warehouse_id}"
    data = {"quantity": quantity, "unlimitedQuantity": unlimited_quantity}
    try:
        response = requests.put(url, json=data, headers=api.headers, timeout=30)
        if response.status_code in [200, 201, 204]:
            return response.json() if response.text else {"status": "success"}
    except Exception as e:
        print(f"         ⚠️  Error setting inventory for SKU {sku_id}: {e}")
    return {}


def set_sku_inventory_all_warehouses(sku_id: int, quantity: int = 100) -> Dict[str, Any]:
    """Set SKU inventory to the specified quantity for all warehouses."""
    warehouses = list_warehouses()
    results = {}
    if not warehouses:
        default_result = set_sku_inventory(sku_id, quantity=quantity)
        results["default"] = default_result
        return results

    print(f"         📦 Setting inventory to {quantity} for {len(warehouses)} warehouse(s)")
    for warehouse in warehouses:
        warehouse_id = warehouse.get("Id") or warehouse.get("id")
        warehouse_name = warehouse.get("Name") or warehouse.get("name") or str(warehouse_id)
        if not warehouse_id:
            continue
        try:
            result = set_sku_inventory(sku_id, warehouse_id=str(warehouse_id), quantity=quantity)
            results[warehouse_name] = result
            print(f"           ✓ Warehouse {warehouse_name}: {quantity}")
        except Exception as e:
            print(f"           ⚠️  Warehouse {warehouse_name}: Failed - {e}")
            results[warehouse_name] = {"error": str(e)}
    return results


# ========== IMAGE TOOLS ==========


def associate_sku_image(
    sku_id: int,
    image_url: str,
    file_name: str,
    is_main: bool = False,
    label: Optional[str] = None,
) -> Dict[str, Any]:
    """Associate an image with a SKU."""
    api = _get_api()
    endpoint = f"pvt/stockkeepingunit/{sku_id}/file"
    data = {
        "url": image_url,
        "name": file_name,
        "isMain": is_main,
        "label": label or "Product Image",
    }
    response = api.catalog_request("POST", endpoint, data=data)
    if response.status_code in [200, 201]:
        return response.json() if response.text else {"status": "success"}
    if response.status_code == 409:
        print(f"         ℹ️  Image already associated with SKU {sku_id}, continuing...")
        return {"status": "already_exists", "sku_id": sku_id}
    if response.status_code not in [200, 201, 409]:
        print(f"         ⚠️  Failed to associate image with SKU {sku_id}. Status: {response.status_code}")
    return {}
