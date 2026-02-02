# VTEX Catalog Migration Agent

An autonomous agent that migrates product catalogs from legacy websites to VTEX using Google Gemini as the extraction engine. The agent intelligently extracts product data, maps it to VTEX schema, and provides an iterative refinement workflow for optimal results.

## Features

- 🗺️ **Sitemap Extraction & Recursive Crawling**: Automatically discovers product URLs from sitemaps or by crawling
- 🤖 **AI-Powered Mapping**: Uses Google Gemini 2.0 Flash to intelligently map HTML to VTEX Catalog Schema
- 🔄 **Iterative Refinement Loop**: Review, refine, and retry extraction with custom feedback until perfect
- 📦 **Complete VTEX Integration**: Creates Departments, Categories, Brands, Products, SKUs, and Images
- 🖼️ **Advanced Image Processing**: Downloads images, uploads to GitHub, and associates with SKUs in VTEX
- 📂 **URL-Based Category Parsing**: Automatically extracts category hierarchy from URL structure
- 🎯 **Custom Extraction Prompts**: Configure site-specific extraction rules via CLI or interactive editor
- 💾 **State Persistence**: Saves progress after each step for resumability and debugging
- ✅ **Validation Gates**: Shows samples and waits for user confirmation before proceeding
- 🔢 **Product/SKU ID Preservation**: Maintains original product and SKU IDs when available
- 💰 **Price & Inventory Management**: Automatically sets SKU prices and inventory levels
- ⚡ **Rate Limiting & Retry Logic**: Handles API rate limits with exponential backoff

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp env_template.txt .env
   # Edit .env with your credentials
   ```

3. **Required Credentials**
   - `GEMINI_API_KEY`: Google Gemini API key (get from [Google AI Studio](https://makersuite.google.com/app/apikey))
   - `GEMINI_MODEL`: Gemini model name (default: `gemini-2.0-flash`)
   - `GEMINI_BASE_URL`: Gemini API base URL (default: `https://generativelanguage.googleapis.com`)
   - `VTEX_ACCOUNT_NAME`: Your VTEX account name
   - `VTEX_APP_KEY`: VTEX API app key (from VTEX admin → Settings → Apps → API Keys)
   - `VTEX_APP_TOKEN`: VTEX API app token
   - `GITHUB_TOKEN`: GitHub personal access token (for image hosting)
   - `GITHUB_REPO`: GitHub repository in format "owner/repo" or full URL
   - `GITHUB_BRANCH`: Branch name (default: `main`)

**Note:** The code uses the new `google-genai` SDK with automatic fallback to legacy `google-generativeai` if needed.

## Usage

### Run Full Workflow
```bash
python main.py
```

### Standalone Scripts

#### Import Existing Extraction Data
If you already have extracted data in `state/legacy_site_extraction.json`, you can import it directly to VTEX:

```bash
# Full import with reporting and approval
python import_to_vtex.py

# Skip reporting, go directly to execution
python import_to_vtex.py --skip-reporting

# Skip approval prompt (for automation)
python import_to_vtex.py --no-approval
```

#### Image Enrichment Agent
After products and SKUs have been created in VTEX, you can enrich them with images:

```bash
python run_image_agent.py state/legacy_site_extraction.json state/vtex_products_skus.json [github_repo_path]
```

Example:
```bash
python run_image_agent.py state/legacy_site_extraction.json state/vtex_products_skus.json images/products
```

### Workflow Steps

1. **Discovery**: Enter target website URL (resumes from saved state if available)
2. **Mapping**: Extract sitemap or recursively crawl for product URLs
3. **Extraction & Alignment**: 
   - Extract 1 sample product using Gemini
   - **Iterative refinement loop**:
     - Review extracted mapping
     - Type `done` to accept and proceed
     - Type `refine` to edit custom prompt and re-extract
     - Type `retry` to re-extract with current prompt
     - Type `feedback` to provide corrections (added to prompt)
