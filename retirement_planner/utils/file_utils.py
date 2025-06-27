"""
File utilities for retirement planning.

This module provides file I/O and configuration file handling utilities
for the retirement planning system.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from retirement_planner.core.validation import Validator, RequiredRule
from retirement_planner.core.exceptions import ValidationError, ConfigurationError


@dataclass(frozen=True)
class FileInfo:
    """Information about a file."""
    path: str
    size: int
    modified_time: float
    file_type: str
    exists: bool


class FileUtils:
    """General file I/O utilities."""

    @staticmethod
    def ensure_directory_exists(directory_path: str) -> None:
        """
        Ensure directory exists, create if it doesn't.

        Args:
            directory_path: Path to directory
        """
        Path(directory_path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_file_info(file_path: str) -> FileInfo:
        """
        Get information about a file.

        Args:
            file_path: Path to file

        Returns:
            File information
        """
        path = Path(file_path)
        exists = path.exists()

        if exists:
            stat = path.stat()
            return FileInfo(
                path=str(path),
                size=stat.st_size,
                modified_time=stat.st_mtime,
                file_type=path.suffix.lower(),
                exists=True
            )
        else:
            return FileInfo(
                path=str(path),
                size=0,
                modified_time=0,
                file_type=path.suffix.lower(),
                exists=False
            )

    @staticmethod
    def is_file_readable(file_path: str) -> bool:
        """
        Check if file is readable.

        Args:
            file_path: Path to file

        Returns:
            True if file is readable
        """
        path = Path(file_path)
        return path.exists() and path.is_file() and os.access(path, os.R_OK)

    @staticmethod
    def is_file_writable(file_path: str) -> bool:
        """
        Check if file is writable.

        Args:
            file_path: Path to file

        Returns:
            True if file is writable
        """
        path = Path(file_path)
        directory = path.parent

        # Check if directory is writable
        if not os.access(directory, os.W_OK):
            return False

        # If file exists, check if it's writable
        if path.exists():
            return os.access(path, os.W_OK)

        # If file doesn't exist, directory must be writable
        return True

    @staticmethod
    def backup_file(file_path: str, backup_suffix: str = ".backup") -> str:
        """
        Create a backup of a file.

        Args:
            file_path: Path to file to backup
            backup_suffix: Suffix for backup file

        Returns:
            Path to backup file
        """
        path = Path(file_path)
        if not path.exists():
            raise ValidationError(f"File does not exist: {file_path}")

        backup_path = str(path) + backup_suffix
        backup_counter = 1

        # Find unique backup name
        while Path(backup_path).exists():
            backup_path = f"{str(path)}{backup_suffix}.{backup_counter}"
            backup_counter += 1

        # Copy file
        import shutil
        shutil.copy2(file_path, backup_path)

        return backup_path

    @staticmethod
    def safe_write_file(file_path: str, content: str, backup: bool = True) -> None:
        """
        Safely write content to file with optional backup.

        Args:
            file_path: Path to file
            content: Content to write
            backup: Whether to create backup before writing
        """
        path = Path(file_path)

        # Create backup if requested and file exists
        if backup and path.exists():
            FileUtils.backup_file(file_path)

        # Ensure directory exists
        FileUtils.ensure_directory_exists(str(path.parent))

        # Write content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    @staticmethod
    def read_file_safe(file_path: str, encoding: str = 'utf-8') -> str:
        """
        Safely read file content.

        Args:
            file_path: Path to file
            encoding: File encoding

        Returns:
            File content
        """
        if not FileUtils.is_file_readable(file_path):
            raise ValidationError(f"File is not readable: {file_path}")

        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()

    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """
        Get file extension.

        Args:
            file_path: Path to file

        Returns:
            File extension (lowercase)
        """
        path = Path(file_path)
        name = path.name
        if name.startswith('.') and '.' not in name[1:]:
            return name  # e.g., '.hidden'
        return path.suffix.lower()

    @staticmethod
    def is_valid_file_path(file_path: str) -> bool:
        """
        Check if file path is valid.

        Args:
            file_path: Path to check

        Returns:
            True if path is valid
        """
        try:
            Path(file_path)
            return True
        except (ValueError, OSError):
            return False


class YamlLoader:
    """YAML file loading utilities."""

    @staticmethod
    def load_yaml(file_path: str) -> Dict[str, Any]:
        """
        Load YAML file and return dictionary.

        Args:
            file_path: Path to YAML file

        Returns:
            Dictionary from YAML content
        """
        if not FileUtils.is_file_readable(file_path):
            raise ValidationError(f"YAML file is not readable: {file_path}")

        if FileUtils.get_file_extension(file_path) not in ['.yaml', '.yml']:
            raise ValidationError(f"File does not have YAML extension: {file_path}")

        try:
            content = FileUtils.read_file_safe(file_path)
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse YAML file {file_path}: {str(e)}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load YAML file {file_path}: {str(e)}")

    @staticmethod
    def save_yaml(data: Dict[str, Any], file_path: str,
                  default_flow_style: bool = False) -> None:
        """
        Save dictionary to YAML file.

        Args:
            data: Data to save
            file_path: Path to YAML file
            default_flow_style: YAML flow style setting
        """
        if not FileUtils.is_valid_file_path(file_path):
            raise ValidationError(f"Invalid file path: {file_path}")

        try:
            content = yaml.dump(data, default_flow_style=default_flow_style,
                              sort_keys=False, allow_unicode=True)
            FileUtils.safe_write_file(file_path, content)
        except Exception as e:
            raise ConfigurationError(f"Failed to save YAML file {file_path}: {str(e)}")

    @staticmethod
    def validate_yaml_structure(data: Dict[str, Any],
                               required_keys: List[str]) -> bool:
        """
        Validate YAML structure has required keys.

        Args:
            data: YAML data
            required_keys: List of required keys

        Returns:
            True if structure is valid
        """
        if not isinstance(data, dict):
            return False

        for key in required_keys:
            if key not in data:
                return False

        return True

    @staticmethod
    def merge_yaml_files(file_paths: List[str]) -> Dict[str, Any]:
        """
        Merge multiple YAML files.

        Args:
            file_paths: List of YAML file paths

        Returns:
            Merged dictionary
        """
        merged_data = {}

        for file_path in file_paths:
            data = YamlLoader.load_yaml(file_path)
            merged_data.update(data)

        return merged_data


class JsonLoader:
    """JSON file loading utilities."""

    @staticmethod
    def load_json(file_path: str) -> Dict[str, Any]:
        """
        Load JSON file and return dictionary.

        Args:
            file_path: Path to JSON file

        Returns:
            Dictionary from JSON content
        """
        if not FileUtils.is_file_readable(file_path):
            raise ValidationError(f"JSON file is not readable: {file_path}")

        if FileUtils.get_file_extension(file_path) != '.json':
            raise ValidationError(f"File does not have JSON extension: {file_path}")

        try:
            content = FileUtils.read_file_safe(file_path)
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Failed to parse JSON file {file_path}: {str(e)}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load JSON file {file_path}: {str(e)}")

    @staticmethod
    def save_json(data: Dict[str, Any], file_path: str,
                  indent: int = 2, sort_keys: bool = False) -> None:
        """
        Save dictionary to JSON file.

        Args:
            data: Data to save
            file_path: Path to JSON file
            indent: JSON indentation
            sort_keys: Whether to sort keys
        """
        if not FileUtils.is_valid_file_path(file_path):
            raise ValidationError(f"Invalid file path: {file_path}")

        try:
            content = json.dumps(data, indent=indent, sort_keys=sort_keys,
                               ensure_ascii=False)
            FileUtils.safe_write_file(file_path, content)
        except Exception as e:
            raise ConfigurationError(f"Failed to save JSON file {file_path}: {str(e)}")

    @staticmethod
    def validate_json_structure(data: Dict[str, Any],
                               required_keys: List[str]) -> bool:
        """
        Validate JSON structure has required keys.

        Args:
            data: JSON data
            required_keys: List of required keys

        Returns:
            True if structure is valid
        """
        if not isinstance(data, dict):
            return False

        for key in required_keys:
            if key not in data:
                return False

        return True

    @staticmethod
    def merge_json_files(file_paths: List[str]) -> Dict[str, Any]:
        """
        Merge multiple JSON files.

        Args:
            file_paths: List of JSON file paths

        Returns:
            Merged dictionary
        """
        merged_data = {}

        for file_path in file_paths:
            data = JsonLoader.load_json(file_path)
            merged_data.update(data)

        return merged_data

    @staticmethod
    def pretty_print_json(data: Dict[str, Any], indent: int = 2) -> str:
        """
        Pretty print JSON data.

        Args:
            data: Data to print
            indent: Indentation level

        Returns:
            Pretty-printed JSON string
        """
        return json.dumps(data, indent=indent, sort_keys=False, ensure_ascii=False)


class ConfigFileManager:
    """Configuration file management utilities."""

    @staticmethod
    def load_config_file(file_path: str) -> Dict[str, Any]:
        """
        Load configuration file (YAML or JSON).

        Args:
            file_path: Path to configuration file

        Returns:
            Configuration dictionary
        """
        extension = FileUtils.get_file_extension(file_path)

        if extension in ['.yaml', '.yml']:
            return YamlLoader.load_yaml(file_path)
        elif extension == '.json':
            return JsonLoader.load_json(file_path)
        else:
            raise ValidationError(f"Unsupported configuration file type: {extension}")

    @staticmethod
    def save_config_file(data: Dict[str, Any], file_path: str) -> None:
        """
        Save configuration file (YAML or JSON).

        Args:
            data: Configuration data
            file_path: Path to configuration file
        """
        extension = FileUtils.get_file_extension(file_path)

        if extension in ['.yaml', '.yml']:
            YamlLoader.save_yaml(data, file_path)
        elif extension == '.json':
            JsonLoader.save_json(data, file_path)
        else:
            raise ValidationError(f"Unsupported configuration file type: {extension}")

    @staticmethod
    def find_config_files(directory: str, patterns: List[str] = None) -> List[str]:
        """
        Find configuration files in directory.

        Args:
            directory: Directory to search
            patterns: File patterns to match (default: yaml, yml, json)

        Returns:
            List of configuration file paths
        """
        if patterns is None:
            patterns = ['*.yaml', '*.yml', '*.json']

        config_files = []
        directory_path = Path(directory)

        if not directory_path.exists():
            return config_files

        for pattern in patterns:
            config_files.extend([str(f) for f in directory_path.glob(pattern)])

        return sorted(config_files)

    @staticmethod
    def validate_config_file(file_path: str, schema: Dict[str, Any]) -> bool:
        """
        Validate configuration file against schema.

        Args:
            file_path: Path to configuration file
            schema: Schema to validate against

        Returns:
            True if configuration is valid
        """
        try:
            config_data = ConfigFileManager.load_config_file(file_path)
            return ConfigFileManager.validate_config_data(config_data, schema)
        except Exception:
            return False

    @staticmethod
    def validate_config_data(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        Validate configuration data against schema.

        Args:
            data: Configuration data
            schema: Schema to validate against

        Returns:
            True if data is valid
        """
        # Simple schema validation - can be enhanced with JSON Schema
        for key, value_type in schema.items():
            if key not in data:
                return False

            if not isinstance(data[key], value_type):
                return False

        return True