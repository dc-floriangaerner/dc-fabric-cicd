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
        return self._execute(command, check=check)

    def run_command(self, command: str, *, check: bool = True) -> FabCommandResult:
        return self._execute(["fab", "-c", command], check=check)

    def _execute(self, command: list[str], *, check: bool = True) -> FabCommandResult:
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
        return self._parse_json_result(result)

    def run_json_command(self, command: str, *, check: bool = True) -> Any:
        result = self.run_command(command, check=check)
        return self._parse_json_result(result)

    def run_api(self, endpoint: str, *, method: str = "get", input_data: Any | None = None, show_headers: bool = False) -> dict[str, Any]:
        command = f"api -X {method} {endpoint}"
        if input_data is not None:
            command += f" -i {json.dumps(input_data)}"
        if show_headers:
            command += " --show_headers"
        payload = self.run_json_command(command)
        return self._normalize_api_response(payload, command=command)

    def run_api_text(
        self,
        endpoint: str,
        *,
        method: str = "get",
        input_data: Any | None = None,
        show_headers: bool = False,
    ) -> Any:
        response = self.run_api(endpoint, method=method, input_data=input_data, show_headers=show_headers)
        return response["text"]

    def _parse_json_result(self, result: FabCommandResult) -> Any:
        if not result.stdout:
            return {}
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise FabCliError(
                f"Fabric CLI command did not return JSON: {' '.join(result.command)}\n{result.stdout}",
                result,
            ) from exc

    def _normalize_api_response(self, payload: Any, *, command: str) -> dict[str, Any]:
        if isinstance(payload, dict) and (
            "status_code" in payload or "text" in payload or "headers" in payload
        ):
            status_code = payload.get("status_code")
            if isinstance(status_code, int) and status_code >= 400:
                raise FabCliError(
                    f"Fabric CLI API command failed: fab -c {command}\n{json.dumps(payload)}",
                    FabCommandResult(command=["fab", "-c", command], returncode=1, stdout=json.dumps(payload), stderr=""),
                )
            return {
                "status_code": status_code,
                "text": payload.get("text"),
                "headers": payload.get("headers", {}),
                "raw": payload,
            }

        return {
            "status_code": None,
            "text": payload,
            "headers": {},
            "raw": payload,
        }
