import datetime
import json
import os
from pathlib import Path
import subprocess
from typing import TypedDict
import re

SCOOP_PATH = Path(os.environ.get('SCOOP')) if "SCOOP" in os.environ else Path.home() / 'scoop'
if not SCOOP_PATH.exists():
    SCOOP_PATH = None

class ScoopEntry(TypedDict):
    name : str
    version : str
    source : str
    updated : str

def scoop_list(filter = "") -> list[ScoopEntry]:
    if SCOOP_PATH is None:
        return []
    entries = []
    res = subprocess.run(
        ['scoop', 'list', filter], capture_output=True, 
        text=True, shell=True
    )
    if res.returncode == 0:
        for line in res.stdout.splitlines()[4:]:
            if not line.strip():
                continue
            name, version, source, updated, updated_union = line.split()

            updated = updated + ' ' + updated_union

            entries.append(ScoopEntry(
                name=name,
                version=version,
                source=source,
                updated=updated
            ))

    return entries

def scoop_list_filter(
    filter : str = '',
    bucket_match : list[str] | None = None,
    bucket_pattern : str | None = None,
    updated_before : datetime.date | None = None,
    updated_after : datetime.date | None = None
):
    entries = scoop_list(filter)
    if bucket_match:
        entries = [e for e in entries if e['source'] in bucket_match]
    if bucket_pattern:
        entries = [e for e in entries if re.search(bucket_pattern, e['source'])]
    if updated_before or updated_after:
        entries = [
            e for e in entries if (
                (not updated_before or datetime.datetime.strptime(e['updated'], '%Y-%m-%d') < updated_before) and
                (not updated_after or datetime.datetime.strptime(e['updated'], '%Y-%m-%d') > updated_after)
            )
        ]
    return entries

def scoop_pkg_path(pkg : str) -> Path | None:
    if SCOOP_PATH is None:
        return None
    pkg_path = SCOOP_PATH / 'apps' / pkg
    if pkg_path.exists():
        return pkg_path / 'current'
    return None

def scoop_pkg_manifest_path(pkg : str) -> Path | None:
    if SCOOP_PATH is None:
        return None
    pkg_path = SCOOP_PATH / 'apps' / pkg
    if pkg_path.exists():
        return pkg_path / 'current' / 'manifest.json'
    return None

def scoop_pkg_manifest(pkg : str) -> dict | None:
    manifest_path = scoop_pkg_manifest_path(pkg)
    if manifest_path and manifest_path.exists():
        with open(manifest_path) as f:
            return json.load(f)
    return None