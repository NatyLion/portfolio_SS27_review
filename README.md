# LIONNA x OEM Catalog Matcher

Cross-references LIONNA SS27 pieces against OEM supplier catalogs (PDF line-sheets)
to surface similar models. Matching is **attribute-based, category-gated, and
construction-flagged** — not raw image-vs-image, which drowns activewear in false
matches (pose/colour/crop noise) and ignores the seamless-vs-cut-and-sew distinction
that drives LIONNA's MOQ decisions.

## Why this shape
- Supplier PDFs are grid line-sheets: many products + colorways per page -> crops.
- A vision fingerprint normalises pose/colour/background into structured attributes.
- Category gate keeps top<->top, pant<->pant (a tennis-skirt catalog never pollutes
  a polo search).
- Construction flag surfaces "great silhouette, wrong construction (seamless)" so a
  visual lookalike doesn't read as a sourcing match.

## Layout
```
config.yaml            # repo/source, paths, taxonomy, scoring weights
lionna/queries.yaml    # LIONNA pieces (the query side) — edit/extend here
pipeline/fetch.py      # pull PDFs from private GitHub repo or local folder
pipeline/inventory.py  # page count + text-layer check
pipeline/fingerprint_text.py  # SKU + material + category from the text layer
pipeline/segment.py    # rasterise pages -> product-cell crops
pipeline/fingerprint_vision.py# build tagging queue / load Claude's tags
pipeline/construction.py      # seamless vs cut-and-sew inference
pipeline/match.py      # category gate + attribute score + construction flag (validated)
pipeline/report.py     # HTML shortlist w/ thumbnails + page refs
run.py                 # orchestrator (build -> tag -> match)
TAG_PROMPT.md          # exact instructions for the vision tagging pass
```

## Setup
```bash
pip install -r requirements.txt
# for private catalogs, either `gh auth login` or:
export GITHUB_TOKEN=ghp_xxx
```
Point `config.yaml` at your repo (`source.github_repo`, `catalogs_subdir`) — keep
the catalogs in a **private** repo (NDA material). Or set `source.local_dir` to a
folder on your machine and skip GitHub entirely (Claude Code reads it directly —
no upload limit).

## Run (3 phases)
```bash
python run.py build      # fetch, parse text, segment crops, write tagging queue
# --- vision pass: have Claude Code follow TAG_PROMPT.md to fill data/vision_tags.jsonl ---
python run.py match      # assemble candidates, score, write data/report/index.html
```

## Tuning seams
- `segment.py`: `SLICE_FALLBACK` for catalogs whose page is one flattened composite.
- `fingerprint_text.py`: extend `SKU_RE` for other supplier SKU formats.
- `config.yaml match.construction_as_filter`: `true` to hard-exclude mismatches.
- `lionna/queries.yaml`: add the full SS27 line and tune attribute salience.

## Validated
The `match.py` engine was validated on two stand-in catalogs: it ranked seamless
long-sleeve tops as partial matches for the Refined Mesh Layer Top but capped the
score (missing `sheer_mesh_panel`) and flagged all as `seamless` mismatches, and
correctly returned *empty* for the Court Longline Polo (no polo in those catalogs).

