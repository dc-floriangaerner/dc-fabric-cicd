"""Tests for the Fabric CLI wrapper."""

from __future__ import annotations

import json
import subprocess

import pytest

from scripts.fabric.fab_cli import FabCli, FabCliError


def _completed(stdout: str = "", stderr: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["fab"], returncode=returncode, stdout=stdout, stderr=stderr)


def test_run_command_uses_fab_c(mocker) -> None:
    run_mock = mocker.patch("subprocess.run", return_value=_completed(stdout="ok"))
    cli = FabCli()

    result = cli.run_command("get 'ws name.Workspace' -q id")

    assert result.stdout == "ok"
    run_mock.assert_called_once()
    assert run_mock.call_args.args[0] == ["fab", "-c", "get 'ws name.Workspace' -q id"]


def test_run_api_text_unwraps_wrapped_payload(mocker) -> None:
    mocker.patch(
        "subprocess.run",
        return_value=_completed(stdout=json.dumps({"status_code": 200, "text": {"id": "abc"}, "headers": {}})),
    )
    cli = FabCli()

    payload = cli.run_api_text("workspaces/abc/git/connection")

    assert payload == {"id": "abc"}


def test_run_api_text_returns_raw_payload_when_cli_does_not_wrap(mocker) -> None:
    mocker.patch("subprocess.run", return_value=_completed(stdout=json.dumps({"id": "abc"})))
    cli = FabCli()

    payload = cli.run_api_text("workspaces/abc/git/connection")

    assert payload == {"id": "abc"}


def test_run_api_raises_for_wrapped_error_payload(mocker) -> None:
    mocker.patch(
        "subprocess.run",
        return_value=_completed(stdout=json.dumps({"status_code": 404, "text": {"errorCode": "NotFound"}})),
    )
    cli = FabCli()

    with pytest.raises(FabCliError, match="Fabric CLI API command failed"):
        cli.run_api("workspaces/abc/git/connection")
