# Fabric CI/CD Toolkit Wiki

This wiki is the in-depth guide for the repository.  
Use `README.md` for fast setup, then use these pages for details.

## Start Here

1. [Setup Guide](Setup-Guide): complete first-time setup end-to-end.
2. [Workspace Configuration](Workspace-Configuration): understand `config.yml` and `parameter.yml`.
3. [Deployment Workflow](Deployment-Workflow): exact behavior of GitHub workflows.
4. [Troubleshooting](Troubleshooting): fix common failure modes.
5. [FAQ](FAQ): concise answers to recurring questions.

## What This Repository Is

- A toolkit to bootstrap Fabric CI/CD quickly.
- Terraform provisions Fabric workspaces and admin role assignment.
- Python scripts + `fabric-cicd` deploy workspace content from `workspaces/`.
- One sample workspace (`Fabric Blueprint`) is included as minimum deployable content.

## What This Repository Is Not

- Not a full Fabric solution architecture.
- Not a catalog of planned features.
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
- [fabric-cicd package](https://pypi.org/project/fabric-cicd/)
- [GitHub Actions docs](https://docs.github.com/actions)
