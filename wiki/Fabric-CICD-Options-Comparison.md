# Fabric CI/CD Options Comparison

This page compares the main Microsoft Fabric CI/CD options and explains which ones this toolkit uses.

Last reviewed: **2026-02-27**

## Quick Positioning

| Option | What it is | Best for | Used in this toolkit? |
|---|---|---|---|
| `fabric-cicd` | Python library for code-first Fabric item deployment automation | Deploying workspace items from source control with parameterization in CI/CD | **Yes** |
| `fabric-cli` | General-purpose CLI (`fab`) for managing Fabric from terminal/scripts | Interactive operations, scripting, ad-hoc automation, API access from CLI | **No** |
| Terraform provider `microsoft/fabric` | Infrastructure-as-code provider for Fabric resources | Provisioning/managing Fabric infrastructure state declaratively | **Yes** |
| Fabric REST API | Low-level HTTP API surface for Fabric | Custom integrations and full-control automation | **Indirectly only** (via higher-level tools) |
| Fabric Deployment Pipelines | Built-in Fabric promotion flow across stages | In-product, stage-based promotion UX/governance | **No** |
| `microsoft-fabric-api` | Python SDK wrapper for Fabric REST API | Building custom Python applications/integrations | **No** |

## What We Use in This Repo

### `fabric-cicd` (Yes)
- Used for workspace item deployment orchestration via Python.
- In this repo:
  - `requirements.txt` pins `fabric-cicd==0.2.0`.
  - `scripts/deploy_to_fabric.py` calls `deploy_with_config`.
  - Deployment is triggered by `.github/workflows/fabric-deploy.yml`.
- Why we use it:
  - It matches the repo's code-first `workspaces/*` model and `config.yml`/`parameter.yml` contract.
  - It avoids implementing raw API orchestration ourselves.

### Terraform provider `microsoft/fabric` (Yes)
- Used for Fabric infrastructure provisioning (not item content deployment).
- In this repo:
  - `terraform/main.tf` uses provider `microsoft/fabric ~> 1.7`.
  - Provisions `fabric_workspace` and `fabric_workspace_role_assignment`.
  - Executed by `.github/workflows/terraform.yml`.
- Why we use it:
  - Declarative, environment-specific, reviewable infrastructure changes.
  - Clear separation from content deployment concerns.

## What We Do Not Use (and Why)

### `fabric-cli` (No)
- Strong for ad-hoc operations, interactive exploration, and scriptable command workflows.
- Not used here because this repo is standardized around non-interactive, deterministic GitHub Actions runs and Python orchestration already built on `fabric-cicd`.
- It can still be useful locally for debugging and one-off inspections.

### Fabric REST API directly (No direct usage)
- Most flexible option, but also the lowest-level option.
- Requires building/maintaining auth handling, retries/throttling behavior, request sequencing, and compatibility management in our own code.
- We intentionally consume higher-level abstractions (`fabric-cicd`, Terraform provider) for maintainability.

### Fabric Deployment Pipelines (No)
- Useful when teams want in-product, stage-based promotion and governance inside Fabric UX.
- Not used because this toolkit standardizes promotion through GitHub Actions and source-controlled assets.
- Using both promotion systems together often introduces duplicated release logic and unclear source of truth.

### `microsoft-fabric-api` SDK (No)
- Python SDK over Fabric REST APIs.
- Good fit for custom app/integration development where a generic CI/CD deployment library is not enough.
- Not used because this toolkit's current deployment requirements are already covered by `fabric-cicd` + Terraform provider.

## Side-by-Side Differences

### 1) Scope: Infra vs Content vs Platform Promotion
- Terraform provider: Infrastructure resources and assignments.
- `fabric-cicd`: Workspace item/content deployment from files.
- Deployment Pipelines: Platform-native stage promotion mechanism.
- REST API / `microsoft-fabric-api` / `fabric-cli`: Generic control planes that can operate across many resource types.

### 2) Abstraction Level
- Highest abstraction for this repo's goal: `fabric-cicd` and Terraform provider.
- Lower abstraction: `fabric-cli`.
- Lowest abstraction: REST API (and SDK wrappers around it).

### 3) Operational Model
- Terraform provider: Declarative desired state (`plan`/`apply`).
- `fabric-cicd`: Procedural deployment execution from config and source-controlled artifacts.
- Deployment Pipelines: Stage promotion model in Fabric service.
- REST/SDK/CLI: Command/API-driven imperative operations.

### 4) CI/CD Fit for This Toolkit
- Best fit (chosen): Terraform + `fabric-cicd` in GitHub Actions.
- Not chosen as primary path: Deployment Pipelines (parallel release mechanism), raw REST/SDK/CLI (more custom engineering overhead).

## Decision Rationale in One Sentence

We use **Terraform provider + `fabric-cicd`** because it gives the cleanest separation between **infrastructure provisioning** and **workspace content deployment**, with deterministic GitHub Actions automation and minimal custom API plumbing.

## Official References

- `fabric-cicd` docs: https://microsoft.github.io/fabric-cicd/latest/
- `fabric-cli` docs: https://microsoft.github.io/fabric-cli/
- Terraform provider docs: https://registry.terraform.io/providers/microsoft/fabric/latest/docs
- Terraform provider source docs: https://github.com/microsoft/terraform-provider-fabric/tree/main/docs
- Fabric REST APIs overview: https://learn.microsoft.com/en-us/rest/api/fabric/articles/using-fabric-apis
- Fabric Deployment Pipelines intro: https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/intro-to-deployment-pipelines?tabs=new-ui
- `microsoft-fabric-api` package: https://pypi.org/project/microsoft-fabric-api/
