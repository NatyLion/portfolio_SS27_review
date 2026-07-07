"""Per-PDF diagnostics: page count + whether a text layer exists.

No text layer (scanned/raster) => fingerprint_text yields nothing for that file,
so category must come from the vision pass. This flags that up front.
"""
import subprocess


def inventory(pdf_paths):
    info = {}
    for p in pdf_paths:
        pinfo = subprocess.run(["pdfinfo", str(p)], capture_output=True, text=True).stdout
        n = next((int(l.split()[-1]) for l in pinfo.splitlines() if l.startswith("Pages")), 0)
        fonts = subprocess.run(["pdffonts", str(p)], capture_output=True, text=True).stdout
        has_text = len(fonts.strip().splitlines()) > 2
        info[p.name] = {"pages": n, "has_text_layer": has_text}
        print(f"[inventory] {p.name}: {n}p  text_layer={has_text}")
    return info
