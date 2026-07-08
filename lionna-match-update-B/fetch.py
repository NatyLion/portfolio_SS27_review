"""Discover catalog PDFs recursively from a local folder or a private GitHub repo.

Catalogs are organised by supplier subfolder, e.g.
    catalogs/YOGI/Seam Yoga Set 2026.pdf   -> supplier 'YOGI'
    catalogs/New Style 2026.pdf            -> supplier 'root' (loose file)

Returns list of dicts:
    {"path": Path, "catalog_id": "YOGI/Seam Yoga Set 2026.pdf",
     "supplier": "YOGI", "name": "Seam Yoga Set 2026.pdf"}
"""
import os, subprocess, shutil
from pathlib import Path


def _collect(root):
    root = Path(root)
    out = []
    for p in sorted(root.rglob("*.pdf")):
        if p.name.startswith("~$") or p.name.startswith("."):
            continue  # skip Word lock files / hidden
        rel = p.relative_to(root)
        supplier = rel.parts[0] if len(rel.parts) > 1 else "root"
        out.append({"path": p, "catalog_id": str(rel).replace(os.sep, "/"),
                    "supplier": supplier, "name": p.name})
    return out


def fetch(cfg):
    src = cfg["source"]
    local = src.get("local_dir")
    if local:
        found = _collect(Path(local))
        n_sup = len(set(f["supplier"] for f in found))
        print(f"[fetch] {len(found)} PDFs under '{local}' across {n_sup} suppliers")
        return found

    repo = src["github_repo"]; ref = src.get("github_ref", "main")
    sub = src.get("catalogs_subdir", "")
    token = os.environ.get("GITHUB_TOKEN")
    clone = Path(cfg["paths"]["work"]) / "_repo"
    if clone.exists():
        shutil.rmtree(clone)
    url = (f"https://x-access-token:{token}@github.com/{repo}.git" if token
           else f"https://github.com/{repo}.git")
    subprocess.run(["git", "clone", "--depth", "1", "--branch", ref, url, str(clone)], check=True)
    found = _collect(clone / sub)
    print(f"[fetch] {len(found)} PDFs from {repo}@{ref}/{sub}")
    return found
