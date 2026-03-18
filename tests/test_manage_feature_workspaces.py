"""Tests for feature workspace lifecycle orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts.manage_feature_workspaces import (
    FeatureCleanupConfig,
    FeatureGitConfig,
    FeatureWorkspaceConfig,
    FeatureWorkspaceManager,
    FeatureWorkspacePermission,
    build_feature_workspace_identity,
    branch_matches_patterns,
    create_feature_workspaces,
    delete_feature_workspaces,
    derive_git_directory,
    discover_feature_workspace_targets,
    get_branch_prefix,
    is_feature_workspace_enabled,
    load_feature_workspace_config,
    resolve_branch_name,
)


@pytest.fixture
def feature_config_file(tmp_path: Path) -> Path:
    path = tmp_path / "feature-workspaces.yml"
    path.write_text(
        """
branch_patterns:
  - "feature/**"
  - "bugfix/**"
workspace_name_template: "[{branch_prefix}] {workspace_folder} ({branch_slug}-{hash8})"
capacity_id: "MyCapacity"
git:
  provider_type: "GitHub"
  repository:
    owner: "contoso"
    name: "dc-fabric-cicd"
  connection_name: "shared-github"
permissions:
  - principal_id: "22222222-2222-2222-2222-222222222222"
    role: "Contributor"
cleanup:
  delete_on_pr_close: true
  delete_on_branch_delete: true
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return path


