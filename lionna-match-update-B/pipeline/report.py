"""Interactive HTML shortlist for the board — two views of the same result:

  1) By LIONNA piece  — reference (name + attribute chips, or lionna/refs/<slug>.png)
     next to ranked visual candidates. Board ticks the ones to quote.
  2) By supplier      — the same matches regrouped per supplier (with catalog page)
     to paste straight into an RFQ.

Board actions (client-side, no server): approve checkboxes, "só cut-and-sew" filter,
and "Exportar aprovadas (CSV RFQ)" -> downloads supplier-grouped CSV.
"""
import html, json, shutil, re
from pathlib import Path


def _slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").lower()


CSS = """
:root{--paper:#F8F6EF;--ink:#1A1A1A;--gold:#BFA97A;--muted:#726A5C;--line:#DCD6C9;--warn:#8a5a2b;--ok:#3a7a3a}
*{box-sizing:border-box;margin:0;font-family:'Inter',system-ui,sans-serif}
body{background:var(--paper);color:var(--ink);padding:28px 38px 80px}
h1{font-family:Georgia,serif;font-weight:500;font-size:27px}
.sub{color:var(--muted);font-size:12px;letter-spacing:.22em;text-transform:uppercase;margin:4px 0 18px}
.tabs{display:flex;gap:8px;margin:14px 0 8px;position:sticky;top:0;background:var(--paper);padding:8px 0;z-index:5;border-bottom:1px solid var(--line)}
.tab{padding:7px 16px;border:1px solid var(--line);border-radius:20px;cursor:pointer;font-size:13px;background:#fff}
.tab.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.toolbar{display:flex;gap:16px;align-items:center;margin:12px 0;font-size:13px;color:var(--muted)}
.toolbar label{cursor:pointer}
.btn{margin-left:auto;background:var(--gold);color:#1a1a1a;border:none;padding:9px 16px;border-radius:6px;font-weight:600;cursor:pointer;font-size:13px}
.btn.sec{background:#fff;border:1px solid var(--line);color:var(--ink);margin-left:8px}
.piece{margin:26px 0 8px;padding-top:10px;border-top:2px solid var(--line)}
.piece h2{font-family:Georgia,serif;font-size:20px}
.piece .cat{font-size:11px;color:var(--gold);letter-spacing:.14em;text-transform:uppercase;font-weight:600}
.chips{margin:6px 0 2px}
.chip{display:inline-block;background:#efe9db;color:#5b5342;font-size:10.5px;padding:2px 8px;border-radius:10px;margin:2px 4px 2px 0}
.row{display:flex;gap:13px;flex-wrap:wrap;margin:8px 0 4px}
.card{width:170px;border:1px solid var(--line);border-radius:8px;overflow:hidden;background:#fff;position:relative}
.card.seamless{opacity:1}
.card img{width:100%;height:150px;object-fit:cover;background:#eee;display:block}
.card .b{padding:8px 10px}
.card .sup{font-size:11px;color:var(--gold);font-weight:700;letter-spacing:.06em;text-transform:uppercase}
.card .sku{font-size:11.5px;font-weight:600;margin-top:1px}
.card .meta{font-size:10px;color:var(--muted);margin-top:2px}
.card .score{position:absolute;top:6px;right:6px;background:rgba(26,26,26,.85);color:#fff;font-weight:700;font-size:12px;padding:2px 7px;border-radius:10px}
.flag-ok{font-size:10px;color:var(--ok);margin-top:3px}
.flag-warn{font-size:10px;color:var(--warn);margin-top:3px}
.appr{display:flex;align-items:center;gap:5px;font-size:11px;margin-top:6px;cursor:pointer;color:var(--ink)}
.empty{color:var(--muted);font-style:italic;padding:6px 0}
.sup-group{margin:22px 0}
.sup-group h3{font-family:Georgia,serif;font-size:18px;border-bottom:1px solid var(--line);padding-bottom:5px;margin-bottom:8px}
.count{color:var(--muted);font-size:12px;font-weight:400}
.hidden{display:none}
"""


