"""
Unit tests for retirement planner configuration management.

These tests verify the configuration loading, validation, and type-safe
access functionality work correctly.
"""

import pytest
import tempfile
import os
import json
from retirement_planner.core.config import (
    BaseConfig,
    ConfigLoader,
    AppConfig,
    get_default_schema,
)
from retirement_planner.core.exceptions import ConfigurationError


class TestBaseConfig:
    """Test BaseConfig functionality."""

    def test_base_config_creation(self):
        """Test creating a BaseConfig instance."""
        config = BaseConfig()
        assert isinstance(config, BaseConfig)

    def test_base_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {"app_name": "TestApp", "debug": True}
        config = BaseConfig.from_dict(data)
        assert isinstance(config, BaseConfig)

    def test_base_config_to_dict(self):
        """Test converting config to dictionary."""
        config = BaseConfig()
        result = config.to_dict()
        assert isinstance(result, dict)


class TestAppConfig:
    """Test AppConfig functionality."""

    def test_app_config_default_values(self):
        """Test AppConfig with default values."""
        config = AppConfig()
        assert config.app_name == "RetirementPlanner"
        assert config.debug is False
        assert config.log_level == "INFO"

    def test_app_config_custom_values(self):
        """Test AppConfig with custom values."""
        config = AppConfig(
            app_name="CustomApp",
            debug=True,
            log_level="DEBUG"
        )
        assert config.app_name == "CustomApp"
        assert config.debug is True
        assert config.log_level == "DEBUG"

    def test_app_config_from_dict(self):
        """Test creating AppConfig from dictionary."""
        data = {
            "app_name": "TestApp",
            "debug": True,
            "log_level": "WARNING"
        }
        config = AppConfig.from_dict(data)
        assert config.app_name == "TestApp"
        assert config.debug is True
        assert config.log_level == "WARNING"

    def test_app_config_to_dict(self):
        """Test converting AppConfig to dictionary."""
        config = AppConfig(app_name="TestApp", debug=True)
        result = config.to_dict()
        assert result["app_name"] == "TestApp"
        assert result["debug"] is True
        assert result["log_level"] == "INFO"  # Default value


