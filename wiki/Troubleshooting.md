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

## 9) Fabric CLI Missing in Feature Workflow

Symptoms:
- `fab: command not found`
- feature workspace workflow fails before any Fabric action

Fix:
1. confirm `ms-fabric-cli` is still present in `requirements.txt`
2. confirm Python setup completed successfully
3. rerun the workflow after fixing the runner step

## 10) Fabric Git Connection Missing or Wrong

Symptoms:
- feature workspace creation fails during Git connect
- connection lookup by `connection_name` fails

Fix:
1. verify `feature-workspaces.yml` uses the correct `connection_id` or `connection_name`
2. confirm the connection already exists in Fabric
3. confirm the service principal can use that connection

## 10a) Fabric CLI Encrypted Cache Error in Feature Workflow

Symptoms:
- `An error occurred with the encrypted cache`
- `Enable plaintext auth token fallback with 'config set encryption_fallback_enabled true'`

Cause:
- the GitHub Actions runner does not expose a usable encrypted credential store for Fabric CLI token caching

Fix:
1. set Fabric CLI fallback before login:
   - `fab config set encryption_fallback_enabled true`
2. rerun the feature workspace create or cleanup workflow
3. if it still fails, confirm the `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, and `AZURE_TENANT_ID` secrets are valid

## 11) Feature Workspace Initialization Failed

Symptoms:
- workspace is created but branch content is not present
- failure during `initializeConnection` or initial update-from-git

Fix:
1. confirm the branch exists remotely
2. confirm the workspace folder exists at `workspaces/<workspace folder>`
3. confirm the Git connection points to the correct repository
4. rerun the create workflow after removing the partial workspace if needed

## 12) Branch Naming Mismatch

Symptoms:
- create or cleanup workflow skips unexpectedly

Checks:
1. branch must match `feature/**` or `bugfix/**`
2. confirm the event payload branch name matches the expected naming scheme
3. confirm `feature-workspaces.yml` branch patterns were not changed accidentally

## 13) Cleanup Drift

Symptoms:
- cleanup workflow succeeds but some feature workspace still exists

Checks:
1. verify the workspace name matches the deterministic naming pattern
2. rerun cleanup because deletion is best-effort and idempotent
3. confirm the service principal still has workspace admin rights

## 14) Later Branch Push Did Not Change the Feature Workspace

This is expected.

Feature workspaces are initialized from Git once, then treated as Fabric-first authoring workspaces.
There is intentionally no auto-sync-on-push workflow for later branch updates because that could overwrite unpublished Fabric-side changes.

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
