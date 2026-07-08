"""Infer construction (seamless vs cut-and-sew) from catalog id + heuristics.
Vision can override via 'construction_visual'. Override per catalog in config."""


def infer_construction(row, cfg):
    cid = row.get("catalog", "").lower()
    for c in cfg.get("catalogs", []):
        f = c.get("file", "")
        if f and f != "*.pdf" and f.lower() in cid and c.get("default_construction", "auto") != "auto":
            return c["default_construction"]
    if "seamless" in cid or "seam " in cid or "/seam" in cid:
        return "seamless"
    return "cut-and-sew"
