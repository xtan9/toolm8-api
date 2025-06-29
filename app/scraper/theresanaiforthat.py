import asyncio
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

from app.database.service import db_service
from app.models import ToolCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TheresAnAIForThatScraper:
    def __init__(self):
        self.base_url = "https://theresanaiforthat.com"
        self.session = None
        self.rate_limit_delay = 2.5
        self.scraped_tools = []
        self.category_mapping = {
            "writing": ["Writing & Content"],
            "content": ["Writing & Content"],
            "image": ["Image Generation"],
            "photo": ["Image Generation"],
            "video": ["Video & Animation"],
            "animation": ["Video & Animation"],
            "code": ["Code & Development"],
            "programming": ["Code & Development"],
            "development": ["Code & Development"],
            "data": ["Data & Analytics"],
            "analytics": ["Data & Analytics"],
            "marketing": ["Marketing & SEO"],
            "seo": ["Marketing & SEO"],
            "audio": ["Audio & Music"],
            "music": ["Audio & Music"],
            "design": ["Design & UI/UX"],
            "ui": ["Design & UI/UX"],
            "ux": ["Design & UI/UX"],
            "productivity": ["Productivity"],
            "research": ["Research & Learning"],
            "learning": ["Research & Learning"],
            "education": ["Research & Learning"],
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_page(self, url: str) -> Optional[str]:
        try:
            await asyncio.sleep(self.rate_limit_delay)

            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"Successfully fetched: {url}")
                    return content
                else:
                    logger.warning(f"Failed to fetch {url}: Status {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def extract_pricing_info(self, text: str) -> Dict[str, Any]:
        text = text.lower()

        if "free" in text and ("trial" in text or "freemium" in text):
            return {"pricing_type": "freemium", "has_free_trial": True}
        elif "free" in text:
            return {"pricing_type": "free", "has_free_trial": False}
        elif "paid" in text or "$" in text or "subscription" in text:
            return {"pricing_type": "paid", "has_free_trial": "trial" in text}
        elif "one-time" in text or "one time" in text:
            return {"pricing_type": "one-time", "has_free_trial": False}
        else:
            return {"pricing_type": "freemium", "has_free_trial": False}

    async def determine_category_id(self, tags: List[str], description: str = "") -> Optional[int]:
        text_to_check = " ".join(tags + [description]).lower()

        categories = db_service.get_all_categories()
        category_map = {cat.name: cat.id for cat in categories}

        for keyword, category_names in self.category_mapping.items():
            if keyword in text_to_check:
                for cat_name in category_names:
                    if cat_name in category_map:
                        return category_map[cat_name]

        return category_map.get("Productivity")

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text.strip())
        text = re.sub(r"[^\w\s\-\.\!\?\,\:\;]", "", text)
        return text[:500] if len(text) > 500 else text

    def extract_features(self, description: str, tags: List[str]) -> List[str]:
        features = []
        text = (description + " " + " ".join(tags)).lower()

        feature_keywords = [
            "api",
            "automation",
            "real-time",
            "collaboration",
            "integration",
            "templates",
            "customization",
            "analytics",
            "export",
            "import",
            "cloud",
            "mobile",
            "web",
            "desktop",
            "ai-powered",
            "machine learning",
            "natural language",
            "image processing",
            "text generation",
        ]

        for keyword in feature_keywords:
            if keyword in text:
                features.append(keyword.replace("-", " ").title())

        return features[:10]

    async def scrape_tool_page(self, tool_url: str) -> Optional[Dict[str, Any]]:
        content = await self.fetch_page(tool_url)
        if not content:
            return None

        soup = BeautifulSoup(content, "html.parser")

        try:
            tool_data = {}

            title_elem = soup.find("h1") or soup.find("title")
            if title_elem:
                tool_data["name"] = self.clean_text(title_elem.get_text())
            else:
                return None

            description_elem = (
                soup.find("meta", {"name": "description"})
                or soup.find("meta", {"property": "og:description"})
                or soup.find("p")
            )
            if description_elem:
                desc_text = (
                    description_elem.get("content")
                    if description_elem.get("content")
                    else description_elem.get_text()
                )
                tool_data["description"] = self.clean_text(desc_text)

            website_link = soup.find("a", {"class": re.compile(r"visit|website|external", re.I)})
            if website_link and website_link.get("href"):
                tool_data["website_url"] = website_link["href"]

            tags = []
            tag_elements = soup.find_all(
                ["span", "div"], {"class": re.compile(r"tag|category|label", re.I)}
            )
            for elem in tag_elements:
                tag_text = self.clean_text(elem.get_text())
                if tag_text and len(tag_text) < 30:
                    tags.append(tag_text)

            tool_data["tags"] = tags[:8]

            pricing_text = ""
            pricing_elem = soup.find(
                ["div", "span", "p"], {"class": re.compile(r"pric|cost|free|paid", re.I)}
            )
            if pricing_elem:
                pricing_text = pricing_elem.get_text()

            pricing_info = self.extract_pricing_info(
                pricing_text + " " + tool_data.get("description", "")
            )
            tool_data.update(pricing_info)

            tool_data["features"] = self.extract_features(
                tool_data.get("description", ""), tool_data.get("tags", [])
            )

            tool_data["quality_score"] = min(
                10, max(1, 5 + len(tool_data.get("features", [])) // 2)
            )
            tool_data["source"] = "theresanaiforthat"

            return tool_data

        except Exception as e:
            logger.error(f"Error extracting tool data from {tool_url}: {e}")
            return None

    async def scrape_tools_listing(self, page_url: str) -> List[str]:
        content = await self.fetch_page(page_url)
        if not content:
            return []

        soup = BeautifulSoup(content, "html.parser")
        tool_links = []

        link_selectors = [
            'a[href*="/ai/"]',
            'a[href*="/tool/"]',
            'a[href*="/product/"]',
            ".tool-card a",
            ".ai-tool a",
            "[data-tool] a",
        ]

        for selector in link_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get("href")
                if href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in tool_links and self.base_url in full_url:
                        tool_links.append(full_url)

        logger.info(f"Found {len(tool_links)} tool links on {page_url}")
        return tool_links[:50]

    async def scrape_all_tools(self, max_pages: int = 5) -> List[ToolCreate]:
        logger.info("Starting scraping of theresanaiforthat.com")

        all_tool_links = []

        for page in range(1, max_pages + 1):
            page_url = f"{self.base_url}/ai-tools?page={page}"
            logger.info(f"Scraping page {page}: {page_url}")

            tool_links = await self.scrape_tools_listing(page_url)
            if not tool_links:
                logger.info(f"No tools found on page {page}, stopping")
                break

            all_tool_links.extend(tool_links)

            if len(all_tool_links) >= 1000:
                logger.info("Reached 1000 tools limit, stopping")
                all_tool_links = all_tool_links[:1000]
                break

        logger.info(f"Found {len(all_tool_links)} total tool links")

        scraped_tools = []
        for i, tool_url in enumerate(all_tool_links, 1):
            logger.info(f"Scraping tool {i}/{len(all_tool_links)}: {tool_url}")

            tool_data = await self.scrape_tool_page(tool_url)
            if tool_data and tool_data.get("name"):
                slug = db_service.generate_slug(tool_data["name"])
                is_duplicate = db_service.check_duplicate_tool(
                    name=tool_data["name"], website_url=tool_data.get("website_url"), slug=slug
                )

                if not is_duplicate:
                    tool_data["slug"] = slug

                    category_id = await self.determine_category_id(
                        tool_data.get("tags", []), tool_data.get("description", "")
                    )
                    tool_data["category_id"] = category_id

                    try:
                        tool = ToolCreate(**tool_data)
                        scraped_tools.append(tool)
                        logger.info(f"Successfully parsed tool: {tool.name}")
                    except Exception as e:
                        logger.error(f"Error creating ToolCreate object: {e}")
                else:
                    logger.info(f"Skipping duplicate tool: {tool_data['name']}")

            if i % 50 == 0:
                logger.info(f"Processed {i} tools so far, found {len(scraped_tools)} valid tools")

        logger.info(f"Scraping completed. Found {len(scraped_tools)} valid tools")
        return scraped_tools


async def run_scraper():
    async with TheresAnAIForThatScraper() as scraper:
        try:
            tools = await scraper.scrape_all_tools(max_pages=10)

            if tools:
                logger.info(f"Inserting {len(tools)} tools into database...")
                inserted_count = db_service.bulk_insert_tools(tools)
                logger.info(f"Successfully inserted {inserted_count} tools")
            else:
                logger.warning("No tools scraped")

        except Exception as e:
            logger.error(f"Scraping failed: {e}")


if __name__ == "__main__":
    asyncio.run(run_scraper())
