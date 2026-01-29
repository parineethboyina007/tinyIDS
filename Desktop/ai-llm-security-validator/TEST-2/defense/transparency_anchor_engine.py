# defense/transparency_anchor_engine.py

import os
import json
import subprocess
from datetime import datetime

TRANSPARENCY_DIR = "governance/transparency"
ANCHOR_FILE = f"{TRANSPARENCY_DIR}/github_anchor.json"
ROOT_FILE = f"{TRANSPARENCY_DIR}/merkle_root.json"


# ==================================================
# INTERNAL HELPERS
# ==================================================

def _ensure():
    os.makedirs(TRANSPARENCY_DIR, exist_ok=True)
    if not os.path.exists(ANCHOR_FILE):
        with open(ANCHOR_FILE, "w") as f:
            json.dump([], f)


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def _save_json(path: str, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _git(*args) -> str:
    """
    Execute git command and return stdout
    """
    result = subprocess.run(
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    return result.stdout.strip()


# ==================================================
# STEP-88 — GITHUB WITNESS ANCHOR
# ==================================================

def anchor_merkle_root(tenant: str) -> dict:
    """
    Publicly anchor current Merkle root via Git commit.
    Produces an immutable external witness.
    """

    _ensure()

    if not os.path.exists(ROOT_FILE):
        raise FileNotFoundError("merkle_root.json not found")

    root_state = _load_json(ROOT_FILE)

    root_hash = root_state["root"]
    tree_size = root_state["size"]

    anchors = _load_json(ANCHOR_FILE)

    # --------------------------------------------------
    # Idempotency: do not anchor same root twice
    # --------------------------------------------------
    for a in anchors:
        if a["root"] == root_hash:
            return {
                "status": "already_anchored",
                "tenant": tenant,
                "root": root_hash,
                "commit": a["commit"],
            }

    # --------------------------------------------------
    # Write deterministic anchor payload
    # --------------------------------------------------
    payload = {
        "tenant": tenant,
        "merkle_root": root_hash,
        "tree_size": tree_size,
        "anchored_at": datetime.utcnow().isoformat(),
    }

    anchor_path = f"{TRANSPARENCY_DIR}/anchor_{root_hash[:12]}.json"
    _save_json(anchor_path, payload)

    # --------------------------------------------------
    # Git commit (external witness)
    # --------------------------------------------------
    _git("add", anchor_path)
    _git(
        "commit",
        "-m",
        f"Transparency anchor: root={root_hash} size={tree_size}",
    )

    commit_hash = _git("rev-parse", "HEAD")

    # --------------------------------------------------
    # Persist anchor metadata
    # --------------------------------------------------
    record = {
        "tenant": tenant,
        "root": root_hash,
        "tree_size": tree_size,
        "commit": commit_hash,
        "anchor_file": anchor_path,
        "anchored_at": payload["anchored_at"],
    }

    anchors.append(record)
    _save_json(ANCHOR_FILE, anchors)

    return {
        "status": "anchored",
        "tenant": tenant,
        "root": root_hash,
        "tree_size": tree_size,
        "commit": commit_hash,
        "anchor_file": anchor_path,
    }