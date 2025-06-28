"""
Tests for configuration management functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from retirement_planner.core.config import (
    UnifiedConfigLoader, ConfigLoader, BaseConfig, AppConfig, get_default_schema
)
from retirement_planner.core.exceptions import ConfigurationError


class TestUnifiedConfigLoader:
    """Test the unified configuration loader."""

    def test_unified_config_loader_creation(self):
        """Test creating a unified config loader."""
        loader = UnifiedConfigLoader()
        assert loader.config_data == {}
        assert loader.loaded_files == []

    def test_load_from_single_file(self):
        """Test loading from a single file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
person:
  name: "John Doe"
  age: 30
assets:
  - type: stock
    current_value: 100000
asset_performance:
  - type: stock
    expected_return: 0.07
    volatility: 0.15
            """)
            file_path = f.name

        try:
            loader = UnifiedConfigLoader()
            loader.load_from_file(file_path)

            assert loader.has_section('person')
            assert loader.has_section('assets')
            assert loader.has_section('asset_performance')
            assert len(loader.loaded_files) == 1
            assert file_path in loader.loaded_files

            person_data = loader.get_section('person')
            assert person_data['name'] == "John Doe"
            assert person_data['age'] == 30

        finally:
            os.unlink(file_path)

    def test_load_from_multiple_files(self):
        """Test loading from multiple files with section merging."""
        # Create first file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f1:
            f1.write("""
person:
  name: "John Doe"
  age: 30
assets:
  - type: stock
    current_value: 100000
            """)
            file_path1 = f1.name

        # Create second file that overrides some values
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f2:
            f2.write("""
person:
  age: 35  # Override age
  city: "New York"  # Add new field
asset_performance:
  - type: stock
    expected_return: 0.07
    volatility: 0.15
            """)
            file_path2 = f2.name

        try:
            loader = UnifiedConfigLoader()
            loader.load_from_files([file_path1, file_path2])

            # Check that sections are merged
            assert loader.has_section('person')
            assert loader.has_section('assets')
            assert loader.has_section('asset_performance')
            assert len(loader.loaded_files) == 2

            # Check that person data is merged correctly
            person_data = loader.get_section('person')
            assert person_data['name'] == "John Doe"  # From first file
            assert person_data['age'] == 35  # Overridden by second file
            assert person_data['city'] == "New York"  # Added by second file

        finally:
            os.unlink(file_path1)
            os.unlink(file_path2)

    def test_get_section(self):
        """Test getting specific sections."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
person:
  name: "John Doe"
assets:
  - type: stock
    current_value: 100000
            """)
            file_path = f.name

        try:
            loader = UnifiedConfigLoader()
            loader.load_from_file(file_path)

            person_section = loader.get_section('person')
            assert person_section['name'] == "John Doe"

            assets_section = loader.get_section('assets')
            assert len(assets_section) == 1
            assert assets_section[0]['type'] == 'stock'

            # Test non-existent section
            non_existent = loader.get_section('non_existent')
            assert non_existent == {}

        finally:
            os.unlink(file_path)

    def test_has_section(self):
        """Test checking if sections exist."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
person:
  name: "John Doe"
            """)
            file_path = f.name

        try:
            loader = UnifiedConfigLoader()
            loader.load_from_file(file_path)

            assert loader.has_section('person')
            assert not loader.has_section('non_existent')

        finally:
            os.unlink(file_path)

    def test_get_all_sections(self):
        """Test getting all sections."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
person:
  name: "John Doe"
