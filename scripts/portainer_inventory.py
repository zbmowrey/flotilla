#!/usr/bin/env python3
"""Snapshot the current Portainer state into ./inventory/.

Reads PORTAINER_URL and PORTAINER_ACCESS_TOKEN from .env (repo root), queries the
Portainer API, and writes one JSON file per resource type plus a markdown
summary. Stdlib-only — no pip install required.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV = REPO_ROOT / ".env"
DEFAULT_OUT = REPO_ROOT / "inventory"


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    text = path.read_text(encoding="utf-8")
    # Strip BOM if present
    if text.startswith("﻿"):
        text = text[1:]
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip('"').strip("'")
        env[key.strip()] = value
    return env


class Portainer:
    def __init__(self, base_url: str, token: str, timeout: int = 20):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _get(self, path: str, params: dict | None = None):
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"X-API-Key": self.token})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read()
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"GET {path} -> HTTP {e.code} {e.reason}: {detail}") from e
        if not body:
            return None
        return json.loads(body)

    def status(self):
        return self._get("/api/status")

    def endpoints(self):
        return self._get("/api/endpoints")

    def stacks(self):
        return self._get("/api/stacks")

    def stack_file(self, stack_id: int):
        return self._get(f"/api/stacks/{stack_id}/file")

    def containers(self, endpoint_id: int):
        # all=true returns stopped containers too
        return self._get(
            f"/api/endpoints/{endpoint_id}/docker/containers/json",
            params={"all": "true"},
        )

    def images(self, endpoint_id: int):
        return self._get(f"/api/endpoints/{endpoint_id}/docker/images/json")

    def volumes(self, endpoint_id: int):
        return self._get(f"/api/endpoints/{endpoint_id}/docker/volumes")

    def networks(self, endpoint_id: int):
        return self._get(f"/api/endpoints/{endpoint_id}/docker/networks")

    def docker_info(self, endpoint_id: int):
        return self._get(f"/api/endpoints/{endpoint_id}/docker/info")

    def docker_version(self, endpoint_id: int):
        return self._get(f"/api/endpoints/{endpoint_id}/docker/version")


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def container_image_ref(c: dict) -> str:
    # Containers list returns the image string the user gave plus the resolved ID
    return c.get("Image", "") or c.get("ImageID", "")[:19]


def container_name(c: dict) -> str:
    names = c.get("Names") or []
    if names:
        return names[0].lstrip("/")
    return c.get("Id", "")[:12]


def container_stack(c: dict) -> str | None:
    labels = c.get("Labels") or {}
    return labels.get("com.docker.compose.project") or labels.get("io.portainer.stack.name")


def summarize_ports(c: dict) -> str:
    parts = []
    for p in c.get("Ports") or []:
        public = p.get("PublicPort")
        private = p.get("PrivatePort")
        proto = p.get("Type", "tcp")
        if public:
            parts.append(f"{public}->{private}/{proto}")
        elif private:
            parts.append(f"{private}/{proto}")
    return ", ".join(sorted(set(parts)))


def render_markdown(snapshot: dict) -> str:
    now = snapshot["generated_at"]
    lines: list[str] = []
    lines.append(f"# Portainer inventory")
    lines.append("")
    lines.append(f"_Generated {now} from `{snapshot['portainer_url']}` (Portainer {snapshot['portainer_version']})_")
    lines.append("")

    for ep in snapshot["endpoints"]:
        eid = ep["endpoint"]["Id"]
        ename = ep["endpoint"]["Name"]
        info = ep.get("info") or {}
        ver = ep.get("version") or {}
        lines.append(f"## Endpoint {eid}: `{ename}`")
        lines.append("")
        lines.append(
            f"- Docker {ver.get('Version', '?')} | OS {info.get('OperatingSystem', '?')} "
            f"| Kernel {info.get('KernelVersion', '?')} | Arch {info.get('Architecture', '?')}"
        )
        lines.append(
            f"- Containers: {info.get('Containers', '?')} "
            f"(running {info.get('ContainersRunning', '?')}, paused {info.get('ContainersPaused', '?')}, "
            f"stopped {info.get('ContainersStopped', '?')}) | Images: {info.get('Images', '?')}"
        )
        lines.append("")

        # Stacks for this endpoint
        ep_stacks = [s for s in snapshot["stacks"] if s["stack"].get("EndpointId") == eid]
        if ep_stacks:
            lines.append("### Stacks")
            lines.append("")
            lines.append("| ID | Name | Type | Status | Source | Updated |")
            lines.append("|----|------|------|--------|--------|---------|")
            for s in ep_stacks:
                st = s["stack"]
                stype = {1: "swarm", 2: "compose", 3: "kubernetes"}.get(st.get("Type"), str(st.get("Type")))
                status = {1: "active", 2: "inactive"}.get(st.get("Status"), str(st.get("Status")))
                source = "git" if st.get("GitConfig") else st.get("EntryPoint") or "file"
                updated = st.get("UpdateDate") or st.get("CreationDate") or 0
                if updated:
                    updated = datetime.fromtimestamp(int(updated), tz=timezone.utc).strftime("%Y-%m-%d")
                lines.append(
                    f"| {st.get('Id')} | `{st.get('Name')}` | {stype} | {status} | {source} | {updated} |"
                )
            lines.append("")

        # Containers grouped by stack
        containers = ep.get("containers") or []
        by_stack: dict[str, list[dict]] = {}
        for c in containers:
            by_stack.setdefault(container_stack(c) or "(unstacked)", []).append(c)

        lines.append("### Containers")
        lines.append("")
        for stack_name in sorted(by_stack):
            lines.append(f"#### Stack: `{stack_name}`")
            lines.append("")
            lines.append("| Name | Image | State | Ports |")
            lines.append("|------|-------|-------|-------|")
            for c in sorted(by_stack[stack_name], key=container_name):
                lines.append(
                    f"| `{container_name(c)}` | `{container_image_ref(c)}` | "
                    f"{c.get('State', '?')} | {summarize_ports(c) or '—'} |"
                )
            lines.append("")

        # Image inventory
        images = ep.get("images") or []
        if images:
            tags: list[tuple[str, str]] = []
            for img in images:
                for tag in img.get("RepoTags") or []:
                    if tag and tag != "<none>:<none>":
                        size_mb = round((img.get("Size") or 0) / 1_000_000, 1)
                        tags.append((tag, f"{size_mb} MB"))
            tags.sort()
            lines.append(f"### Images ({len(tags)} tagged)")
            lines.append("")
            lines.append("| Tag | Size |")
            lines.append("|-----|------|")
            for tag, size in tags:
                lines.append(f"| `{tag}` | {size} |")
            lines.append("")

    return "\n".join(lines) + "\n"


def gather_endpoint(api: Portainer, endpoint: dict) -> dict:
    eid = endpoint["Id"]
    out = {"endpoint": endpoint}
    for label, fn in (
        ("info", api.docker_info),
        ("version", api.docker_version),
        ("containers", api.containers),
        ("images", api.images),
        ("volumes", api.volumes),
        ("networks", api.networks),
    ):
        try:
            out[label] = fn(eid)
        except RuntimeError as e:
            print(f"  warn: endpoint {eid} {label}: {e}", file=sys.stderr)
            out[label] = None
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--env-file", type=Path, default=DEFAULT_ENV)
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    p.add_argument("--skip-stack-files", action="store_true",
                   help="Don't fetch each stack's compose contents.")
    args = p.parse_args()

    env = load_env(args.env_file)
    url = env.get("PORTAINER_URL")
    token = env.get("PORTAINER_ACCESS_TOKEN")
    if not url or not token:
        print("PORTAINER_URL and PORTAINER_ACCESS_TOKEN must be set in .env", file=sys.stderr)
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)

    api = Portainer(url, token)

    print(f"-> {url}")
    status = api.status()
    print(f"   Portainer {status.get('Version')}")

    endpoints = api.endpoints() or []
    print(f"   {len(endpoints)} endpoint(s)")

    stacks = api.stacks() or []
    print(f"   {len(stacks)} stack(s)")

    stack_records = []
    for s in stacks:
        rec = {"stack": s}
        if not args.skip_stack_files:
            try:
                rec["file"] = api.stack_file(s["Id"])
            except RuntimeError as e:
                print(f"  warn: stack {s.get('Id')} file: {e}", file=sys.stderr)
                rec["file"] = None
        stack_records.append(rec)

    endpoint_records = []
    for ep in endpoints:
        print(f"   gathering endpoint {ep['Id']} ({ep['Name']})")
        endpoint_records.append(gather_endpoint(api, ep))

    snapshot = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "portainer_url": url,
        "portainer_version": status.get("Version"),
        "portainer_instance": status.get("InstanceID"),
        "endpoints": endpoint_records,
        "stacks": stack_records,
    }

    write_json(args.out_dir / "snapshot.json", snapshot)
    write_json(args.out_dir / "endpoints.json", endpoints)
    write_json(args.out_dir / "stacks.json", stack_records)
    for ep_rec in endpoint_records:
        eid = ep_rec["endpoint"]["Id"]
        ename = ep_rec["endpoint"]["Name"]
        ep_dir = args.out_dir / f"endpoint-{eid}-{ename}"
        ep_dir.mkdir(exist_ok=True)
        write_json(ep_dir / "info.json", ep_rec.get("info"))
        write_json(ep_dir / "version.json", ep_rec.get("version"))
        write_json(ep_dir / "containers.json", ep_rec.get("containers"))
        write_json(ep_dir / "images.json", ep_rec.get("images"))
        write_json(ep_dir / "volumes.json", ep_rec.get("volumes"))
        write_json(ep_dir / "networks.json", ep_rec.get("networks"))

    md = render_markdown(snapshot)
    (args.out_dir / "README.md").write_text(md, encoding="utf-8")

    print(f"   wrote inventory to {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
