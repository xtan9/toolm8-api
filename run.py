#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.seed import seed_categories
from app.scraper.theresanaiforthat import run_scraper

async def main():
    print("ToolM8 Setup and Scraper")
    print("=" * 40)
    
    choice = input("What would you like to do?\n1. Seed categories\n2. Run scraper\n3. Both\nChoice (1-3): ")
    
    if choice in ["1", "3"]:
        print("\n🌱 Seeding categories...")
        await seed_categories()
        print("✅ Categories seeded successfully")
    
    if choice in ["2", "3"]:
        print("\n🕷️ Starting web scraper...")
        await run_scraper()
        print("✅ Scraping completed")
    
    print("\n🎉 Setup completed!")

if __name__ == "__main__":
    asyncio.run(main())