# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Core tests for deploy_to_fabric.py deployment logic."""

import pytest

from scripts.deploy_to_fabric import (
    DeploymentResult,
    DeploymentSummary,
    discover_workspace_folders,
    get_workspace_name_from_config,
    load_workspace_config,
)


class TestLoadWorkspaceConfig:
    """Test suite for load_workspace_config function."""

    def test_load_valid_config(self, temp_workspace_dir):
        """Test loading a valid config.yml file."""
        workspace_folder = "Test Workspace"
        config = load_workspace_config(workspace_folder, str(temp_workspace_dir))

        assert config is not None
        assert "core" in config
        assert "workspace" in config["core"]

    def test_load_config_missing_file(self, tmp_path):
        """Test loading config from non-existent workspace."""
        with pytest.raises(FileNotFoundError):
            load_workspace_config("NonExistent", str(tmp_path))


class TestDiscoverWorkspaceFolders:
    """Test suite for discover_workspace_folders function."""

    def test_discover_workspace_with_config(self, temp_workspace_dir):
        """Test discovering workspace folders that have config.yml."""
        workspaces = discover_workspace_folders(str(temp_workspace_dir))

        assert len(workspaces) > 0
        assert "Test Workspace" in workspaces

    def test_discover_no_workspaces(self, tmp_path):
        """Test discovering workspaces when none exist."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(ValueError, match="No workspace folders with 'config.yml' found"):
            discover_workspace_folders(str(empty_dir))


class TestGetWorkspaceNameFromConfig:
    """Test suite for get_workspace_name_from_config function."""

    def test_get_workspace_name_dev(self, sample_workspace_config):
        """Test getting workspace name for dev environment."""
        name = get_workspace_name_from_config(sample_workspace_config, "dev")
        assert name == "[D] Test Workspace"

    def test_get_workspace_name_test(self, sample_workspace_config):
        """Test getting workspace name for test environment."""
        name = get_workspace_name_from_config(sample_workspace_config, "test")
        assert name == "[T] Test Workspace"

    def test_get_workspace_name_prod(self, sample_workspace_config):
        """Test getting workspace name for prod environment."""
        name = get_workspace_name_from_config(sample_workspace_config, "prod")
        assert name == "[P] Test Workspace"

    def test_get_workspace_name_missing_environment(self, sample_workspace_config):
        """Test getting workspace name for undefined environment."""
        # Remove 'test' from config
        del sample_workspace_config["core"]["workspace"]["test"]

        with pytest.raises(KeyError):
            get_workspace_name_from_config(sample_workspace_config, "test")

    def test_get_workspace_name_invalid_config(self):
        """Test getting workspace name with invalid config structure."""
        invalid_config = {"invalid": "structure"}

        with pytest.raises(KeyError):
            get_workspace_name_from_config(invalid_config, "dev")


class TestDeploymentModels:
    """Test suite for deployment dataclass behavior."""

    def test_deployment_summary_properties(self):
        """Test DeploymentSummary calculated properties."""
        results = [
            DeploymentResult("WS1", "[D] WS1", True),
            DeploymentResult("WS2", "[D] WS2", True),
            DeploymentResult("WS3", "[D] WS3", False, "Error"),
        ]

        summary = DeploymentSummary(environment="dev", duration=120.5, results=results)

        assert summary.total_workspaces == 3
        assert summary.successful_count == 2
        assert summary.failed_count == 1

        assert summary.results[2].error_message == "Error"
