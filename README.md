# VTEX Catalog Migration Agent

An autonomous agent that migrates product catalogs from legacy websites to VTEX using Google Gemini as the extraction engine. The agent intelligently extracts product data, maps it to VTEX schema, and provides an iterative refinement workflow for optimal results.

## Features

- 🗺️ **Sitemap Extraction & Recursive Crawling**: Automatically discovers product URLs from sitemaps or by crawling
- 🤖 **LLM-Powered URL Review**: Uses AI to analyze and filter URLs, identifying Product Detail Pages (PDPs)
- 🎯 **Category-Based Crawling**: Option to crawl specific category pages when sitemaps aren't available
- 🤖 **AI-Powered Extraction**: Uses Google Gemini 2.0 Flash to intelligently extract all product data from HTML
- 🖼️ **Smart Image Selection**: LLM identifies and extracts only product images (excludes banners, logos, etc.)
- 📂 **Intelligent Category Extraction**: LLM extracts categories from HTML content (breadcrumbs, navigation) not just URL
- 🔄 **Iterative Refinement Loop**: Review, refine, and retry extraction with custom feedback until perfect
- 📦 **Complete VTEX Integration**: Creates Departments, Categories, Brands, Products, SKUs, and Images
- 🖼️ **Advanced Image Processing**: Downloads images, uploads to GitHub, and associates with SKUs in VTEX
- 🎯 **Custom Extraction Prompts**: Configure site-specific extraction rules via CLI or interactive editor
- 💾 **State Persistence**: Saves progress after each step for resumability and debugging (numbered files for ordering)
- ✅ **Validation Gates**: Shows samples and waits for user confirmation before proceeding
- 🔢 **Product/SKU ID Preservation**: Maintains original product and SKU IDs when available
- 💰 **Price & Inventory Management**: Automatically sets SKU prices and inventory levels
- ⚡ **Rate Limiting & Retry Logic**: Handles API rate limits with exponential backoff and global endpoint
- 🚀 **Flexible Workflow**: Run full workflow, legacy site agent only, or import existing data

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
   - `GEMINI_BASE_URL`: Leave unset for Vertex AI global endpoint (recommended to avoid 429 errors), or set to `https://generativelanguage.googleapis.com` for Google AI Studio
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

### Run Legacy Site Agent Only
Extract products from a legacy website without importing to VTEX:

```bash
# Basic usage (will prompt for target URL)
python main.py --run-legacy-site-agent-only

# With target URL
python main.py --run-legacy-site-agent-only --target-url https://example.com

# Extract 5 products with more pages
python main.py --run-legacy-site-agent-only --sample-size 5 --max-pages 100

# Disable iterative refinement
python main.py --run-legacy-site-agent-only --no-iterative-refinement
```

### Import Existing Extraction Data
If you already have extracted data in `state/legacy_site_extraction.json`, you can import it directly to VTEX:

```bash
# Full import with reporting and approval
python main.py --import-to-vtex-only

# Skip reporting, go directly to execution
python main.py --import-to-vtex-only --skip-reporting

# Skip approval prompt (for automation)
python main.py --import-to-vtex-only --skip-reporting --no-approval
```

### Image Enrichment Agent
After products and SKUs have been created in VTEX, you can enrich them with images:

```bash
# Use default paths from state/ folder
python main.py --run-image-agent-only

# Specify custom GitHub repo path
python main.py --run-image-agent-only --github-repo-path images/products

# Specify custom file paths
python main.py --run-image-agent-only --legacy-site-path custom/path.json --vtex-products-path custom/vtex.json
```

### Workflow Steps

1. **Discovery**: Enter target website URL (resumes from saved state if available)
2. **Mapping**: 
   - Extract sitemap or recursively crawl for product URLs
   - **LLM URL Review**: AI analyzes all URLs and identifies Product Detail Pages (PDPs)
   - User can refine the selection (include/exclude URLs)
3. **Extraction & Alignment**: 
   - Extract 1 sample product using Gemini (for validation)
   - **Iterative refinement loop**:
     - Review extracted mapping
     - Type `done` to accept and proceed
     - Type `refine` to edit custom prompt and re-extract
     - Type `retry` to re-extract with current prompt
     - Type `feedback` to provide corrections (added to prompt)
   - **After approval**: Ask how many products to extract (or 'all')
   - Extract selected products
