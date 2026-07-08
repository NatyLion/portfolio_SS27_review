"""Text layer -> per-page {supplier, skus, materials, garment types}."""
import subprocess, re

SKU_RE = re.compile(r"(YG[-A-Z0-9]+|YGXT\d+)")
MAT_RE = re.compile(r"(\d{1,3}\s?%\s?[A-Za-z]+(?:\s*\+\s*\d{1,3}\s?%\s?[A-Za-z]+)+)")


def _pages(pdf):
    txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                         capture_output=True, text=True).stdout
    return txt.split("\f")


def build_text_db(catalogs, categories):
    db = []
    for c in catalogs:
        for i, pg in enumerate(_pages(c["path"]), 1):
            low = pg.lower()
            skus = sorted(set(SKU_RE.findall(pg)))
            mats = sorted(set(m.strip() for m in MAT_RE.findall(pg)))
            types = [cat for cat, kw in categories.items() if any(k in low for k in kw)]
            if not (skus or types):
                continue
            db.append({"catalog": c["catalog_id"], "supplier": c["supplier"], "page": i,
                       "skus": skus, "materials": mats, "types": types})
    print(f"[text] {len(db)} informative pages")
    return db
