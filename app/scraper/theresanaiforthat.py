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
    def __init__(self) -> None:
        self.base_url = "https://theresanaiforthat.com"
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_delay = 2.5
        self.scraped_tools: List[ToolCreate] = []

    async def __aenter__(self) -> "TheresAnAIForThatScraper":
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.session:
            await self.session.close()

    async def fetch_page(self, url: str) -> Optional[str]:
        try:
            await asyncio.sleep(self.rate_limit_delay)

            if self.session is None:
                return None
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"Successfully fetched: {url}")
                    return str(content)
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

    def enhance_tags(self, tags: List[str], description: str = "", name: str = "") -> List[str]:
        """Enhance tags based on content analysis"""
        text_to_check = f"{name} {description} {' '.join(tags)}".lower()

        # Common AI tool categories as tags
        category_keywords = {
            "writing": ["writing", "content", "text", "blog", "copy", "editor", "grammar"],
            "image-generation": ["image", "photo", "picture", "visual", "art", "design", "graphic"],
            "video": ["video", "animation", "motion", "film", "movie", "editing"],
            "development": ["code", "programming", "development", "software", "api", "github"],
            "data": ["data", "analytics", "analysis", "dashboard", "visualization"],
            "marketing": ["marketing", "seo", "social", "campaign", "ads", "email"],
            "audio": ["audio", "music", "voice", "sound", "speech", "podcast"],
            "design": ["design", "ui", "ux", "interface", "prototype", "figma"],
            "productivity": ["productivity", "task", "project", "management", "organize"],
            "research": ["research", "learning", "education", "study", "knowledge"],
        }

        enhanced_tags = set(tags)  # Start with existing tags

        for category_tag, keywords in category_keywords.items():
            if any(keyword in text_to_check for keyword in keywords):
                enhanced_tags.add(category_tag)

        # Add general AI tag if not present
        if not any(tag.lower() in ["ai", "artificial-intelligence"] for tag in enhanced_tags):
            enhanced_tags.add("ai")

        return sorted(list(enhanced_tags))[:10]  # Limit to 10 tags

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
            tool_data: Dict[str, Any] = {}

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

            tags_for_features: List[str] = tool_data.get("tags", [])  # type: ignore[assignment]
            if isinstance(tags_for_features, str):
                tags_for_features = [tags_for_features]
            tool_data["features"] = self.extract_features(
                tool_data.get("description", ""), tags_for_features
            )  # type: ignore[assignment]

            tool_data["quality_score"] = min(
                10, max(1, 5 + len(tool_data.get("features", [])) // 2)
            )  # type: ignore[assignment]
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

                    # Enhance tags based on content analysis
                    enhanced_tags = self.enhance_tags(
                        tool_data.get("tags", []),
                        tool_data.get("description", ""),
                        tool_data.get("name", ""),
                    )
                    tool_data["tags"] = enhanced_tags

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


async def run_scraper() -> None:
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
