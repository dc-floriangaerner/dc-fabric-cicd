# AGENTS.md - Codex Operating Guide for dc-fabric-cicd

## Goal
Make safe, CI-ready changes quickly in a Microsoft Fabric CI/CD reference repo.
Keep infrastructure provisioning, workspace item deployment, and documentation flows clearly separated.

## Project Snapshot
- Stack: Python 3.11+, GitHub Actions, Terraform, Microsoft Fabric, `fabric-cicd`.
- Core runtime scripts: `scripts/deploy_to_fabric.py`, `scripts/check_unmapped_ids.py`.
- Main deployable assets: `workspaces/<Workspace Name>/...`.
- Infrastructure-as-code: `terraform/`.
- Tests: `tests/`.

## Source of Truth (Read First)
1. `README.md` for architecture and deployment flow.
2. `.github/workflows/*.yml` for actual CI/CD behavior.
3. `scripts/deploy_to_fabric.py` for deployment orchestration logic.
4. `scripts/check_unmapped_ids.py` for GUID parameterization enforcement.
5. `workspaces/*/config.yml` and `workspaces/*/parameter.yml` for workspace-specific contract.

## Issue and PR Templates
- When creating or updating issues, follow:
  - `.github/ISSUE_TEMPLATE/bug_report.md`
  - `.github/ISSUE_TEMPLATE/feature_request.md`
- When drafting PRs, follow `.github/pull_request_template.md`.
- Do not skip template sections; mark non-applicable sections explicitly as `N/A`.
- Ensure issue/PR text includes concrete scope, testing performed, and deployment impact.

## Non-Negotiable Rules
- Do not mix concerns:
  - `terraform/` provisions workspaces and role assignments.
  - `scripts/` + `workspaces/` deploy workspace items.
- Every workspace folder must contain `config.yml` to be discovered for deployment.
- Treat `parameter.yml` as mandatory for environment transformations.
- For workspace item edits, preserve Fabric file structure and naming patterns.
- Never break notebook metadata/cell markers in `notebook-content.py`.
- Never commit secrets, credentials, tenant-specific sensitive values, or private keys.

## High-Value Local Commands
- Install runtime deps: `pip install -r requirements.txt`
- Install dev deps: `pip install -r requirements-dev.txt`
- Lint scripts: `ruff check scripts/`
- Format scripts: `ruff format scripts/`
- Run tests: `pytest tests/ -v`
- Scan unmapped GUIDs: `python -m scripts.check_unmapped_ids --workspaces_directory workspaces`
- Local deploy (dev): `python -m scripts.deploy_to_fabric --workspaces_directory workspaces --environment dev`

## Workflow Trigger Awareness
- `fabric-deploy.yml`
  - Auto: push to `main` with changes under `workspaces/**`.
  - Manual: dispatch with `dev|test|prod`.
  - Runs Terraform reusable workflow first, then deployment.
- `terraform.yml`
  - Auto: push to `main` with changes under `terraform/**`.
  - Manual/reusable: `dev|test|prod`.
- `ci.yml` (PR to `main`)
  - Runs on changes in `scripts/**`, `tests/**`, `workspaces/**`, dependency files, and workflow file itself.
  - Executes unmapped-ID scan, Ruff, pytest, coverage.
- `sync-wiki.yml`
  - Auto: push to `main` with changes under `wiki/**`.

## Change Playbooks

### If editing `scripts/**`
- Follow existing typing and logging style.
- Use logger utilities (`scripts/logger.py`), avoid `print` (Ruff `T20` enforced).
- Run: Ruff + pytest before finalizing.

### If editing `workspaces/**`
- Keep each item in `<name>.<ItemType>/` structure.
- Preserve notebook `# METADATA` and `# CELL` sections exactly.
- Add/update find-replace rules in workspace `parameter.yml` (or templates via `extend`) for any hardcoded GUIDs.
- Run unmapped-ID scanner before finalizing.

### If editing `terraform/**`
- Keep workspace names aligned with `workspaces/*/config.yml` per environment.
- Validate Terraform file consistency (`main.tf`, `variables.tf`, `outputs.tf`, `environments/*.tfvars`).
- Do not change backend/state conventions unless explicitly requested.

### If editing `wiki/**`
- Keep markdown clean and link-consistent.
- Remember merged changes sync automatically to GitHub Wiki.

## Definition of Done (Before Hand-off)
- Scope-limited changes only; no unrelated file churn.
- Required checks for changed area executed locally (at minimum):
  - `scripts/**`: Ruff + pytest.
  - `workspaces/**`: unmapped-ID scan.
  - `terraform/**`: logical consistency across tf files and env tfvars.
- No secrets introduced.
- Documentation updated when behavior/config/commands changed.
- If opening/updating issue or PR text, repository templates were followed.

## Common Failure Patterns to Prevent
- Missing `config.yml` in a workspace folder (workspace not discovered).
- Hardcoded Dev GUIDs in item files without matching `find_replace` rules.
- Broken notebook metadata comments after manual edits.
- Workspace naming mismatch between Terraform and workspace config.
- Assuming non-workspace changes trigger auto Fabric deployment.
