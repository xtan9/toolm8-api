#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.scraper.theresanaiforthat import run_scraper

async def main():
    print("ToolM8 Web Scraper")
    print("=" * 40)
    
    choice = input("Start web scraper? (y/n): ")
    
    if choice.lower() in ["y", "yes"]:
        print("\n🕷️ Starting web scraper...")
        await run_scraper()
        print("✅ Scraping completed")
    else:
        print("Cancelled.")
    
    print("\n🎉 Done!")

if __name__ == "__main__":
    asyncio.run(main())