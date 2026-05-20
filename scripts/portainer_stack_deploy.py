#!/usr/bin/env python3
"""Create or redeploy the `flotilla` stack on Portainer via the API.

First run: creates a git-backed stack pointing at the GitHub repo + branch +
compose path defined below, passing all relevant .env values as stack env vars.
Subsequent runs: redeploys the existing stack (`pullImage=true, prune=true`) so
fresh image versions are pulled.

Stdlib-only.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV = REPO_ROOT / ".env"

STACK_NAME = "flotilla"
ENDPOINT_ID = 2  # 'local' endpoint on dtr; discovered via inventory
REPO_URL = "https://github.com/zbmowrey/flotilla"
REPO_REF = "refs/heads/main"
COMPOSE_PATH = "docker-compose.yml"

# Keys in .env that exist for these scripts, not for compose itself.
LOCAL_ONLY_KEYS = {"PORTAINER_URL", "PORTAINER_ACCESS_TOKEN"}


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    text = path.read_text(encoding="utf-8")
    if text.startswith("﻿"):
        text = text[1:]
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        v = v.strip().strip('"').strip("'")
        env[k.strip()] = v
    return env


def api(method: str, base: str, token: str, path: str, body=None, params=None):
    url = f"{base.rstrip('/')}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    data = None
    headers = {"X-API-Key": token}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:1000]
        raise SystemExit(f"{method} {path} -> HTTP {e.code} {e.reason}\n{detail}") from e
    if not payload:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return payload.decode("utf-8", errors="replace")


def stack_env_payload(env: dict[str, str]) -> list[dict[str, str]]:
    return [
        {"name": k, "value": v}
        for k, v in sorted(env.items())
        if k not in LOCAL_ONLY_KEYS and v != ""
    ]


def find_stack(base: str, token: str, name: str) -> dict | None:
    stacks = api("GET", base, token, "/api/stacks") or []
    for s in stacks:
        if s.get("Name") == name:
            return s
    return None


def create_stack(base: str, token: str, env: dict[str, str]) -> dict:
    body = {
        "name": STACK_NAME,
        "repositoryURL": REPO_URL,
        "repositoryReferenceName": REPO_REF,
        "composeFile": COMPOSE_PATH,
        "repositoryAuthentication": False,
        "env": stack_env_payload(env),
    }
    print(f"creating stack '{STACK_NAME}' from {REPO_URL} @ {REPO_REF}")
    return api(
        "POST",
        base,
        token,
        "/api/stacks/create/standalone/repository",
        body=body,
        params={"endpointId": ENDPOINT_ID},
    )


def redeploy_stack(base: str, token: str, stack: dict, env: dict[str, str]) -> dict:
    sid = stack["Id"]
    body = {
        "env": stack_env_payload(env),
        "prune": True,
        "pullImage": True,
        "repositoryReferenceName": REPO_REF,
        "repositoryAuthentication": False,
    }
    print(f"redeploying stack '{stack['Name']}' (id={sid}) with pullImage=true")
    return api(
        "PUT",
        base,
        token,
        f"/api/stacks/{sid}/git/redeploy",
        body=body,
        params={"endpointId": ENDPOINT_ID},
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--env-file", type=Path, default=DEFAULT_ENV)
    p.add_argument("--force-create", action="store_true",
                   help="If the stack already exists, delete and recreate instead of redeploying.")
    args = p.parse_args()

    env = load_env(args.env_file)
    base = env.get("PORTAINER_URL")
    token = env.get("PORTAINER_ACCESS_TOKEN")
    if not base or not token:
        print("PORTAINER_URL and PORTAINER_ACCESS_TOKEN must be set in .env", file=sys.stderr)
        return 2

    existing = find_stack(base, token, STACK_NAME)
    if existing and args.force_create:
        print(f"deleting existing stack id={existing['Id']}")
        api("DELETE", base, token, f"/api/stacks/{existing['Id']}",
            params={"endpointId": ENDPOINT_ID})
        existing = None

    if existing:
        result = redeploy_stack(base, token, existing, env)
    else:
        result = create_stack(base, token, env)

    print("done.")
    if isinstance(result, dict):
        for k in ("Id", "Name", "Status", "EndpointId", "GitConfig"):
            if k in result:
                print(f"  {k}: {result[k]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
