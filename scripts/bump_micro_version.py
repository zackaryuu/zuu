import re
import sys
from pathlib import Path

PYPROJECT_PATH = Path(__file__).parent.parent / "pyproject.toml"

version_re = re.compile(r'^(version\s*=\s*")([0-9]+)\.([0-9]+)\.([0-9]+)(".*)$', re.MULTILINE)

with PYPROJECT_PATH.open("r", encoding="utf-8") as f:
    content = f.read()

match = version_re.search(content)
if not match:
    print("No version field found in pyproject.toml", file=sys.stderr)
    sys.exit(1)

major, minor, micro = int(match.group(2)), int(match.group(3)), int(match.group(4))
micro += 1
new_version = f'{major}.{minor}.{micro}'
new_content = version_re.sub(rf'\1{major}.{minor}.{micro}\5', content)

with PYPROJECT_PATH.open("w", encoding="utf-8") as f:
    f.write(new_content)

print(f"Version bumped to {new_version}")