4. **Sampling**: Choose how many products to import (or 'all')
5. **Reporting**: Generate `final_plan.md` report with catalog structure analysis
6. **Execution**: Type `APPROVED` to execute VTEX API calls in correct order

## Project Structure

```
vtex-poc-agent-catalog/
├── vtex_agent/              # Agent modules
│   ├── agents/
│   │   ├── migration_agent.py          # Migration orchestrator & workflow
│   │   ├── legacy_site_agent.py        # Legacy site extraction agent
│   │   ├── vtex_category_tree_agent.py  # Category tree creation
│   │   ├── vtex_product_sku_agent.py    # Product & SKU creation
│   │   └── vtex_image_agent.py          # Image enrichment agent
│   ├── clients/
│   │   └── vtex_client.py               # VTEX API client
│   ├── tools/
│   │   ├── gemini_mapper.py             # AI mapping with retry logic
│   │   ├── image_manager.py             # Image download & GitHub upload
│   │   ├── prompt_manager_cli.py       # CLI for prompt management
│   │   ├── sitemap_crawler.py          # URL discovery (sitemap + recursive crawl)
│   │   └── url_parser.py               # Category tree parsing from URLs
│   └── utils/
│       ├── error_handler.py            # Error handling utilities
│       ├── logger.py                   # Logging utilities
│       ├── prompt_manager.py           # Custom prompt management
│       ├── state_manager.py            # State persistence
│       └── validation.py               # Data validation
├── state/                   # State JSON files (auto-generated, git-ignored, local only)
│   ├── discovery.json       # Target URL
│   ├── mapping.json         # Product URLs found
│   ├── legacy_site_extraction.json  # Extracted product data
│   ├── vtex_category_tree.json     # VTEX category tree
│   ├── vtex_products_skus.json     # VTEX products and SKUs
│   ├── vtex_images.json            # Image associations
│   ├── sampling.json               # Selected products
│   ├── reporting.json              # Catalog structure analysis
│   ├── execution.json              # Import results
│   └── custom_prompt.json          # Custom extraction instructions
├── scrapper/                # Legacy scraping scripts (git-ignored, local only)
├── main.py                  # Main entry point
├── import_to_vtex.py        # Direct import script
├── run_image_agent.py       # Standalone image enrichment script
├── requirements.txt         # Dependencies
├── env_template.txt         # Environment template
├── QUICKSTART.md            # Quick start guide
└── .env                     # Configuration (create from env_template.txt)
```

## State Files

State is automatically saved in `state/[step_name].json`:
- `discovery.json`: Target URL
- `mapping.json`: Product URLs found with count
- `legacy_site_extraction.json`: Extracted product data, iteration history, custom instructions used
- `vtex_category_tree.json`: Created departments, categories, and brands
- `vtex_products_skus.json`: Created products and SKUs with IDs
- `vtex_images.json`: Image associations per SKU
- `sampling.json`: Selected products and URLs
- `reporting.json`: Catalog structure analysis and report path
- `execution.json`: Import results summary
- `custom_prompt.json`: Custom extraction prompt instructions

All state files are JSON and can be manually edited if needed to resume or modify the workflow.

## Custom Extraction Prompts

You can customize the extraction prompt to optimize product/SKU information extraction for your specific website structure. Custom prompts take **priority** over default extraction rules.

### Using the CLI Tool

```bash
# View current custom prompt
python -m vtex_agent.tools.prompt_manager_cli show

# Edit prompt interactively (multi-line editor)
python -m vtex_agent.tools.prompt_manager_cli edit

# Set prompt from command line
python -m vtex_agent.tools.prompt_manager_cli set "Always extract technical specs from the specifications table"

# Load prompt from file
python -m vtex_agent.tools.prompt_manager_cli file my_prompt.txt

# Clear custom prompt (use default)
python -m vtex_agent.tools.prompt_manager_cli clear
```

