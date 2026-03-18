"""Thin Fabric CLI wrapper for feature workspace automation."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class FabCommandResult:
    """Captured result from a `fab` CLI invocation."""

    command: list[str]
    returncode: int
    stdout: str
    stderr: str


class FabCliError(RuntimeError):
    """Raised when a `fab` command fails."""

    def __init__(self, message: str, result: FabCommandResult):
        super().__init__(message)
        self.result = result


class FabCli:
    """Small helper to execute Fabric CLI commands consistently."""

    def run(self, args: list[str], *, check: bool = True) -> FabCommandResult:
        command = ["fab", *args]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        result = FabCommandResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout.strip(),
            stderr=completed.stderr.strip(),
        )
        if check and result.returncode != 0:
            detail = result.stderr or result.stdout or "No output returned."
            raise FabCliError(f"Fabric CLI command failed: {' '.join(command)}\n{detail}", result)
        return result

    def run_json(self, args: list[str], *, check: bool = True) -> Any:
        result = self.run(args, check=check)
        if not result.stdout:
            return {}
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise FabCliError(
                f"Fabric CLI command did not return JSON: {' '.join(result.command)}\n{result.stdout}",
                result,
            ) from exc
