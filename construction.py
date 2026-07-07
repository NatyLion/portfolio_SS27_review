"""Vision fingerprint.

Default (Claude Code native): write a tagging queue of crops + text hints.
The Claude Code agent opens each crop and appends ONE JSON line per crop to
paths.tags, following TAG_PROMPT.md. The 'vision model' is Claude itself —
no external API key required.

Optional: a CLIP-embedding prefilter (guarded import) to shrink the queue by
pre-clustering near-duplicate colorways before Claude tags representatives.
"""
import json
from pathlib import Path

TAG_SCHEMA = {
    "crop": "<filename>",
    "category": "<one of config.categories or 'unknown'>",
    "attrs": {"<feature>": "0..1 salience"},
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
    print(f"[vision] now have Claude Code tag them into {cfg['paths']['tags']} (see TAG_PROMPT.md)")
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
    print(f"[vision] loaded {len(tags)} vision tags")
    return tags
