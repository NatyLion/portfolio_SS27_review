"""Rasterize pages and extract product-cell crops from grid line-sheets.

Strategy: pull embedded raster images with their page bounding boxes (PyMuPDF),
filter by area fraction, save each as a crop tied to (catalog, page).

TODO tuning seam: catalogs whose grid is ONE flattened composite image per page
won't split this way -> set SLICE_FALLBACK and tune rows/cols per catalog.
"""
from pathlib import Path

SLICE_FALLBACK = False   # flip on for composite-image catalogs
SLICE_GRID = (3, 4)      # rows, cols for the fallback slicer


def _fitz():
    try:
        import fitz  # PyMuPDF
        return fitz
    except ImportError:
        import pymupdf as fitz
        return fitz


def _save_pixmap(doc, xref, out):
    fitz = _fitz()
    pix = fitz.Pixmap(doc, xref)
    if pix.n - pix.alpha > 3:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    pix.save(str(out))


def segment(pdf_paths, cfg):
    crops = Path(cfg["paths"]["crops"]); crops.mkdir(parents=True, exist_ok=True)
    lo, hi = cfg["cell_min_area_frac"], cfg["cell_max_area_frac"]
    fitz = _fitz()
    manifest = []
    for pdf in pdf_paths:
        doc = fitz.open(str(pdf))
        for pno in range(len(doc)):
            page = doc[pno]
            parea = abs(page.rect.width * page.rect.height) or 1
            for idx, im in enumerate(page.get_images(full=True)):
                xref = im[0]
                for r in page.get_image_rects(xref):
                    frac = abs(r.width * r.height) / parea
                    if frac < lo or frac > hi:
                        continue
                    name = f"{pdf.stem}_p{pno+1:03d}_{idx:03d}.png"
                    try:
                        _save_pixmap(doc, xref, crops / name)
                    except Exception as e:
                        print(f"  [segment] skip {name}: {e}"); continue
                    manifest.append({"catalog": pdf.name, "page": pno + 1,
                                     "crop": name, "bbox": [r.x0, r.y0, r.x1, r.y1],
                                     "area_frac": round(frac, 3)})
        doc.close()
        print(f"[segment] {pdf.name}: total crops {len(manifest)}")
    return manifest
