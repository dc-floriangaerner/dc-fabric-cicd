# IT Admin Prerequisites

This page is the IT admin handoff for setting up and operating this repository.
It answers:

- what must be created
- what IDs, names, and secrets must be provided
- which permissions are required
- which parts are mandatory for the stable `dev | test | prod` flow
- which parts are only needed for the optional feature workspace flow

The content below is derived from the current repository implementation in:

- `terraform/`
- `.github/workflows/`
- `scripts/deploy_to_fabric.py`
- `scripts/manage_feature_workspaces.py`
- `workspaces/Fabric Blueprint/config.yml`
- `feature-workspaces.yml`

## 1. Mandatory Setup for the Stable Deployment Flow

These items are required for the normal repository lifecycle:

- Terraform provisions Fabric workspaces.
- GitHub Actions runs Terraform and content deployment.
- Python deployment scripts publish content into pre-created workspaces.

### 1.1 Service Principal

Create one Microsoft Entra ID application / Service Principal for CI/CD.

This repository expects the following GitHub secrets to come from that Service Principal:

- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_TENANT_ID`

This same Service Principal is used by:

- `terraform.yml`
- `fabric-deploy.yml`
- optional feature workspace workflows

#### Service Principal permissions required

Required:

- Access to authenticate against Microsoft Fabric from GitHub Actions.
- Access to authenticate against Azure for the Terraform backend state storage.
- Permission to create Fabric workspaces through Terraform.
- Permission to deploy content into the target Fabric workspaces.

Required Azure permission:

- `Storage Blob Data Contributor` on the Azure Storage Account that holds Terraform state.

Required effective Fabric access:

- For Terraform-created workspaces, the repo assumes the creating Service Principal becomes `Admin` on the workspace automatically.
- For content deployment, the Service Principal must be able to access the target workspace and deploy items into it.

Operational assumption inferred from the repo:

- The tenant must allow this Service Principal to use the Fabric APIs / provider / deployment tooling used by the workflows. The repository uses Service Principal authentication everywhere, so tenant policy must not block that pattern.

### 1.2 Entra ID Admin Group

Create an Entra ID security group that should remain the human-admin owner of each workspace.

The repository expects its Object ID in Terraform as:

- `entra_admin_group_object_id`

Current Terraform behavior:

- the group is assigned the Fabric workspace role `Admin`
- assignment is done by `fabric_workspace_role_assignment`

#### Admin group permissions required

Required Fabric workspace role:

- `Admin` on each stable workspace

Purpose of this group:

- human break-glass and operational administration
- workspace access independent of the CI/CD Service Principal
- manual validation and support when deployments fail

Recommended operating model:

- use one shared admin group across all stages, or one per environment if your governance model requires separation
- if you use environment-specific groups, provide the correct Object ID in each `terraform/environments/*.tfvars`

### 1.3 Fabric Capacities

Provide a Fabric capacity for each environment that will host the workspace.

The repository expects:

- `capacity_id` in `terraform/environments/dev.tfvars`
- `capacity_id` in `terraform/environments/test.tfvars`
- `capacity_id` in `terraform/environments/prod.tfvars`

Current workspace names expected by the sample content:

- Dev: `[D] Fabric Blueprint`
- Test: `[T] Fabric Blueprint`
- Prod: `[P] Fabric Blueprint`

Capacity requirement:

- each target workspace must be assignable to the provided capacity ID

What IT needs to provide for each environment:

- capacity display name
- capacity GUID (`capacity_id`)
- confirmation that workspace creation on that capacity is allowed

### 1.4 Azure Storage for Terraform State

Create Azure Blob Storage for Terraform state, or provide an existing one and update `terraform/main.tf`.

The current repository defaults are:

- resource group: `rg-fabric-cicd-tfstate`
- storage account: `stsfabriccicdtfstate`
- container: `tfstate`

Required Azure details:

- `ARM_SUBSCRIPTION_ID`
- storage account scope where the Service Principal gets `Storage Blob Data Contributor`

Required access:

- the CI/CD Service Principal must have `Storage Blob Data Contributor` on the storage account scope

### 1.5 GitHub Environments

Create these GitHub Environments exactly:

- `dev`
- `test`
- `prod`

Why:

- the workflows reference these names directly
- environment protection and approvals can be configured there

### 1.6 GitHub Secrets

Create these repository secrets:

- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_TENANT_ID`
- `ARM_SUBSCRIPTION_ID`

Secret usage:

- `terraform.yml` uses all four
- `fabric-deploy.yml` uses the `AZURE_*` secrets
- optional feature workspace workflows also use the `AZURE_*` secrets

## 2. Exact Items IT Must Create

For the stable flow, IT should create or provide the following:

| Item | Mandatory | What to create / provide | Used by |
|---|---|---|---|
| Entra application + Service Principal | Yes | Client ID, secret, tenant ID | Terraform, deploy workflow, optional feature flow |
| Entra admin security group | Yes | Group Object ID | Terraform workspace role assignment |
| Fabric capacity for Dev | Yes | Capacity GUID | Dev workspace creation |
| Fabric capacity for Test | Yes | Capacity GUID | Test workspace creation |
| Fabric capacity for Prod | Yes | Capacity GUID | Prod workspace creation |
| Azure resource group for tfstate | Yes | Resource group | Terraform backend |
| Azure storage account for tfstate | Yes | Storage account | Terraform backend |
| Azure Blob container for tfstate | Yes | Container | Terraform backend |
| GitHub repository secrets | Yes | `AZURE_*`, `ARM_SUBSCRIPTION_ID` | GitHub Actions |
| GitHub Environments | Yes | `dev`, `test`, `prod` | GitHub Actions |

## 3. Exact Values IT Must Hand Over to the Project Team

At minimum, the project team needs these values:

| Value | Format | Where used |
|---|---|---|
| `AZURE_CLIENT_ID` | GUID / app ID | GitHub secrets |
| `AZURE_CLIENT_SECRET` | secret value | GitHub secrets |
| `AZURE_TENANT_ID` | GUID | GitHub secrets |
| `ARM_SUBSCRIPTION_ID` | GUID | GitHub secrets |
| `entra_admin_group_object_id` | GUID | `terraform/environments/*.tfvars` |
| `capacity_id` for Dev | GUID | `terraform/environments/dev.tfvars` |
| `capacity_id` for Test | GUID | `terraform/environments/test.tfvars` |
| `capacity_id` for Prod | GUID | `terraform/environments/prod.tfvars` |

The project team also needs confirmation of:

- the exact workspace names to be used per environment
- whether the same admin group is used across all stages or one per stage
- whether the same Fabric capacity is shared across stages or separate capacities are used

## 4. Permission Matrix

### 4.1 CI/CD Service Principal

| Target | Permission / role needed | Why |
|---|---|---|
| Azure Storage Account for tfstate | `Storage Blob Data Contributor` | Terraform backend state read/write |
| Fabric tenant | Service Principal authentication must be allowed | All workflows authenticate non-interactively |
| Stable Fabric workspaces | Effective workspace access to deploy content | `fabric-deploy.yml` publishes items |
| Fabric workspace creation | Ability to create workspaces via Terraform | `terraform.yml` provisions workspaces |

Notes:

- The repo explicitly states that the Service Principal automatically becomes workspace `Admin` on workspaces it creates.
- If a workspace already exists outside Terraform, the Service Principal still needs enough workspace access for content deployment.

### 4.2 Entra Admin Group

| Target | Permission / role needed | Why |
|---|---|---|
| Stable Fabric workspaces | `Admin` | Terraform assigns this role intentionally |

### 4.3 GitHub Repository Admin

| Target | Permission / role needed | Why |
|---|---|---|
| GitHub repository | Ability to create secrets | Store `AZURE_*` and `ARM_SUBSCRIPTION_ID` |
| GitHub repository | Ability to create environments | `dev`, `test`, `prod` are workflow targets |
| GitHub environments | Optional approval / protection setup | Promote safely to `test` and `prod` |

## 5. Optional Setup for Feature Workspace Lifecycle

This is only needed if you want ephemeral workspaces for `feature/**` and `bugfix/**` branches.

The feature flow is driven by:

- `.github/workflows/feature-workspace-create.yml`
- `.github/workflows/feature-workspace-cleanup.yml`
- `scripts/manage_feature_workspaces.py`
- `feature-workspaces.yml`

### 5.1 Additional items to create

| Item | Mandatory for feature flow | What to create / provide |
|---|---|---|
| Feature workspace capacity | Yes | `capacity_id` in `feature-workspaces.yml` |
| Fabric Git connection | Yes | either `connection_name` or `connection_id` |
| GitHub repository details | Yes | repository owner and name in `feature-workspaces.yml` |
| Feature workspace ACL principals | Yes | principal IDs and roles in `feature-workspaces.yml` |

Current sample configuration expects:

- `git.provider_type: GitHub`
- `git.connection_name: github-default`
- repository owner and repository name
- at least one ACL entry in `permissions`

### 5.2 Feature flow permissions required

The CI/CD Service Principal needs effective ability to:

- create feature workspaces
- delete feature workspaces
- set workspace ACLs
- connect workspaces to the Fabric Git connection
- initialize workspaces from Git
- run update-from-git during initial seed

The principals listed in `feature-workspaces.yml` need whichever workspace role you assign there.

Current sample role:

- `Admin`

### 5.3 Fabric Git connection requirements

IT or a Fabric admin must create an existing Fabric Git connection that points to the GitHub repository used by this project.

The repository requires either:

- `git.connection_name`
- or `git.connection_id`

The connection must be usable by the CI/CD Service Principal.

The script connects each feature workspace to:

- provider: `GitHub`
- branch: the created `feature/**` or `bugfix/**` branch
- directory: `workspaces/<workspace folder>`

## 6. Repository-Specific Naming and Mapping Rules

These values must stay aligned across infrastructure and deployment:

- `terraform/environments/*.tfvars` -> `workspace_name`
- `workspaces/Fabric Blueprint/config.yml` -> `core.workspace.dev|test|prod`

Current expected names:

- `[D] Fabric Blueprint`
- `[T] Fabric Blueprint`
- `[P] Fabric Blueprint`

If IT requests different workspace names, the project team must update both Terraform and workspace config.

## 7. Recommended Delivery Checklist for IT

IT can use this as the handoff checklist.

### Stable flow

- [ ] Create the CI/CD Service Principal
- [ ] Provide `AZURE_CLIENT_ID`
- [ ] Provide `AZURE_CLIENT_SECRET`
- [ ] Provide `AZURE_TENANT_ID`
- [ ] Create the Entra admin group
- [ ] Provide `entra_admin_group_object_id`
- [ ] Provide the Dev capacity ID
- [ ] Provide the Test capacity ID
- [ ] Provide the Prod capacity ID
- [ ] Create the Azure Storage Account backend for Terraform state
- [ ] Grant the Service Principal `Storage Blob Data Contributor` on the storage account
- [ ] Provide `ARM_SUBSCRIPTION_ID`
- [ ] Create GitHub Environments `dev`, `test`, `prod`
- [ ] Confirm the tenant allows the Service Principal authentication pattern used by this repository

### Optional feature workspace flow

- [ ] Provide a feature-workspace capacity ID
- [ ] Create or provide a Fabric Git connection for this repository
- [ ] Provide `connection_name` or `connection_id`
- [ ] Confirm the Service Principal can use that Git connection
- [ ] Provide the principals and roles to apply to feature workspaces

## 8. Out of Scope for IT

These are project-team tasks, not IT-admin creation tasks:

- editing `workspaces/**` content
- maintaining `parameter.yml` find/replace rules
- keeping notebook metadata intact
- updating Terraform code when new workspaces are added
- validating unmapped GUID coverage
- running pytest and deployment checks

## 9. Fast Summary

If IT only wants the shortest possible request list, ask for this:

1. One Entra Service Principal for GitHub Actions, with:
   `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`
2. One Entra admin security group, with:
   `entra_admin_group_object_id`
3. Fabric capacity IDs for:
   Dev, Test, Prod
4. Azure subscription and storage access for Terraform state, including:
   `ARM_SUBSCRIPTION_ID` and `Storage Blob Data Contributor` for the Service Principal
5. GitHub Environments:
   `dev`, `test`, `prod`
6. Optional only for feature workspaces:
   feature capacity, Fabric Git connection, and ACL principal list
