"""Match engine: category gate + attribute score + construction flag.

Validated interactively on the stand-in catalogs. Score is an IoU-style overlap
of salience-weighted attributes (0..1). Construction mismatch is flagged (or
hard-filtered if match.construction_as_filter is true).
"""


def _iou(qa, ca):
    keys = set(qa) | set(ca)
    num = sum(min(float(qa.get(k, 0)), float(ca.get(k, 0))) for k in keys)
    den = sum(max(float(qa.get(k, 0)), float(ca.get(k, 0))) for k in keys) or 1.0
    return num / den


def match_all(queries, candidates, cfg):
    """candidates: [{catalog,page,sku|crop,category,attrs,construction,source}]"""
    gate = cfg["match"]["category_gate"]
    hard = cfg["match"]["construction_as_filter"]
    topk = cfg["match"]["top_k"]
    results = {}
    for q in queries:
        rows = []
        for c in candidates:
            if gate and q["category"] != c.get("category"):
                continue
            con = c.get("construction", "unknown")
            mismatch = con not in (q["construction"], "unknown")
            if hard and mismatch:
                continue
            s = _iou(q.get("attrs", {}), c.get("attrs", {})) if c.get("attrs") else 0.35
            flag = "OK" if not mismatch else f"\u26a0 {con} (LIONNA={q['construction']})"
            rows.append({"score": round(s, 3), "flag": flag, **c})
        rows.sort(key=lambda r: r["score"], reverse=True)
        results[q["name"]] = rows[:topk]
        tag = "no candidates (category gap)" if not rows else f"{len(rows[:topk])} shown"
        print(f"[match] {q['name']}: {tag}")
    return results
