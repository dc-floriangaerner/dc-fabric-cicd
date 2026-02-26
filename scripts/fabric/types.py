# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Shared dataclasses for Fabric deployment results."""

from dataclasses import dataclass


@dataclass
class DeploymentResult:
    """Result of a single workspace deployment."""

    workspace_folder: str
    workspace_name: str
    success: bool
    error_message: str = ""


@dataclass
class DeploymentSummary:
    """Summary of all workspace deployments."""

    environment: str
    duration: float
    results: list[DeploymentResult]

    @property
    def total_workspaces(self) -> int:
        return len(self.results)

    @property
    def successful_count(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.success)
