#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sqlite3

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

import qrcode


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "Lager_live.db"

OUT_KONSTANZ = ROOT / "data" / "qr_konstanz.pdf"
OUT_SINDELFINGEN = ROOT / "data" / "qr_sindelfingen.pdf"

LAGERS = [
    (1, "Konstanz", OUT_KONSTANZ),
    (2, "Sindelfingen", OUT_SINDELFINGEN),
]


def get_conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def fetch_products():
    con = get_conn()

    rows = con.execute(
        """
        SELECT id, kind, nc_nummer, product_name, active
        FROM products
        WHERE active = 1
        ORDER BY id
        """
    ).fetchall()

    con.close()
    return rows


def make_qr_image(payload: str):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").get_image()


def wrap_name_fixed(text: str, max_chars: int = 10) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []

    words = text.split()
    lines: list[str] = []
    cur = ""

    for w in words:
        if len(w) > max_chars:
            if cur:
                lines.append(cur)
                cur = ""
            for i in range(0, len(w), max_chars):
                lines.append(w[i:i + max_chars])
            continue

        test = w if not cur else cur + " " + w
        if len(test) <= max_chars:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w

    if cur:
        lines.append(cur)

    return lines


def wrap_text(c, text: str, font: str, size: int, width: float):
    c.setFont(font, size)

    words = text.split()
    lines = []
    cur = ""

    for w in words:
        test = w if not cur else cur + " " + w
        if c.stringWidth(test, font, size) <= width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w

    if cur:
        lines.append(cur)

    return lines


def draw_label(c, x, y, label_w, label_h, r):

    pid = int(r["id"])
    lager_id = r["lager_id"]
    payload = f"{lager_id}-{pid}"

    pad = 4 * mm
    gap = 4 * mm

    qr_side = label_h - 2 * pad
    qr_img = make_qr_image(payload)

    c.drawImage(
        ImageReader(qr_img),
        x + pad,
        y + pad,
        qr_side,
        qr_side,
        mask="auto",
    )

    text_x = x + pad + qr_side + gap
    text_w = (x + label_w - pad) - text_x
    top_y = y + label_h - pad

    name = r["product_name"] or ""
    nc = r["nc_nummer"] or ""

    name_font = ("Helvetica-Bold", 9)
    nc_font = ("Helvetica", 8)
    site_font = ("Helvetica-Bold", 8)

    name_lines = wrap_name_fixed(name, max_chars=10)
    nc_lines = wrap_text(c, nc, nc_font[0], nc_font[1], text_w)

    cursor = top_y - 2.5 * mm
    min_y = y + 16 * mm

    # product name
    c.setFont(*name_font)
    for line in name_lines:
        if cursor < min_y:
            break
        c.drawString(text_x, cursor, line)
        cursor -= 5 * mm

    # site
    if cursor >= min_y:
        c.setFont(*site_font)
        c.drawString(text_x, cursor, r["lager_name"])
        cursor -= 5 * mm

    # NC number
    c.setFont(*nc_font)
    for line in nc_lines:
        if cursor < y + 8 * mm:
            break
        c.drawString(text_x, cursor, line)
        cursor -= 4 * mm

    c.setFont("Helvetica", 8)
    c.drawRightString(x + label_w - pad, y + pad, f"QR: {payload}")

    c.setLineWidth(0.6)
    c.rect(x, y, label_w, label_h)


def generate_for_lager(products, lager_id, lager_name, out_pdf):

    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(out_pdf), pagesize=A4)
    W, H = A4

    cols_n = 3
    rows_per_page = 6

    margin_x = 8 * mm
    margin_y = 10 * mm

    label_w = (W - 2 * margin_x) / cols_n
    label_h = (H - 2 * margin_y) / rows_per_page

    labels_per_page = cols_n * rows_per_page

    rows = []

    for p in products:
        rows.append(
            {
                "id": p["id"],
                "product_name": p["product_name"],
                "nc_nummer": p["nc_nummer"],
                "lager_id": lager_id,
                "lager_name": lager_name,
            }
        )

    for i, r in enumerate(rows):

        idx = i % labels_per_page
        row_i = idx // cols_n
        col_i = idx % cols_n

        x = margin_x + col_i * label_w
        y = H - margin_y - (row_i + 1) * label_h

        draw_label(c, x, y, label_w, label_h, r)

        if (i + 1) % labels_per_page == 0 and (i + 1) != len(rows):
            c.showPage()

    c.save()

    print(f"Wrote: {out_pdf}")


def main():

    products = fetch_products()

    if not products:
        raise SystemExit("No products found.")

    for lager_id, lager_name, out_pdf in LAGERS:
        generate_for_lager(products, lager_id, lager_name, out_pdf)


if __name__ == "__main__":
    main()