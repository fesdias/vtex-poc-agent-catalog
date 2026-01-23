# VTEX Catalog Migration Agent

An autonomous agent that migrates product catalogs from legacy websites to VTEX using Google Gemini as the extraction engine. The agent intelligently extracts product data, maps it to VTEX schema, and provides an iterative refinement workflow for optimal results.

## Features

- 🗺️ **Sitemap Extraction & Recursive Crawling**: Automatically discovers product URLs from sitemaps or by crawling
- 🤖 **AI-Powered Mapping**: Uses Google Gemini 2.0 Flash to intelligently map HTML to VTEX Catalog Schema
- 🔄 **Iterative Refinement Loop**: Review, refine, and retry extraction with custom feedback until perfect
- 📦 **Complete VTEX Integration**: Creates Departments, Categories, Brands, Products, SKUs, Specifications, and Images
- 🖼️ **Advanced Image Extraction**: Extracts high-res images from multiple sources (JSON-LD, og:image, galleries, srcset)
- 📂 **URL-Based Category Parsing**: Automatically extracts category hierarchy from URL structure
- 🎯 **Custom Extraction Prompts**: Configure site-specific extraction rules via CLI or interactive editor
- 💾 **State Persistence**: Saves progress after each step for resumability and debugging
- ✅ **Validation Gates**: Shows samples and waits for user confirmation before proceeding
- 🔢 **Product/SKU ID Preservation**: Maintains original product and SKU IDs when available
- 📋 **Specification Management**: Automatically creates and manages specification fields and values
- ⚡ **Rate Limiting & Retry Logic**: Handles API rate limits with exponential backoff

## Setup

1. **Install Dependencies**
   ```bash
   cd POC
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

**Note:** The code uses the new `google-genai` SDK with automatic fallback to legacy `google-generativeai` if needed.

## Usage

### Run Full Workflow
```bash
python main.py
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
4. **Asset Management**: Verify extracted images (images already extracted during extraction phase)
5. **Sampling**: Choose how many products to import (or 'all')
6. **Reporting**: Generate `final_plan.md` report with catalog structure analysis
7. **Execution**: Type `APPROVED` to execute VTEX API calls in correct order

## Project Structure

```
POC/
├── vtex_agent/              # Agent modules
│   ├── agents/
│   │   ├── migration_agent.py   # Migration orchestrator & workflow
│   ├── state_manager.py     # State persistence
│   ├── prompt_manager.py    # Custom prompt management
│   ├── sitemap_crawler.py   # URL discovery (sitemap + recursive crawl)
│   ├── gemini_mapper.py     # AI mapping with retry logic
│   ├── vtex_client.py       # VTEX API client
│   ├── image_manager.py     # Multi-source image extraction
│   └── url_parser.py        # Category tree parsing from URLs
├── state/                   # State JSON files (auto-generated)
│   ├── discovery.json       # Target URL
│   ├── mapping.json         # Product URLs found
│   ├── extraction.json      # Extracted product data
│   ├── asset_management.json # Image upload status
│   ├── sampling.json        # Selected products
│   ├── reporting.json       # Catalog structure analysis
│   ├── execution.json       # Import results
│   └── custom_prompt.json   # Custom extraction instructions
├── scrapper/                # Existing scraping scripts (legacy)
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── env_template.txt         # Environment template
├── QUICKSTART.md            # Quick start guide
└── .env                     # Configuration (create from env_template.txt)
```

## State Files

