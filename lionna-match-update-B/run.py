#!/usr/bin/env python3
"""LIONNA x OEM catalog matcher — orchestrator.

Phases:
  python run.py build   # fetch (recursive) -> inventory -> text db -> crops -> tagging queue
  # vision pass: Claude Code tags data/crops via TAG_PROMPT.md -> data/vision_tags.jsonl
  python run.py match   # assemble candidates -> score -> data/report/index.html
  python run.py all      # build, then match if tags already exist
"""
import sys, json, yaml
from pathlib import Path
from pipeline import (fetch, inventory, fingerprint_text, segment,
                      fingerprint_vision, construction, match, report)


def load_cfg():
    return yaml.safe_load(Path("config.yaml").read_text())


def load_queries():
    return yaml.safe_load(Path("lionna/queries.yaml").read_text())


def phase_build(cfg):
    cats = fetch.fetch(cfg)
    if not cats:
        print("[build] no PDFs found — check source.local_dir / catalogs_subdir.")
        return
    inventory.inventory(cats)
    tdb = fingerprint_text.build_text_db(cats, cfg["categories"])
    Path(cfg["paths"]["db"]).parent.mkdir(parents=True, exist_ok=True)
    Path(cfg["paths"]["db"]).write_text(json.dumps(tdb, ensure_ascii=False, indent=1))
    seg = segment.segment(cats, cfg)
    Path(cfg["paths"]["work"], "segments.json").write_text(json.dumps(seg, ensure_ascii=False, indent=1))
    fingerprint_vision.build_queue(seg, tdb, cfg)
    print(f"\n[build] done: {len(cats)} catalogs, {len(seg)} crops queued. "
          f"Next: tag crops (TAG_PROMPT.md), then `python run.py match`.")


def assemble_candidates(cfg):
    tags = fingerprint_vision.load_tags(cfg)
    seg = json.loads(Path(cfg["paths"]["work"], "segments.json").read_text())
    tdb = json.loads(Path(cfg["paths"]["db"]).read_text())
    bypage = {(r["catalog"], r["page"]): r for r in tdb}
    cands = []
    for m in seg:
        t = tags.get(m["crop"])
        tr = bypage.get((m["catalog"], m["page"]), {})
        cat = (t or {}).get("category")
        if not cat or cat == "unknown":
            cat = (tr.get("types") or ["unknown"])[0]
        con = (t or {}).get("construction_visual")
        if con not in ("seamless", "cut-and-sew"):
            con = construction.infer_construction({"catalog": m["catalog"]}, cfg)
        cands.append({"catalog": m["catalog"], "supplier": m.get("supplier", "?"),
                      "page": m["page"], "crop": m["crop"],
                      "sku": (tr.get("skus") or [None])[0], "category": cat,
                      "attrs": (t or {}).get("attrs", {}),
                      "construction": con, "source": "vision" if t else "text"})
    return cands


def phase_match(cfg):
    q = load_queries()
    c = assemble_candidates(cfg)
    res = match.match_all(q, c, cfg)
    Path(cfg["paths"]["work"], "results.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    report.build_report(res, cfg, q)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    cfg = load_cfg()
    if cmd in ("build", "all"):
        phase_build(cfg)
    if cmd == "match":
        phase_match(cfg)
    if cmd == "all":
        if Path(cfg["paths"]["tags"]).exists():
            phase_match(cfg)
        else:
            print("\n[all] no vision tags yet — tag crops, then `python run.py match`.")


if __name__ == "__main__":
    main()
