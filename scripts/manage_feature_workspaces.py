"""Manage ephemeral Fabric workspaces for feature and bugfix branches."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

import yaml

from .common.logger import get_logger
from .fabric.config import CONFIG_FILE, EXIT_FAILURE, EXIT_SUCCESS, SEPARATOR_LONG, SEPARATOR_SHORT
from .fabric.fab_cli import FabCli, FabCliError

logger = get_logger(__name__)

FEATURE_CONFIG_FILE = "feature-workspaces.yml"
DEFAULT_BRANCH_SLUG_MAX_LENGTH = 40
WORKSPACE_LOOKUP_RETRIES = 6
WORKSPACE_LOOKUP_DELAY_SECONDS = 2.0
GIT_CONNECTION_RETRIES = 5
GIT_CONNECTION_DELAY_SECONDS = 2.0
UPDATE_OPERATION_RETRIES = 10
UPDATE_OPERATION_DELAY_SECONDS = 2.0


@dataclass(frozen=True)
class FeatureGitConfig:
    """Git integration settings for feature workspaces."""

    provider_type: str
    repository_owner: str
    repository_name: str
    connection_id: str | None = None
    connection_name: str | None = None


@dataclass(frozen=True)
class FeatureWorkspacePermission:
    """Workspace ACL assignment to apply after creation."""

    principal_id: str
    role: str


@dataclass(frozen=True)
class FeatureCleanupConfig:
    """Best-effort cleanup contract for ephemeral workspaces."""

    delete_on_pr_close: bool
    delete_on_branch_delete: bool


@dataclass(frozen=True)
class FeatureWorkspaceConfig:
    """Repository-level feature workspace lifecycle configuration."""

    branch_patterns: list[str]
    workspace_name_template: str
    capacity_id: str
    git: FeatureGitConfig
    permissions: list[FeatureWorkspacePermission]
    cleanup: FeatureCleanupConfig


@dataclass(frozen=True)
class FeatureWorkspaceTarget:
    """Opted-in workspace folder for feature lifecycle management."""

    workspace_folder: str
    config_path: Path

    @property
    def git_directory(self) -> str:
        return derive_git_directory(self.workspace_folder)


@dataclass(frozen=True)
class FeatureWorkspaceIdentity:
    """Branch-specific identity of one ephemeral workspace."""

    workspace_folder: str
    display_name: str
    branch_name: str
    branch_slug: str
    branch_hash: str
    branch_prefix: str
    git_directory: str


class FeatureWorkspaceManager:
    """Orchestrates create/delete/status flows through the Fabric CLI."""

    def __init__(self, cli: FabCli | None = None):
        self.cli = cli or FabCli()

    @staticmethod
    def _workspace_path(display_name: str) -> str:
        escaped = display_name.replace("/", "\\/")
        return f"'{escaped}.Workspace'"

    def workspace_exists(self, display_name: str) -> bool:
        result = self.cli.run_command(f"exists {self._workspace_path(display_name)}")
        return result.stdout.replace("*", "").strip().lower() == "true"

    def get_workspace_id(self, display_name: str) -> str:
        result = self.cli.run_command(f"get {self._workspace_path(display_name)} -q id")
        workspace_id = result.stdout.strip().strip('"')
        if not workspace_id:
            raise ValueError(f"Workspace '{display_name}' did not return a valid id")
        return workspace_id

    def create_workspace(self, display_name: str, capacity_name: str) -> None:
        self.cli.run_command(f"create {self._workspace_path(display_name)} -P capacityName={capacity_name}")

    def resolve_workspace_id(
        self,
        display_name: str,
        *,
        retries: int = WORKSPACE_LOOKUP_RETRIES,
        delay_seconds: float = WORKSPACE_LOOKUP_DELAY_SECONDS,
    ) -> str:
        """Resolve a workspace id by polling the CLI path lookup."""
        last_error: ValueError | None = None
        attempts = max(1, retries)
        for attempt in range(attempts):
            try:
                return self.get_workspace_id(display_name)
            except ValueError as exc:
                last_error = exc
                if attempt == attempts - 1:
                    break
                time.sleep(delay_seconds)

        assert last_error is not None
        raise last_error

    def delete_workspace(self, display_name: str) -> None:
        self.cli.run_command(f"rm {self._workspace_path(display_name)} -f")

    def set_workspace_permission(self, display_name: str, principal_id: str, role: str) -> None:
        self.cli.run_command(
            f"acl set {self._workspace_path(display_name)} -I {principal_id} -R {role.lower()} -f"
        )

    def resolve_connection_id(self, connection_name: str) -> str:
        result = self.cli.run_command(f"get .connections/{connection_name}.Connection -q id")
        return result.stdout.strip().strip('"')

    def wait_for_git_connection(
        self,
        workspace_id: str,
        *,
        retries: int = GIT_CONNECTION_RETRIES,
        delay_seconds: float = GIT_CONNECTION_DELAY_SECONDS,
    ) -> dict[str, Any] | None:
        for attempt in range(max(1, retries)):
            git_connection = self.get_git_connection(workspace_id)
            state = git_connection.get("gitConnectionState") if isinstance(git_connection, dict) else None
            if state != "NotConnected":
                return git_connection
            if attempt < retries - 1:
                time.sleep(delay_seconds)
        return None

    def poll_operation_status(
        self,
        operation_id: str,
        *,
        retries: int = UPDATE_OPERATION_RETRIES,
        delay_seconds: float = UPDATE_OPERATION_DELAY_SECONDS,
    ) -> dict[str, Any] | None:
        for attempt in range(max(1, retries)):
            response = self.cli.run_api_text(f"operations/{operation_id}")
            if not isinstance(response, dict):
                return None

            status = response.get("status")
            if status in {"NotStarted", "Running"}:
                if attempt < retries - 1:
                    time.sleep(delay_seconds)
                    continue
                return None
            if status == "Succeeded":
                return response
            return None
        return None

    def connect_workspace_to_git(
        self,
        workspace_id: str,
        git_config: FeatureGitConfig,
        branch_name: str,
        directory_name: str,
        connection_id: str,
    ) -> None:
        payload = {
            "gitProviderDetails": {
                "gitProviderType": git_config.provider_type,
                "ownerName": git_config.repository_owner,
                "repositoryName": git_config.repository_name,
                "branchName": branch_name,
                "directoryName": directory_name,
            },
            "myGitCredentials": {
                "source": "ConfiguredConnection",
                "connectionId": connection_id,
            },
        }
        self.cli.run_api(f"workspaces/{workspace_id}/git/connect", method="post", input_data=payload)
        return self.wait_for_git_connection(workspace_id)

    def initialize_workspace_from_git(self, workspace_id: str) -> dict[str, Any]:
        response = self.cli.run_api(f"workspaces/{workspace_id}/git/initializeConnection", method="post")
        payload = response["text"]
        return payload if isinstance(payload, dict) else {}

    def update_workspace_from_git(self, workspace_id: str, remote_commit_hash: str) -> dict[str, Any] | None:
        payload = {
            "remoteCommitHash": remote_commit_hash,
            "conflictResolution": {
                "conflictResolutionType": "Workspace",
                "conflictResolutionPolicy": "PreferRemote",
            },
            "options": {
                "allowOverrideItems": True,
            },
        }
        response = self.cli.run_api(
            f"workspaces/{workspace_id}/git/updateFromGit",
            method="post",
            input_data=payload,
            show_headers=True,
        )
        if response["status_code"] == 202:
            operation_id = response["headers"].get("x-ms-operation-id")
            if not operation_id:
                return None
            return self.poll_operation_status(operation_id)
        payload_response = response["text"]
        return payload_response if isinstance(payload_response, dict) else None

    def get_git_connection(self, workspace_id: str) -> dict[str, Any] | None:
        try:
            response = self.cli.run_api_text(f"workspaces/{workspace_id}/git/connection")
        except FabCliError:
            return None
        if response is None:
            return {}
        return response if isinstance(response, dict) else {}


def load_yaml_file(path: Path) -> dict[str, Any]:
    """Load a YAML file as a dictionary."""
    with path.open(encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected a mapping in {path}")
    return loaded


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def load_feature_workspace_config(config_path: Path) -> FeatureWorkspaceConfig:
    """Parse and validate the central feature workspace configuration file."""
    raw = load_yaml_file(config_path)

    git_raw = raw.get("git")
    if not isinstance(git_raw, dict):
        raise ValueError("feature-workspaces.yml is missing a valid 'git' section")

    repo_raw = git_raw.get("repository")
    if not isinstance(repo_raw, dict):
        raise ValueError("feature-workspaces.yml is missing git.repository.owner/name")

    branch_patterns = [str(pattern) for pattern in raw.get("branch_patterns") or [] if str(pattern).strip()]
    if not branch_patterns:
        raise ValueError("feature-workspaces.yml must define at least one branch pattern")

    connection_id = _optional_str(git_raw.get("connection_id"))
    connection_name = _optional_str(git_raw.get("connection_name"))
    if not connection_id and not connection_name:
        raise ValueError("feature-workspaces.yml git section must define connection_id or connection_name")

    permissions = [
        FeatureWorkspacePermission(
            principal_id=str(entry["principal_id"]).strip(),
            role=str(entry["role"]).strip(),
        )
        for entry in raw.get("permissions") or []
        if isinstance(entry, dict) and entry.get("principal_id") and entry.get("role")
    ]

    cleanup_raw = raw.get("cleanup") or {}
    if not isinstance(cleanup_raw, dict):
        raise ValueError("feature-workspaces.yml cleanup section must be a mapping")

    return FeatureWorkspaceConfig(
        branch_patterns=branch_patterns,
        workspace_name_template=str(raw["workspace_name_template"]).strip(),
        capacity_id=str(raw["capacity_id"]).strip(),
        git=FeatureGitConfig(
            provider_type=str(git_raw.get("provider_type", "GitHub")).strip(),
            repository_owner=str(repo_raw["owner"]).strip(),
            repository_name=str(repo_raw["name"]).strip(),
            connection_id=connection_id,
            connection_name=connection_name,
        ),
        permissions=permissions,
        cleanup=FeatureCleanupConfig(
            delete_on_pr_close=bool(cleanup_raw.get("delete_on_pr_close", True)),
            delete_on_branch_delete=bool(cleanup_raw.get("delete_on_branch_delete", True)),
        ),
    )


def is_feature_workspace_enabled(workspace_config: dict[str, Any]) -> bool:
    """Return True when feature_workspace.enabled is explicitly true."""
    raw_feature_config = workspace_config.get("feature_workspace")
    if not isinstance(raw_feature_config, dict):
        return False
    return bool(raw_feature_config.get("enabled", False))


def discover_feature_workspace_targets(workspaces_dir: Path) -> list[FeatureWorkspaceTarget]:
    """Discover workspace folders explicitly opted into the feature lifecycle."""
    if not workspaces_dir.is_dir():
        raise FileNotFoundError(f"Workspaces directory not found: {workspaces_dir}")

    targets: list[FeatureWorkspaceTarget] = []
    for workspace_path in sorted(workspaces_dir.iterdir()):
        config_path = workspace_path / CONFIG_FILE
        if not workspace_path.is_dir() or not config_path.exists():
            continue
        workspace_config = load_yaml_file(config_path)
        if is_feature_workspace_enabled(workspace_config):
            targets.append(FeatureWorkspaceTarget(workspace_folder=workspace_path.name, config_path=config_path))
    return targets


def derive_git_directory(workspace_folder: str) -> str:
    """Build the fixed Git directory for a workspace folder."""
    return f"workspaces/{workspace_folder}"


def strip_branch_ref(branch_ref: str) -> str:
    """Strip Git ref prefixes so naming uses the logical branch name."""
    if branch_ref.startswith("refs/heads/"):
        return branch_ref[len("refs/heads/") :]
    if branch_ref.startswith("refs/"):
        return branch_ref[len("refs/") :]
    return branch_ref


def sanitize_branch_name(branch_ref: str) -> str:
    """Normalize a branch name into a workspace-safe slug fragment."""
    candidate = strip_branch_ref(branch_ref).lower()
    candidate = re.sub(r"[^a-z0-9]+", "-", candidate)
    candidate = re.sub(r"-{2,}", "-", candidate).strip("-")
    return candidate or "branch"


def get_branch_prefix(branch_ref: str) -> str:
    """Return the display prefix for a supported branch family."""
    branch_name = strip_branch_ref(branch_ref).lower()
    if branch_name.startswith("feature/"):
        return "F"
    if branch_name.startswith("bugfix/"):
        return "B"
    return "X"


def build_feature_workspace_identity(
    workspace_folder: str,
    branch_ref: str,
    template: str,
    *,
    max_branch_slug_length: int = DEFAULT_BRANCH_SLUG_MAX_LENGTH,
) -> FeatureWorkspaceIdentity:
    """Compute the deterministic display name for one feature workspace."""
    branch_name = strip_branch_ref(branch_ref)
    branch_slug = sanitize_branch_name(branch_name)[:max_branch_slug_length].rstrip("-") or "branch"
    branch_hash = hashlib.sha256(branch_name.encode("utf-8")).hexdigest()[:8]
    branch_prefix = get_branch_prefix(branch_name)
    display_name = template.format(
        branch_prefix=branch_prefix,
        workspace_folder=workspace_folder,
        branch_slug=branch_slug,
        hash8=branch_hash,
    )
    return FeatureWorkspaceIdentity(
        workspace_folder=workspace_folder,
        display_name=display_name[:256],
        branch_name=branch_name,
        branch_slug=branch_slug,
        branch_hash=branch_hash,
        branch_prefix=branch_prefix,
        git_directory=derive_git_directory(workspace_folder),
    )


def branch_matches_patterns(branch_name: str, patterns: list[str]) -> bool:
    """Check whether a branch should participate in the feature lifecycle."""
    branch_name = strip_branch_ref(branch_name)
    return any(fnmatchcase(branch_name, pattern) for pattern in patterns)


def resolve_branch_name(
    *,
    branch: str | None,
    event_name: str | None,
    github_event_path: Path | None,
) -> str:
    """Resolve a branch name from explicit args or GitHub event payloads."""
    if branch:
        return strip_branch_ref(branch)

    if not event_name or not github_event_path:
        raise ValueError("Branch name was not provided and no GitHub event payload was available")

    with github_event_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    if event_name in {"create", "delete"}:
        ref = payload.get("ref")
        if isinstance(ref, str) and ref.strip():
            return strip_branch_ref(ref)
    if event_name == "pull_request":
        head_ref = payload.get("pull_request", {}).get("head", {}).get("ref")
        if isinstance(head_ref, str) and head_ref.strip():
            return strip_branch_ref(head_ref)

    raise ValueError(f"Could not resolve branch name for event '{event_name}' from {github_event_path}")


def create_feature_workspaces(
    manager: FeatureWorkspaceManager,
    feature_config: FeatureWorkspaceConfig,
    targets: list[FeatureWorkspaceTarget],
    branch_name: str,
) -> int:
    """Create and initialize all opted-in feature workspaces for a branch."""
    if not branch_matches_patterns(branch_name, feature_config.branch_patterns):
        logger.info("Branch '%s' does not match feature workspace patterns - nothing to create.", branch_name)
        return EXIT_SUCCESS

    if not targets:
        logger.info("No workspaces opted into feature_workspace.enabled - nothing to create.")
        return EXIT_SUCCESS

    connection_id = feature_config.git.connection_id
    if not connection_id and feature_config.git.connection_name:
        connection_id = manager.resolve_connection_id(feature_config.git.connection_name)

    assert connection_id is not None

    for target in targets:
        identity = build_feature_workspace_identity(
            workspace_folder=target.workspace_folder,
            branch_ref=branch_name,
            template=feature_config.workspace_name_template,
        )
        logger.info(SEPARATOR_SHORT)
        logger.info("Workspace folder: %s", target.workspace_folder)
        logger.info("Feature workspace: %s", identity.display_name)

        if manager.workspace_exists(identity.display_name):
            logger.info("-> Workspace already exists, skipping create.")
        else:
            logger.info("-> Creating workspace on capacity %s", feature_config.capacity_id)
            manager.create_workspace(identity.display_name, feature_config.capacity_id)

        workspace_id = manager.resolve_workspace_id(identity.display_name)

        for permission in feature_config.permissions:
            logger.info("-> Applying %s role to %s", permission.role, permission.principal_id)
            manager.set_workspace_permission(identity.display_name, permission.principal_id, permission.role)
        logger.info("-> Connecting workspace to Git branch '%s' in '%s'", identity.branch_name, identity.git_directory)
        git_connection = manager.connect_workspace_to_git(
            workspace_id=workspace_id,
            git_config=feature_config.git,
            branch_name=identity.branch_name,
            directory_name=identity.git_directory,
            connection_id=connection_id,
        )
        if not git_connection:
            raise ValueError(f"Workspace '{identity.display_name}' could not establish a Git connection")

        logger.info("-> Initializing workspace from Git")
        initialize_response = manager.initialize_workspace_from_git(workspace_id)
        remote_commit_hash = initialize_response.get("remoteCommitHash")
        if initialize_response.get("requiredAction") != "None" and remote_commit_hash:
            logger.info("-> Completing initial Git pull into workspace")
            manager.update_workspace_from_git(workspace_id, remote_commit_hash)

    return EXIT_SUCCESS


def delete_feature_workspaces(
    manager: FeatureWorkspaceManager,
    feature_config: FeatureWorkspaceConfig,
    targets: list[FeatureWorkspaceTarget],
    branch_name: str,
) -> int:
    """Delete all expected feature workspaces for a branch, idempotently."""
    if not branch_matches_patterns(branch_name, feature_config.branch_patterns):
        logger.info("Branch '%s' does not match feature workspace patterns - nothing to delete.", branch_name)
        return EXIT_SUCCESS

    if not targets:
        logger.info("No workspaces opted into feature_workspace.enabled - nothing to delete.")
        return EXIT_SUCCESS

    for target in targets:
        identity = build_feature_workspace_identity(
            workspace_folder=target.workspace_folder,
            branch_ref=branch_name,
            template=feature_config.workspace_name_template,
        )
        logger.info(SEPARATOR_SHORT)
        logger.info("Workspace folder: %s", target.workspace_folder)
        logger.info("Feature workspace: %s", identity.display_name)

        if not manager.workspace_exists(identity.display_name):
            logger.info("-> Workspace already absent, skipping delete.")
            continue

        logger.info("-> Deleting workspace")
        manager.delete_workspace(identity.display_name)

    return EXIT_SUCCESS


def get_feature_workspace_status(
    manager: FeatureWorkspaceManager,
    feature_config: FeatureWorkspaceConfig,
    targets: list[FeatureWorkspaceTarget],
    branch_name: str,
) -> list[dict[str, Any]]:
    """Return status data for all expected feature workspaces."""
    statuses: list[dict[str, Any]] = []
    for target in targets:
        identity = build_feature_workspace_identity(
            workspace_folder=target.workspace_folder,
            branch_ref=branch_name,
            template=feature_config.workspace_name_template,
        )
        exists = manager.workspace_exists(identity.display_name)
        status: dict[str, Any] = {
            "workspace_folder": target.workspace_folder,
            "display_name": identity.display_name,
            "exists": exists,
            "branch": identity.branch_name,
            "git_directory": identity.git_directory,
            "git_connected": False,
        }
        if exists:
            workspace_id = manager.get_workspace_id(identity.display_name)
            git_connection = manager.get_git_connection(workspace_id)
            status["git_connected"] = git_connection is not None
            status["git_connection"] = git_connection
        statuses.append(status)
    return statuses


def cleanup_enabled_for_event(feature_config: FeatureWorkspaceConfig, event_name: str | None) -> bool:
    """Check whether cleanup is enabled for the current GitHub event type."""
    if event_name == "pull_request":
        return feature_config.cleanup.delete_on_pr_close
    if event_name == "delete":
        return feature_config.cleanup.delete_on_branch_delete
    return True


def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for feature workspace lifecycle commands."""
    parser = argparse.ArgumentParser(description="Create, delete, or inspect Fabric feature workspaces.")
    parser.add_argument("command", choices=["create", "delete", "status"], help="Lifecycle operation to execute")
    parser.add_argument(
        "--workspaces_directory",
        type=str,
        required=True,
        help="Root directory containing workspace folders",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=FEATURE_CONFIG_FILE,
        help="Path to the feature workspace configuration file",
    )
    parser.add_argument("--branch", type=str, default=None, help="Branch name or ref to manage")
    parser.add_argument("--event-name", type=str, default=None, help="GitHub event name for payload-based branch resolution")
    parser.add_argument(
        "--github-event-path",
        type=str,
        default=None,
        help="Path to the GitHub event payload JSON file",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entrypoint for feature workspace lifecycle operations."""
    args = parse_cli_args(argv)

    logger.info(SEPARATOR_LONG)
    logger.info("FABRIC FEATURE WORKSPACE LIFECYCLE")
    logger.info(SEPARATOR_LONG)

    config_path = Path(args.config).resolve()
    workspaces_dir = Path(args.workspaces_directory).resolve()

    try:
        feature_config = load_feature_workspace_config(config_path)
        targets = discover_feature_workspace_targets(workspaces_dir)
        branch_name = resolve_branch_name(
            branch=args.branch,
            event_name=args.event_name,
            github_event_path=Path(args.github_event_path).resolve() if args.github_event_path else None,
        )
        manager = FeatureWorkspaceManager()

        if args.command == "create":
            return create_feature_workspaces(manager, feature_config, targets, branch_name)
        if args.command == "delete":
            if not cleanup_enabled_for_event(feature_config, args.event_name):
                logger.info("Cleanup is disabled for event '%s' - nothing to delete.", args.event_name)
                return EXIT_SUCCESS
            return delete_feature_workspaces(manager, feature_config, targets, branch_name)

        statuses = get_feature_workspace_status(manager, feature_config, targets, branch_name)
        logger.info(json.dumps(statuses, indent=2))
        return EXIT_SUCCESS

    except (FileNotFoundError, ValueError, FabCliError, json.JSONDecodeError, KeyError) as exc:
        logger.error("\n[FAIL] FEATURE WORKSPACE ERROR: %s\n", exc)
        return EXIT_FAILURE


if __name__ == "__main__":
    sys.exit(main())
