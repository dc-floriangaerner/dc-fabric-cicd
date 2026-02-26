# Troubleshooting

Common issues in this toolkit and how to resolve them quickly.

## 1) Authentication Fails

Symptoms:
- `ClientSecretCredential authentication failed`
- token acquisition errors in deploy or Terraform jobs

Checks:
1. Verify repo secrets exist and are correct:
   - `AZURE_CLIENT_ID`
   - `AZURE_CLIENT_SECRET`
   - `AZURE_TENANT_ID`
   - `ARM_SUBSCRIPTION_ID` (Terraform)
2. Verify Service Principal secret is not expired.
3. Verify Service Principal is in the expected tenant.

## 2) Workspace Not Found

Symptoms:
- deployment fails with workspace not found for target environment

Checks:
1. Confirm `terraform.yml` ran successfully for that environment.
2. Compare names exactly:
   - `terraform/environments/<env>.tfvars` -> `workspace_name`
   - `workspaces/Fabric Blueprint/config.yml` -> `core.workspace.<env>`
3. Verify Service Principal has access to that workspace.

## 3) No Workspaces Discovered

Symptoms:
- deploy script reports no workspaces with `config.yml`

Checks:
1. Ensure workspace folders are directly under `workspaces/`.
2. Ensure each workspace contains `config.yml`.
3. Validate YAML:
   - `python -c "import yaml; yaml.safe_load(open('workspaces/Fabric Blueprint/config.yml', encoding='utf-8'))"`

## 4) Unmapped GUID Scan Fails

Symptoms:
- `scripts.check_unmapped_ids` reports unmapped GUIDs

Cause:
- one or more Dev GUIDs exist in item files but are not covered by find/replace rules.

Fix:
1. Add or update rules in workspace `parameter.yml` or extended templates.
2. Re-run:
   - `python -m scripts.check_unmapped_ids --workspaces_directory workspaces`

## 5) Item Deployment Fails

Symptoms:
- item publish errors during `deploy_to_fabric.py`

Checks:
1. Confirm item folder structure follows Fabric export conventions.
2. Confirm notebook metadata markers remain intact in `notebook-content.py`.
3. Confirm JSON files are valid:
   - `python -m json.tool <path-to-json>`
4. Review mapping rules for item-specific IDs.

## 6) Terraform Fails

Symptoms:
- `terraform init/plan/apply` errors in workflow

Checks:
1. Confirm backend storage exists and backend settings in `terraform/main.tf` are valid.
2. Confirm Service Principal has Blob role on state storage account.
3. Confirm tfvars have real values (not placeholder GUIDs).
4. Confirm `ARM_SUBSCRIPTION_ID` is configured.

## 7) Deployment Not Triggered Automatically

Facts:
- `fabric-deploy.yml` auto-trigger requires `workspaces/**` changes on push to `main`.
- `terraform.yml` auto-trigger requires `terraform/**` changes on push to `main`.

Fix:
- Use manual workflow dispatch when no auto-triggering paths changed.

## 8) Partial Deployment Concern

Current behavior:
- workspace deployments run sequentially.
- if one workspace fails, the job fails.
- there is no automatic rollback.

Action:
- inspect logs for the failed workspace.
- fix root cause and rerun workflow.

## Useful Commands

```bash
python -m scripts.check_unmapped_ids --workspaces_directory workspaces
pytest tests/ -v
python -m scripts.deploy_to_fabric --workspaces_directory workspaces --environment dev
```

## Next References

- [Setup Guide](Setup-Guide)
- [Workspace Configuration](Workspace-Configuration)
- [Deployment Workflow](Deployment-Workflow)
