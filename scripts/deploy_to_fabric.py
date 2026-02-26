# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Deploy workspaces to Fabric via GitHub Actions with continue-on-failure support"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import yaml
from fabric_cicd import append_feature_flag, change_log_level, deploy_with_config  # type: ignore[import-untyped]

# Import local modules using relative imports
from .common.logger import get_logger
from .fabric.auth import CredentialType, create_azure_credential
from .fabric.config import (
    CONFIG_FILE,
    ENV_ACTIONS_RUNNER_DEBUG,
    EXIT_FAILURE,
    EXIT_SUCCESS,
    RESULTS_FILENAME,
    SEPARATOR_LONG,
    SEPARATOR_SHORT,
    VALID_ENVIRONMENTS,
)
from .fabric.reporting import build_deployment_results_json, print_deployment_summary
from .fabric.types import DeploymentResult, DeploymentSummary

# Initialize logger
logger = get_logger(__name__)


def load_workspace_config(workspace_folder: str, workspaces_dir: str) -> dict[str, Any]:
    """Load config.yml for a workspace.

    Args:
        workspace_folder: Name of workspace folder
        workspaces_dir: Root workspaces directory

    Returns:
        Parsed config dictionary

    Raises:
        FileNotFoundError: If config.yml doesn't exist
        yaml.YAMLError: If config.yml is invalid
    """
    config_path = Path(workspaces_dir) / workspace_folder / CONFIG_FILE
    if not config_path.exists():
        raise FileNotFoundError(f"{CONFIG_FILE} not found in {workspace_folder}")

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def get_workspace_name_from_config(config: dict[str, Any], environment: str) -> str:
    """Extract workspace name for environment from config.

    Args:
        config: Parsed config.yml dictionary
        environment: Target environment (dev/test/prod)

    Returns:
        Workspace name for environment

    Raises:
        KeyError: If environment not defined in config
    """
    try:
        workspace_name = config["core"]["workspace"][environment]
        return workspace_name
    except KeyError:
        raise KeyError(
            f"Workspace name for environment '{environment}' not found in config.yml. "
            f"Expected: core.workspace.{environment}"
        ) from None


def get_workspace_folders(workspaces_dir: str) -> list[str]:
    """Get all workspace folders from the workspaces directory.

    Args:
        workspaces_dir: Root directory containing workspace folders

    Returns:
        Sorted list of workspace folder names that contain config.yml

    Raises:
        FileNotFoundError: If workspaces directory doesn't exist
    """
    workspaces_path = Path(workspaces_dir)
    if not workspaces_path.exists():
        raise FileNotFoundError(f"Workspaces directory not found: {workspaces_dir}")

    workspace_folders = [
        folder.name for folder in workspaces_path.iterdir() if folder.is_dir() and (folder / CONFIG_FILE).exists()
    ]

    if not workspace_folders:
        raise ValueError(
            f"No workspace folders with '{CONFIG_FILE}' found in {workspaces_dir}. "
            "Each workspace folder must contain a config.yml file."
        )

    return sorted(workspace_folders)


def deploy_workspace(
    workspace_folder: str,
    workspaces_dir: str,
    environment: str,
    token_credential: CredentialType,
) -> DeploymentResult:
    """Deploy a single workspace using config.yml.

    Workspaces are pre-provisioned by Terraform. This function only deploys items
    into an already-existing workspace.

    Args:
        workspace_folder: Name of the workspace folder
        workspaces_dir: Root directory containing workspace folders
        environment: Target environment (dev/test/prod)
        token_credential: Azure credential for authentication

    Returns:
        DeploymentResult object with success status and error message if applicable.
    """
    workspace_name = ""  # Initialize for error handling
    try:
        logger.info(f"\n{SEPARATOR_SHORT}")
        logger.info(f"Deploying workspace: {workspace_folder}")
        logger.info(f"{SEPARATOR_SHORT}\n")

        # Load workspace config
        config = load_workspace_config(workspace_folder, workspaces_dir)
        workspace_name = get_workspace_name_from_config(config, environment)
        config_file_path = str(Path(workspaces_dir) / workspace_folder / CONFIG_FILE)

        logger.info(f"-> Target workspace: {workspace_name}")
        logger.info(f"-> Config file: {config_file_path}")
        logger.info(f"-> Environment: {environment}")

        # Deploy using config.yml
        logger.info("-> Deploying items using config-based deployment...")
        deploy_with_config(
            config_file_path=config_file_path, environment=environment, token_credential=token_credential
        )

        logger.info(f"\n[OK] Deployment to {workspace_name} completed successfully!\n")
        return DeploymentResult(workspace_folder=workspace_folder, workspace_name=workspace_name, success=True)

    except Exception as e:
        error_message = str(e)
        display_name = workspace_name if workspace_name else workspace_folder
        logger.error(f"\n[FAIL] ERROR: Deployment failed for workspace '{display_name}': {error_message}\n")
        return DeploymentResult(
            workspace_folder=workspace_folder,
            workspace_name=workspace_name if workspace_name else workspace_folder,
            success=False,
            error_message=error_message,
        )


def discover_workspace_folders(workspaces_directory: str) -> list[str]:
    """Discover and return all workspace folders to deploy.

    Automatically discovers all workspace folders in the workspaces directory
    that contain a config.yml file.

    Args:
        workspaces_directory: Root directory containing workspace folders

    Returns:
        Sorted list of workspace folder names to deploy

    Raises:
        ValueError: If no workspace folders are found
        FileNotFoundError: If workspaces directory doesn't exist
    """
    workspace_folders = get_workspace_folders(workspaces_directory)
    logger.info(f"-> Discovered {len(workspace_folders)} workspace(s): {', '.join(workspace_folders)}\n")
    return workspace_folders




