
"""Reporting helpers for Fabric deployment scripts."""

from typing import Any

from ..common.logger import get_logger
from .config import SEPARATOR_LONG
from .types import DeploymentSummary

logger = get_logger(__name__)


def build_deployment_results_json(summary: DeploymentSummary) -> dict[str, Any]:
    """Build the deployment results dictionary for JSON output."""
    workspaces_list = sorted(
        (
            {
                "name": result.workspace_folder,
                "full_name": result.workspace_name,
                "status": "success" if result.success else "failure",
                "error": result.error_message,
            }
            for result in summary.results
        ),
        key=lambda workspace: workspace["name"],
    )

    return {
        "environment": summary.environment,
        "duration": summary.duration,
        "total_workspaces": summary.total_workspaces,
        "successful_count": summary.successful_count,
        "failed_count": summary.failed_count,
        "workspaces": workspaces_list,
    }


def print_deployment_summary(summary: DeploymentSummary) -> None:
    """Print comprehensive deployment summary to console."""
    logger.info(f"\n{SEPARATOR_LONG}")
    logger.info("DEPLOYMENT SUMMARY")
    logger.info(SEPARATOR_LONG)
    logger.info(f"Environment: {summary.environment.upper()}")
    logger.info(f"Duration: {summary.duration:.2f} seconds")
    logger.info(f"Total workspaces: {summary.total_workspaces}")
    logger.info(f"Successful: {summary.successful_count}")
    logger.info(f"Failed: {summary.failed_count}")
    logger.info(SEPARATOR_LONG)

    successful = [result.workspace_name for result in summary.results if result.success]
    failed = [(result.workspace_name, result.error_message) for result in summary.results if not result.success]

    if successful:
        logger.info("\n[OK] SUCCESSFUL DEPLOYMENTS:")
        for full_name in successful:
            logger.info(f"  [OK] {full_name}")

    if failed:
        logger.error("\n[FAIL] FAILED DEPLOYMENTS:")
        for full_name, error in failed:
            logger.error(f"  [FAIL] {full_name}")
            logger.error(f"    Error: {error}")

    logger.info(f"\n{SEPARATOR_LONG}")
