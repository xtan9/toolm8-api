import pytest
from unittest.mock import Mock, patch, call
from app.database.seed import seed_categories
from app.models import Category, CategoryCreate


class TestSeedCategories:
    """Test the seed_categories function"""

    @patch('app.database.seed.db_service')
    def test_seed_categories_all_new(self, mock_db_service):
        """Test seeding when all categories are new"""
        # Mock that no categories exist
        mock_db_service.find_category_by_name.return_value = None
        
        # Mock successful insertions
        mock_category = Category(
            id=1, name="Writing & Content", slug="writing-content",
            description="AI tools for writing, content creation, and text generation",
            display_order=1, is_featured=True,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        mock_db_service.insert_category.return_value = mock_category
        
        seed_categories()
        
        # Should check for all 10 categories
        assert mock_db_service.find_category_by_name.call_count == 10
        
        # Should insert all 10 categories
        assert mock_db_service.insert_category.call_count == 10
        
        # Verify some specific category calls
        expected_calls = [
            call("Writing & Content"),
            call("Image Generation"),
            call("Video & Animation"),
            call("Code & Development"),
            call("Data & Analytics"),
            call("Marketing & SEO"),
            call("Audio & Music"),
            call("Design & UI/UX"),
            call("Productivity"),
            call("Research & Learning")
        ]
        mock_db_service.find_category_by_name.assert_has_calls(expected_calls)

    @patch('app.database.seed.db_service')
    def test_seed_categories_all_exist(self, mock_db_service):
        """Test seeding when all categories already exist"""
        # Mock that all categories exist
        mock_category = Category(
            id=1, name="Existing Category", slug="existing-category",
            description="Already exists", display_order=1, is_featured=True,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        mock_db_service.find_category_by_name.return_value = mock_category
        
        seed_categories()
        
        # Should check for all 10 categories
        assert mock_db_service.find_category_by_name.call_count == 10
        
        # Should not insert any categories
        mock_db_service.insert_category.assert_not_called()

    @patch('app.database.seed.db_service')
    def test_seed_categories_mixed_existing_new(self, mock_db_service):
        """Test seeding with mix of existing and new categories"""
        # Mock that first 5 categories exist, next 5 don't
        def mock_find_category(name):
            existing_categories = [
                "Writing & Content", "Image Generation", "Video & Animation",
                "Code & Development", "Data & Analytics"
            ]
            if name in existing_categories:
                return Category(
                    id=1, name=name, slug="existing-slug",
                    description="Existing", display_order=1, is_featured=True,
                    created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
                )
            return None
        
        mock_db_service.find_category_by_name.side_effect = mock_find_category
        
        # Mock successful insertions for new categories
        mock_new_category = Category(
            id=2, name="New Category", slug="new-category",
            description="Newly created", display_order=1, is_featured=True,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        mock_db_service.insert_category.return_value = mock_new_category
        
        seed_categories()
        
        # Should check for all 10 categories
        assert mock_db_service.find_category_by_name.call_count == 10
        
        # Should insert only 5 new categories
        assert mock_db_service.insert_category.call_count == 5

    @patch('app.database.seed.db_service')
    def test_seed_categories_insert_failure(self, mock_db_service):
        """Test seeding when some insertions fail"""
        # Mock that no categories exist
        mock_db_service.find_category_by_name.return_value = None
        
        # Mock that insertions return None (failure)
        mock_db_service.insert_category.return_value = None
        
        # Should not raise exception, just log errors
        seed_categories()
        
        # Should still attempt all insertions
        assert mock_db_service.insert_category.call_count == 10

    @patch('app.database.seed.db_service')
    def test_seed_categories_exception_handling(self, mock_db_service):
        """Test seeding handles exceptions gracefully"""
        # Mock that checking for first category raises exception
        def mock_find_with_exception(name):
            if name == "Writing & Content":
                raise Exception("Database connection error")
            return None
        
        mock_db_service.find_category_by_name.side_effect = mock_find_with_exception
        mock_db_service.insert_category.return_value = Category(
            id=1, name="Test", slug="test", description="Test",
            display_order=1, is_featured=True,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        # Should not raise exception
        seed_categories()
        
        # Should continue with other categories (9 remaining)
        assert mock_db_service.insert_category.call_count == 9

    @patch('app.database.seed.logger')
    @patch('app.database.seed.db_service')
    def test_seed_categories_logging(self, mock_db_service, mock_logger):
        """Test that seeding logs appropriately"""
        # Mock mixed scenario
        call_count = 0
        def mock_find_category(name):
            nonlocal call_count
            call_count += 1
            if call_count <= 3:  # First 3 exist
                return Category(
                    id=1, name=name, slug="existing",
                    description="Existing", display_order=1, is_featured=True,
                    created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
                )
            return None
        
        mock_db_service.find_category_by_name.side_effect = mock_find_category
        mock_db_service.insert_category.return_value = Category(
            id=2, name="New", slug="new", description="New",
            display_order=1, is_featured=True,
            created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
        )
        
        seed_categories()
        
        # Should log start and completion
        mock_logger.info.assert_any_call("Starting category seeding...")
        mock_logger.info.assert_any_call("Category seeding completed")
        
        # Should log existing categories (3 times)
        existing_calls = [call for call in mock_logger.info.call_args_list 
                         if "already exists" in str(call)]
        assert len(existing_calls) == 3
        
        # Should log created categories (7 times)
        created_calls = [call for call in mock_logger.info.call_args_list 
                        if "Created category" in str(call)]
        assert len(created_calls) == 7

    def test_seed_categories_data_structure(self):
        """Test that all required category data is present"""
        with patch('app.database.seed.db_service') as mock_db_service:
            mock_db_service.find_category_by_name.return_value = None
            
            # Capture the CategoryCreate objects passed to insert_category
            insert_calls = []
            def capture_insert(category_create):
                insert_calls.append(category_create)
                return Category(
                    id=1, name=category_create.name, slug=category_create.slug,
                    description=category_create.description,
                    display_order=category_create.display_order,
                    is_featured=category_create.is_featured,
                    created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
                )
            
            mock_db_service.insert_category.side_effect = capture_insert
            
            seed_categories()
            
            assert len(insert_calls) == 10
            
            # Verify all categories have required fields
            expected_names = [
                "Writing & Content", "Image Generation", "Video & Animation",
                "Code & Development", "Data & Analytics", "Marketing & SEO",
                "Audio & Music", "Design & UI/UX", "Productivity", "Research & Learning"
            ]
            
            actual_names = [cat.name for cat in insert_calls]
            assert set(actual_names) == set(expected_names)
            
            # Verify all have required fields
            for category in insert_calls:
                assert isinstance(category, CategoryCreate)
                assert category.name
                assert category.slug
                assert category.description
                assert isinstance(category.display_order, int)
                assert isinstance(category.is_featured, bool)
                assert category.display_order > 0

    def test_seed_categories_order_consistency(self):
        """Test that categories are seeded in consistent order"""
        with patch('app.database.seed.db_service') as mock_db_service:
            mock_db_service.find_category_by_name.return_value = None
            
            insert_calls = []
            def capture_insert(category_create):
                insert_calls.append(category_create)
                return Category(
                    id=len(insert_calls), name=category_create.name,
                    slug=category_create.slug, description=category_create.description,
                    display_order=category_create.display_order,
                    is_featured=category_create.is_featured,
                    created_at="2023-01-01T00:00:00Z", updated_at="2023-01-01T00:00:00Z"
                )
            
            mock_db_service.insert_category.side_effect = capture_insert
            
            seed_categories()
            
            # Verify display_order is sequential
            display_orders = [cat.display_order for cat in insert_calls]
            assert display_orders == list(range(1, 11))
            
            # Verify first category is Writing & Content
            assert insert_calls[0].name == "Writing & Content"
            assert insert_calls[0].display_order == 1