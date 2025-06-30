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
        logger.info("Hexofy data processor initialized")

    def enhance_tags(self, tool_name: str, description: str = "", 
                   category_hint: str = "", tags: List[str] = None) -> List[str]:
        """Enhance tags based on tool information"""
        if tags is None:
            tags = []
        
        # Start with existing tags
        enhanced_tags = set(tags)
        
        # Add category hint as tag if provided
        if category_hint:
            enhanced_tags.add(category_hint.lower().replace(" ", "-"))
        
        # Combine all text for analysis
        text = f"{tool_name} {description} {category_hint} {' '.join(tags)}".lower()
        
        # Simple tag mapping for common categories
        tag_keywords = {
            "writing": ["writing", "content", "text", "blog", "copy", "editor"],
            "image-generation": ["image", "photo", "picture", "visual", "art", "graphic"],
            "video": ["video", "animation", "motion", "film", "movie", "editing"],
            "development": ["code", "programming", "development", "software", "api"],
            "data": ["data", "analytics", "analysis", "dashboard", "visualization"],
            "marketing": ["marketing", "seo", "social", "campaign", "ads"],
            "audio": ["audio", "music", "voice", "sound", "speech", "podcast"],
            "design": ["design", "ui", "ux", "interface", "prototype"],
            "productivity": ["productivity", "task", "project", "management"],
            "research": ["research", "learning", "education", "study"]
        }
        
        # Add relevant tags based on content
        for tag, keywords in tag_keywords.items():
            if any(keyword in text for keyword in keywords):
                enhanced_tags.add(tag)
        
        # Add general AI tag if not present
        if not any(tag.lower() in ["ai", "artificial-intelligence"] for tag in enhanced_tags):
            enhanced_tags.add("ai")
        
        return sorted(list(enhanced_tags))[:10]  # Limit to 10 tags

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
            
            # Extract pricing info
            pricing_info = self.extract_pricing_info(pricing_text)
            
            # Extract features from description
            features = self.extract_features(description)
            
            # Calculate quality score
            quality_score = self.calculate_quality_score(name, description, website_url, features)
            
            # Enhance tags using the enhanced method
            enhanced_tags = self.enhance_tags(name, description, category_hint)
            
            tool = ToolCreate(
                name=name,
                slug=slug,
                description=description[:500] if description else f"AI tool: {name}",
                website_url=website_url,
                tags=enhanced_tags[:10],  # Limit to 10 tags
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
        tag_usage = {}
        pricing_types = {}
        for tool in tools:
            # Count tag usage
            for tag in tool.tags:
                tag_usage[tag] = tag_usage.get(tag, 0) + 1
            pricing_types[tool.pricing_type] = pricing_types.get(tool.pricing_type, 0) + 1
        
        logger.info("Top tags distribution:")
        for tag, count in sorted(tag_usage.items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"  {tag}: {count} tools")
        
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