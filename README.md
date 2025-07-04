# ToolM8 Data Management API

A FastAPI-based data management service for AI tools directory, focused on scraping, seeding, and managing AI tools data from various sources. This is an internal/admin service for data collection, not a public-facing API.

## Features

- **Data Management**: Admin endpoints for scraping, seeding, and database operations
- **CSV Import System**: Multi-source CSV import with extensible architecture
- **Web Scraper**: Async scraper for theresanaiforthat.com with rate limiting and duplicate detection
- **Database Foundation**: PostgreSQL/Supabase schema with categories, tools, and analytics tables
- **Background Tasks**: Non-blocking scraping and seeding operations
- **Data Quality**: Validation, categorization, and quality scoring
- **Analytics**: Database statistics and monitoring

## Project Structure

```
toolm8_api/
├── app/
│   ├── database/
│   │   ├── schema.sql          # Database schema
│   │   ├── connection.py       # Database connection
│   │   └── service.py          # Database service layer
│   ├── routers/
│   │   ├── health.py           # Health check endpoints
│   │   └── admin.py            # Admin management endpoints
│   ├── services/
│   │   ├── base_csv_importer.py     # Base CSV importer class
│   │   ├── taaft_csv_importer.py    # TAAFT-specific CSV importer
│   │   ├── csv_importer_factory.py  # Factory for CSV importers
│   │   └── csv_parser.py            # CSV parser for TAAFT data
│   ├── scraper/
│   │   └── theresanaiforthat.py # Web scraper
│   ├── sample/
│   │   └── theresanaiforthat.csv    # Sample CSV data
│   ├── models.py              # Pydantic models
│   ├── config.py              # Configuration
│   └── main.py                # FastAPI application
├── tests/
│   ├── test_health_router.py   # Health endpoint tests
│   └── test_admin_router.py    # Admin endpoint tests
├── requirements.txt
├── .env.example
└── run.py                     # Setup and run script
```

## Database Schema

### Categories Table
- 10 pre-defined categories (Writing, Image Generation, Video, etc.)
- Display order and featured status
- Automatic timestamps

### Tools Table  
- Comprehensive tool information (name, description, website, pricing)
- Category association and tagging system
- Quality and popularity scoring
- Click tracking integration
- Source attribution

### Analytics
- Tool click tracking with IP logging
- Automatic popularity score updates

## Installation

1. **Clone and setup**:
```bash
cd toolm8_api
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

3. **Setup database**:
```bash
# Run the SQL schema in your Supabase/PostgreSQL database
psql -f app/database/schema.sql
```

## Usage

### Development Commands
```bash
# Install dependencies
make install

# Run tests
make test

# Run tests with coverage
make test-cov

# Format and lint code
make format
make lint
make check
```

### Setup and Scraping
```bash
python run.py
# Choose option 3 to seed categories and run scraper
```

### Start API Server
```bash
python app/main.py
# Or: uvicorn app.main:app --reload
```

### Import CSV Data
```bash
# Test with sample TAAFT data
curl -X POST "http://localhost:8000/admin/import-csv" \
  -F "source=taaft" \
  -F "file=@app/sample/theresanaiforthat.csv" \
  -F "replace_existing=false"
```

### API Endpoints

**Health Endpoints:**
- `GET /` - Root endpoint with API information
- `GET /health` - Health check status

**Admin Endpoints:**
- `GET /admin/stats` - Database statistics and monitoring
- `POST /admin/seed-categories` - Seed categories (background task)
- `POST /admin/scrape-tools?max_pages=10` - Start scraping tools (background task)
- `POST /admin/import-csv` - Import tools from CSV files (multi-source support)
- `DELETE /admin/clear-tools?source=theresanaiforthat` - Clear tools by source

## CSV Import System

The API includes a powerful multi-source CSV import system that supports importing tools from various data sources.

### Supported Sources
- **TAAFT**: `taaft`, `theresanaiforthat`, `theresanaiforthat.com`
- **Extensible**: Easy to add new sources via factory pattern

### Import Endpoint

**POST** `/admin/import-csv`

**Parameters:**
- `source` (form field): Source identifier (e.g., "taaft")
- `file` (file upload): CSV file containing tool data
- `replace_existing` (form field): Boolean - whether to update existing tools

**Example Usage:**
```bash
# Import TAAFT CSV data
curl -X POST "http://localhost:8000/admin/import-csv" \
  -F "source=taaft" \
  -F "file=@sample_data.csv" \
  -F "replace_existing=false"
