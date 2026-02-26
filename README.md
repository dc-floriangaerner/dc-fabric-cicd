# Fabric CI/CD Toolkit

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)

This repository is a practical starter toolkit for Microsoft Fabric CI/CD:
- `terraform/` provisions Fabric workspaces and role assignments.
- `workspaces/` + `scripts/` deploy Fabric items with `fabric-cicd`.
- `.github/workflows/` automates validation and deployment.

The included `workspaces/Fabric Blueprint` content is a minimum sample so the pipeline has real deployable assets.

## Quick Start (First Successful Deployment)

1. Clone or fork this repository.
2. Create a Service Principal in Microsoft Entra ID.
3. Configure GitHub secrets:
   - Required for deploy + CI: `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`
   - Required for Terraform workflow: `ARM_SUBSCRIPTION_ID`
4. Edit Terraform environment files:
   - `terraform/environments/dev.tfvars`
   - `terraform/environments/test.tfvars`
   - `terraform/environments/prod.tfvars`
5. In each tfvars file, set real values for:
   - `workspace_name_fabric_blueprint`
   - `capacity_id`
   - `entra_admin_group_object_id`
6. Ensure workspace names in `workspaces/Fabric Blueprint/config.yml` match tfvars names for each environment.
7. Replace sample GUIDs in `workspaces/Fabric Blueprint/parameter_templates/*.yml` with your real Dev IDs.
8. Run local validation:
   - `python -m scripts.check_unmapped_ids --workspaces_directory workspaces`
   - `pytest tests/ -v`
9. Run infrastructure:
   - GitHub Actions -> `Terraform — Fabric Infrastructure` -> select `dev`, then `test`, then `prod`
10. Merge a PR with `workspaces/**` changes to deploy automatically to Dev.
11. Promote manually to Test/Prod:
   - GitHub Actions -> `Deploy to Microsoft Fabric` -> `test` or `prod`

## What You Must Change First

If you only update these files correctly, you can start deploying quickly:

- `terraform/environments/*.tfvars`
  - Replace placeholder `capacity_id` values.
  - Replace placeholder `entra_admin_group_object_id` values.
  - Keep workspace names aligned with workspace configs.
- `workspaces/Fabric Blueprint/config.yml`
  - Verify `core.workspace.dev|test|prod` names are exactly the same as Terraform provisions.
- `workspaces/Fabric Blueprint/parameter_templates/*.yml`
  - Replace sample Dev GUIDs with IDs from your Dev workspace content.
- GitHub repository secrets
  - Add `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`, `ARM_SUBSCRIPTION_ID`.

## Current CI/CD Behavior

### `ci.yml`
- Trigger: PRs to `main` with changes in `scripts/**`, `tests/**`, `workspaces/**`, dependency files, or `ci.yml`.
- Runs:
  - unmapped ID scanner
  - pytest + coverage

### `terraform.yml`
- Trigger:
  - push to `main` with `terraform/**` changes (auto dev apply)
  - manual dispatch (`dev|test|prod`)
  - reusable call from other workflows
- Purpose: provision/update Fabric workspaces and role assignments.

### `fabric-deploy.yml`
- Trigger:
  - push to `main` with `workspaces/**` changes (auto dev deploy)
  - manual dispatch (`dev|test|prod`)
- Always runs Terraform reusable workflow first, then deploys workspace items.

### `sync-wiki.yml`
- Trigger: push to `main` with `wiki/**` changes.
- Syncs `/wiki` folder to GitHub Wiki.

## Repository Contract

### Infrastructure
- `terraform/` is the source of truth for workspace provisioning and role assignments.

### Content Deployment
- `scripts/deploy_to_fabric.py` deploys items to pre-existing workspaces.
- Workspaces are auto-discovered from folders in `workspaces/` that contain `config.yml`.

### Parameterization
- Every workspace needs `parameter.yml`.
- `scripts/check_unmapped_ids.py` enforces GUID parameterization coverage.

## Local Developer Commands

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
mypy scripts/
python -m scripts.check_unmapped_ids --workspaces_directory workspaces
pytest tests/ -v
python -m scripts.deploy_to_fabric --workspaces_directory workspaces --environment dev
```

## Add Your Own Workspace

1. Add `workspaces/<Workspace Name>/` with:
   - `config.yml`
   - `parameter.yml`
   - Fabric item folders/files
2. Add matching Terraform resources and variables in:
   - `terraform/main.tf`
   - `terraform/variables.tf`
   - `terraform/outputs.tf`
   - `terraform/environments/*.tfvars`
3. Keep workspace names consistent between Terraform and `config.yml`.
4. Add find/replace rules for all relevant Dev GUIDs.

## Documentation

- Wiki home: [wiki/Home.md](wiki/Home.md)
- Setup guide: [wiki/Setup-Guide.md](wiki/Setup-Guide.md)
- Workspace config: [wiki/Workspace-Configuration.md](wiki/Workspace-Configuration.md)
- Deployment flow: [wiki/Deployment-Workflow.md](wiki/Deployment-Workflow.md)
- Troubleshooting: [wiki/Troubleshooting.md](wiki/Troubleshooting.md)
