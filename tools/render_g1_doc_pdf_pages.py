from pathlib import Path

import fitz


pdf = Path(r"C:\Users\tbond\OneDrive - Fundación UADE\Escritorio\TPO_G1_MuJoCo_QA\TPO_G1_MuJoCo_Guia_Docente.pdf")
out = pdf.parent / "pages"
out.mkdir(exist_ok=True)

doc = fitz.open(pdf)
for i, page in enumerate(doc, start=1):
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
    pix.save(out / f"page-{i:02d}.png")

print("pages", doc.page_count)
print(out)
