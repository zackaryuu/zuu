import os
from pathlib import Path

SCOOP_PATH = Path(os.environ.get('SCOOP')) if "SCOOP" in os.environ else Path.home() / 'scoop'
