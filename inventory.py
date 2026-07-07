"""Infer construction (seamless vs cut-and-sew) from catalog source + heuristics.

This is the flag that encodes the LIONNA MOQ lesson: a seamless-supplier match
for a cut-and-sew LIONNA piece is a construction mismatch, however similar the photo.
Vision can override via 'construction_visual' when confident.
"""


def infer_construction(row, cfg):
    for c in cfg.get("catalogs", []):
        f = c.get("file", "")
        if f and f != "*.pdf" and f in row["catalog"] and c.get("default_construction", "auto") != "auto":
            return c["default_construction"]
    name = row["catalog"].lower()
    if "seamless" in name:
        return "seamless"
    return "cut-and-sew"
