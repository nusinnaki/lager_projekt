from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COMMANDS = [
    [sys.executable, "-m", "backend.seed"],
    [sys.executable, str(ROOT / "scripts" / "import_sites.py")],
    [sys.executable, str(ROOT / "scripts" / "import_workers.py")],
    [sys.executable, str(ROOT / "scripts" / "import_products.py")],
]


def main() -> None:
    for cmd in COMMANDS:
        print("Running:", " ".join(map(str, cmd)))
        subprocess.run(cmd, check=True)

    print("OK: bootstrap completed")


if __name__ == "__main__":
    main()