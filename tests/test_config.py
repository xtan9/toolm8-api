import pytest
import os
from unittest.mock import patch
from app.config import Settings, settings


class TestConfig:
    
    def test_settings_default_values(self):
        """Test that settings have default empty values"""
        with patch.dict(os.environ, {}, clear=True):
            test_settings = Settings()
            assert test_settings.SUPABASE_URL == ""
            assert test_settings.SUPABASE_ANON_KEY == ""
            assert test_settings.SUPABASE_JWT_SECRET == ""
            assert test_settings.DATABASE_URL == ""

    def test_settings_from_environment(self):
        """Test that settings are loaded from environment variables"""
        env_vars = {
            "SUPABASE_URL": "https://test-supabase.com",
            "SUPABASE_ANON_KEY": "test-anon-key",
            "SUPABASE_JWT_SECRET": "test-jwt-secret",
            "DATABASE_URL": "postgresql://test:test@localhost/test"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()
            assert test_settings.SUPABASE_URL == "https://test-supabase.com"
            assert test_settings.SUPABASE_ANON_KEY == "test-anon-key"
            assert test_settings.SUPABASE_JWT_SECRET == "test-jwt-secret"
            assert test_settings.DATABASE_URL == "postgresql://test:test@localhost/test"

    def test_settings_case_sensitivity(self):
        """Test that settings are case sensitive"""
        env_vars = {
            "supabase_url": "https://lowercase-supabase.com",  # lowercase
            "SUPABASE_URL": "https://uppercase-supabase.com"   # uppercase
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()
            # Should use uppercase version due to case sensitivity
            assert test_settings.SUPABASE_URL == "https://uppercase-supabase.com"

    def test_settings_partial_environment(self):
        """Test settings with only some environment variables set"""
        env_vars = {
            "SUPABASE_URL": "https://partial-supabase.com",
            "DATABASE_URL": "postgresql://partial:partial@localhost/partial"
            # SUPABASE_ANON_KEY and SUPABASE_JWT_SECRET not set
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()
            assert test_settings.SUPABASE_URL == "https://partial-supabase.com"
            assert test_settings.DATABASE_URL == "postgresql://partial:partial@localhost/partial"
            assert test_settings.SUPABASE_ANON_KEY == ""
            assert test_settings.SUPABASE_JWT_SECRET == ""

    def test_global_settings_instance(self):
        """Test that global settings instance exists"""
        assert settings is not None
        assert isinstance(settings, Settings)

    def test_settings_config_class(self):
        """Test Settings config class"""
        test_settings = Settings()
        assert hasattr(test_settings, 'Config')
        assert test_settings.Config.case_sensitive is True