from __future__ import annotations

import subprocess
import sys
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SUPPORTED_SERVER_TRANSPORTS = ["streamable-http", "sse"]
DEFAULT_SERVER_HOST = "0.0.0.0"
DEFAULT_SERVER_PORT = 7000

REPO_ROOT = Path(__file__).resolve().parents[3]
SERVER_SCRIPT = REPO_ROOT / "server" / "server.py"
LOG_FILE = REPO_ROOT / "server" / "managed_server.log"


def default_path_for_transport(transport: str) -> str:
    return "/sse" if transport == "sse" else "/mcp"


def format_uptime(started_at: float | None) -> str:
    if not started_at:
        return "n/a"
    elapsed = max(0, int(time.time() - started_at))
    hours, remainder = divmod(elapsed, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class ManagedServerRuntime:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._process: subprocess.Popen[str] | None = None
        self._log_handle: Any | None = None
        self._started_at: float | None = None
        self._config: dict[str, Any] = {
            "transport": "streamable-http",
            "protocol_version": "2025-11-25",
            "host": DEFAULT_SERVER_HOST,
            "port": DEFAULT_SERVER_PORT,
        }
        self._last_error: str | None = None
        self._last_exit_code: int | None = None

    def _close_handle(self) -> None:
        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None

    def _reap_if_needed(self) -> None:
        if not self._process:
            return
        return_code = self._process.poll()
        if return_code is None:
            return
        self._last_exit_code = return_code
        if self._last_error is None and return_code != 0:
            self._last_error = f"Server exited with code {return_code}."
        self._process = None
        self._started_at = None
        self._close_handle()

    def _status_unlocked(self) -> dict[str, Any]:
        running = self._process is not None and self._process.poll() is None
        config = dict(self._config)
        path = default_path_for_transport(config["transport"])
        return {
            "running": running,
            "state": "running" if running else "stopped",
            "transport": config["transport"],
            "protocol_version": config["protocol_version"],
            "host": config["host"],
            "port": config["port"],
            "path": path,
            "endpoint_url": f"http://{config['host']}:{config['port']}{path}",
            "pid": self._process.pid if running and self._process else None,
            "uptime": format_uptime(self._started_at),
            "started_at": (
                datetime.fromtimestamp(self._started_at, tz=timezone.utc).isoformat()
                if self._started_at
                else None
            ),
            "last_error": self._last_error,
            "last_exit_code": self._last_exit_code,
            "log_file": str(LOG_FILE),
        }

    def status(self) -> dict[str, Any]:
        with self._lock:
            self._reap_if_needed()
            return self._status_unlocked()

    def start(self, *, transport: str, protocol_version: str, host: str, port: int) -> dict[str, Any]:
        with self._lock:
            self._reap_if_needed()
            if self._process and self._process.poll() is None:
                raise RuntimeError("The managed MCP server is already running.")

            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            self._config = {
                "transport": transport,
                "protocol_version": protocol_version,
                "host": host,
                "port": port,
            }
            self._last_error = None
            self._last_exit_code = None
            self._log_handle = LOG_FILE.open("a", encoding="utf-8")
            self._log_handle.write(
                f"\n[{datetime.now(timezone.utc).isoformat()}] Starting managed MCP server.\n"
            )
            self._log_handle.flush()

            self._process = subprocess.Popen(
                [
                    sys.executable,
                    str(SERVER_SCRIPT),
                    "--transport",
                    transport,
                    "--host",
                    host,
                    "--port",
                    str(port),
                    "--protocol-version",
                    protocol_version,
                ],
                cwd=str(REPO_ROOT),
                stdout=self._log_handle,
                stderr=subprocess.STDOUT,
                text=True,
            )
            self._started_at = time.time()

            time.sleep(0.8)
            self._reap_if_needed()
            if not self._process:
                logs = "\n".join(self.tail_logs(20))
                raise RuntimeError(
                    "The managed MCP server exited immediately."
                    + (f" Recent logs:\n{logs}" if logs else "")
                )
            return self._status_unlocked()

    def stop(self) -> dict[str, Any]:
        with self._lock:
            self._reap_if_needed()
            if not self._process:
                return self._status_unlocked()

            process = self._process
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

            self._last_exit_code = process.returncode
            self._process = None
            self._started_at = None
            self._close_handle()
            return self._status_unlocked()

    def restart(self, *, transport: str, protocol_version: str, host: str, port: int) -> dict[str, Any]:
        with self._lock:
            self._reap_if_needed()
            if self._process:
                process = self._process
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                self._last_exit_code = process.returncode
                self._process = None
                self._started_at = None
                self._close_handle()
        return self.start(
            transport=transport,
            protocol_version=protocol_version,
            host=host,
            port=port,
        )

    def tail_logs(self, max_lines: int = 80) -> list[str]:
        if not LOG_FILE.exists():
            return []
        with LOG_FILE.open("r", encoding="utf-8", errors="replace") as handle:
            return list(deque((line.rstrip("\n") for line in handle), maxlen=max_lines))

    def clear_logs(self) -> list[str]:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        if self._log_handle is not None:
            self._log_handle.flush()
            self._log_handle.close()
            self._log_handle = LOG_FILE.open("w", encoding="utf-8")
        else:
            with LOG_FILE.open("w", encoding="utf-8"):
                pass
        return self.tail_logs()


managed_server = ManagedServerRuntime()