4. **Sampling**: (Full workflow only) Choose how many products to import (or 'all')
5. **Reporting**: Generate `state/final_plan.md` report with catalog structure analysis
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
│   ├── 01_discovery.json       # Target URL
│   ├── 02_mapping.json         # Product URLs found
│   ├── 03_extraction.json      # Extraction iteration state
│   ├── legacy_site_extraction.json  # Extracted product data (final output, no number prefix)
│   ├── 05_sampling.json        # Selected products
│   ├── 06_reporting.json       # Catalog structure analysis
│   ├── 07_vtex_category_tree.json     # VTEX category tree
│   ├── 08_vtex_products_skus.json     # VTEX products and SKUs
│   ├── 09_vtex_images.json            # Image associations
│   ├── 10_execution.json              # Import results
│   ├── final_plan.md                   # Migration plan report
│   └── custom_prompt.json              # Custom extraction instructions
├── scrapper/                # Legacy scraping scripts (git-ignored, local only)
├── main.py                  # Unified entry point (supports all workflows via flags)
├── requirements.txt         # Dependencies
├── env_template.txt         # Environment template
├── QUICKSTART.md            # Quick start guide
└── .env                     # Configuration (create from env_template.txt)
```

## State Files

State is automatically saved in `state/` with numbered prefixes for workflow ordering:
- `01_discovery.json`: Target URL
- `02_mapping.json`: Product URLs found with count
- `03_extraction.json`: Extraction iteration state (intermediate)
- `legacy_site_extraction.json`: Extracted product data (final output, no number prefix)
- `05_sampling.json`: Selected products and URLs
- `06_reporting.json`: Catalog structure analysis and report path
- `07_vtex_category_tree.json`: Created departments, categories, and brands
- `08_vtex_products_skus.json`: Created products and SKUs with IDs
- `09_vtex_images.json`: Image associations per SKU
- `10_execution.json`: Import results summary
- `final_plan.md`: Migration plan report (saved in state folder)
- `custom_prompt.json`: Custom extraction prompt instructions (no number prefix)

All state files are JSON and can be manually edited if needed to resume or modify the workflow. Files are numbered to show workflow order, except for final outputs and configuration files.

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

### Smart Image Extraction

The LLM intelligently identifies and extracts only product images:
- **Includes**: Product galleries, carousels, main product photos, zoom images
- **Excludes**: Site logos, banners, icons, social media images, decorative backgrounds, navigation images
- Prioritizes high-resolution images (1200Wx1200H or larger)
- Converts relative URLs to absolute URLs
- Returns empty array if no clear product images are found (doesn't include non-product images)

### LLM-Powered URL Review

During the mapping phase, the LLM analyzes all discovered URLs to:
- Identify Product Detail Pages (PDPs) vs category pages, home pages, etc.
- Categorize URLs as: definitely PDP, possibly PDP, or not PDP
- Process URLs in batches with retry logic for rate limits
- Allow user refinement (include/exclude specific URLs)

### Intelligent Category Extraction

The LLM extracts categories from HTML content in priority order:
1. Breadcrumb navigation (nav.breadcrumb, ol.breadcrumb)
2. Category navigation menus on the page
3. Category links in product detail sections
4. Meta tags (product:category)
5. Structured data (JSON-LD)
6. URL path structure (fallback only)

This ensures accurate category extraction even when categories aren't in the URL.

### Product/SKU ID Preservation

- Extracts ProductId and SkuId from HTML when available
- Preserves original IDs during VTEX import (if numeric)
- Falls back to auto-generated IDs if extraction fails

### Price & Inventory Management

- **Price**: Extracted from product data, set as `basePrice` with `markup=0`
- **Inventory**: Automatically set to 100 in all available warehouses
- Both are set after SKU creation and image association

### Rate Limiting & Retry

- **Global Endpoint**: Uses Vertex AI global endpoint by default (recommended to avoid 429 errors)
- **Automatic Exponential Backoff**: Retries up to 5 times with increasing delays (2s → 4s → 8s → 16s → 32s, max 120s)
- **Pre-request Delays**: Small delays before LLM calls to avoid immediate rate limits
- **Batch Processing**: Processes URLs in batches with delays between batches
- **Error Handling**: Distinguishes rate limit errors from other errors, provides helpful tips
- **Handles**: Both Gemini API and VTEX API rate limits
- **Concise Error Messages**: Shows helpful messages without full tracebacks

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
     🤖 Extracting product data with Gemini (images, categories, and all fields)...
     🖼️  LLM identified 5 product images
     📂 LLM extracted 2 categories
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

============================================================
📊 PRODUCT EXTRACTION - QUANTITY SELECTION
============================================================
📈 Total product URLs available: 150
✅ Sample product extraction approved.
How many products would you like to extract? (or 'all' for all): 10

📥 Extracting 10 products...
[... extraction continues ...]

📄 STEP 5: REPORTING
============================================================
📊 Analyzing catalog structure...
✅ Report generated: state/final_plan.md

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
   - Use `python main.py --import-to-vtex-only` for faster re-imports

5. **Image Enrichment (if needed)**
   - If images weren't associated during execution, use `python main.py --run-image-agent-only`
   - This processes images separately and associates them with existing SKUs