class TestConfigLoader:
    """Test ConfigLoader functionality."""

    def test_config_loader_creation(self):
        """Test creating ConfigLoader with and without schema."""
        # Without schema
        loader = ConfigLoader()
        assert loader.schema is None
        assert loader.config_data == {}

        # With schema
        schema = {"type": "object"}
        loader = ConfigLoader(schema)
        assert loader.schema == schema

    def test_load_from_yaml_file(self):
        """Test loading configuration from YAML file."""
        loader = ConfigLoader()

        # Create temporary YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("app_name: TestApp\ndebug: true\nlog_level: DEBUG")
            yaml_file = f.name

        try:
            loader.load_from_file(yaml_file)
            assert loader.config_data["app_name"] == "TestApp"
            assert loader.config_data["debug"] is True
            assert loader.config_data["log_level"] == "DEBUG"
        finally:
            os.unlink(yaml_file)

    def test_load_from_json_file(self):
        """Test loading configuration from JSON file."""
        loader = ConfigLoader()

        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "app_name": "TestApp",
                "debug": True,
                "log_level": "DEBUG"
            }, f)
            json_file = f.name

        try:
            loader.load_from_file(json_file)
            assert loader.config_data["app_name"] == "TestApp"
            assert loader.config_data["debug"] is True
            assert loader.config_data["log_level"] == "DEBUG"
        finally:
            os.unlink(json_file)

    def test_load_from_path_object(self):
        """Test loading configuration from Path object."""
        from pathlib import Path

        loader = ConfigLoader()

        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "app_name": "TestApp",
                "debug": True,
                "log_level": "DEBUG"
            }, f)
            json_file = f.name

        try:
            # Test with Path object
            path = Path(json_file)
            loader.load_from_file(path)
            assert loader.config_data["app_name"] == "TestApp"
            assert loader.config_data["debug"] is True
            assert loader.config_data["log_level"] == "DEBUG"
        finally:
            os.unlink(json_file)

    def test_load_from_unsupported_file_type(self):
        """Test loading from unsupported file type raises error."""
        loader = ConfigLoader()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("some content")
            txt_file = f.name

        try:
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load_from_file(txt_file)
            assert "Unsupported config file type" in str(exc_info.value)
        finally:
            os.unlink(txt_file)

    def test_load_from_nonexistent_file(self):
        """Test loading from nonexistent file raises error."""
        loader = ConfigLoader()

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load_from_file("nonexistent_file.yaml")
        assert "Failed to load configuration file" in str(exc_info.value)

    def test_override_with_env_variables(self):
        """Test overriding config with environment variables."""
        loader = ConfigLoader()
        loader.config_data = {
            "app_name": "DefaultApp",
            "debug": False,
            "log_level": "INFO"
        }

        # Set environment variables
        os.environ["RP_APP_NAME"] = "EnvApp"
        os.environ["RP_DEBUG"] = "true"
        os.environ["RP_LOG_LEVEL"] = "DEBUG"

        try:
            loader.override_with_env()
            assert loader.config_data["app_name"] == "EnvApp"
            assert loader.config_data["debug"] is True
            assert loader.config_data["log_level"] == "DEBUG"
        finally:
            # Clean up environment variables
            del os.environ["RP_APP_NAME"]
            del os.environ["RP_DEBUG"]
            del os.environ["RP_LOG_LEVEL"]

    def test_override_with_env_json_values(self):
        """Test overriding config with JSON environment variables."""
        loader = ConfigLoader()
        loader.config_data = {
            "settings": {"default": "value"}
        }

        # Set JSON environment variable
        os.environ["RP_SETTINGS"] = '{"env": "value"}'

        try:
            loader.override_with_env()
            assert loader.config_data["settings"] == {"env": "value"}
        finally:
            del os.environ["RP_SETTINGS"]

    def test_override_with_env_custom_prefix(self):
        """Test overriding config with custom environment variable prefix."""
        loader = ConfigLoader()
        loader.config_data = {
            "app_name": "DefaultApp"
        }

        # Set environment variable with custom prefix
        os.environ["CUSTOM_APP_NAME"] = "CustomApp"

        try:
            loader.override_with_env(prefix="CUSTOM_")
            assert loader.config_data["app_name"] == "CustomApp"
        finally:
            del os.environ["CUSTOM_APP_NAME"]

    def test_get_config_type_safe(self):
        """Test getting type-safe config object."""
        loader = ConfigLoader()
        loader.config_data = {
            "app_name": "TestApp",
            "debug": True,
            "log_level": "DEBUG"
        }

        config = loader.get_config(AppConfig)
        assert isinstance(config, AppConfig)
        assert config.app_name == "TestApp"
        assert config.debug is True
        assert config.log_level == "DEBUG"


class TestSchemaValidation:
    """Test schema validation functionality."""

    def test_validate_schema_with_valid_data(self):
        """Test schema validation with valid data."""
        schema = {
            "type": "object",
            "properties": {
                "app_name": {"type": "string"},
                "debug": {"type": "boolean"}
            },
            "required": ["app_name", "debug"]
        }

        loader = ConfigLoader(schema)
        loader.config_data = {
            "app_name": "TestApp",
            "debug": True
        }

        # Should not raise an exception
        loader.validate_schema()

    def test_validate_schema_with_invalid_data(self):
        """Test schema validation with invalid data."""
        schema = {
            "type": "object",
            "properties": {
                "app_name": {"type": "string"},
                "debug": {"type": "boolean"}
            },
            "required": ["app_name", "debug"]
        }

        loader = ConfigLoader(schema)
        loader.config_data = {
            "app_name": 123,  # Should be string
            "debug": True
        }

        with pytest.raises(ConfigurationError) as exc_info:
            loader.validate_schema()
        assert "Configuration schema validation failed" in str(exc_info.value)

    def test_validate_schema_with_missing_required_field(self):
        """Test schema validation with missing required field."""
        schema = {
            "type": "object",
            "properties": {
                "app_name": {"type": "string"},
                "debug": {"type": "boolean"}
            },
            "required": ["app_name", "debug"]
        }

        loader = ConfigLoader(schema)
        loader.config_data = {
            "app_name": "TestApp"
            # Missing "debug" field
        }

        with pytest.raises(ConfigurationError) as exc_info:
            loader.validate_schema()
        assert "Configuration schema validation failed" in str(exc_info.value)

    def test_validate_schema_without_schema(self):
        """Test schema validation when no schema is provided."""
        loader = ConfigLoader()  # No schema
        loader.config_data = {"any": "data"}

        # Should not raise an exception
        loader.validate_schema()

    def test_validate_schema_with_enum_constraint(self):
        """Test schema validation with enum constraint."""
        schema = {
            "type": "object",
            "properties": {
                "log_level": {
                    "type": "string",
                    "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]
                }
            }
        }

        loader = ConfigLoader(schema)

        # Valid enum value
        loader.config_data = {"log_level": "DEBUG"}
        loader.validate_schema()  # Should not raise

        # Invalid enum value
        loader.config_data = {"log_level": "INVALID"}
        with pytest.raises(ConfigurationError):
            loader.validate_schema()


