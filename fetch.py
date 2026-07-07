"""Text layer -> per-page {skus, materials, garment types}.

Ports the parser validated in the prototype. Robust to catalogs that use
different SKU prefixes (extend SKU_RE as needed).
"""
import subprocess, re

SKU_RE = re.compile(r"(YG[-A-Z0-9]+|YGXT\d+)")
MAT_RE = re.compile(r"(\d{1,3}\s?%\s?[A-Za-z]+(?:\s*\+\s*\d{1,3}\s?%\s?[A-Za-z]+)+)")


def _pages(pdf):
    txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                         capture_output=True, text=True).stdout
    return txt.split("\f")


def build_text_db(pdf_paths, categories):
    db = []
    for pdf in pdf_paths:
        for i, pg in enumerate(_pages(pdf), 1):
            low = pg.lower()
            skus = sorted(set(SKU_RE.findall(pg)))
            if not skus:
                continue
            mats = sorted(set(m.strip() for m in MAT_RE.findall(pg)))
            types = [c for c, kw in categories.items() if any(k in low for k in kw)]
            db.append({"catalog": pdf.name, "page": i,
                       "skus": skus, "materials": mats, "types": types})
    print(f"[text] {len(db)} SKU-bearing pages parsed")
    return db
