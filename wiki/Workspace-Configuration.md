# Workspace Configuration

This page explains the deployment contract for each workspace folder.

## Required Files Per Workspace

Each folder under `workspaces/` must contain:
- `config.yml` (required for discovery)
- `parameter.yml` (required for transformations)

If `config.yml` is missing, the workspace is not discovered by deployment scripts.

## `config.yml` Contract

Current sample (`workspaces/Fabric Blueprint/config.yml`) contains:
- `core.workspace.dev`
- `core.workspace.test`
- `core.workspace.prod`
- `core.repository_directory`
- `core.parameter`
- `publish.skip.*`
- `unpublish.skip.*`
- `features`

Example:

```yaml
core:
  workspace:
    dev: "[D] Fabric Blueprint"
    test: "[T] Fabric Blueprint"
    prod: "[P] Fabric Blueprint"
  repository_directory: "."
  parameter: "parameter.yml"
```

Critical rule:
- Workspace names in `config.yml` must match names provisioned by Terraform in `terraform/environments/*.tfvars`.

## `parameter.yml` Contract

`parameter.yml` contains transformation rules (`find_replace`) and can extend template files.

Current sample:

```yaml
extend:
  - "./parameter_templates/nb_parameters.yml"
  - "./parameter_templates/cp_parameters.yml"
```

This means rule content is stored in template files, while `parameter.yml` acts as a root aggregator.

## What Must Be Parameterized

The scanner `scripts/check_unmapped_ids.py` checks for uncovered GUIDs in:
- Notebook `# META` fields:
  - `default_lakehouse`
  - `default_lakehouse_workspace_id`
  - `default_lakehouse_sql_endpoint`
  - `known_lakehouses` ID entries
- JSON content fields:
  - `workspaceId`
  - `artifactId`
  - `lakehouseId`
  - `connectionId`

If a GUID is found without matching find/replace coverage, CI fails.

## Rule Format

A typical rule:

```yaml
find_replace:
  - find_value: "12345678-1234-1234-1234-123456789abc"
    replace_value:
      _ALL_: "$items.Lakehouse.lakehouse_bronze.id"
    item_type: "Notebook"
```

Useful optional fields:
- `is_regex: "true"`
- `item_type`
- `item_name`
- `file_path`
- `description`

## Validation Commands

Run before PR:

```bash
python -m scripts.check_unmapped_ids --workspaces_directory workspaces
pytest tests/ -v
```

Validate YAML locally:

```bash
python -c "import yaml; yaml.safe_load(open('workspaces/Fabric Blueprint/config.yml', encoding='utf-8'))"
python -c "import yaml; yaml.safe_load(open('workspaces/Fabric Blueprint/parameter.yml', encoding='utf-8'))"
```

## Adding a New Workspace

1. Create `workspaces/<Workspace Name>/`.
2. Add `config.yml` and `parameter.yml`.
3. Add Fabric item folders/files using normal Fabric structure.
4. Add matching Terraform resources and tfvars values.
5. Keep workspace names identical across Terraform and `config.yml`.
6. Add find/replace mappings for Dev GUIDs.
7. Run scanner and tests.
