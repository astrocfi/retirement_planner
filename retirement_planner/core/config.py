"""
Configuration management for the retirement planner package.

Provides type-safe configuration loading, schema validation, and environment variable overrides.
"""

import os
import yaml
import json
import dataclasses
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar, Union
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

class ConfigLoader:
    """
    Loads and validates configuration from YAML/JSON files and environment variables.
    """
    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        self.schema = schema
        self.config_data: Dict[str, Any] = {}

    def load_from_file(self, file_path: Union[str, Path]) -> None:
        """Load configuration from a YAML or JSON file."""
        # Convert Path to string if needed
        file_path_str = str(file_path)

        try:
            with open(file_path_str, 'r') as f:
                if file_path_str.endswith('.yaml') or file_path_str.endswith('.yml'):
                    self.config_data = yaml.safe_load(f)
                elif file_path_str.endswith('.json'):
                    self.config_data = json.load(f)
                else:
                    raise ConfigurationError(f"Unsupported config file type: {file_path_str}")
        except Exception as e:
            raise create_configuration_error(
                f"Failed to load configuration file: {file_path_str}",
                file_path=file_path_str,
                value=str(e)
            )

    def override_with_env(self, prefix: str = "RP_") -> None:
        """Override config values with environment variables (using prefix)."""
        for key in self.config_data:
            env_key = f"{prefix}{key.upper()}"
            if env_key in os.environ:
                value = os.environ[env_key]
                # Try to parse JSON for complex types, else use as string
                try:
                    self.config_data[key] = json.loads(value)
                except Exception:
                    self.config_data[key] = value

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

# Example default schema (extend as needed)
def get_default_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "app_name": {"type": "string"},
            "debug": {"type": "boolean"},
            "log_level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
        },
        "required": ["app_name", "debug"],
        "additionalProperties": True
    }

# Example default config dataclass (extend as needed)
@dataclass
class AppConfig(BaseConfig):
    app_name: str = "RetirementPlanner"
    debug: bool = False
    log_level: str = "INFO"