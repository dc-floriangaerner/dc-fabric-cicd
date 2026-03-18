# Feature Workspace Lifecycle

This page documents the optional branch-based workspace lifecycle that sits beside the stable `dev|test|prod` model.

## Stable vs Feature Split

- Stable stages:
  - provisioned by `terraform/`
  - deployed by `scripts/deploy_to_fabric.py`
  - source of truth remains the repository plus Terraform
- Feature stages:
  - created and deleted by `scripts/manage_feature_workspaces.py`
  - initialized from Git once through Fabric Git integration
  - source of truth becomes the Fabric feature workspace during active development

This separation is intentional. The repository does not try to continuously reconcile later branch pushes into a feature workspace after the initial Git seed.

## Branch Trigger Rules

- Included branches:
  - `feature/**`
  - `bugfix/**`
- Creation trigger:
  - GitHub `create` event for qualifying branches
- Cleanup triggers:
  - `pull_request` closed against `main`
  - GitHub `delete` event for qualifying branches

## Central Config Contract

Repository-level config lives in `feature-workspaces.yml`.

Supported keys:
- `branch_patterns`
- `workspace_name_template`
- `capacity_id`
- `git.provider_type`
- `git.repository.owner`
- `git.repository.name`
- `git.connection_id` or `git.connection_name`
- `permissions`
- `cleanup.delete_on_pr_close`
- `cleanup.delete_on_branch_delete`

## Naming Pattern

The script uses one deterministic algorithm everywhere:
1. strip `refs/heads/`
2. lowercase the branch name
3. replace invalid characters with `-`
4. collapse duplicate dashes
5. truncate the branch slug to a safe length
6. append an 8-character hash suffix based on the branch name

Recommended template:

```yaml
workspace_name_template: "[{branch_prefix}] {workspace_folder} ({branch_slug}-{hash8})"
```

Supported placeholders:
- `{branch_prefix}`:
  - `F` for `feature/**`
  - `B` for `bugfix/**`
- `{workspace_folder}`
- `{branch_slug}`
- `{hash8}`

## Per-Workspace Opt-In

Each workspace `config.yml` may include:

```yaml
feature_workspace:
  enabled: true
```

Rules:
- only opted-in workspaces participate
- all opted-in workspaces are created for a qualifying branch
- selection is not based on changed files

## Fixed Git Directory Rule

The directory is not configurable.

For every opted-in workspace folder, the Git connection always targets:

```text
workspaces/<workspace folder>
```

## Fabric-First Authoring Model

Lifecycle:
1. create branch under `feature/**` or `bugfix/**`
2. workflow creates opted-in feature workspaces
3. workspace connects to the branch and pulls the fixed directory once
4. development continues in Fabric
5. user commits back to the same branch from Fabric
6. PR closes or branch is deleted
7. cleanup workflow deletes the feature workspaces

Important:
- no background Git-to-Fabric sync runs after creation
- later branch pushes do not auto-update the feature workspace
- this avoids overwriting unpublished Fabric-side changes

## Cleanup Semantics

- cleanup is best-effort and idempotent
- already-deleted workspaces are skipped
- cleanup behavior can be toggled in `feature-workspaces.yml`

## Operator Expectations

- Fabric CLI must be available in the workflow runtime
- the service principal must be able to create/delete workspaces and manage Git connections
- the configured Fabric Git connection must already exist
- the configured capacity must allow workspace creation

## Limitations

- stable `dev|test|prod` still require Terraform and the existing deployment flow
- feature lifecycle does not promote to stable environments
- no auto-sync-on-push exists for feature workspaces by design
