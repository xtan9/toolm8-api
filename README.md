# ToolM8 Data Management API

A FastAPI-based data management service for AI tools directory, focused on scraping, seeding, and managing AI tools data from various sources. This is an internal/admin service for data collection, not a public-facing API.

## Features

- **Data Management**: Admin endpoints for scraping, seeding, and database operations
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
│   ├── scraper/
│   │   └── theresanaiforthat.py # Web scraper
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

### API Endpoints

**Health Endpoints:**
- `GET /` - Root endpoint with API information
- `GET /health` - Health check status

**Admin Endpoints:**
- `GET /admin/stats` - Database statistics and monitoring
- `POST /admin/seed-categories` - Seed categories (background task)
- `POST /admin/scrape-tools?max_pages=10` - Start scraping tools (background task)
- `DELETE /admin/clear-tools?source=theresanaiforthat` - Clear tools by source

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