assets:
  - type: stock
    current_value: 100000
            """)
            file_path = f.name

        try:
            loader = UnifiedConfigLoader()
            loader.load_from_file(file_path)

            all_sections = loader.get_all_sections()
            assert 'person' in all_sections
            assert 'assets' in all_sections
            assert len(all_sections) == 2

        finally:
            os.unlink(file_path)

    def test_save_to_file(self):
        """Test saving configuration to file."""
        config_data = {
            'person': {'name': 'John Doe', 'age': 30},
            'assets': [{'type': 'stock', 'current_value': 100000}]
        }

        loader = UnifiedConfigLoader()
        loader.config_data = config_data

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            file_path = f.name

        try:
            loader.save_to_file(file_path)

            # Load it back and verify
            new_loader = UnifiedConfigLoader()
            new_loader.load_from_file(file_path)

            assert new_loader.get_section('person') == config_data['person']
            assert new_loader.get_section('assets') == config_data['assets']

        finally:
            os.unlink(file_path)

    def test_invalid_file_type(self):
        """Test loading invalid file type."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("invalid content")
            file_path = f.name

        try:
            loader = UnifiedConfigLoader()
            with pytest.raises(ConfigurationError, match="Unsupported config file type"):
                loader.load_from_file(file_path)
        finally:
            os.unlink(file_path)

    def test_invalid_yaml_content(self):
        """Test loading invalid YAML content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            file_path = f.name

        try:
            loader = UnifiedConfigLoader()
            with pytest.raises(ConfigurationError):
                loader.load_from_file(file_path)
        finally:
            os.unlink(file_path)

    def test_non_dict_content(self):
        """Test loading non-dictionary content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("not a dictionary")
            file_path = f.name

        try:
            loader = UnifiedConfigLoader()
            with pytest.raises(ConfigurationError, match="Configuration file must contain a dictionary"):
                loader.load_from_file(file_path)
        finally:
            os.unlink(file_path)


class TestConfigLoader:
    """Test the legacy config loader for backward compatibility."""

    def test_legacy_config_loader(self):
        """Test that legacy config loader still works."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
app_name: "TestApp"
debug: true
log_level: "INFO"
            """)
            file_path = f.name

        try:
            loader = ConfigLoader()
            loader.load_from_file(file_path)

            assert loader.config_data['app_name'] == "TestApp"
            assert loader.config_data['debug'] is True
            assert loader.config_data['log_level'] == "INFO"

        finally:
            os.unlink(file_path)


class TestSchemaValidation:
    """Test schema validation functionality."""

    def test_validate_schema_with_valid_data(self):
        """Test schema validation with valid data."""
        schema = {
            "type": "object",
            "properties": {
                "person": {"type": "object"},
                "assets": {"type": "array"}
            },
            "required": ["person"]
        }

        config_data = {
            "person": {"name": "John"},
            "assets": []
        }

        loader = UnifiedConfigLoader(schema=schema)
        loader.config_data = config_data
        loader.validate_schema()  # Should not raise

    def test_validate_schema_with_invalid_data(self):
        """Test schema validation with invalid data."""
        schema = {
            "type": "object",
            "properties": {
                "person": {"type": "object"}
            },
            "required": ["person"]
        }

        config_data = {
            "person": "not an object"
        }

        loader = UnifiedConfigLoader(schema=schema)
        loader.config_data = config_data

        with pytest.raises(ConfigurationError):
            loader.validate_schema()

    def test_validate_schema_with_missing_required_field(self):
        """Test schema validation with missing required field."""
        schema = {
            "type": "object",
            "properties": {
                "person": {"type": "object"}
            },
            "required": ["person"]
        }

        config_data = {}

        loader = UnifiedConfigLoader(schema=schema)
        loader.config_data = config_data

        with pytest.raises(ConfigurationError):
            loader.validate_schema()

    def test_validate_schema_without_schema(self):
        """Test validation without schema (should not raise)."""
        loader = UnifiedConfigLoader()
        loader.config_data = {"any": "data"}
        loader.validate_schema()  # Should not raise

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

        # Valid enum value
        config_data = {"log_level": "INFO"}
        loader = UnifiedConfigLoader(schema=schema)
        loader.config_data = config_data
        loader.validate_schema()  # Should not raise

        # Invalid enum value
        config_data = {"log_level": "INVALID"}
        loader.config_data = config_data
        with pytest.raises(ConfigurationError):
            loader.validate_schema()


