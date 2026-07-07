"""Static HTML shortlist: per LIONNA query, ranked candidate cards with crop
thumbnails + catalog/page refs + construction flag. LIONNA palette."""
import html, shutil
from pathlib import Path

CSS = """
:root{--onyx:#0A0A0A;--paper:#F8F6EF;--ink:#1A1A1A;--gold:#BFA97A;--muted:#726A5C;--line:#DCD6C9;--warn:#8a5a2b}
*{box-sizing:border-box;margin:0;font-family:'Inter',system-ui,sans-serif}
body{background:var(--paper);color:var(--ink);padding:32px 40px}
h1{font-family:Georgia,serif;font-weight:500;font-size:26px;letter-spacing:.01em}
.sub{color:var(--muted);font-size:12px;letter-spacing:.24em;text-transform:uppercase;margin:4px 0 26px}
.q{margin:30px 0 10px;font-family:Georgia,serif;font-size:19px;border-bottom:1px solid var(--line);padding-bottom:6px}
.q small{font-family:Inter;font-size:11px;color:var(--gold);letter-spacing:.14em;text-transform:uppercase;margin-left:8px}
.row{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:8px}
.card{width:172px;border:1px solid var(--line);border-radius:6px;overflow:hidden;background:#fff}
.card img{width:100%;height:150px;object-fit:cover;background:#eee}
.card .b{padding:8px 10px}
.sku{font-weight:600;font-size:12px}
.meta{font-size:10.5px;color:var(--muted);margin-top:2px}
.score{float:right;font-weight:700;color:var(--gold)}
.flag-ok{font-size:10px;color:#3a7a3a}
.flag-warn{font-size:10px;color:var(--warn)}
.empty{color:var(--muted);font-style:italic;padding:8px 0}
"""


def build_report(results, cfg):
    out = Path(cfg["paths"]["report"]); out.parent.mkdir(parents=True, exist_ok=True)
    crops = Path(cfg["paths"]["crops"])
    thumbs = out.parent / "thumbs"; thumbs.mkdir(exist_ok=True)

    def thumb(crop):
        if not crop:
            return ""
        src = crops / crop
        if src.exists():
            dst = thumbs / crop
            if not dst.exists():
                shutil.copy(src, dst)
            return f"thumbs/{crop}"
        return ""

    parts = [f"<!doctype html><meta charset=utf-8><style>{CSS}</style>",
             "<h1>LIONNA \u00d7 OEM \u2014 Match Shortlist</h1>",
             "<div class=sub>Attribute fingerprint \u00b7 category-gated \u00b7 construction-flagged</div>"]
    for qname, rows in results.items():
        parts.append(f"<div class=q>{html.escape(qname)}</div>")
        if not rows:
            parts.append("<div class=empty>No candidate in this category across the loaded catalogs (category gap).</div>")
            continue
        parts.append("<div class=row>")
        for r in rows:
            t = thumb(r.get("crop"))
            img = f"<img src='{t}'>" if t else "<img alt='no crop'>"
            fl = r.get("flag", "")
            flcls = "flag-ok" if fl == "OK" else "flag-warn"
            ref = f"{r.get('catalog','')} \u00b7 p{r.get('page','')}"
            sku = r.get("sku") or r.get("crop", "")
            parts.append(
                f"<div class=card>{img}<div class=b>"
                f"<span class=score>{r.get('score','')}</span>"
                f"<div class=sku>{html.escape(str(sku))}</div>"
                f"<div class=meta>{html.escape(ref)}</div>"
                f"<div class='{flcls}'>{html.escape(fl)}</div>"
                f"</div></div>")
        parts.append("</div>")
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"[report] wrote {out}")
    return out
