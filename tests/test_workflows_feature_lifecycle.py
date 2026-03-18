"""Static validation for workflow separation between stable and feature lifecycles."""

from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_workflow(name: str) -> dict:
    path = REPO_ROOT / ".github" / "workflows" / name
    with path.open(encoding="utf-8") as handle:
        workflow = yaml.safe_load(handle)
    if True in workflow and "on" not in workflow:
        workflow["on"] = workflow.pop(True)
    return workflow


def test_feature_create_workflow_never_invokes_terraform() -> None:
    workflow = _load_workflow("feature-workspace-create.yml")
    jobs = workflow["jobs"]

    assert "terraform" not in jobs
    run_steps = [
        step.get("run", "")
        for step in jobs["create_feature_workspaces"]["steps"]
        if isinstance(step, dict)
    ]
    assert all("terraform" not in run.lower() for run in run_steps)


def test_stable_workflows_remain_dev_test_prod_only() -> None:
    fabric_deploy = _load_workflow("fabric-deploy.yml")
    terraform = _load_workflow("terraform.yml")

    deploy_options = fabric_deploy["on"]["workflow_dispatch"]["inputs"]["environment"]["options"]
    terraform_options = terraform["on"]["workflow_dispatch"]["inputs"]["environment"]["options"]

    assert deploy_options == ["dev", "test", "prod"]
    assert terraform_options == ["dev", "test", "prod"]


def test_no_feature_branch_push_sync_workflow_exists() -> None:
    create_workflow = _load_workflow("feature-workspace-create.yml")
    cleanup_workflow = _load_workflow("feature-workspace-cleanup.yml")

    assert "push" not in cleanup_workflow["on"]
    assert "push" not in create_workflow["on"]
    assert "create" in create_workflow["on"]
    assert "pull_request" in cleanup_workflow["on"]
    assert "delete" in cleanup_workflow["on"]
