"""Tests for semantic model GUID coverage in check_unmapped_ids scanner."""

from pathlib import Path

from scripts.check_unmapped_ids import scan_workspace


def _create_workspace_root(tmp_path: Path, with_rules: bool) -> tuple[Path, str]:
    workspace_name = "Test Workspace"
    workspaces_dir = tmp_path / "workspaces"
    workspace_dir = workspaces_dir / workspace_name
    semantic_model_dir = workspace_dir / "3_Gold" / "Sample.SemanticModel" / "definition"

    semantic_model_dir.mkdir(parents=True)
    (workspace_dir / "config.yml").write_text(
        "core:\n  workspace:\n    dev: \"[D] Test Workspace\"\n", encoding="utf-8"
    )

    one_lake_workspace_id = "11111111-1111-1111-1111-111111111111"
    one_lake_item_id = "22222222-2222-2222-2222-222222222222"

    if with_rules:
        (workspace_dir / "parameter.yml").write_text(
            f"""
find_replace:
  - find_value: "{one_lake_workspace_id}"
    replace_value:
      _ALL_: "$workspace.$id"
    item_type: "SemanticModel"
    file_path: "**/*.SemanticModel/definition/expressions.tmdl"
  - find_value: "{one_lake_item_id}"
    replace_value:
      _ALL_: "$items.Lakehouse.lakehouse_gold.$id"
    item_type: "SemanticModel"
    file_path: "**/*.SemanticModel/definition/expressions.tmdl"
""".strip()
            + "\n",
            encoding="utf-8",
        )
    else:
        (workspace_dir / "parameter.yml").write_text("find_replace: []\n", encoding="utf-8")

    (semantic_model_dir / "expressions.tmdl").write_text(
        f"""
expression 'DirectLake - lakehouse_gold' =
        let
            Source = AzureStorage.DataLake("https://onelake.dfs.fabric.microsoft.com/{one_lake_workspace_id}/{one_lake_item_id}", [HierarchicalNavigation=true])
        in
            Source
    lineageTag: aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
""".strip()
        + "\n",
        encoding="utf-8",
    )

    return workspaces_dir, workspace_name


def test_scan_workspace_detects_unmapped_semantic_model_ids(tmp_path: Path) -> None:
    workspaces_dir, workspace_name = _create_workspace_root(tmp_path, with_rules=False)

    unmapped = scan_workspace(
        workspace_folder=workspace_name,
        workspaces_dir=workspaces_dir,
        repo_root=tmp_path,
    )

    assert len(unmapped) == 2
    assert {u.field_name for u in unmapped} == {"onelake_workspace_id", "onelake_item_id"}
    assert all(u.item_type == "SemanticModel" for u in unmapped)


def test_scan_workspace_semantic_model_ids_covered_by_rules(tmp_path: Path) -> None:
    workspaces_dir, workspace_name = _create_workspace_root(tmp_path, with_rules=True)

    unmapped = scan_workspace(
        workspace_folder=workspace_name,
        workspaces_dir=workspaces_dir,
        repo_root=tmp_path,
    )

    assert unmapped == []