def _create_workspace_config(path: Path, enabled: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""
core:
  workspace:
    dev: "[D] {path.parent.name}"
feature_workspace:
  enabled: {"true" if enabled else "false"}
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _sample_feature_config() -> FeatureWorkspaceConfig:
    return FeatureWorkspaceConfig(
        branch_patterns=["feature/**", "bugfix/**"],
        workspace_name_template="[{branch_prefix}] {workspace_folder} ({branch_slug}-{hash8})",
        capacity_id="MyCapacity",
        git=FeatureGitConfig(
            provider_type="GitHub",
            repository_owner="contoso",
            repository_name="dc-fabric-cicd",
            connection_name="shared-github",
        ),
        permissions=[],
        cleanup=FeatureCleanupConfig(delete_on_pr_close=True, delete_on_branch_delete=True),
    )


def _sample_feature_config_with_permissions() -> FeatureWorkspaceConfig:
    return FeatureWorkspaceConfig(
        branch_patterns=["feature/**", "bugfix/**"],
        workspace_name_template="[{branch_prefix}] {workspace_folder} ({branch_slug}-{hash8})",
        capacity_id="MyCapacity",
        git=FeatureGitConfig(
            provider_type="GitHub",
            repository_owner="contoso",
            repository_name="dc-fabric-cicd",
            connection_name="shared-github",
        ),
        permissions=[
            FeatureWorkspacePermission(
                principal_id="22222222-2222-2222-2222-222222222222",
                role="Admin",
            )
        ],
        cleanup=FeatureCleanupConfig(delete_on_pr_close=True, delete_on_branch_delete=True),
    )


def test_load_feature_workspace_config(feature_config_file: Path) -> None:
    config = load_feature_workspace_config(feature_config_file)

    assert config.branch_patterns == ["feature/**", "bugfix/**"]
    assert config.workspace_name_template == "[{branch_prefix}] {workspace_folder} ({branch_slug}-{hash8})"
    assert config.capacity_id == "MyCapacity"
    assert config.git.repository_owner == "contoso"
    assert config.git.repository_name == "dc-fabric-cicd"
    assert config.git.connection_name == "shared-github"
    assert config.permissions[0].role == "Contributor"
    assert config.cleanup.delete_on_pr_close is True


def test_build_feature_workspace_identity_normalizes_branch_name() -> None:
    identity = build_feature_workspace_identity(
        workspace_folder="Fabric Blueprint",
        branch_ref="refs/heads/feature/My Big_Thing",
        template="[{branch_prefix}] {workspace_folder} ({branch_slug}-{hash8})",
    )

    assert identity.branch_name == "feature/My Big_Thing"
    assert identity.branch_slug == "feature-my-big-thing"
    assert identity.branch_prefix == "F"
    assert identity.display_name.startswith("[F] Fabric Blueprint (feature-my-big-thing-")
    assert len(identity.branch_hash) == 8


def test_build_feature_workspace_identity_uses_bugfix_prefix() -> None:
    identity = build_feature_workspace_identity(
        workspace_folder="Fabric Blueprint",
        branch_ref="refs/heads/bugfix/fix-thing",
        template="[{branch_prefix}] {workspace_folder} ({branch_slug}-{hash8})",
    )

    assert identity.branch_prefix == "B"
    assert identity.display_name.startswith("[B] Fabric Blueprint (bugfix-fix-thing-")


def test_get_branch_prefix_returns_expected_values() -> None:
    assert get_branch_prefix("feature/new-thing") == "F"
    assert get_branch_prefix("bugfix/fix-thing") == "B"
    assert get_branch_prefix("chore/other") == "X"


def test_discover_feature_workspace_targets_only_returns_opted_in_workspaces(tmp_path: Path) -> None:
    workspaces_dir = tmp_path / "workspaces"
    _create_workspace_config(workspaces_dir / "Enabled Workspace" / "config.yml", enabled=True)
    _create_workspace_config(workspaces_dir / "Disabled Workspace" / "config.yml", enabled=False)
    (workspaces_dir / "No Config").mkdir(parents=True)

    targets = discover_feature_workspace_targets(workspaces_dir)

    assert [target.workspace_folder for target in targets] == ["Enabled Workspace"]


def test_is_feature_workspace_enabled_defaults_to_false() -> None:
    assert is_feature_workspace_enabled({}) is False
    assert is_feature_workspace_enabled({"feature_workspace": {"enabled": False}}) is False
    assert is_feature_workspace_enabled({"feature_workspace": {"enabled": True}}) is True


def test_derive_git_directory_uses_fixed_workspace_path() -> None:
    assert derive_git_directory("Fabric Blueprint") == "workspaces/Fabric Blueprint"


def test_branch_matches_patterns() -> None:
    assert branch_matches_patterns("feature/my-change", ["feature/**", "bugfix/**"]) is True
    assert branch_matches_patterns("bugfix/my-change", ["feature/**", "bugfix/**"]) is True
    assert branch_matches_patterns("main", ["feature/**", "bugfix/**"]) is False


def test_resolve_branch_name_for_delete_event(tmp_path: Path) -> None:
    event_path = tmp_path / "delete.json"
    event_path.write_text(json.dumps({"ref": "feature/example-branch"}), encoding="utf-8")

    branch = resolve_branch_name(branch=None, event_name="delete", github_event_path=event_path)

    assert branch == "feature/example-branch"


def test_resolve_branch_name_for_pull_request_closed_event(tmp_path: Path) -> None:
    event_path = tmp_path / "pr.json"
    event_path.write_text(
        json.dumps({"pull_request": {"head": {"ref": "bugfix/fix-a-thing"}}}),
        encoding="utf-8",
    )

    branch = resolve_branch_name(branch=None, event_name="pull_request", github_event_path=event_path)

    assert branch == "bugfix/fix-a-thing"


def test_workspace_path_quotes_and_escapes_slashes() -> None:
    assert FeatureWorkspaceManager._workspace_path("Folder/Sub Name") == "'Folder\\/Sub Name.Workspace'"


def test_create_feature_workspaces_constructs_expected_calls() -> None:
    manager = Mock(spec=FeatureWorkspaceManager)
    manager.resolve_connection_id.return_value = "33333333-3333-3333-3333-333333333333"
    manager.workspace_exists.return_value = False
    manager.resolve_workspace_id.return_value = "44444444-4444-4444-4444-444444444444"
    manager.connect_workspace_to_git.return_value = {"gitConnectionState": "ConnectedAndInitialized"}
    manager.initialize_workspace_from_git.return_value = {
        "requiredAction": "UpdateFromGit",
        "remoteCommitHash": "remote-hash",
    }
    targets = [Mock(workspace_folder="Fabric Blueprint", git_directory="workspaces/Fabric Blueprint")]
    identity = build_feature_workspace_identity(
        workspace_folder="Fabric Blueprint",
        branch_ref="feature/new-thing",
        template="[{branch_prefix}] {workspace_folder} ({branch_slug}-{hash8})",
    )

    exit_code = create_feature_workspaces(manager, _sample_feature_config(), targets, "feature/new-thing")

    assert exit_code == 0
    manager.create_workspace.assert_called_once_with(identity.display_name, "MyCapacity")
    manager.resolve_workspace_id.assert_called_once_with(identity.display_name)
    manager.connect_workspace_to_git.assert_called_once()
    _, kwargs = manager.connect_workspace_to_git.call_args
    assert kwargs["branch_name"] == "feature/new-thing"
    assert kwargs["directory_name"] == "workspaces/Fabric Blueprint"
    manager.update_workspace_from_git.assert_called_once_with("44444444-4444-4444-4444-444444444444", "remote-hash")


def test_create_feature_workspaces_is_idempotent_when_workspace_exists() -> None:
    manager = Mock(spec=FeatureWorkspaceManager)
    manager.resolve_connection_id.return_value = "33333333-3333-3333-3333-333333333333"
    manager.workspace_exists.return_value = True
    manager.resolve_workspace_id.return_value = "44444444-4444-4444-4444-444444444444"
    manager.connect_workspace_to_git.return_value = {"gitConnectionState": "ConnectedAndInitialized"}
    manager.initialize_workspace_from_git.return_value = {"requiredAction": "None"}
    targets = [Mock(workspace_folder="Fabric Blueprint", git_directory="workspaces/Fabric Blueprint")]
    identity = build_feature_workspace_identity(
        workspace_folder="Fabric Blueprint",
        branch_ref="feature/new-thing",
        template="[{branch_prefix}] {workspace_folder} ({branch_slug}-{hash8})",
    )

    exit_code = create_feature_workspaces(manager, _sample_feature_config(), targets, "feature/new-thing")

    assert exit_code == 0
    manager.create_workspace.assert_not_called()
    manager.resolve_workspace_id.assert_called_once_with(identity.display_name)


def test_create_feature_workspaces_applies_permissions_by_workspace_path() -> None:
    manager = Mock(spec=FeatureWorkspaceManager)
    manager.resolve_connection_id.return_value = "33333333-3333-3333-3333-333333333333"
    manager.workspace_exists.return_value = True
    manager.resolve_workspace_id.return_value = "44444444-4444-4444-4444-444444444444"
    manager.connect_workspace_to_git.return_value = {"gitConnectionState": "ConnectedAndInitialized"}
    manager.initialize_workspace_from_git.return_value = {"requiredAction": "None"}
    targets = [Mock(workspace_folder="Fabric Blueprint", git_directory="workspaces/Fabric Blueprint")]
    identity = build_feature_workspace_identity(
        workspace_folder="Fabric Blueprint",
        branch_ref="feature/new-thing",
        template="[{branch_prefix}] {workspace_folder} ({branch_slug}-{hash8})",
    )

    exit_code = create_feature_workspaces(
        manager,
        _sample_feature_config_with_permissions(),
        targets,
        "feature/new-thing",
    )

    assert exit_code == 0
    manager.set_workspace_permission.assert_called_once_with(
        identity.display_name,
        "22222222-2222-2222-2222-222222222222",
        "Admin",
    )


def test_create_feature_workspaces_raises_when_git_connection_never_establishes() -> None:
    manager = Mock(spec=FeatureWorkspaceManager)
    manager.resolve_connection_id.return_value = "33333333-3333-3333-3333-333333333333"
    manager.workspace_exists.return_value = True
    manager.resolve_workspace_id.return_value = "44444444-4444-4444-4444-444444444444"
    manager.connect_workspace_to_git.return_value = None
    targets = [Mock(workspace_folder="Fabric Blueprint", git_directory="workspaces/Fabric Blueprint")]

    with pytest.raises(ValueError, match="could not establish a Git connection"):
        create_feature_workspaces(manager, _sample_feature_config(), targets, "feature/new-thing")


def test_delete_feature_workspaces_is_idempotent_when_workspace_missing() -> None:
    manager = Mock(spec=FeatureWorkspaceManager)
    manager.workspace_exists.return_value = False
    targets = [Mock(workspace_folder="Fabric Blueprint")]

    exit_code = delete_feature_workspaces(manager, _sample_feature_config(), targets, "feature/new-thing")

    assert exit_code == 0
    manager.delete_workspace.assert_not_called()


def test_delete_feature_workspaces_deletes_by_workspace_path() -> None:
    manager = Mock(spec=FeatureWorkspaceManager)
    manager.workspace_exists.return_value = True
    targets = [Mock(workspace_folder="Fabric Blueprint")]
    identity = build_feature_workspace_identity(
        workspace_folder="Fabric Blueprint",
        branch_ref="feature/new-thing",
        template="[{branch_prefix}] {workspace_folder} ({branch_slug}-{hash8})",
    )

    exit_code = delete_feature_workspaces(manager, _sample_feature_config(), targets, "feature/new-thing")

    assert exit_code == 0
    manager.delete_workspace.assert_called_once_with(identity.display_name)
