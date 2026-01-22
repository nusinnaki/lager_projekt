from __future__ import annotations

import csv
from pathlib import Path

from reportlab.pdfbase.pdfmetrics import stringWidth

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "data" / "products_master.csv"
OUT = ROOT / "data" / "qr_labels.pdf"


def norm(x) -> str:
    return " ".join(str(x or "").replace("\xa0", " ").split()).strip()


def wrap_text_to_width(
    text: str,
    font_name: str,
    font_size: float,
    max_width: float,
    max_lines: int = 3,
) -> list[str]:
    text = norm(text)
    if not text:
        return []

    words = text.split()
    lines: list[str] = []
    current: list[str] = []

    def width(s: str) -> float:
        return stringWidth(s, font_name, font_size)

    for word in words:
        test = " ".join(current + [word])
        if current and width(test) > max_width:
            lines.append(" ".join(current))
            current = [word]
            if len(lines) >= max_lines:
                break
        else:
            current.append(word)

    if current and len(lines) < max_lines:
        lines.append(" ".join(current))

    # hard cut with ellipsis if a line is still too wide (single long token)
    out: list[str] = []
    ell = "…"
    for ln in lines:
        if width(ln) <= max_width:
            out.append(ln)
        else:
            s = ln
            while s and width(s + ell) > max_width:
                s = s[:-1]
            out.append((s + ell) if s else ell)

    return out


def main() -> None:
    if not MASTER.exists():
        raise FileNotFoundError(MASTER)

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.graphics.barcode.qr import QrCodeWidget
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics import renderPDF

    rows: list[tuple[str, str, str]] = []
    with MASTER.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        needed = {"product_name", "internal_id", "qr_code"}
        if not reader.fieldnames or not needed.issubset(reader.fieldnames):
            raise ValueError("CSV must contain product_name, internal_id, qr_code")

        for r in reader:
            name = norm(r.get("product_name"))
            iid = norm(r.get("internal_id"))
            qr = norm(r.get("qr_code"))
            if name and iid and qr:
                rows.append((name, iid, qr))

    OUT.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(OUT), pagesize=A4)
    W, H = A4

    cols = 3
    rows_per_page = 8
    margin_x = 10 * mm
    margin_y = 12 * mm
    gap_x = 4 * mm
    gap_y = 4 * mm

    label_w = (W - 2 * margin_x - (cols - 1) * gap_x) / cols
    label_h = (H - 2 * margin_y - (rows_per_page - 1) * gap_y) / rows_per_page

    pad = 3 * mm
    qr_size = min(label_h - 2 * pad, label_w * 0.48)

    def draw_qr(x: float, y: float, size: float, text: str) -> None:
        qrw = QrCodeWidget(text)
        b = qrw.getBounds()
        w = b[2] - b[0]
        h = b[3] - b[1]

        inner = size - 2 * mm
        scale = min(inner / w, inner / h)
        tx = (size - w * scale) / 2 - b[0] * scale
        ty = (size - h * scale) / 2 - b[1] * scale

        d = Drawing(size, size, transform=[scale, 0, 0, scale, tx, ty])
        d.add(qrw)
        renderPDF.draw(d, c, x, y)

    def draw_label(x0: float, y0: float, name: str, iid: str, qr_text: str) -> None:
        c.rect(x0, y0, label_w, label_h, stroke=1, fill=0)

        qr_x = x0 + pad
        qr_y = y0 + (label_h - qr_size) / 2
        draw_qr(qr_x, qr_y, qr_size, qr_text)

        text_x = qr_x + qr_size + 3 * mm
        top_y = y0 + label_h - pad - 2 * mm

        name_font = "Helvetica-Bold"
        name_size = 7
        c.setFont(name_font, name_size)

        available_w = (x0 + label_w) - text_x - pad
        line_step = 3.6 * mm

        y = top_y
        for ln in wrap_text_to_width(name, name_font, name_size, available_w, max_lines=3):
            c.drawString(text_x, y, ln)
            y -= line_step

        c.setFont("Helvetica", 7)
        c.drawString(text_x, y0 + pad + 9.5 * mm, f"ID: {iid}")

        c.setFont("Helvetica", 6.5)
        qr_line = qr_text[:47] + "…" if len(qr_text) > 48 else qr_text
        c.drawString(text_x, y0 + pad + 4.5 * mm, qr_line)

    per_page = cols * rows_per_page
    for i, (name, iid, qr_text) in enumerate(rows):
        pos = i % per_page
        if i > 0 and pos == 0:
            c.showPage()

        r = pos // cols
        col = pos % cols
        x = margin_x + col * (label_w + gap_x)
        y = H - margin_y - (r + 1) * label_h - r * gap_y

        draw_label(x, y, name, iid, qr_text)

    c.save()
    print(f"Wrote {len(rows)} labels to {OUT}")


if __name__ == "__main__":
    main()