def validate_environment(environment: str) -> None:
    """Validate that the environment is one of the expected values.

    Args:
        environment: Environment name to validate

    Raises:
        ValueError: If environment is not valid
    """
    if environment.lower() not in VALID_ENVIRONMENTS:
        raise ValueError(
            f"Invalid environment '{environment}'. Must be one of: {', '.join(sorted(VALID_ENVIRONMENTS))}"
        )


def deploy_all_workspaces(
    workspace_folders: list[str],
    workspaces_directory: str,
    environment: str,
    token_credential: CredentialType,
) -> list[DeploymentResult]:
    """Deploy all specified workspaces and return results.

    Workspaces are pre-provisioned by Terraform. This function only deploys items
    into already-existing workspaces.

    Args:
        workspace_folders: List of workspace folder names to deploy
        workspaces_directory: Root directory containing workspace folders
        environment: Target environment (dev/test/prod)
        token_credential: Azure credential for authentication

    Returns:
        List of DeploymentResult objects, one per workspace
    """
    results: list[DeploymentResult] = []

    logger.info(f"Starting deployment of {len(workspace_folders)} workspace(s)...\n")
    for i, workspace_folder in enumerate(workspace_folders, 1):
        logger.info(f"[{i}/{len(workspace_folders)}] Processing workspace: {workspace_folder}")

        result = deploy_workspace(
            workspace_folder=workspace_folder,
            workspaces_dir=workspaces_directory,
            environment=environment,
            token_credential=token_credential,
        )

        results.append(result)

    return results


def parse_cli_args() -> argparse.Namespace:
    """Parse command-line arguments for workspace deployment."""
    parser = argparse.ArgumentParser(description="Deploy Fabric Workspaces - Auto-discovers all workspace folders")
    parser.add_argument("--workspaces_directory", type=str, required=True, help="Root directory containing workspace folders")
    parser.add_argument(
        "--environment",
        type=str,
        required=True,
        choices=list(VALID_ENVIRONMENTS),
        help="Target environment (dev/test/prod)",
    )
    return parser.parse_args()


def configure_runtime() -> None:
    """Configure feature flags and runtime logging behavior."""
    # Enable experimental features for config-based deployment
    append_feature_flag("enable_experimental_features")
    append_feature_flag("enable_config_deploy")

    # Force unbuffered output for GitHub Actions logs.
    # Use getattr for typing/runtime compatibility across stream implementations.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(line_buffering=True, write_through=True)

    # Enable debugging if ACTIONS_RUNNER_DEBUG is set
    # Note: This only affects fabric_cicd library logging.
    # Local script logger (from logger.py) remains at INFO level.
    if os.getenv(ENV_ACTIONS_RUNNER_DEBUG, "false").lower() == "true":
        change_log_level("DEBUG")


def log_deployment_header(environment: str, workspaces_directory: str) -> None:
    """Log deployment header metadata for run visibility."""
    logger.info(f"\n{SEPARATOR_LONG}")
    logger.info("FABRIC MULTI-WORKSPACE DEPLOYMENT")
    logger.info(SEPARATOR_LONG)
    logger.info(f"Environment: {environment.upper()}")
    logger.info(f"Workspaces directory: {workspaces_directory}")
    logger.info(f"{SEPARATOR_LONG}\n")


def run_deployment_pipeline(
    workspaces_directory: str, environment: str, token_credential: CredentialType
) -> DeploymentSummary:
    """Execute workspace discovery + deployment and return a summary."""
    workspace_folders = discover_workspace_folders(workspaces_directory)

    deployment_start_time = time.time()
    results = deploy_all_workspaces(
        workspace_folders=workspace_folders,
        workspaces_directory=workspaces_directory,
        environment=environment,
        token_credential=token_credential,
    )
    deployment_duration = time.time() - deployment_start_time

    return DeploymentSummary(environment=environment, duration=deployment_duration, results=results)


def write_deployment_results(summary: DeploymentSummary) -> None:
    """Write deployment result payload to disk for workflow summary scripts."""
    deployment_results_json = build_deployment_results_json(summary)
    with open(RESULTS_FILENAME, "w", encoding="utf-8") as f:
        json.dump(deployment_results_json, f, indent=2)
    logger.info(f"\n-> Deployment results written to {RESULTS_FILENAME}")


def main():
    """Main deployment orchestration."""
    configure_runtime()
    args = parse_cli_args()

    workspaces_directory = args.workspaces_directory
    environment = args.environment

    log_deployment_header(environment, workspaces_directory)

    try:
        validate_environment(environment)
        token_credential = create_azure_credential()
        summary = run_deployment_pipeline(workspaces_directory, environment, token_credential)
        write_deployment_results(summary)
        print_deployment_summary(summary)

        if summary.failed_count > 0:
            logger.warning(f"\nDeployment completed with {summary.failed_count} failure(s)\n")
            sys.exit(EXIT_FAILURE)
        else:
            logger.info(f"\nAll {summary.successful_count} workspace(s) deployed successfully!\n")
            sys.exit(EXIT_SUCCESS)

    except (ValueError, FileNotFoundError) as e:
        logger.error(f"\n[FAIL] VALIDATION ERROR: {e!s}\n")
        sys.exit(EXIT_FAILURE)
    except Exception as e:
        logger.error(f"\n[FAIL] CRITICAL ERROR: {e!s}\n")
        sys.exit(EXIT_FAILURE)


if __name__ == "__main__":
    main()