```

**Response Example:**
```json
{
  "success": true,
  "message": "Successfully processed 161 tools from theresanaiforthat.com",
  "total_parsed": 161,
  "imported": 150,
  "skipped": 11,
  "errors": 0,
  "source": "theresanaiforthat.com"
}
```

### CSV Import Features
- **Bulk Operations**: Efficient upsert operations (2 DB queries vs 300+)
- **Duplicate Handling**: Smart detection of existing tools by slug
- **Source Attribution**: Automatic source tagging for imported data
- **Error Handling**: Comprehensive validation and error reporting
- **Performance Optimized**: Uses Supabase bulk operations for speed

### Adding New CSV Sources

The system is **parser-centric** - the parser is the most important component since each source has completely different CSV formats. The importer logic is mostly the same (bulk operations), but parsing is source-specific.

**1. Create Parser (MOST IMPORTANT)**: 
```python
class ProductHuntCSVParser(BaseCSVParser):
    @property
    def source_name(self) -> str:
        return "producthunt.com"
    
    @property  
    def expected_columns(self) -> List[str]:
        return ["name", "tagline", "description", "website", "upvotes"]
    
    def validate_csv_format(self, csv_content: str) -> bool:
        # Validate ProductHunt format
        pass
        
    def parse_csv_content(self, content: str) -> List[Dict]:
        # Transform ProductHunt CSV → Standard tool format
        # Handle ProductHunt-specific columns: "upvotes", "maker", "launch_date"
        # Extract features based on ProductHunt metrics
        pass
```

**2. Create Simple Importer** (just connects parser):
```python
class ProductHuntCSVImporter(BaseCSVImporter):
    def get_parser(self):
        return ProductHuntCSVParser()
```

**3. Register & Use**:
```python
CSVImporterFactory.register_importer("producthunt", ProductHuntCSVImporter)
# Now works with existing endpoint: source=producthunt
```

**Key Insight**: Different sources have vastly different formats:
- **TAAFT**: `ai_link`, `task_label`, `external_ai_link href`
- **ProductHunt**: `name`, `tagline`, `maker`, `upvotes` 
- **AngelList**: `company_name`, `funding_stage`, `investors`

The parser handles these differences and converts everything to the standard tool format.

## Scraper Features

- **Rate Limited**: 2.5 second delays between requests
- **Duplicate Detection**: Prevents duplicate tools by name/URL
- **Smart Categorization**: Automatic category assignment based on tags/description
- **Data Validation**: Cleans and validates all scraped data
- **Quality Scoring**: Assigns quality scores based on features and completeness
- **Error Handling**: Robust error handling with logging

## Configuration

Environment variables in `.env`:
```bash
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key  
SUPABASE_JWT_SECRET=your_jwt_secret
DATABASE_URL=postgresql://user:pass@host/db
```

## Testing

The project includes comprehensive tests with pytest:

```bash
# Run all tests
make test

# Run tests with coverage report
make test-cov

# Run specific test file
make test-file FILE=tests/test_basic.py
```

**Test Coverage:**
- ✅ **CSV Import System**: Comprehensive parser-centric testing
  - Base CSV parser interface and abstract class enforcement
  - TAAFT CSV parser (format validation, data transformation)
  - Base CSV importer (bulk operations, duplicate handling)
  - CSV importer factory (source registration, dynamic creation)
  - CSV import endpoint (HTTP validation, file upload, error handling)
- ✅ Health router endpoints (root, health check)
- ✅ Admin router endpoints (stats and management)
- ✅ Model validation and Pydantic schemas
- ✅ Configuration management  
- ✅ Database service layer (with mocked connections)
- ✅ Web scraper functionality
- ✅ Error handling and edge cases

Current test coverage focuses on core functionality with modular router testing.

## Expected Results

After running the data management operations, you should have:
- ✅ 10 categories populated in database
- ✅ 500-1000 AI tools scraped and categorized
- ✅ Clean, validated data with proper categorization
- ✅ Quality scores and features extracted
- ✅ Database ready for your frontend application to consume

## Data Quality

The scraper implements several quality measures:
- Text cleaning and validation
- URL validation and normalization  
- Pricing type detection and classification
- Feature extraction from descriptions
- Duplicate prevention
- Category mapping based on keywords
- Quality scoring algorithm

## API Response Example

```json
{
  "id": 1,
  "name": "GPT-4",
  "slug": "gpt-4", 
  "description": "Advanced language model for text generation",
  "website_url": "https://openai.com/gpt-4",
  "pricing_type": "paid",
  "category_id": 1,
  "tags": ["nlp", "text-generation"],
  "features": ["API", "Real-time", "Customization"],
  "quality_score": 9,
  "popularity_score": 150,
  "click_count": 1250
}
```

## Monitoring

The scraper includes comprehensive logging:
- Progress tracking during scraping
- Error logging with context
- Duplicate detection notifications
- Database insertion results
- Performance metrics

Ready to scrape 500-1000 high-quality AI tools with clean, categorized data!