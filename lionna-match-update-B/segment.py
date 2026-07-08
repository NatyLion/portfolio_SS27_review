"""Rasterise pages -> product-cell crops from grid line-sheets.

Pulls embedded raster images with their page bounding boxes (PyMuPDF), filters by
area fraction, saves each crop tied to (catalog_id, supplier, page).

TODO tuning: catalogs whose grid is ONE flattened composite image per page won't
split this way -> set SLICE_FALLBACK and tune SLICE_GRID per catalog.
"""
import re
from pathlib import Path

SLICE_FALLBACK = False
SLICE_GRID = (3, 4)


def _fitz():
    try:
        import fitz  # PyMuPDF
        return fitz
    except ImportError:
        import pymupdf as fitz
        return fitz


def _slug(catalog_id):
    return re.sub(r"[^A-Za-z0-9]+", "_", catalog_id).strip("_")


def _save(doc, xref, out, fitz):
    pix = fitz.Pixmap(doc, xref)
    if pix.n - pix.alpha > 3:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    pix.save(str(out))


def segment(catalogs, cfg):
    fitz = _fitz()
    crops = Path(cfg["paths"]["crops"]); crops.mkdir(parents=True, exist_ok=True)
    lo, hi = cfg["cell_min_area_frac"], cfg["cell_max_area_frac"]
    manifest = []
    for c in catalogs:
        slug = _slug(c["catalog_id"])
        doc = fitz.open(str(c["path"]))
        for pno in range(len(doc)):
            page = doc[pno]
            parea = abs(page.rect.width * page.rect.height) or 1
            for idx, im in enumerate(page.get_images(full=True)):
                xref = im[0]
                for r in page.get_image_rects(xref):
                    frac = abs(r.width * r.height) / parea
                    if frac < lo or frac > hi:
                        continue
                    name = f"{slug}_p{pno+1:03d}_{idx:03d}.png"
                    try:
                        _save(doc, xref, crops / name, fitz)
                    except Exception as e:
                        print(f"  [segment] skip {name}: {e}"); continue
                    manifest.append({"catalog": c["catalog_id"], "supplier": c["supplier"],
                                     "page": pno + 1, "crop": name,
                                     "bbox": [r.x0, r.y0, r.x1, r.y1], "area_frac": round(frac, 3)})
        doc.close()
        print(f"[segment] {c['catalog_id']}: total crops {len(manifest)}")
    return manifest