def build_report(results, cfg, queries=None):
    out = Path(cfg["paths"]["report"]); out.parent.mkdir(parents=True, exist_ok=True)
    crops = Path(cfg["paths"]["crops"])
    thumbs = out.parent / "thumbs"; thumbs.mkdir(exist_ok=True)
    refs_dir = Path("lionna/refs")
    qmeta = {q["name"]: q for q in (queries or [])}

    def thumb(crop):
        if not crop:
            return ""
        src = crops / crop
        if src.exists():
            dst = thumbs / crop
            if not dst.exists():
                try: shutil.copy(src, dst)
                except Exception: return ""
            return f"thumbs/{crop}"
        return ""

    def card(r, piece):
        t = thumb(r.get("crop"))
        img = f"<img src='{t}'>" if t else "<img alt=''>"
        fl = r.get("flag", ""); cls = "flag-ok" if fl == "OK" else "flag-warn"
        seam = "" if fl == "OK" else " seamless"
        sku = r.get("sku") or (r.get("crop", "") or "")[:16]
        data = html.escape(json.dumps({"supplier": r.get("supplier", ""), "catalog": r.get("catalog", ""),
                                       "page": r.get("page", ""), "piece": piece, "score": r.get("score", ""),
                                       "construction": r.get("construction", ""), "flag": fl,
                                       "crop": r.get("crop", "")}), quote=True)
        return (f"<div class='card{seam}' data-seamless='{0 if fl=='OK' else 1}'>"
                f"<span class=score>{r.get('score','')}</span>{img}<div class=b>"
                f"<div class=sup>{html.escape(str(r.get('supplier','')))}</div>"
                f"<div class=sku>{html.escape(str(sku))}</div>"
                f"<div class=meta>{html.escape(str(r.get('catalog','')))} · p{r.get('page','')}</div>"
                f"<div class='{cls}'>{html.escape(fl)}</div>"
                f"<label class=appr><input type=checkbox class=ap data-row=\"{data}\"> aprovar p/ cotação</label>"
                f"</div></div>")

    # ---- View 1: by LIONNA piece ----
    v1 = ["<div id=bypiece>"]
    for qname, rows in results.items():
        q = qmeta.get(qname, {})
        chips = "".join(f"<span class=chip>{html.escape(k)}</span>" for k in (q.get("attrs") or {}))
        ref = refs_dir / f"{_slug(qname)}.png"
        refimg = ""
        if ref.exists():
            dst = thumbs / f"ref_{_slug(qname)}.png"
            if not dst.exists():
                try: shutil.copy(ref, dst)
                except Exception: pass
            refimg = f"<img src='thumbs/ref_{_slug(qname)}.png' style='width:120px;height:150px;object-fit:cover;border-radius:8px;border:1px solid var(--line)'>"
        v1.append(f"<div class=piece><div style='display:flex;gap:16px;align-items:flex-start'>"
                  f"<div style='flex:0 0 auto'>{refimg}</div><div>"
                  f"<div class=cat>{html.escape(str(q.get('category','')))} · {html.escape(str(q.get('construction','')))}</div>"
                  f"<h2>{html.escape(qname)}</h2><div class=chips>{chips}</div></div></div>")
        if not rows:
            v1.append("<div class=empty>Sem candidato visual relevante nos catálogos (possível lacuna de fornecedor p/ esta peça).</div>")
        else:
            v1.append("<div class=row>")
            for r in rows:
                v1.append(card(r, qname))
            v1.append("</div>")
        v1.append("</div>")
    v1.append("</div>")

    # ---- View 2: by supplier ----
    by_sup = {}
    for qname, rows in results.items():
        for r in rows:
            by_sup.setdefault(r.get("supplier", "?"), []).append((qname, r))
    v2 = ["<div id=bysupplier class=hidden>"]
    for sup in sorted(by_sup):
        items = sorted(by_sup[sup], key=lambda x: (str(x[1].get("catalog", "")), x[1].get("page", 0)))
        v2.append(f"<div class=sup-group><h3>{html.escape(sup)} <span class=count>· {len(items)} peças candidatas</span></h3><div class=row>")
        for qname, r in items:
            v2.append(card(r, qname))
        v2.append("</div></div>")
    v2.append("</div>")

    JS = """
<script>
function setTab(t){document.getElementById('bypiece').classList.toggle('hidden',t!=='piece');
 document.getElementById('bysupplier').classList.toggle('hidden',t!=='sup');
 document.getElementById('tp').classList.toggle('on',t==='piece');
 document.getElementById('ts').classList.toggle('on',t==='sup');}
function applyFilter(){var only=document.getElementById('cutonly').checked;
 document.querySelectorAll('.card').forEach(function(c){c.style.display=(only&&c.dataset.seamless==='1')?'none':'';});}
function approved(){var out=[];document.querySelectorAll('.ap:checked').forEach(function(cb){out.push(JSON.parse(cb.dataset.row));});return out;}
function exportCSV(){var rows=approved();if(!rows.length){alert('Nenhuma peça aprovada ainda.');return;}
 rows.sort(function(a,b){return (a.supplier+a.catalog+a.page).localeCompare(b.supplier+b.catalog+b.page);});
 var head=['supplier','catalog','page','lionna_piece','score','construction','flag','crop'];
 var csv=[head.join(',')].concat(rows.map(function(r){return head.map(function(h){var v=(''+r[h]).replace(/"/g,'""');return '"'+v+'"';}).join(',');})).join('\\n');
 var b=new Blob([csv],{type:'text/csv'});var a=document.createElement('a');a.href=URL.createObjectURL(b);
 a.download='lionna_rfq_aprovadas.csv';a.click();}
function copyRFQ(){var rows=approved();if(!rows.length){alert('Nenhuma peça aprovada ainda.');return;}
 var bySup={};rows.forEach(function(r){(bySup[r.supplier]=bySup[r.supplier]||[]).push(r);});
 var txt=Object.keys(bySup).sort().map(function(s){var ls=bySup[s].map(function(r){return '  • '+r.catalog+' — pág '+r.page+'  ('+r.lionna_piece+')';});return s+':\\n'+ls.join('\\n');}).join('\\n\\n');
 navigator.clipboard.writeText(txt).then(function(){alert('Lista de RFQ copiada (agrupada por fornecedor).');});}
</script>
"""
    header = (f"<!doctype html><meta charset=utf-8><style>{CSS}</style>"
              "<h1>LIONNA \u00d7 OEM \u2014 Shortlist de Aprovação</h1>"
              "<div class=sub>Semelhança visual por atributo · flag de construção · agrupável por fornecedor p/ RFQ</div>"
              "<div class=tabs><div id=tp class='tab on' onclick=\"setTab('piece')\">Por peça LIONNA</div>"
              "<div id=ts class=tab onclick=\"setTab('sup')\">Por fornecedor (RFQ)</div></div>"
              "<div class=toolbar><label><input type=checkbox id=cutonly onchange=applyFilter()> só cut-and-sew</label>"
              "<button class=btn onclick=exportCSV()>Exportar aprovadas (CSV RFQ)</button>"
              "<button class='btn sec' onclick=copyRFQ()>Copiar lista p/ fornecedor</button></div>")
    out.write_text(header + "".join(v1) + "".join(v2) + JS, encoding="utf-8")
    print(f"[report] wrote {out}")
    return out