class TestDefaultSchema:
    """Test the default schema functionality."""

    def test_get_default_schema_structure(self):
        """Test that default schema has expected structure."""
        schema = get_default_schema()

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema
        assert "additionalProperties" in schema

    def test_default_schema_properties(self):
        """Test that default schema has expected properties."""
        schema = get_default_schema()
        properties = schema["properties"]

        assert "app_name" in properties
        assert properties["app_name"]["type"] == "string"

        assert "debug" in properties
        assert properties["debug"]["type"] == "boolean"

        assert "log_level" in properties
        assert properties["log_level"]["type"] == "string"
        assert "enum" in properties["log_level"]

    def test_default_schema_required_fields(self):
        """Test that default schema has expected required fields."""
        schema = get_default_schema()
        required = schema["required"]

        assert "app_name" in required
        assert "debug" in required

    def test_default_schema_with_valid_data(self):
        """Test default schema validation with valid data."""
        schema = get_default_schema()
        loader = ConfigLoader(schema)

        loader.config_data = {
            "app_name": "TestApp",
            "debug": True,
            "log_level": "INFO"
        }

        loader.validate_schema()  # Should not raise

    def test_default_schema_with_invalid_data(self):
        """Test default schema validation with invalid data."""
        schema = get_default_schema()
        loader = ConfigLoader(schema)

        loader.config_data = {
            "app_name": 123,  # Should be string
            "debug": True
        }

        with pytest.raises(ConfigurationError):
            loader.validate_schema()


class TestConfigurationIntegration:
    """Test integration scenarios for configuration management."""

    def test_complete_configuration_workflow(self):
        """Test complete configuration loading and validation workflow."""
        # Create temporary YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
app_name: TestApp
debug: true
log_level: DEBUG
""")
            yaml_file = f.name

        try:
            # Load configuration
            schema = get_default_schema()
            loader = ConfigLoader(schema)
            loader.load_from_file(yaml_file)

            # Override with environment variables
            os.environ["RP_LOG_LEVEL"] = "WARNING"
            try:
                loader.override_with_env()

                # Validate schema
                loader.validate_schema()

                # Get type-safe config
                config = loader.get_config(AppConfig)

                assert config.app_name == "TestApp"
                assert config.debug is True
                assert config.log_level == "WARNING"  # Overridden by env var

            finally:
                del os.environ["RP_LOG_LEVEL"]
        finally:
            os.unlink(yaml_file)

    def test_configuration_with_nested_data(self):
        """Test configuration with nested data structures."""
        loader = ConfigLoader()

        # Create temporary JSON file with nested data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "app_name": "TestApp",
                "settings": {
                    "database": {
                        "host": "localhost",
                        "port": 5432
                    },
                    "cache": {
                        "enabled": True,
                        "ttl": 3600
                    }
                }
            }, f)
            json_file = f.name

        try:
            loader.load_from_file(json_file)

            assert loader.config_data["app_name"] == "TestApp"
            assert loader.config_data["settings"]["database"]["host"] == "localhost"
            assert loader.config_data["settings"]["database"]["port"] == 5432
            assert loader.config_data["settings"]["cache"]["enabled"] is True
            assert loader.config_data["settings"]["cache"]["ttl"] == 3600
        finally:
            os.unlink(json_file)

    def test_configuration_error_context(self):
        """Test that configuration errors include proper context."""
        loader = ConfigLoader()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            yaml_file = f.name

        try:
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load_from_file(yaml_file)

            error = exc_info.value
            assert "Failed to load configuration file" in str(error)
            assert error.context.file_path == yaml_file
        finally:
            os.unlink(yaml_file)