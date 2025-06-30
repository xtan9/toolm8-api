# Hexofy Integration Guide for AI Tools Directory

This guide shows you how to use Hexofy to scrape real AI tools data for your directory.

## Step 1: Set Up Hexofy

1. **Create Hexofy Account**
   - Go to [Hexofy.com](https://hexofy.com)
   - Sign up for a free account

2. **Install Browser Extension**
   - **Chrome**: [Hexofy Chrome Extension](https://chromewebstore.google.com/detail/hexofy-scraper-web-scrapi/bmcfkceaciejniimbpekgcgkodlgfadj)
   - **Firefox**: [Hexofy Firefox Extension](https://addons.mozilla.org/en-US/firefox/addon/hexofy/)

## Step 2: Scrape AI Tools Data

### Recommended AI Tools Directory Sites

1. **Product Hunt AI Category**
   - URL: `https://www.producthunt.com/topics/artificial-intelligence`
   - Has 4.5M+ active users and dedicated AI section

2. **TopAI.tools**
   - URL: `https://topai.tools/`
   - Clean directory with good structure

3. **AI Tools Directory**
   - URL: `https://aitoolsdirectory.com/`
   - Comprehensive AI tools listing

4. **There's An AI For That** (if accessible)
   - URL: `https://theresanaiforthat.com/ai-tools`
   - Large directory but may require specific techniques

### Scraping Process

1. **Navigate to Target Site**
   ```
   Go to one of the recommended sites above
   Browse or search for AI tools in specific categories
   ```

2. **Activate Hexofy**
   ```
   Click the Hexofy extension icon in your browser toolbar
   Select the scraping mode (list scraping for directories)
   ```

3. **Configure Scraping**
   ```
   Select the data fields you want to capture:
   - Tool names/titles
   - Descriptions
   - URLs/links
   - Categories
   - Pricing information
   - Images (optional)
   ```

4. **Execute Scraping**
   ```
   Click start scraping
   Let Hexofy automatically capture the data
   Process usually takes a few seconds
   ```

5. **Export Data**
   ```
   Save to CSV format (recommended for our processor)
   Or export to Google Sheets and download as CSV
   ```

## Step 3: Process Scraped Data

Once you have your CSV file from Hexofy:

```bash
# Place your CSV file in the project directory
# Example: hexofy_ai_tools.csv

# Run the processor
python process_hexofy_data.py hexofy_ai_tools.csv
```

### Expected CSV Columns

The processor handles various column names automatically:

**Tool Names**: `title`, `name`, `tool_name`, `product_name`, `heading`
**Descriptions**: `description`, `desc`, `summary`, `content`, `text`
**URLs**: `url`, `link`, `website`, `page_url`, `tool_url`
**Categories**: `category`, `type`, `tag`, `classification`
**Pricing**: `price`, `pricing`, `cost`, `plan`

### Processing Features

- ✅ **Automatic Category Detection** - Intelligently categorizes tools
- ✅ **Duplicate Prevention** - Skips tools already in database
- ✅ **Data Cleaning** - Validates and cleans scraped data
- ✅ **Quality Scoring** - Assigns quality scores based on data completeness
- ✅ **Feature Extraction** - Extracts features from descriptions
- ✅ **Tag Generation** - Creates relevant tags automatically

## Step 4: Verify Results

Check your database for imported tools:

```bash
# Run the API to see stats
python -c "
from app.database.service import db_service
tools = db_service.get_tools_by_category(1, limit=5)
print(f'Sample tools: {[t.name for t in tools]}')
"
```

Or use the admin API:
```bash
curl http://localhost:8000/admin/stats
```

## Tips for Better Results

### 1. Target Specific Categories
```
Instead of scraping entire directories, focus on:
- Product Hunt AI tools by category
- Specific tool types (e.g., writing AI, image AI)
- Featured/trending tools sections
```

### 2. Multiple Small Batches
```
Better to scrape 50-100 tools at a time than thousands
This ensures:
- Higher data quality
- Less likely to be blocked
- Easier to process and verify
```

### 3. Clean Data Sources
```
Prefer sites with:
- Clear tool descriptions
- Consistent data structure
- Active moderation
- Recent/updated listings
```

### 4. Verify and Enhance
```
After importing:
- Check for missing descriptions
- Verify category assignments
- Add logos/images manually if needed
- Update featured flags for top tools
```

## Troubleshooting

### Common Issues

1. **No data in CSV file**
   - Check if Hexofy captured the right elements
   - Try different scraping selectors
   - Verify the target site allows scraping

2. **Import errors**
   - Check CSV format and encoding (UTF-8)
   - Ensure column headers match expected names
   - Verify required fields (name/title) are present

3. **Many duplicates skipped**
   - Normal behavior if database already has tools
   - Check different categories or newer tools
   - Clear existing data if starting fresh

### Getting Help

- **Hexofy Support**: Check their academy and documentation
- **Data Issues**: Review the processor logs for specific errors
- **Database Problems**: Ensure categories exist in database

## Example Workflow

1. **Scrape with Hexofy**
   - Visit Product Hunt AI category
   - Use Hexofy to scrape 50-100 tools
   - Export as CSV

2. **Process Data**
   ```bash
   python process_hexofy_data.py producthunt_ai_tools.csv
   ```

3. **Verify Results**
   ```bash
   curl http://localhost:8000/admin/stats
   ```

This approach gives you real, up-to-date AI tools data without the complexities of dealing with anti-bot protection!