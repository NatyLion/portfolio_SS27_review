"""Per-PDF diagnostics: page count + text-layer presence."""
import subprocess


def inventory(catalogs):
    info = {}
    for c in catalogs:
        p = c["path"]
        pinfo = subprocess.run(["pdfinfo", str(p)], capture_output=True, text=True).stdout
        n = next((int(l.split()[-1]) for l in pinfo.splitlines() if l.startswith("Pages")), 0)
        fonts = subprocess.run(["pdffonts", str(p)], capture_output=True, text=True).stdout
        has_text = len(fonts.strip().splitlines()) > 2
        info[c["catalog_id"]] = {"pages": n, "has_text_layer": has_text, "supplier": c["supplier"]}
        print(f"[inventory] {c['catalog_id']}: {n}p text={has_text}")
    return info
