"""
Configuration management for the retirement planner package.

Provides type-safe configuration loading, schema validation, and environment variable overrides.
Supports unified configuration files with section merging from multiple files.
"""

import os
import yaml
import json
import dataclasses
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar, Union, List
from dataclasses import dataclass, field, asdict
from jsonschema import validate as jsonschema_validate, ValidationError as JsonSchemaValidationError
from .exceptions import ConfigurationError, create_configuration_error

T = TypeVar('T', bound='BaseConfig')

@dataclass
class BaseConfig:
    """
    Base class for configuration objects.
    Extend this for specific config sections.
    """
    # Example fields (extend as needed)
    # app_name: str = "RetirementPlanner"
    # debug: bool = False
    # ...

    def __post_init__(self):
        """Allow arbitrary keyword arguments by ignoring them."""
        pass

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create config object from dictionary."""
        # Filter out keys that don't match dataclass fields
        valid_fields = {field.name for field in dataclasses.fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config object to dictionary."""
        return asdict(self)

class UnifiedConfigLoader:
    """
    Loads and validates unified configuration from multiple YAML/JSON files with section merging.
    """
    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        self.schema = schema
        self.config_data: Dict[str, Any] = {}
        self.loaded_files: List[str] = []

    def load_from_files(self, file_paths: Union[str, Path, List[Union[str, Path]]]) -> None:
        """Load configuration from one or more YAML or JSON files with section merging."""
        if isinstance(file_paths, (str, Path)):
            file_paths = [file_paths]

        for file_path in file_paths:
            self.load_from_file(file_path)

    def load_from_file(self, file_path: Union[str, Path]) -> None:
        """Load configuration from a YAML or JSON file and merge with existing data."""
        file_path_str = str(file_path)

        try:
            with open(file_path_str, 'r') as f:
                if file_path_str.endswith('.yaml') or file_path_str.endswith('.yml'):
                    file_data = yaml.safe_load(f)
                elif file_path_str.endswith('.json'):
                    file_data = json.load(f)
                else:
                    raise ConfigurationError(f"Unsupported config file type: {file_path_str}")

                # Merge sections from this file
                self._merge_sections(file_data)
                self.loaded_files.append(file_path_str)

        except Exception as e:
            raise create_configuration_error(
                f"Failed to load configuration file: {file_path_str}",
                file_path=file_path_str,
                value=str(e)
            )

    def _merge_sections(self, new_data: Dict[str, Any]) -> None:
        """Merge sections from new data into existing config data."""
        if not isinstance(new_data, dict):
            raise ConfigurationError("Configuration file must contain a dictionary")

        for section, section_data in new_data.items():
            if section in self.config_data:
                # Merge existing section
                if isinstance(section_data, dict) and isinstance(self.config_data[section], dict):
                    self.config_data[section].update(section_data)
                elif isinstance(section_data, list) and isinstance(self.config_data[section], list):
                    # For lists, replace with new data (could be enhanced for more sophisticated merging)
                    self.config_data[section] = section_data
                else:
                    # Replace with new data
                    self.config_data[section] = section_data
            else:
                # Add new section
                self.config_data[section] = section_data

    def get_section(self, section_name: str) -> Dict[str, Any]:
        """Get a specific section from the configuration."""
        return self.config_data.get(section_name, {})

    def has_section(self, section_name: str) -> bool:
        """Check if a section exists in the configuration."""
        return section_name in self.config_data

    def get_all_sections(self) -> Dict[str, Any]:
        """Get all configuration sections."""
        return self.config_data.copy()

    def override_with_env(self, prefix: str = "RP_") -> None:
        """Override config values with environment variables (using prefix)."""
        for section_name, section_data in self.config_data.items():
            if isinstance(section_data, dict):
                for key in section_data:
                    env_key = f"{prefix}{section_name.upper()}_{key.upper()}"
                    if env_key in os.environ:
                        value = os.environ[env_key]
                        # Try to parse JSON for complex types, else use as string
                        try:
                            self.config_data[section_name][key] = json.loads(value)
                        except Exception:
                            self.config_data[section_name][key] = value

    def validate_schema(self) -> None:
        """Validate config data against the provided JSON schema."""
        if self.schema is None:
            return
        try:
            jsonschema_validate(instance=self.config_data, schema=self.schema)
        except JsonSchemaValidationError as e:
            raise create_configuration_error(
                "Configuration schema validation failed",
                value=self.config_data,
                field_name=str(e)
            )

    def get_config(self, config_class: Type[T]) -> T:
        """Return a type-safe config object."""
        return config_class.from_dict(self.config_data)

    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save the current configuration to a file."""
        file_path_str = str(file_path)

        try:
            with open(file_path_str, 'w') as f:
                if file_path_str.endswith('.yaml') or file_path_str.endswith('.yml'):
                    yaml.dump(self.config_data, f, default_flow_style=False, indent=2)
                elif file_path_str.endswith('.json'):
                    json.dump(self.config_data, f, indent=2)
                else:
                    raise ConfigurationError(f"Unsupported config file type: {file_path_str}")
        except Exception as e:
            raise create_configuration_error(
                f"Failed to save configuration file: {file_path_str}",
                file_path=file_path_str,
                value=str(e)
            )

# Legacy ConfigLoader for backward compatibility
class ConfigLoader(UnifiedConfigLoader):
    """
    Legacy configuration loader for backward compatibility.
    """
    def load_from_file(self, file_path: Union[str, Path]) -> None:
        """Load configuration from a single file (legacy behavior)."""
        super().load_from_file(file_path)

# Example default schema (extend as needed)
def get_default_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "person": {"type": "object"},
            "assets": {"type": "array"},
            "asset_performance": {"type": "array"},
            "events": {"type": "object"},
            "simulation": {"type": "object"},
            "economy": {"type": "object"},
        },
        "additionalProperties": True
    }

# Example default config dataclass (extend as needed)
@dataclass
class AppConfig(BaseConfig):
    app_name: str = "RetirementPlanner"
    debug: bool = False
    log_level: str = "INFO"