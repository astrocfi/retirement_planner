"""
Unit tests for file_utils module.
"""

import pytest
import tempfile
import os
import json
import yaml
from pathlib import Path
from retirement_planner.utils.file_utils import (
    FileUtils, YamlLoader, JsonLoader, ConfigFileManager, FileInfo
)
from retirement_planner.core.exceptions import ValidationError, ConfigurationError


class TestFileUtils:
    """Test file utilities."""

    def test_ensure_directory_exists(self, tmp_path):
        """Test directory creation."""
        new_dir = tmp_path / "test_dir" / "subdir"
        FileUtils.ensure_directory_exists(str(new_dir))
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_get_file_info_existing(self, tmp_path):
        """Test file info for existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        file_info = FileUtils.get_file_info(str(test_file))

        assert file_info.path == str(test_file)
        assert file_info.size > 0
        assert file_info.modified_time > 0
        assert file_info.file_type == ".txt"
        assert file_info.exists is True

    def test_get_file_info_nonexistent(self, tmp_path):
        """Test file info for nonexistent file."""
        test_file = tmp_path / "nonexistent.txt"

        file_info = FileUtils.get_file_info(str(test_file))

        assert file_info.path == str(test_file)
        assert file_info.size == 0
        assert file_info.modified_time == 0
        assert file_info.file_type == ".txt"
        assert file_info.exists is False

    def test_is_file_readable(self, tmp_path):
        """Test file readability check."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        assert FileUtils.is_file_readable(str(test_file)) is True
        assert FileUtils.is_file_readable(str(tmp_path / "nonexistent.txt")) is False

    def test_is_file_writable(self, tmp_path):
        """Test file writability check."""
        test_file = tmp_path / "test.txt"

        # File doesn't exist, directory is writable
        assert FileUtils.is_file_writable(str(test_file)) is True

        # Create file and test
        test_file.write_text("test content")
        assert FileUtils.is_file_writable(str(test_file)) is True

    def test_backup_file(self, tmp_path):
        """Test file backup."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")

        backup_path = FileUtils.backup_file(str(test_file))

        assert Path(backup_path).exists()
        assert Path(backup_path).read_text() == "original content"
        assert backup_path != str(test_file)

    def test_backup_file_nonexistent(self, tmp_path):
        """Test backup of nonexistent file."""
        test_file = tmp_path / "nonexistent.txt"

        with pytest.raises(ValidationError):
            FileUtils.backup_file(str(test_file))

    def test_backup_file_multiple(self, tmp_path):
        """Test multiple backups of same file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")

        # Create first backup
        backup1 = FileUtils.backup_file(str(test_file))
        assert Path(backup1).exists()

        # Create second backup
        backup2 = FileUtils.backup_file(str(test_file))
        assert Path(backup2).exists()
        assert backup1 != backup2

    def test_safe_write_file(self, tmp_path):
        """Test safe file writing."""
        test_file = tmp_path / "test.txt"
        content = "test content"

        FileUtils.safe_write_file(str(test_file), content)

        assert test_file.exists()
        assert test_file.read_text() == content

    def test_safe_write_file_with_backup(self, tmp_path):
        """Test safe file writing with backup."""
        test_file = tmp_path / "test.txt"
        original_content = "original content"
        new_content = "new content"

        # Create original file
        test_file.write_text(original_content)

        # Write new content with backup
        FileUtils.safe_write_file(str(test_file), new_content, backup=True)

        assert test_file.read_text() == new_content

        # Check backup exists
        backup_files = list(tmp_path.glob("test.txt.backup*"))
        assert len(backup_files) > 0
        assert backup_files[0].read_text() == original_content

    def test_read_file_safe(self, tmp_path):
        """Test safe file reading."""
        test_file = tmp_path / "test.txt"
        content = "test content"
        test_file.write_text(content)

        result = FileUtils.read_file_safe(str(test_file))
        assert result == content

    def test_read_file_safe_nonexistent(self, tmp_path):
        """Test safe file reading of nonexistent file."""
        test_file = tmp_path / "nonexistent.txt"

        with pytest.raises(ValidationError):
            FileUtils.read_file_safe(str(test_file))

    def test_get_file_extension(self):
        """Test file extension extraction."""
        assert FileUtils.get_file_extension("test.txt") == ".txt"
        assert FileUtils.get_file_extension("config.yaml") == ".yaml"
        assert FileUtils.get_file_extension("data.json") == ".json"
        assert FileUtils.get_file_extension("no_extension") == ""
        assert FileUtils.get_file_extension(".hidden") == ".hidden"

    def test_is_valid_file_path(self):
        """Test file path validation."""
        assert FileUtils.is_valid_file_path("test.txt") is True
        assert FileUtils.is_valid_file_path("/path/to/file.txt") is True
        assert FileUtils.is_valid_file_path("") is True  # Empty path is valid
        assert FileUtils.is_valid_file_path("file with spaces.txt") is True


