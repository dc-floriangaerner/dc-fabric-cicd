# Deployment Workflow

This page describes exactly what is implemented in current workflows.

## Workflow Overview

| Workflow | File | Purpose | Trigger |
|---|---|---|---|
| CI | `.github/workflows/ci.yml` | Tests and validation on PRs | `pull_request` to `main` on configured paths |
| Terraform | `.github/workflows/terraform.yml` | Provision/update Fabric workspace infrastructure | push on `terraform/**`, manual dispatch, reusable call |
| Fabric Deploy | `.github/workflows/fabric-deploy.yml` | Deploy workspace items | push on `workspaces/**`, manual dispatch |
| Wiki Sync | `.github/workflows/sync-wiki.yml` | Sync `/wiki` folder to GitHub Wiki | push on `wiki/**`, manual dispatch |

## End-to-End Path

1. Developer updates workspace content or scripts.
2. PR to `main` runs `ci.yml` (scanner + tests).
3. Merge with `workspaces/**` changes triggers `fabric-deploy.yml`.
4. `fabric-deploy.yml` first calls reusable `terraform.yml`.
5. Deploy job runs scanner, then deploy script.
6. Team promotes manually to `test` and `prod` via workflow dispatch.

## `terraform.yml` Behavior

- Auto on push to `main` with `terraform/**` changes (targets `dev`).
- Manual dispatch with selected `dev|test|prod`.
- Reusable workflow call from `fabric-deploy.yml`.

Steps:
1. `terraform init` with environment-specific state key.
2. `terraform validate`
3. `terraform plan`
4. `terraform apply`

Secrets used:
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_TENANT_ID`
- `ARM_SUBSCRIPTION_ID`

## `fabric-deploy.yml` Behavior

- Auto on push to `main` with `workspaces/**` changes:
  - target environment = `dev`
- Manual dispatch:
  - target environment = selected input (`dev|test|prod`)

Pipeline order:
1. Run Terraform prerequisites via reusable workflow.
2. Run `python -m scripts.check_unmapped_ids --workspaces_directory workspaces`.
3. Run `python -m scripts.deploy_to_fabric --workspaces_directory workspaces --environment <env>`.
4. Generate summary and upload `deployment-results.json` artifact.

Important:
- Deploy script only deploys into existing workspaces.
- Workspace discovery is based on folders containing `config.yml`.

## Environment Promotion

- Dev:
  - automatic after merge to `main` when `workspaces/**` changed
  - or manual
- Test:
  - manual only
- Prod:
  - manual only

Recommended promotion:
1. Deploy and validate Dev.
2. Run manual deploy to Test and validate.
3. Run manual deploy to Prod.

## What Does Not Trigger Auto Deploy

Changes only in these areas do not auto-trigger `fabric-deploy.yml`:
- `scripts/**`
- `.github/**`
- `README.md`
- `wiki/**`
- `terraform/**`

Use manual workflow dispatch when needed.

## Deployment Semantics

- Workspaces are processed sequentially.
- If one workspace fails, job exits with failure.
- No automatic rollback is implemented.

## Validation Gates

Primary guardrail:
- `check_unmapped_ids.py` blocks deployment if GUIDs are not covered by `parameter.yml` rules.

CI also runs:
- pytest
- coverage reporting

## Related Pages

- [Setup Guide](Setup-Guide)
- [Workspace Configuration](Workspace-Configuration)
- [Troubleshooting](Troubleshooting)
