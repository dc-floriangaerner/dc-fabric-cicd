# Setup Guide

This guide gets you from clone to first successful deployment.

## Prerequisites

- Microsoft Fabric tenant and capacity access.
- Permission to create an Entra ID Service Principal.
- GitHub repository admin access (for secrets and environments).
- Azure subscription access for Terraform state storage.

## Step 1: Create Service Principal

Create one Service Principal and capture:
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_TENANT_ID`

The same principal is used by:
- `terraform.yml` (workspace provisioning)
- `fabric-deploy.yml` (content deployment)

## Step 2: Bootstrap Terraform State Storage (One-Time)

Create Azure Blob Storage for Terraform backend state if you do not already have one.

Default backend settings in `terraform/main.tf`:
- `resource_group_name = "rg-fabric-cicd-tfstate"`
- `storage_account_name = "stsfabriccicdtfstate"`
- `container_name = "tfstate"`

If you use different names, update `terraform/main.tf` accordingly.

Grant the Service Principal `Storage Blob Data Contributor` on the storage account scope.

## Step 3: Configure Terraform Inputs

Edit all environment files:
- `terraform/environments/dev.tfvars`
- `terraform/environments/test.tfvars`
- `terraform/environments/prod.tfvars`

Set real values for:
- `workspace_name`
- `capacity_id`
- `entra_admin_group_object_id`

Important:
- `workspace_name` must match the workspace name in `workspaces/Fabric Blueprint/config.yml` for the same environment.
- Placeholder GUIDs like `00000000-0000-0000-0000-000000000000` must be replaced.

## Step 4: Configure GitHub Secrets

Create repository secrets:
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_TENANT_ID`
- `ARM_SUBSCRIPTION_ID`

## Step 5: Configure GitHub Environments

Create GitHub Environments with exact names:
- `dev`
- `test`
- `prod`

These names are used directly by workflow jobs.

## Step 6: Provision Workspaces

Run workflow:
- GitHub Actions -> `Terraform — Fabric Infrastructure`

Run it for:
1. `dev`
2. `test`
3. `prod`

You can also run Terraform locally:

```bash
cd terraform
terraform init -backend-config="key=fabric-cicd-dev.tfstate"
terraform apply -var-file=environments/dev.tfvars
```

Use the matching state key for `test` and `prod`.

## Step 7: Configure Content Mapping

Update content mapping rules with your real Dev IDs:
- `workspaces/Fabric Blueprint/parameter_templates/nb_parameters.yml`
- `workspaces/Fabric Blueprint/parameter_templates/cp_parameters.yml`

`workspaces/Fabric Blueprint/parameter.yml` already extends these templates.

## Step 8: Validate Locally

Run before opening your first PR:

```bash
python -m scripts.check_unmapped_ids --workspaces_directory workspaces
pytest tests/ -v
```

## Step 9: Deploy

### Dev (automatic)
- Merge a PR to `main` with changes under `workspaces/**`.

### Test/Prod (manual)
- GitHub Actions -> `Deploy to Microsoft Fabric` -> `Run workflow` -> select `test` or `prod`.

The deploy workflow always runs Terraform prerequisites first.

## Done Checklist

- [ ] `terraform/environments/*.tfvars` updated with real IDs
- [ ] Workspace names aligned between tfvars and `config.yml`
- [ ] GitHub secrets configured (`AZURE_*`, `ARM_SUBSCRIPTION_ID`)
- [ ] `terraform.yml` succeeded for `dev`, `test`, `prod`
- [ ] `check_unmapped_ids` passed
- [ ] First deployment to Dev completed

## Next

- [Workspace Configuration](Workspace-Configuration)
- [Deployment Workflow](Deployment-Workflow)
- [Troubleshooting](Troubleshooting)