### During Workflow

The agent will automatically:
1. Load custom prompts from state if available
2. Ask if you want to configure custom instructions during extraction phase
3. Use custom instructions for all subsequent extractions
4. Allow iterative refinement with feedback that gets added to the prompt

### Iterative Refinement

During extraction, you can:
- Type `done` - Accept current mapping and proceed
- Type `refine` - Edit custom prompt and re-extract
- Type `retry` - Re-extract with current prompt (useful for transient errors)
- Type `feedback` - Provide corrections that are automatically added to the prompt

### Example Custom Instructions

```
- Always extract technical specifications from the specifications table
- Use the product code (found in URL or product ID) as the RefId for SKUs
- Map color variations to the "Cor" specification group
- Extract dimensions from the product details section
- For pricing, use the "price" field, not "listPrice"
- Product ID and SKU ID = <span class='code'>10010801</span>
- Product Description = text from 'body > main > section.product-details > span.description'
- SKU Price = 'value' attribute from input '#qty-[ProductID]'
```

### CSS Selector Format

You can use CSS selectors in your custom instructions:
- `'body > main > section.class-name'` - CSS selector path
- `'src from img'` - Extract attribute from element
- `<span class='code'>` - Match specific element structure

## Safety Rails

- ✅ **Validation Gates**: Shows JSON samples and waits for confirmation before proceeding
- ✅ **Iterative Refinement**: Review and refine extraction until perfect
- ✅ **Error Handling**: Analyzes failures with retry logic and exponential backoff
- ✅ **State Persistence**: Can resume from any step (all state saved automatically)
- ✅ **Rate Limiting**: Respects API rate limits with automatic retry (429 handling)
- ✅ **Approval Required**: Execution phase requires explicit `APPROVED` confirmation
- ✅ **Sample First**: Always extracts 1 sample product before bulk extraction

## VTEX API Execution Order

The agent executes API calls in the correct dependency order:

1. **Department** (top-level category from URL structure)
2. **Categories** (sub-categories in hierarchy, parent-child relationships)
3. **Brand**
4. **Product** (with ProductId preservation if available)
5. **SKU** (with SkuId preservation if available, includes RefId, Price, ListPrice)
6. **Images** (downloaded, uploaded to GitHub, then associated with SKU)
7. **Price** (set as basePrice with markup=0)
8. **Inventory** (set to 100 in all available warehouses)

**Note:** Specifications are currently disabled - no specification fields are created or set in VTEX.

### Category Hierarchy

The agent automatically builds category trees:
- First category in URL → Department
- Subsequent categories → Sub-categories (parent-child chain)
- If only one category → Department serves as category

## Key Features Explained

### Image Processing Workflow

The image processing follows these steps:
1. **Extraction**: Images are extracted from HTML during product extraction phase
2. **Download**: Images are downloaded from the legacy site
3. **Rename**: Images are renamed using format: `[SkuId]_[SequenceNumber].jpg`
4. **GitHub Upload**: Images are uploaded to a GitHub repository (requires GitHub credentials)
5. **VTEX Association**: Raw GitHub URLs are associated with SKUs in VTEX

Images are processed per SKU, and the first image is marked as the main image.

### Image Extraction Sources

The agent extracts images from multiple sources in priority order:
1. JSON-LD structured data (`@type: Product`)
2. Open Graph meta tags (`og:image`)
3. Product gallery selectors (multiple CSS patterns)
4. High-resolution images from `srcset` attributes
5. Standard `img` tags with size filtering

### URL-Based Category Parsing

Automatically extracts category hierarchy from URL structure:
- `/p/category1/category2/product-name` → `[Category1, Category2]`
- Converts URL slugs to readable category names
- Handles multi-level hierarchies

### Product/SKU ID Preservation

- Extracts ProductId and SkuId from HTML when available
- Preserves original IDs during VTEX import (if numeric)
- Falls back to auto-generated IDs if extraction fails

