# Browser-Based Web Scraping Guide for AI Tools Directory

This guide shows you how to use browser extensions to manually scrape AI tools data from any directory website.

## Recommended Extensions

### 🥇 **Instant Data Scraper** (Recommended)
- **Rating**: 4.9/5 stars, 1M+ users
- **Price**: 100% Free
- **Best for**: AI-powered automatic detection, no coding required

### 🥈 **Table Capture** 
- **Rating**: 4.4/5 stars
- **Price**: Free with premium features
- **Best for**: Table-specific extraction, multiple export formats

### 🥉 **Web Scraper**
- **Rating**: Popular with advanced users
- **Price**: Free + paid cloud features
- **Best for**: Complex scraping, scheduled extraction

## Setup Guide: Instant Data Scraper

### Step 1: Install Extension
```
1. Go to Chrome Web Store
2. Search "Instant Data Scraper"
3. Click "Add to Chrome"
4. Extension will appear in your toolbar
```

### Step 2: Navigate to AI Tools Directory
**Recommended Sites:**
- `https://www.producthunt.com/topics/artificial-intelligence`
- `https://topai.tools/`
- `https://aitoolsdirectory.com/`
- `https://www.futurepedia.io/`
- `https://theresanaiforthat.com/ai-tools` (if accessible)

### Step 3: Activate Scraping
```
1. Open the AI tools directory page
2. Click the Instant Data Scraper icon in your browser
3. The extension will automatically detect tables/lists
4. You'll see highlighted data sections
```

### Step 4: Configure Extraction
```
1. Select the data you want to capture
2. Preview the detected fields:
   - Tool names
   - Descriptions
   - URLs
   - Categories
   - Pricing info
3. Adjust selection if needed
```

### Step 5: Export Data
```
1. Click "Export" or "Download"
2. Choose CSV format
3. Save the file to your project directory
```

## Alternative: Table Capture

### When to Use Table Capture
- When data is in clean HTML tables
- Need multiple export formats (Excel, Google Sheets)
- Want to capture specific table sections

### Setup Process
```
1. Install "Table Capture" from Chrome Web Store
2. Navigate to AI tools page with tables
3. Click Table Capture icon
4. Select the table you want
5. Choose export format (CSV recommended)
6. Download the file
```

## Processing Scraped Data

Once you have your CSV file, use our processor:

```bash
# Process the scraped data
python process_hexofy_data.py your_scraped_file.csv

# Example with different names
python process_hexofy_data.py producthunt_ai_tools.csv
python process_hexofy_data.py topai_tools_export.csv
```

## Target Sites and Strategies

### 1. Product Hunt AI Category
**URL**: `https://www.producthunt.com/topics/artificial-intelligence`

**Strategy**:
```
- Browse different time periods (today, this week, this month)
- Look for "Show more" buttons to load additional tools
- Focus on highly-rated tools (4+ stars)
- Capture: Name, description, maker, website URL
```

### 2. TopAI.tools
**URL**: `https://topai.tools/`

**Strategy**:
```
- Browse by categories (Writing, Image, Video, etc.)
- Use search for specific tool types
- Look for pricing information
- Capture: Tool name, description, category, pricing
```

### 3. AI Tools Directory
**URL**: `https://aitoolsdirectory.com/`

**Strategy**:
```
- Browse featured tools section
- Check category-specific pages
- Look for "new tools" or "trending" sections
- Capture: Name, description, website, category
```

### 4. Futurepedia
**URL**: `https://www.futurepedia.io/`

**Strategy**:
```
- Excellent structured data
- Clear categories and pricing
- High-quality tool descriptions
- Capture: All available fields
```

## Tips for Better Results

### 1. **Work in Batches**
```
- Scrape 20-50 tools at a time
- Process each batch before moving to next
- Easier to verify data quality
- Less likely to encounter issues
```

### 2. **Target Specific Categories**
```
Instead of entire directories, focus on:
- Writing AI tools
- Image generation tools
- Code assistants
- Productivity tools
```

### 3. **Check Data Quality**
```
Before processing, verify CSV contains:
- Tool names in first column
- Descriptions (even if brief)
- URLs when available
- Category information
```

### 4. **Handle Pagination**
```
Many sites load more content as you scroll:
- Scroll to load all tools before scraping
- Look for "Load more" or "Show more" buttons
- Some extensions handle infinite scroll automatically
```

## Example Workflow

### Complete Process (15-30 minutes)
```
1. Install Instant Data Scraper (2 minutes)
2. Navigate to Product Hunt AI (1 minute)
3. Scroll through tools list (3 minutes)
4. Activate scraper and export CSV (2 minutes)
5. Process data with our script (5 minutes)
6. Verify results in database (2 minutes)
```

### Sample Commands
```bash
# Process your scraped data
python process_hexofy_data.py my_scraped_tools.csv

# Check results
curl http://localhost:8000/admin/stats
```

## Troubleshooting

### Common Issues

**1. Extension not detecting data**
```
Solution:
- Refresh the page and try again
- Look for table or list structures
- Try scrolling to load more content
- Switch to Table Capture for table-specific data
```

**2. CSV file is empty or malformed**
```
Solution:
- Check if data was actually selected
- Verify export completed successfully
- Try re-exporting with different settings
- Open CSV in text editor to check format
```

**3. Processor fails to import data**
```
Solution:
- Check CSV has column headers
- Verify file encoding is UTF-8
- Ensure at least name/title column exists
- Check logs for specific error messages
```

**4. Many duplicates skipped**
```
This is normal if:
- Database already has similar tools
- Processing same site multiple times
- Tools have similar names/URLs
```

## Expected Results

### Quality Metrics
- **50-200 tools** per scraping session
- **80%+ import success rate** with good data
- **Automatic categorization** accuracy ~85%
- **Processing time**: 2-5 minutes per 100 tools

### Data Coverage
You should get tools with:
- ✅ Names and descriptions
- ✅ Website URLs (when available)  
- ✅ Categories (automatically assigned)
- ✅ Basic pricing info (when detected)
- ✅ Quality scores (calculated automatically)

This approach gives you real, current AI tools data without fighting anti-bot systems!