class TestDefaultSchema:
    """Test the default schema functionality."""

    def test_get_default_schema_structure(self):
        """Test that default schema has the expected structure."""
        schema = get_default_schema()

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "additionalProperties" in schema

        properties = schema["properties"]
        assert "person" in properties
        assert "assets" in properties
        assert "asset_performance" in properties
        assert "events" in properties
        assert "simulation" in properties
        assert "economy" in properties

    def test_default_schema_properties(self):
        """Test that default schema properties have correct types."""
        schema = get_default_schema()
        properties = schema["properties"]

        assert properties["person"]["type"] == "object"
        assert properties["assets"]["type"] == "array"
        assert properties["asset_performance"]["type"] == "array"
        assert properties["events"]["type"] == "object"
        assert properties["simulation"]["type"] == "object"
        assert properties["economy"]["type"] == "object"

    def test_default_schema_required_fields(self):
        """Test that default schema has no required fields (all optional)."""
        schema = get_default_schema()
        assert "required" not in schema

    def test_default_schema_with_valid_data(self):
        """Test default schema with valid data."""
        schema = get_default_schema()
        config_data = {
            "person": {"name": "John"},
            "assets": [],
            "asset_performance": [],
            "events": {},
            "simulation": {},
            "economy": {}
        }

        loader = UnifiedConfigLoader(schema=schema)
        loader.config_data = config_data
        loader.validate_schema()  # Should not raise

    def test_default_schema_with_invalid_data(self):
        """Test default schema with invalid data."""
        schema = get_default_schema()
        config_data = {
            "person": "not an object",
            "assets": "not an array"
        }

        loader = UnifiedConfigLoader(schema=schema)
        loader.config_data = config_data

        with pytest.raises(ConfigurationError):
            loader.validate_schema()


class TestConfigurationIntegration:
    """Test integration scenarios."""

    def test_complete_configuration_workflow(self):
        """Test a complete configuration workflow."""
        # Create a comprehensive configuration
        config_data = {
            "person": {
                "name": "Jane Doe",
                "age": 45,
                "retirement_age": 65,
                "life_expectancy": 90,
                "risk_tolerance": "moderate"
            },
            "assets": [
                {"type": "stock", "current_value": 500000},
                {"type": "bond", "current_value": 300000}
            ],
            "asset_performance": [
                {
                    "type": "stock",
                    "asset_type": "equity",
                    "expected_return": 0.07,
                    "volatility": 0.15
                },
                {
                    "type": "bond",
                    "asset_type": "bond",
                    "expected_return": 0.03,
                    "volatility": 0.05
                }
            ],
            "events": {
                "events": {
                    "income": [],
                    "expenses": []
                }
            },
            "simulation": {
                "num_scenarios": 1000,
                "time_horizon": 45
            },
            "economy": {
                "inflation": {"expected_rate": 0.025}
            }
        }

        # Test loading and validation
        schema = get_default_schema()
        loader = UnifiedConfigLoader(schema=schema)
        loader.config_data = config_data

        # Validate
        loader.validate_schema()

        # Test section access
        assert loader.has_section('person')
        assert loader.has_section('assets')
        assert loader.has_section('asset_performance')

        person_data = loader.get_section('person')
        assert person_data['name'] == "Jane Doe"
        assert person_data['age'] == 45

        assets_data = loader.get_section('assets')
        assert len(assets_data) == 2
        assert assets_data[0]['type'] == 'stock'
        assert assets_data[1]['type'] == 'bond'

    def test_configuration_with_nested_data(self):
        """Test configuration with nested data structures."""
        config_data = {
            "person": {
                "name": "John",
                "goals": [
                    {"name": "retirement", "target_amount": 1000000},
                    {"name": "vacation", "target_amount": 50000}
                ]
            },
            "simulation": {
                "portfolio": {
                    "rebalancing": {
                        "frequency": "annual",
                        "threshold": 0.05
                    }
                }
            }
        }

        loader = UnifiedConfigLoader()
        loader.config_data = config_data

        # Test nested access
        person_data = loader.get_section('person')
        assert len(person_data['goals']) == 2
        assert person_data['goals'][0]['name'] == 'retirement'

        simulation_data = loader.get_section('simulation')
        assert simulation_data['portfolio']['rebalancing']['frequency'] == 'annual'

    def test_configuration_error_context(self):
        """Test that configuration errors provide good context."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: [")
            file_path = f.name

        try:
            loader = UnifiedConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load_from_file(file_path)

            error = exc_info.value
            assert "Failed to load configuration file" in str(error)
            assert file_path in str(error)

        finally:
            os.unlink(file_path)