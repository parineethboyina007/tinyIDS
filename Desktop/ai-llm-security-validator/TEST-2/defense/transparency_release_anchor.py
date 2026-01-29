# defense/transparency_release_anchor.py

import os
import json
import subprocess
from datetime import datetime

TRANSPARENCY_DIR = "governance/transparency"
ROOT_FILE = f"{TRANSPARENCY_DIR}/merkle_root.json"


def anchor_merkle_root_release(tenant: str) -> dict:
    if not os.path.exists(ROOT_FILE):
        raise FileNotFoundError("Merkle root not found")

    with open(ROOT_FILE) as f:
        root_data = json.load(f)

    root = root_data["root"]
    size = root_data["size"]

    tag = f"transparency-{tenant}-{root[:12]}"
    title = f"Transparency Anchor ({tenant})"
    notes = (
        f"Merkle Root: {root}\n"
        f"Tree Size: {size}\n"
        f"Anchored At: {datetime.utcnow().isoformat()}Z\n"
    )

    # Requires GitHub CLI (gh) authenticated
    subprocess.run(
        [
            "gh", "release", "create", tag,
            "--title", title,
            "--notes", notes,
        ],
        check=True,
    )

    return {
        "status": "anchored",
        "tenant": tenant,
        "root": root,
        "tree_size": size,
        "release_tag": tag,
    }