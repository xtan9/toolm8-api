# ToolM8 Data Management API - Claude Context

## Project Overview

This is a **data management service** for an AI tools directory. It's focused on scraping and managing AI tools data from various sources. This is an **internal/admin service** for data collection, NOT a public-facing API.

## Tech Stack

- **FastAPI** - Web framework for admin endpoints
- **Supabase/PostgreSQL** - Database with categories, tools tables
- **AsyncIO** - Async web scraping with rate limiting
- **BeautifulSoup + aiohttp** - Web scraping tools
- **Python linting** - Black, flake8, isort, mypy, pylint

## Database Schema

- `categories` - 10 predefined AI tool categories (Writing, Image Gen, etc.)
- `tools` - AI tools with metadata, pricing, quality scores, categorization

## Key Admin Endpoints
- `POST /admin/scrape-tools?max_pages=10` - Start scraping (background task)
- `GET /admin/stats` - Database statistics and monitoring
- `DELETE /admin/clear-tools?source=X` - Clear tools by source

## Development Commands

```bash
# Install dependencies
make install

# Testing
make test               # Run all tests
make test-cov          # Run with coverage
make test-file FILE=x  # Run specific test file

# Format and lint code
make format
make lint
make check

# Run application
make run
python app/main.py

# Setup and scraping
make setup
python run.py
```

## Environment Setup

Required `.env` variables:

```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_JWT_SECRET=your_jwt_secret
DATABASE_URL=postgresql://user:pass@host/db
```

## Project Purpose

1. **Scrape AI tools** from theresanaiforthat.com with rate limiting
2. **Categorize and validate** scraped data with quality scoring
3. **Populate database** for frontend applications to consume
4. **Monitor data quality** with statistics and duplicate detection

## Architecture Notes

- **Background tasks** for non-blocking scraping operations
- **Rate limiting** (2.5s delays) to be respectful to source sites
- **Duplicate detection** by name/URL/slug to prevent data pollution
- **Smart categorization** based on tags and descriptions
- **Quality scoring** algorithm based on features and completeness

## Recent Changes

- Refactored from public API to data management service
- Removed click tracking (tool_clicks table) - not needed for data mgmt
- Added comprehensive Python linting setup
- Code formatted with Black (100 char line length)
- Admin-focused endpoints only

## Data Flow

1. Seed categories → 2. Scrape tools → 3. Validate & categorize → 4. Store in DB → 5. Frontend consumes data

The service is designed to run periodically to keep the AI tools database fresh and up-to-date.

## Remember

- make sure to run existing tests, lint, typecheck... all necessary checks after code change to make sure it doesn't break anything.
- make sure to add new tests after code changes.
