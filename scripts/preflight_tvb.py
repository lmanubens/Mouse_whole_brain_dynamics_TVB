#!/usr/bin/env python3
"""
TVB preflight checks for Mouse_whole_brain_dynamics_TVB.

Purpose:
- Validate Python/dependency baseline before running notebooks.
- Detect missing critical packages (e.g., allensdk).
- Check connectivity to external services used by siibra/TVB adapters.
"""

from __future__ import annotations

import importlib
import socket
import sys
from urllib.parse import urlparse

import requests

REQUIRED_IMPORTS = [
    "tvb",
    "allensdk",
    "siibra",
    "numpy",
    "scipy",
    "pandas",
]

ENDPOINTS = [
    "https://api.github.com",
    "https://gitlab.ebrains.eu",
]


def check_imports() -> tuple[bool, list[str]]:
    failures: list[str] = []
    for mod in REQUIRED_IMPORTS:
        try:
            importlib.import_module(mod)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{mod}: {type(exc).__name__}: {exc}")
    return (len(failures) == 0, failures)


def _check_dns(host: str, port: int = 443, timeout: float = 5.0) -> tuple[bool, str]:
    try:
        socket.setdefaulttimeout(timeout)
        socket.getaddrinfo(host, port)
        return True, "ok"
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def check_http(url: str, timeout: float = 10.0) -> tuple[bool, str]:
    host = urlparse(url).hostname or ""
    dns_ok, dns_msg = _check_dns(host)
    if not dns_ok:
        return False, f"DNS failed ({host}): {dns_msg}"

    try:
        response = requests.get(url, timeout=timeout)
        return True, f"HTTP {response.status_code}"
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    print("== TVB Preflight ==")
    print(f"Python: {sys.version}")

    imports_ok, import_failures = check_imports()
    print("\n[Imports]")
    if imports_ok:
        print("  PASS: all required imports available")
    else:
        print("  FAIL: missing/broken imports:")
        for item in import_failures:
            print(f"    - {item}")

    print("\n[Network]")
    network_ok = True
    for endpoint in ENDPOINTS:
        ok, msg = check_http(endpoint)
        status = "PASS" if ok else "FAIL"
        print(f"  {status}: {endpoint} -> {msg}")
        network_ok = network_ok and ok

    overall_ok = imports_ok and network_ok
    print("\n[Result]")
    if overall_ok:
        print("  PASS: environment ready for TVB notebook execution")
        return 0

    print("  FAIL: environment not ready. Resolve failures above and retry.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