State is automatically saved in `/POC/state/[step_name].json`:
- `discovery.json`: Target URL
- `mapping.json`: Product URLs found with count
- `extraction.json`: Extracted product data, iteration history, custom instructions used
- `asset_management.json`: Image extraction status and counts
- `sampling.json`: Selected products and URLs
- `reporting.json`: Catalog structure analysis and report path
- `execution.json`: Import results (departments, categories, brands, products created)
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
4. **Specification Fields** (created per category if they don't exist)
5. **Product** (with ProductId preservation if available)
6. **Product Specifications** (set specification values on product)
7. **SKU** (with SkuId preservation if available, includes RefId, Price, ListPrice)
8. **Images** (uploaded to product, up to 5 images per product)

### Category Hierarchy

The agent automatically builds category trees:
- First category in URL → Department
- Subsequent categories → Sub-categories (parent-child chain)
- If only one category → Department serves as category

## Key Features Explained

### Image Extraction
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

### Specification Management
- Automatically creates specification fields per category
- Normalizes field names (capitalize first letter, rest lowercase)
- Reuses existing fields if they already exist in VTEX
- Sets specification values on products after creation

### Rate Limiting & Retry
- Automatic exponential backoff for 429 (rate limit) errors
- Retries up to 5 times with increasing delays
- Handles both Gemini API and VTEX API rate limits

## Troubleshooting

### Common Issues

**"GEMINI_API_KEY not found"**
- Check that `.env` file exists in `POC/` directory
- Verify `GEMINI_API_KEY=your_key` is set (no quotes needed)
- Ensure you're running from the `POC/` directory

**"VTEX credentials not configured"**
- Verify all three VTEX credentials are in `.env`:
  - `VTEX_ACCOUNT_NAME=your_account`
  - `VTEX_APP_KEY=your_key`
  - `VTEX_APP_TOKEN=your_token`
- Check account name is case-sensitive and matches exactly
- Verify API keys have catalog write permissions

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
- Check `state/extraction.json` to see what was extracted
- Review `state/debug_response.json` for Gemini's raw responses

**VTEX API errors (400, 404, 500)**
- Check error messages in console output
- Verify category hierarchy doesn't conflict with existing VTEX structure
- Ensure specification field names don't contain invalid characters
- Review VTEX API documentation for field requirements

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
- Review `state/extraction.json` to see extracted data structure
- Check console output for detailed error messages
- VTEX API errors include status codes and response snippets

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
  "specifications": [
    {"Name": "Material", "Value": "Leather"},
    {"Name": "Size", "Value": "42"}
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

🖼️  STEP 4: ASSET MANAGEMENT
============================================================
   📦 Air Max Running Shoes: 5 images found
✅ Asset management complete - 5 total images extracted

📊 STEP 5: SAMPLING & STRATEGY
============================================================
📈 Total product URLs available: 150
How many products would you like to import for this phase? (or 'all' for all): 10
✅ Selected 10 products for import

📥 Extracting 10 selected products...
[... extraction continues ...]

📄 STEP 6: REPORTING
============================================================
📊 Analyzing catalog structure...
✅ Report generated: /path/to/final_plan.md

🚀 STEP 7: EXECUTION - VTEX Catalog Import
============================================================
⚠️  Ready to execute? Type 'APPROVED' to proceed: APPROVED

📦 Processing 10 products...
   [1/10] Processing product...
     📁 Creating department: Fashion
     📂 Creating category: Shoes (Level 2)
     🏷️  Creating brand: Nike
     📦 Creating product: Air Max Running Shoes
     📋 Processing 2 specifications...
       📝 Creating specification field: Material
       📝 Creating specification field: Size
     🔢 Creating SKU: Size 42 - Black
         🖼️  Uploading image to VTEX...
[... continues for all products ...]

============================================================
✅ EXECUTION COMPLETE
============================================================
   Departments: 1
   Categories: 1
   Brands: 1
   Specification Fields: 5
   Products: 10
```

## Next Steps After Import

1. **Review in VTEX Admin**
   - Check imported products in Catalog → Products
   - Verify category hierarchy is correct
   - Review specification fields and values

2. **Verify Images**
   - Check that images are loading correctly
   - Verify image quality and order

3. **Adjust as Needed**
   - Modify specification groups if needed
   - Update product descriptions
   - Set inventory levels
   - Configure pricing rules

4. **Bulk Import Remaining Products**
   - Run the agent again with 'all' products
   - Or use the state files to resume from where you left off

