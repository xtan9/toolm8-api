import asyncio
import logging
from app.database.service import db_service
from app.models import CategoryCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_categories():
    categories_data = [
        {
            "name": "Writing & Content",
            "slug": "writing-content",
            "description": "AI tools for writing, content creation, and text generation",
            "display_order": 1,
            "is_featured": True,
        },
        {
            "name": "Image Generation",
            "slug": "image-generation",
            "description": "AI-powered image creation and manipulation tools",
            "display_order": 2,
            "is_featured": True,
        },
        {
            "name": "Video & Animation",
            "slug": "video-animation",
            "description": "AI tools for video creation, editing, and animation",
            "display_order": 3,
            "is_featured": True,
        },
        {
            "name": "Code & Development",
            "slug": "code-development",
            "description": "AI-assisted coding, debugging, and development tools",
            "display_order": 4,
            "is_featured": True,
        },
        {
            "name": "Data & Analytics",
            "slug": "data-analytics",
            "description": "AI tools for data analysis, visualization, and insights",
            "display_order": 5,
            "is_featured": True,
        },
        {
            "name": "Marketing & SEO",
            "slug": "marketing-seo",
            "description": "AI-powered marketing automation and SEO optimization tools",
            "display_order": 6,
            "is_featured": True,
        },
        {
            "name": "Audio & Music",
            "slug": "audio-music",
            "description": "AI tools for audio processing, music generation, and voice synthesis",
            "display_order": 7,
            "is_featured": True,
        },
        {
            "name": "Design & UI/UX",
            "slug": "design-ui-ux",
            "description": "AI-assisted design tools for UI/UX and graphic design",
            "display_order": 8,
            "is_featured": True,
        },
        {
            "name": "Productivity",
            "slug": "productivity",
            "description": "AI tools to boost productivity and automate workflows",
            "display_order": 9,
            "is_featured": True,
        },
        {
            "name": "Research & Learning",
            "slug": "research-learning",
            "description": "AI tools for research, education, and knowledge discovery",
            "display_order": 10,
            "is_featured": True,
        },
    ]

    logger.info("Starting category seeding...")

    for category_data in categories_data:
        try:
            category = CategoryCreate(**category_data)
            existing = await db_service.find_category_by_name(category.name)

            if not existing:
                result = await db_service.insert_category(category)
                if result:
                    logger.info(f"Created category: {category.name}")
                else:
                    logger.error(f"Failed to create category: {category.name}")
            else:
                logger.info(f"Category already exists: {category.name}")

        except Exception as e:
            logger.error(f"Error seeding category {category_data['name']}: {e}")

    logger.info("Category seeding completed")


if __name__ == "__main__":
    asyncio.run(seed_categories())
