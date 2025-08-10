import re
import sys
from pathlib import Path

PYPROJECT_PATH = Path(__file__).parent.parent / "pyproject.toml"

version_re = re.compile(r'^(version\s*=\s*")([0-9]+)\.([0-9]+)\.([0-9]+)(")', re.MULTILINE)

with PYPROJECT_PATH.open("r", encoding="utf-8") as f:
    content = f.read()

def bump_version(match):
    major = int(match.group(2))
    minor = int(match.group(3))
    micro = int(match.group(4)) + 1
    return f'{match.group(1)}{major}.{minor}.{micro}{match.group(5)}'

if not version_re.search(content):
    print("No version field found in pyproject.toml", file=sys.stderr)
    sys.exit(1)

new_content = version_re.sub(bump_version, content)

with PYPROJECT_PATH.open("w", encoding="utf-8") as f:
    f.write(new_content)

# Stage pyproject.toml and lefthook.yml for commit
import subprocess
subprocess.run(["git", "add", str(PYPROJECT_PATH), "lefthook.yml"], check=True)

new_version_match = version_re.search(new_content)
if new_version_match:
    new_version = f'{new_version_match.group(2)}.{new_version_match.group(3)}.{new_version_match.group(4)}'
    print(f"Version bumped to {new_version}")