class TestYamlLoader:
    """Test YAML loading utilities."""

    def test_load_yaml_valid(self, tmp_path):
        """Test loading valid YAML file."""
        yaml_content = """
        name: test
        value: 42
        items:
          - item1
          - item2
        """
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        data = YamlLoader.load_yaml(str(yaml_file))

        assert data["name"] == "test"
        assert data["value"] == 42
        assert data["items"] == ["item1", "item2"]

    def test_load_yaml_invalid_extension(self, tmp_path):
        """Test loading YAML with invalid extension."""
        yaml_file = tmp_path / "test.txt"
        yaml_file.write_text("name: test")

        with pytest.raises(ValidationError):
            YamlLoader.load_yaml(str(yaml_file))

    def test_load_yaml_invalid_content(self, tmp_path):
        """Test loading invalid YAML content."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("invalid: yaml: content: [")

        with pytest.raises(ConfigurationError):
            YamlLoader.load_yaml(str(yaml_file))

    def test_save_yaml(self, tmp_path):
        """Test saving YAML file."""
        data = {"name": "test", "value": 42, "items": ["item1", "item2"]}
        yaml_file = tmp_path / "test.yaml"

        YamlLoader.save_yaml(data, str(yaml_file))

        assert yaml_file.exists()
        loaded_data = yaml.safe_load(yaml_file.read_text())
        assert loaded_data == data

    def test_save_yaml_invalid_path(self):
        """Test saving YAML with invalid path."""
        data = {"name": "test"}

        with pytest.raises(ConfigurationError):
            YamlLoader.save_yaml(data, "/invalid/path/test.yaml")

    def test_validate_yaml_structure(self):
        """Test YAML structure validation."""
        data = {"name": "test", "value": 42}
        required_keys = ["name", "value"]

        assert YamlLoader.validate_yaml_structure(data, required_keys) is True

        # Missing key
        assert YamlLoader.validate_yaml_structure(data, ["name", "value", "missing"]) is False

        # Not a dict
        assert YamlLoader.validate_yaml_structure("not a dict", required_keys) is False

    def test_merge_yaml_files(self, tmp_path):
        """Test merging YAML files."""
        yaml1_content = "name: test1\nvalue1: 42"
        yaml2_content = "name: test2\nvalue2: 84"

        yaml1_file = tmp_path / "test1.yaml"
        yaml2_file = tmp_path / "test2.yaml"

        yaml1_file.write_text(yaml1_content)
        yaml2_file.write_text(yaml2_content)

        merged = YamlLoader.merge_yaml_files([str(yaml1_file), str(yaml2_file)])

        # Second file should override first file's 'name'
        assert merged["name"] == "test2"
        assert merged["value1"] == 42
        assert merged["value2"] == 84


class TestJsonLoader:
    """Test JSON loading utilities."""

    def test_load_json_valid(self, tmp_path):
        """Test loading valid JSON file."""
        json_content = '{"name": "test", "value": 42, "items": ["item1", "item2"]}'
        json_file = tmp_path / "test.json"
        json_file.write_text(json_content)

        data = JsonLoader.load_json(str(json_file))

        assert data["name"] == "test"
        assert data["value"] == 42
        assert data["items"] == ["item1", "item2"]

    def test_load_json_invalid_extension(self, tmp_path):
        """Test loading JSON with invalid extension."""
        json_file = tmp_path / "test.txt"
        json_file.write_text('{"name": "test"}')

        with pytest.raises(ValidationError):
            JsonLoader.load_json(str(json_file))

    def test_load_json_invalid_content(self, tmp_path):
        """Test loading invalid JSON content."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"name": "test", "value": [}')

        with pytest.raises(ConfigurationError):
            JsonLoader.load_json(str(json_file))

    def test_save_json(self, tmp_path):
        """Test saving JSON file."""
        data = {"name": "test", "value": 42, "items": ["item1", "item2"]}
        json_file = tmp_path / "test.json"

        JsonLoader.save_json(data, str(json_file))

        assert json_file.exists()
        loaded_data = json.loads(json_file.read_text())
        assert loaded_data == data

    def test_save_json_with_options(self, tmp_path):
        """Test saving JSON with options."""
        data = {"b": 2, "a": 1}
        json_file = tmp_path / "test.json"

        JsonLoader.save_json(data, str(json_file), indent=4, sort_keys=True)

        content = json_file.read_text()
        # Should be sorted and indented
        assert '"a"' in content
        assert '"b"' in content
        assert content.count('    ') > 0  # Indentation

    def test_validate_json_structure(self):
        """Test JSON structure validation."""
        data = {"name": "test", "value": 42}
        required_keys = ["name", "value"]

        assert JsonLoader.validate_json_structure(data, required_keys) is True

        # Missing key
        assert JsonLoader.validate_json_structure(data, ["name", "value", "missing"]) is False

        # Not a dict
        assert JsonLoader.validate_json_structure("not a dict", required_keys) is False

    def test_merge_json_files(self, tmp_path):
        """Test merging JSON files."""
        json1_content = '{"name": "test1", "value1": 42}'
        json2_content = '{"name": "test2", "value2": 84}'

        json1_file = tmp_path / "test1.json"
        json2_file = tmp_path / "test2.json"

        json1_file.write_text(json1_content)
        json2_file.write_text(json2_content)

        merged = JsonLoader.merge_json_files([str(json1_file), str(json2_file)])

        # Second file should override first file's 'name'
        assert merged["name"] == "test2"
        assert merged["value1"] == 42
        assert merged["value2"] == 84

    def test_pretty_print_json(self):
        """Test JSON pretty printing."""
        data = {"name": "test", "value": 42, "items": ["item1", "item2"]}

        pretty = JsonLoader.pretty_print_json(data, indent=2)

        assert '"name"' in pretty
        assert '"value"' in pretty
        assert '"items"' in pretty
        assert pretty.count('  ') > 0  # Indentation


