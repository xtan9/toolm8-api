#!/usr/bin/env python3
"""
Process AI tools data scraped with Hexofy
"""
import sys
import os
import pandas as pd
import logging
import json
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.service import db_service
from app.models import ToolCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HexofyDataProcessor:
    def __init__(self):
        self.categories_map = {}
        self.setup_categories()
        
    def setup_categories(self):
        """Set up category mapping"""
        categories = db_service.get_all_categories()
        self.categories_map = {cat.name: cat.id for cat in categories}
        logger.info(f"Available categories: {list(self.categories_map.keys())}")

    def determine_category_id(self, tool_name: str, description: str = "", 
                            category_hint: str = "", tags: List[str] = None) -> int:
        """Determine category ID based on tool information"""
        if tags is None:
            tags = []
        
        # Combine all text for analysis
        text = f"{tool_name} {description} {category_hint} {' '.join(tags)}".lower()
        
        # Category keywords mapping (enhanced for better detection)
        category_keywords = {
            "Writing & Content": [
                "writing", "content", "text", "blog", "copy", "editor", "grammar", 
                "translation", "copywriting", "article", "essay", "creative writing",
                "content creation", "blogging", "documentation", "seo content"
            ],
            "Image Generation": [
                "image", "photo", "picture", "visual", "art", "design", "graphic", 
                "logo", "avatar", "illustration", "dalle", "midjourney", "stable diffusion",
                "ai art", "image creation", "photo editing", "visual content"
            ],
            "Video & Animation": [
                "video", "animation", "motion", "film", "movie", "editing", "streaming",
                "youtube", "tiktok", "short video", "video creation", "motion graphics",
                "video editing", "video production", "animated", "gif"
            ],
            "Code & Development": [
                "code", "programming", "development", "software", "api", "github", 
                "developer", "coding", "copilot", "programming assistant", "code generation",
                "debugging", "code review", "software engineering", "web development"
            ],
            "Data & Analytics": [
                "data", "analytics", "analysis", "dashboard", "visualization", "chart", 
                "report", "database", "business intelligence", "data science", 
                "machine learning", "ai model", "statistics", "metrics"
            ],
            "Marketing & SEO": [
                "marketing", "seo", "social", "campaign", "ads", "email", "growth", 
                "conversion", "social media", "advertising", "lead generation",
                "marketing automation", "digital marketing", "brand", "promotion"
            ],
            "Audio & Music": [
                "audio", "music", "voice", "sound", "speech", "podcast", "recording",
                "voice synthesis", "text to speech", "music generation", "audio editing",
                "voice cloning", "sound effects", "audio production"
            ],
            "Design & UI/UX": [
                "design", "ui", "ux", "interface", "prototype", "figma", "wireframe",
                "user experience", "user interface", "web design", "app design",
                "design system", "mockup", "layout", "visual design"
            ],
            "Productivity": [
                "productivity", "task", "project", "management", "organize", "planning", 
                "workflow", "automation", "efficiency", "scheduling", "calendar",
                "note taking", "document", "collaboration", "team work"
            ],
            "Research & Learning": [
                "research", "learning", "education", "study", "knowledge", "academic", 
                "training", "course", "tutorial", "teaching", "e-learning",
                "knowledge base", "information", "reference", "search"
            ]
        }
        
        # Score each category
        best_category = "Productivity"  # Default fallback
        best_score = 0
        
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > best_score:
                best_score = score
                best_category = category
        
        return self.categories_map.get(best_category, self.categories_map.get("Productivity", 1))

    def extract_pricing_info(self, pricing_text: str) -> Dict[str, Any]:
        """Extract pricing information from text"""
        if not pricing_text:
            return {"pricing_type": "freemium", "has_free_trial": False}
        
        text = pricing_text.lower()
        
        if "free" in text and ("trial" in text or "freemium" in text):
            return {"pricing_type": "freemium", "has_free_trial": True}
        elif "free" in text:
            return {"pricing_type": "free", "has_free_trial": False}
        elif "paid" in text or "$" in text or "subscription" in text or "premium" in text:
            return {"pricing_type": "paid", "has_free_trial": "trial" in text}
        elif "one-time" in text or "one time" in text:
            return {"pricing_type": "one-time", "has_free_trial": False}
        else:
            return {"pricing_type": "freemium", "has_free_trial": False}

    def process_csv_file(self, file_path: str) -> List[ToolCreate]:
        """Process CSV file from Hexofy"""
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} rows from {file_path}")
            logger.info(f"Columns: {list(df.columns)}")
            
            tools = []
            for idx, row in df.iterrows():
                try:
                    tool = self.process_row(row, idx)
                    if tool:
                        tools.append(tool)
                except Exception as e:
                    logger.error(f"Error processing row {idx}: {e}")
                    continue
            
            logger.info(f"Processed {len(tools)} valid tools from CSV")
            return tools
            
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {e}")
            return []

    def process_json_file(self, file_path: str) -> List[ToolCreate]:
        """Process JSON file from Hexofy"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and 'data' in data:
                data = data['data']
            elif not isinstance(data, list):
                logger.error("JSON file should contain a list or object with 'data' key")
                return []
            
            logger.info(f"Loaded {len(data)} items from {file_path}")
            
            tools = []
            for idx, item in enumerate(data):
                try:
                    tool = self.process_dict_item(item, idx)
                    if tool:
                        tools.append(tool)
                except Exception as e:
                    logger.error(f"Error processing item {idx}: {e}")
                    continue
            
            logger.info(f"Processed {len(tools)} valid tools from JSON")
            return tools
            
        except Exception as e:
            logger.error(f"Error reading JSON file {file_path}: {e}")
            return []

    def process_row(self, row: pd.Series, idx: int) -> Optional[ToolCreate]:
        """Process a single row from CSV data"""
        # Common column name variations from Hexofy
        name_columns = ['title', 'name', 'tool_name', 'product_name', 'heading']
        desc_columns = ['description', 'desc', 'summary', 'content', 'text']
        url_columns = ['url', 'link', 'website', 'page_url', 'tool_url']
        category_columns = ['category', 'type', 'tag', 'classification']
        price_columns = ['price', 'pricing', 'cost', 'plan']
        
        # Extract name
        name = None
        for col in name_columns:
            if col in row and pd.notna(row[col]):
                name = str(row[col]).strip()
                break
        
        if not name or name.lower() in ['nan', 'none', '']:
            logger.warning(f"Row {idx}: No valid name found")
            return None
        
        # Extract description
        description = ""
        for col in desc_columns:
            if col in row and pd.notna(row[col]):
                description = str(row[col]).strip()
                break
        
        # Extract URL
        website_url = None
        for col in url_columns:
            if col in row and pd.notna(row[col]):
                url = str(row[col]).strip()
                if url.startswith(('http://', 'https://')):
                    website_url = url
                    break
        
        # Extract category hint
        category_hint = ""
        for col in category_columns:
            if col in row and pd.notna(row[col]):
                category_hint = str(row[col]).strip()
                break
        
        # Extract pricing
        pricing_text = ""
        for col in price_columns:
            if col in row and pd.notna(row[col]):
                pricing_text = str(row[col]).strip()
                break
        
        return self.create_tool(name, description, website_url, category_hint, pricing_text)

    def process_dict_item(self, item: Dict, idx: int) -> Optional[ToolCreate]:
        """Process a single item from JSON data"""
        # Extract name
        name = (item.get('title') or item.get('name') or 
                item.get('tool_name') or item.get('heading', '')).strip()
        
        if not name:
            logger.warning(f"Item {idx}: No valid name found")
            return None
        
        # Extract other fields
        description = (item.get('description') or item.get('summary') or 
                      item.get('content') or '').strip()
        
        website_url = None
        url = (item.get('url') or item.get('link') or item.get('website', '')).strip()
        if url.startswith(('http://', 'https://')):
            website_url = url
        
        category_hint = (item.get('category') or item.get('type') or 
                        item.get('tag') or '').strip()
        
        pricing_text = (item.get('price') or item.get('pricing') or 
                       item.get('cost') or '').strip()
        
        return self.create_tool(name, description, website_url, category_hint, pricing_text)

    def create_tool(self, name: str, description: str, website_url: Optional[str], 
                   category_hint: str, pricing_text: str) -> Optional[ToolCreate]:
        """Create a ToolCreate object from extracted data"""
        try:
            # Generate slug
            slug = db_service.generate_slug(name)
            
            # Check for duplicates
            is_duplicate = db_service.check_duplicate_tool(
                name=name, website_url=website_url, slug=slug
            )
            if is_duplicate:
                logger.info(f"Skipping duplicate tool: {name}")
                return None
            
            # Determine category
            category_id = self.determine_category_id(name, description, category_hint)
            
            # Extract pricing info
            pricing_info = self.extract_pricing_info(pricing_text)
            
            # Extract features from description
            features = self.extract_features(description)
            
            # Calculate quality score
            quality_score = self.calculate_quality_score(name, description, website_url, features)
            
            # Create tags
            tags = self.extract_tags(name, description, category_hint)
            
            tool = ToolCreate(
                name=name,
                slug=slug,
                description=description[:500] if description else f"AI tool: {name}",
                website_url=website_url,
                category_id=category_id,
                tags=tags[:8],  # Limit to 8 tags
                features=features[:10],  # Limit to 10 features
                pricing_type=pricing_info["pricing_type"],
                has_free_trial=pricing_info["has_free_trial"],
                quality_score=quality_score,
                popularity_score=0,  # Default, could be enhanced
                is_featured=False,  # Default
                source="hexofy_scraped"
            )
            
            return tool
            
        except Exception as e:
            logger.error(f"Error creating tool for {name}: {e}")
            return None

    def extract_features(self, description: str) -> List[str]:
        """Extract features from description"""
        if not description:
            return []
        
        text = description.lower()
        feature_keywords = [
            "api", "automation", "real-time", "collaboration", "integration",
            "templates", "customization", "analytics", "export", "import",
            "cloud", "mobile", "web", "desktop", "ai-powered", "machine learning",
            "natural language", "image processing", "text generation", "no-code"
        ]
        
        features = []
        for keyword in feature_keywords:
            if keyword in text:
                features.append(keyword.replace("-", " ").title())
        
        return features[:10]

    def extract_tags(self, name: str, description: str, category_hint: str) -> List[str]:
        """Extract relevant tags"""
        text = f"{name} {description} {category_hint}".lower()
        
        common_tags = [
            "ai", "artificial intelligence", "machine learning", "automation",
            "productivity", "business", "creative", "design", "development",
            "marketing", "writing", "image", "video", "audio", "data"
        ]
        
        tags = []
        for tag in common_tags:
            if tag in text and tag not in tags:
                tags.append(tag)
        
        # Add category hint as tag if available
        if category_hint and category_hint.lower() not in tags:
            tags.append(category_hint.lower())
        
        return tags[:8]

    def calculate_quality_score(self, name: str, description: str, 
                              website_url: Optional[str], features: List[str]) -> int:
        """Calculate quality score based on available data"""
        score = 5  # Base score
        
        if description and len(description) > 50:
            score += 2
        if website_url:
            score += 1
        if features:
            score += min(2, len(features) // 2)
        if len(name) > 5 and len(name) < 50:  # Reasonable name length
            score += 1
        
        return min(10, score)

def process_hexofy_data(file_path: str):
    """Main function to process Hexofy scraped data"""
    logger.info(f"Processing Hexofy data from: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return
    
    processor = HexofyDataProcessor()
    
    # Determine file type and process accordingly
    if file_path.endswith('.csv'):
        tools = processor.process_csv_file(file_path)
    elif file_path.endswith('.json'):
        tools = processor.process_json_file(file_path)
    else:
        logger.error("Unsupported file format. Please provide CSV or JSON file.")
        return
    
    if tools:
        logger.info(f"Inserting {len(tools)} tools into database...")
        inserted_count = db_service.bulk_insert_tools(tools)
        logger.info(f"Successfully inserted {inserted_count} tools from Hexofy data")
        
        # Log some statistics
        categories_used = {}
        pricing_types = {}
        for tool in tools:
            cat_name = next((name for name, id in processor.categories_map.items() 
                           if id == tool.category_id), "Unknown")
            categories_used[cat_name] = categories_used.get(cat_name, 0) + 1
            pricing_types[tool.pricing_type] = pricing_types.get(tool.pricing_type, 0) + 1
        
        logger.info("Category distribution:")
        for cat, count in sorted(categories_used.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {cat}: {count} tools")
        
        logger.info("Pricing distribution:")
        for pricing, count in sorted(pricing_types.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {pricing}: {count} tools")
        
    else:
        logger.warning("No valid tools found to insert")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python process_hexofy_data.py <csv_or_json_file>")
        print("Example: python process_hexofy_data.py hexofy_ai_tools.csv")
        sys.exit(1)
    
    file_path = sys.argv[1]
    process_hexofy_data(file_path)