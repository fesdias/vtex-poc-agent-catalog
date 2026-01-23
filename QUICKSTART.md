# Quick Start Guide

## Setup (5 minutes)

1. **Install dependencies:**
   ```bash
   cd /Users/felipe.dias/Downloads/SE\ -\ Ciser\ POC/POC
   pip install -r requirements.txt
   ```

2. **Create `.env` file:**
   ```bash
   cp env_template.txt .env
   # Edit .env with your actual credentials
   ```

3. **Required credentials:**
   - **GEMINI_API_KEY**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - **VTEX credentials**: Get from your VTEX admin panel → Settings → Apps → API Keys

## Running the Agent

```bash
python main.py
```

## Workflow Overview

The agent will guide you through 7 steps:

1. **Discovery** → Enter website URL
2. **Mapping** → Finds product URLs (sitemap or crawl)
3. **Extraction** → Extracts 1 sample product using Gemini
   - ⚠️ **STOP HERE**: Review the sample mapping
   - Answer: "Does this mapping match your VTEX store architecture?"
4. **Asset Management** → Extracts and uploads images
5. **Sampling** → Choose how many products to import
6. **Reporting** → Generates `final_plan.md`
7. **Execution** → Type `APPROVED` to import to VTEX

## Example Session

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
   ✅ Found 150 URLs from sitemap
✅ Mapping complete. Found 150 unique product URLs

🔬 STEP 3: DATA EXTRACTION & ALIGNMENT
============================================================
📥 Extracting 1 sample product(s)...
   [1/1] Processing: https://example-store.com/product-123
     🖼️  Found 5 images
     🤖 Mapping to VTEX schema with Gemini...
     ✅ Extraction complete

============================================================
📊 SAMPLE PRODUCT MAPPING
============================================================
{
  "department": {"Name": "Fashion"},
  "category": {"Name": "Shoes"},
  "brand": {"Name": "Nike"},
  "product": {
    "Name": "Air Max Running Shoes",
    "Description": "...",
    ...
  },
  ...
}

❓ USER CONFIRMATION REQUIRED
============================================================
Does this mapping match your VTEX store architecture?
Do you have specific Specification Groups you'd like me to use?

Enter any corrections or specifications (or press Enter to continue):
```

## Troubleshooting

### "GEMINI_API_KEY not found"
- Check that `.env` file exists and contains `GEMINI_API_KEY=your_key`

### "VTEX credentials not configured"
- Verify `.env` has all VTEX credentials
- Check that account name matches exactly (case-sensitive)

### "No product URLs found"
- Website might not have a sitemap
- Agent will fall back to recursive crawling (slower)
- You can manually provide URLs by editing `state/mapping.json`

### Gemini API errors
- Check API quota/limits
- Verify API key is valid
- Try reducing HTML content size

## Resuming from State

If the agent stops, it saves state automatically. To resume:

```python
from vtex_agent.agents.migration_agent import MigrationAgent

agent = MigrationAgent()
# State is automatically loaded by agents
# Just run the workflow again - it will resume from saved state
agent.run_full_workflow()
```

## Next Steps After Import

1. Review imported products in VTEX admin
2. Check category hierarchy
3. Verify images are loading
4. Adjust specifications if needed
5. Set inventory and pricing

