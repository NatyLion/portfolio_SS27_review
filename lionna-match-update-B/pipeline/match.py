"""Match engine: attribute-visual score, soft/hard category, construction flag.

Option B (category_gate: false): NO nomenclature filtering. Candidates are ranked
purely by visual-attribute overlap; same-category gets a small tie-break bonus.
Option A (category_gate: true): hard-filter to same category (legacy).
"""

CATEGORY_BONUS = 0.05  # tie-break weight when category matches (Option B)


def _iou(qa, ca):
    keys = set(qa) | set(ca)
    num = sum(min(float(qa.get(k, 0)), float(ca.get(k, 0))) for k in keys)
    den = sum(max(float(qa.get(k, 0)), float(ca.get(k, 0))) for k in keys) or 1.0
    return num / den


def match_all(queries, candidates, cfg):
    gate = cfg["match"]["category_gate"]
    hard = cfg["match"]["construction_as_filter"]
    topk = cfg["match"]["top_k"]
    results = {}
    for q in queries:
        rows = []
        for c in candidates:
            same_cat = q["category"] == c.get("category")
            if gate and not same_cat:
                continue                      # Option A: hard category gate
            con = c.get("construction", "unknown")
            mismatch = con not in (q["construction"], "unknown")
            if hard and mismatch:
                continue
            base = _iou(q.get("attrs", {}), c.get("attrs", {})) if c.get("attrs") else 0.0
            score = base + (CATEGORY_BONUS if (not gate and same_cat) else 0.0)
            score = min(round(score, 3), 1.0)
            flag = "OK" if not mismatch else f"\u26a0 {con} (LIONNA={q['construction']})"
            rows.append({"score": score, "flag": flag, "same_cat": same_cat, **c})
        rows.sort(key=lambda r: r["score"], reverse=True)
        results[q["name"]] = rows[:topk]
        print(f"[match] {q['name']}: {'no candidates' if not rows else str(len(rows[:topk]))+' shown'}")
    return results
