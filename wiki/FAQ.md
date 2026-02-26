# FAQ

## What is this repository?

A Fabric CI/CD toolkit:
- Terraform provisions workspaces and group role assignment.
- Python scripts + `fabric-cicd` deploy workspace items.
- GitHub Actions runs CI and deployment workflows.

## Is `Fabric Blueprint` a recommended target architecture?

No. It is minimal sample content to demonstrate deployment mechanics.

## Which files do I need to change first?

1. `terraform/environments/dev.tfvars`
2. `terraform/environments/test.tfvars`
3. `terraform/environments/prod.tfvars`
4. `workspaces/Fabric Blueprint/config.yml`
5. `workspaces/Fabric Blueprint/parameter_templates/*.yml`
6. GitHub secrets (`AZURE_*`, `ARM_SUBSCRIPTION_ID`)

## Does the deployment workflow create workspaces automatically?

No. Workspaces are expected to be provisioned by Terraform first.

## Why did my merge not auto-deploy?

`fabric-deploy.yml` only auto-triggers when `workspaces/**` changes are pushed to `main`.

## Why did CI fail with unmapped GUIDs?

At least one GUID found in item files is not covered by a find/replace rule in `parameter.yml` (or extended templates). Add mappings and rerun scanner.

## Is there automatic rollback if one workspace deployment fails?

No. The workflow fails on error, but there is no automatic rollback implementation.

## Can I deploy multiple workspaces from this repository?

Yes. Any workspace folder under `workspaces/` with `config.yml` is discovered and processed.

## What is the minimum required secret set?

- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_TENANT_ID`
- `ARM_SUBSCRIPTION_ID`

## Do workspace names have to match between Terraform and config files?

Yes, exactly. Mismatches are a common cause of deployment failure.

## Which environments are supported by workflows?

Exact names:
- `dev`
- `test`
- `prod`

## Where should I debug failures first?

1. GitHub Actions job logs.
2. `terraform/environments/*.tfvars` values.
3. Workspace `config.yml` and `parameter.yml`.
4. Local scanner/test commands.