### Price & Inventory Management

- **Price**: Extracted from product data, set as `basePrice` with `markup=0`
- **Inventory**: Automatically set to 100 in all available warehouses
- Both are set after SKU creation and image association

### Rate Limiting & Retry

- Automatic exponential backoff for 429 (rate limit) errors
- Retries up to 5 times with increasing delays
- Handles both Gemini API and VTEX API rate limits

## Troubleshooting

### Common Issues

**"GEMINI_API_KEY not found"**
- Check that `.env` file exists in the project root directory
- Verify `GEMINI_API_KEY=your_key` is set (no quotes needed)
- Ensure you're running from the project root directory

**"VTEX credentials not configured"**
- Verify all three VTEX credentials are in `.env`:
  - `VTEX_ACCOUNT_NAME=your_account`
  - `VTEX_APP_KEY=your_key`
  - `VTEX_APP_TOKEN=your_token`
- Check account name is case-sensitive and matches exactly
- Verify API keys have catalog write permissions

**"GitHub credentials not found"**
- Set `GITHUB_TOKEN` and `GITHUB_REPO` in `.env`
- `GITHUB_REPO` can be in format "owner/repo" or full URL
- Verify GitHub token has repository write permissions

**"No product URLs found"**
- Website might not have a sitemap
- Agent will fall back to recursive crawling (slower, max 50 pages by default)
- You can manually add URLs by editing `state/mapping.json`

**Gemini API errors (429, quota exceeded)**
- Check API quota/limits in Google AI Studio
- Verify API key is valid and has credits
- Agent automatically retries with exponential backoff
- Try reducing HTML content size if consistently failing

**Extraction quality issues**
- Use custom prompts to guide extraction (`python -m vtex_agent.tools.prompt_manager_cli edit`)
- Provide feedback during iterative refinement loop
- Check `state/legacy_site_extraction.json` to see what was extracted
- Review `state/debug_response.json` for Gemini's raw responses

**VTEX API errors (400, 404, 500)**
- Check error messages in console output
- Verify category hierarchy doesn't conflict with existing VTEX structure
- Review VTEX API documentation for field requirements
- Ensure product/SKU IDs don't conflict with existing ones

**Image upload failures**
- Verify GitHub credentials are correct
- Check repository permissions (token needs write access)
- Ensure repository exists and is accessible
- Check network connectivity for image downloads

**State file issues**
- All state files are JSON - you can manually edit them
- Delete state files to restart from that step
- Check JSON syntax if manually editing (use a JSON validator)

### Resuming from State

If the agent stops, you can resume by:
1. Running `python main.py` again - it will detect existing state
2. Or programmatically:
```python
from vtex_agent.agents.migration_agent import MigrationAgent
from vtex_agent.utils.state_manager import load_state

agent = MigrationAgent()
# Load previous state
state = load_state("legacy_site_extraction")
if state:
    # State is automatically loaded by agents
    pass
# Continue from where you left off
agent.execution_phase(state, require_approval=False)
```

### Debugging

- Check `state/debug_response.json` for Gemini's raw responses
- Review `state/legacy_site_extraction.json` to see extracted data structure
- Check console output for detailed error messages
- VTEX API errors include status codes and response snippets
- Image processing logs show download, upload, and association status

## Workflow Example

Here's what a typical session looks like:

