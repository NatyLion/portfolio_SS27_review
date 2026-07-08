"""Vision fingerprint (Claude-Code-native).

build_queue: writes crops + text hints to paths.queue. The Claude Code agent opens
each crop and appends one JSON line per crop to paths.tags (see TAG_PROMPT.md).
No external API key required — the 'vision model' is Claude.
"""
import json
from pathlib import Path

TAG_SCHEMA = {
    "crop": "<filename>",
    "category": "<taxonomy or unknown>",
    "attrs": {"<feature>": "0..1"},
    "construction_visual": "seamless | cut-and-sew | unknown",
    "notes": "<short>",
}


def build_queue(seg_manifest, text_db, cfg):
    bypage = {(r["catalog"], r["page"]): r for r in text_db}
    q = []
    for m in seg_manifest:
        h = bypage.get((m["catalog"], m["page"]), {})
        q.append({**m,
                  "hint_skus": h.get("skus", []),
                  "hint_types": h.get("types", []),
                  "hint_materials": h.get("materials", [])})
    out = Path(cfg["paths"]["queue"]); out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for row in q:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"[vision] queued {len(q)} crops -> {out}")
    return q


def load_tags(cfg):
    p = Path(cfg["paths"]["tags"])
    if not p.exists():
        return {}
    tags = {}
    for line in p.read_text().splitlines():
        line = line.strip()
        if line:
            t = json.loads(line)
            tags[t["crop"]] = t
    print(f"[vision] loaded {len(tags)} tags")
    return tags
