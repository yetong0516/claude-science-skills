#!/usr/bin/env python3
"""Check the exported snapshot without importing or executing upstream code."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


class SnapshotError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SnapshotError(message)


def safe_path(root: Path, name: str) -> Path:
    require(isinstance(name, str), "path must be a string")
    path = PurePosixPath(name)
    require(not path.is_absolute() and ".." not in path.parts
            and path.parts and path.parts[0] == "skills"
            and str(path) == name and "\\" not in name, "unsafe snapshot path")
    current = root
    for part in path.parts:
        current /= part
        require(not current.is_symlink(), f"symlink refused: {name}")
    return current


def verify(root: Path) -> dict[str, int]:
    root = root.resolve()
    manifest = json.loads((root / "SNAPSHOT.json").read_text(encoding="utf-8"))
    require(manifest["schema_version"] == 1, "unsupported manifest schema")
    require(isinstance(manifest["runtime_version"], str), "missing runtime version")
    rows = manifest["files"]
    require(isinstance(rows, list) and bool(rows), "empty file manifest")
    names: set[str] = set()
    packages: set[str] = set()
    python_files = 0
    for row in rows:
        name = row["file"]
        path = safe_path(root, name)
        require(name not in names, f"duplicate snapshot entry: {name}")
        names.add(name)
        require(path.is_file(), f"missing file: {name}")
        data = path.read_bytes()
        require(type(row["bytes"]) is int and row["bytes"] == len(data),
                f"size mismatch: {name}")
        require(isinstance(row["sha256"], str)
                and re.fullmatch(r"[0-9a-f]{64}", row["sha256"]) is not None,
                f"invalid sha256: {name}")
        require(hashlib.sha256(data).hexdigest() == row["sha256"],
                f"hash mismatch: {name}")
        if path.name == "SKILL.md":
            parts = PurePosixPath(name).parts
            require(len(parts) == 3, f"unexpected SKILL.md location: {name}")
            text = data.decode("utf-8")
            frontmatter = text.split("---", 2)
            require(text.startswith("---\n") and len(frontmatter) == 3,
                    f"missing frontmatter: {name}")
            require(re.search(r"^name:\s*\S", frontmatter[1], re.M) is not None
                    and re.search(r"^description:\s*\S", frontmatter[1], re.M) is not None,
                    f"missing skill metadata: {name}")
            packages.add(parts[1])
        if path.suffix == ".py":
            ast.parse(data, filename=name)
            python_files += 1

    legacy = manifest["legacy_files_outside_snapshot"]
    require(isinstance(legacy, list) and len(set(legacy)) == len(legacy),
            "invalid legacy file list")
    for name in legacy:
        path = safe_path(root, name)
        parts = PurePosixPath(name).parts
        require(len(parts) == 3 and parts[1] in packages
                and parts[2] == ".catalog_stamp" and path.is_file(),
                "legacy exceptions must be existing per-package catalog stamps")
    require(not names.intersection(legacy), "legacy file also listed as current export")
    actual = set()
    for path in (root / "skills").rglob("*"):
        name = path.relative_to(root).as_posix()
        require(not path.is_symlink(), f"symlink refused: {name}")
        if path.is_file():
            actual.add(name)
        else:
            require(path.is_dir(), f"special file refused: {name}")
    require(actual == names.union(legacy), "unexpected or unlisted file in skills tree")
    scope = manifest["scope"]
    require(scope["exported_files"] == len(names), "exported file count mismatch")
    require(scope["skill_packages"] == len(packages), "skill package count mismatch")
    require(scope["credentials_or_account_data_included"] is False
            and scope["runtime_services_tested"] is False, "invalid snapshot scope claims")

    delta = json.loads((root / "docs/updates/0.1.70-files.json").read_text(encoding="utf-8"))
    require(delta["baseline_commit"] == manifest["baseline_commit"]
            and delta["runtime_version"] == manifest["runtime_version"],
            "comparison provenance mismatch")
    changed = delta["changed_existing_files"]
    added = delta["added_files"]
    require(len(changed) == len(set(changed)) and len(added) == len(set(added))
            and not set(changed).intersection(added)
            and set(changed + added).issubset(names), "invalid delta file lists")
    require(len(changed) == scope["changed_existing_files"]
            and sum(name.endswith("/SKILL.md") for name in changed)
            == scope["changed_skill_instructions"]
            and added == scope["added_files"]
            and delta["removed_files"] == scope["removed_export_files"],
            "delta count mismatch")

    catalog = json.loads((root / "catalogs/bundled-mcp.json").read_text(encoding="utf-8"))
    require(catalog["schema_version"] == 1
            and catalog["runtime_version"] == manifest["runtime_version"],
            "catalog version mismatch")
    require(catalog["connectivity_tested"] is False
            and catalog["credentials_or_account_data_included"] is False
            and catalog["complete_platform_catalog"] is False, "invalid catalog scope claims")
    servers = catalog["servers"]
    server_names = set()
    for server in servers:
        require(set(server) == {"package", "relative_server_path", "server_sha256"},
                "unexpected catalog fields")
        package = server["package"]
        require(re.fullmatch(r"mcp_[a-z_]+", package) is not None
                and package not in server_names, "invalid or duplicate MCP package")
        server_names.add(package)
        require(server["relative_server_path"] == f"{package}/server.py"
                and re.fullmatch(r"[0-9a-f]{64}", server["server_sha256"]) is not None,
                "invalid MCP entry")
    require(catalog["server_groups"] == len(server_names), "MCP server count mismatch")
    return {"exported_files": len(names), "skill_packages": len(packages),
            "python_files_parsed": python_files, "mcp_groups": len(server_names)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        result = verify(args.root)
    except (SnapshotError, OSError, ValueError, KeyError, TypeError, SyntaxError) as exc:
        print(f"Snapshot verification failed: {exc}")
        return 1
    print("Snapshot verified: " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
