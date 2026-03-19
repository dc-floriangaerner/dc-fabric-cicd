# Fabric CI/CD Toolkit Wiki

This wiki is the in-depth guide for the repository.  
Use `README.md` for fast setup, then use these pages for details.

## Start Here

1. [Setup Guide](Setup-Guide): complete first-time setup end-to-end.
2. [IT Admin Prerequisites for Fabric](IT-Admin-Prerequisites-For-Fabric): exact admin-side setup, IDs, permissions, and handoff checklist.
3. [Feature Workspace Lifecycle](Feature-Workspace-Lifecycle): optional branch-based ephemeral workspaces.
4. [Workspace Configuration](Workspace-Configuration): understand `config.yml` and `parameter.yml`.
5. [Deployment Workflow](Deployment-Workflow): exact behavior of GitHub workflows.
6. [Troubleshooting](Troubleshooting): fix common failure modes.
7. [FAQ](FAQ): concise answers to recurring questions.
8. [Fabric CI/CD Options Comparison](Fabric-CICD-Options-Comparison): deep comparison of Fabric CI/CD tooling choices.

## What This Repository Is

- A toolkit to bootstrap Fabric CI/CD quickly.
- Terraform provisions Fabric workspaces and admin role assignment.
- Python scripts + `fabric-cicd` deploy workspace content from `workspaces/`.
- Optional feature lifecycle creates ephemeral workspaces from `feature/**` and `bugfix/**` branches.
- One sample workspace (`Fabric Blueprint`) is included as minimum deployable content.

## What This Repository Is Not

- Not a full Fabric solution architecture.
- Not a generic deployment engine for every CI platform.

## Required Knowledge

- Basic GitHub workflow usage (PRs, Actions, secrets).
- Basic Microsoft Fabric workspace concepts.
- Basic YAML editing.

## Core Contract to Remember

- `terraform/` creates workspace infrastructure.
- `workspaces/` + `scripts/` deploy content into those workspaces.
- Workspace names must match across:
  - `terraform/environments/*.tfvars`
  - `workspaces/*/config.yml`

## External References

- [Microsoft Fabric docs](https://learn.microsoft.com/fabric/)
- [fabric-cicd docs](https://microsoft.github.io/fabric-cicd/)
- [GitHub Actions docs](https://docs.github.com/actions)