```
🤖 VTEX CATALOG MIGRATION AGENT
============================================================
📋 STEP 1: DISCOVERY
============================================================
🌐 Enter the target website URL to migrate: https://example-store.com
✅ Target URL saved: https://example-store.com

🗺️  STEP 2: MAPPING - Finding Product URLs
============================================================
🔍 Extracting sitemap from: https://example-store.com
   🔍 Checking: https://example-store.com/sitemap.xml
   ✅ Found 150 URLs from sitemap
✅ Mapping complete. Found 150 unique product URLs

🔬 STEP 3: DATA EXTRACTION & ALIGNMENT
============================================================
💡 Using default extraction prompt
   Configure custom instructions? (y/n): n

📥 Extracting 1 product(s)...
   [1/1] Processing: https://example-store.com/product-123
     🖼️  Found 5 images from HTML
     📂 Parsed 2 categories from URL
     🤖 Mapping to VTEX schema with Gemini...
     🖼️  Total images after merge: 5
     ✅ Extraction complete

============================================================
📊 ITERATION 1 - SAMPLE PRODUCT MAPPING
============================================================
{
  "department": {"Name": "Fashion"},
  "categories": [
    {"Name": "Fashion", "Level": 1},
    {"Name": "Shoes", "Level": 2}
  ],
  "brand": {"Name": "Nike"},
  "product": {
    "Name": "Air Max Running Shoes",
    "Description": "Premium running shoes...",
    "ProductId": 12345
  },
  "skus": [
    {
      "Name": "Size 42 - Black",
      "SkuId": 12345001,
      "Price": 199.99,
      "RefId": "NIKE-AM-42-BLK"
    }
  ],
  "images": [
    "https://example-store.com/images/product-123-1.jpg",
    ...
  ]
}

============================================================
🔄 EXTRACTION ITERATION
============================================================
Options:
  - Type 'done' to accept and proceed
  - Type 'refine' to edit custom prompt and re-extract
  - Type 'retry' to re-extract with current prompt
  - Type 'feedback' to provide corrections (will be added to prompt)
  - Press Enter to continue

What would you like to do? done

✅ Extraction approved. Proceeding with current results.

📊 STEP 4: SAMPLING & STRATEGY
============================================================
📈 Total product URLs available: 150
How many products would you like to import for this phase? (or 'all' for all): 10
✅ Selected 10 products for import

📥 Extracting 10 selected products...
[... extraction continues ...]

📄 STEP 5: REPORTING
============================================================
📊 Analyzing catalog structure...
✅ Report generated: /path/to/final_plan.md

🚀 STEP 6: EXECUTION - VTEX Catalog Import
============================================================
⚠️  Ready to execute? Type 'APPROVED' to proceed: APPROVED

📦 Processing 10 products...
   [1/10] Processing product...
     📁 Creating department: Fashion
     📂 Creating category: Shoes (Level 2)
     🏷️  Creating brand: Nike
     📦 Creating product: Air Max Running Shoes
     🔢 Creating SKU: Size 42 - Black
       🖼️  Processing 5 images for SKU 12345001...
         [1/5] Step 1: Downloading image...
         [1/5] Step 2: Uploading to GitHub...
         [1/5] Step 3: Associating image with VTEX SKU...
         ✅ Association successful!
       💰 Price set: 199.99 (basePrice, markup=0)
       📦 Inventory set to 100 in 1/1 warehouse(s)
[... continues for all products ...]

============================================================
✅ EXECUTION COMPLETE
============================================================
   Departments: 1
   Categories: 1
   Brands: 1
   Products: 10
   SKUs: 10
   Images: 50
   Note: Specifications are disabled - no specification fields created or set
```

## Next Steps After Import

1. **Review in VTEX Admin**
   - Check imported products in Catalog → Products
   - Verify category hierarchy is correct
   - Review SKU prices and inventory levels

2. **Verify Images**
   - Check that images are loading correctly from GitHub
   - Verify image quality and order
   - Ensure main images are set correctly

3. **Adjust as Needed**
   - Update product descriptions if needed
   - Adjust pricing rules
   - Modify inventory levels per warehouse
   - Configure additional product attributes

4. **Bulk Import Remaining Products**
   - Run the agent again with 'all' products
   - Or use the state files to resume from where you left off
   - Use `import_to_vtex.py` for faster re-imports

5. **Image Enrichment (if needed)**
   - If images weren't associated during execution, use `run_image_agent.py`
   - This script processes images separately and associates them with existing SKUs