class TestConfigFileManager:
    """Test configuration file manager."""

    def test_load_config_file_yaml(self, tmp_path):
        """Test loading YAML config file."""
        yaml_content = "name: test\nvalue: 42"
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml_content)

        data = ConfigFileManager.load_config_file(str(config_file))

        assert data["name"] == "test"
        assert data["value"] == 42

    def test_load_config_file_json(self, tmp_path):
        """Test loading JSON config file."""
        json_content = '{"name": "test", "value": 42}'
        config_file = tmp_path / "config.json"
        config_file.write_text(json_content)

        data = ConfigFileManager.load_config_file(str(config_file))

        assert data["name"] == "test"
        assert data["value"] == 42

    def test_load_config_file_unsupported(self, tmp_path):
        """Test loading unsupported config file."""
        config_file = tmp_path / "config.txt"
        config_file.write_text("some content")

        with pytest.raises(ValidationError):
            ConfigFileManager.load_config_file(str(config_file))

    def test_save_config_file_yaml(self, tmp_path):
        """Test saving YAML config file."""
        data = {"name": "test", "value": 42}
        config_file = tmp_path / "config.yaml"

        ConfigFileManager.save_config_file(data, str(config_file))

        assert config_file.exists()
        loaded_data = yaml.safe_load(config_file.read_text())
        assert loaded_data == data

    def test_save_config_file_json(self, tmp_path):
        """Test saving JSON config file."""
        data = {"name": "test", "value": 42}
        config_file = tmp_path / "config.json"

        ConfigFileManager.save_config_file(data, str(config_file))

        assert config_file.exists()
        loaded_data = json.loads(config_file.read_text())
        assert loaded_data == data

    def test_find_config_files(self, tmp_path):
        """Test finding config files."""
        # Create various config files
        (tmp_path / "config1.yaml").write_text("name: test1")
        (tmp_path / "config2.yml").write_text("name: test2")
        (tmp_path / "config3.json").write_text('{"name": "test3"}')
        (tmp_path / "other.txt").write_text("not a config file")

        config_files = ConfigFileManager.find_config_files(str(tmp_path))

        assert len(config_files) == 3
        assert any("config1.yaml" in f for f in config_files)
        assert any("config2.yml" in f for f in config_files)
        assert any("config3.json" in f for f in config_files)
        assert not any("other.txt" in f for f in config_files)

    def test_find_config_files_custom_patterns(self, tmp_path):
        """Test finding config files with custom patterns."""
        (tmp_path / "config.yaml").write_text("name: test")
        (tmp_path / "config.json").write_text('{"name": "test"}')
        (tmp_path / "config.xml").write_text("<config>test</config>")

        # Only YAML files
        yaml_files = ConfigFileManager.find_config_files(str(tmp_path), ["*.yaml", "*.yml"])
        assert len(yaml_files) == 1
        assert "config.yaml" in yaml_files[0]

        # Only XML files
        xml_files = ConfigFileManager.find_config_files(str(tmp_path), ["*.xml"])
        assert len(xml_files) == 1
        assert "config.xml" in xml_files[0]

    def test_validate_config_file(self, tmp_path):
        """Test config file validation."""
        config_content = '{"name": "test", "value": 42}'
        config_file = tmp_path / "config.json"
        config_file.write_text(config_content)

        schema = {"name": str, "value": int}

        assert ConfigFileManager.validate_config_file(str(config_file), schema) is True

        # Invalid schema
        invalid_schema = {"name": str, "value": str}  # value should be int
        assert ConfigFileManager.validate_config_file(str(config_file), invalid_schema) is False

    def test_validate_config_data(self):
        """Test config data validation."""
        data = {"name": "test", "value": 42}
        schema = {"name": str, "value": int}

        assert ConfigFileManager.validate_config_data(data, schema) is True

        # Missing key
        assert ConfigFileManager.validate_config_data(data, {"name": str, "missing": int}) is False

        # Wrong type
        assert ConfigFileManager.validate_config_data(data, {"name": str, "value": str}) is False