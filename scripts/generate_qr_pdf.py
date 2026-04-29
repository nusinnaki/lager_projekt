#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sqlite3

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

import qrcode


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "Lager_live.db"
OUTPUT_DIR = ROOT / "data"


def get_conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def fetch_label_rows():
    con = get_conn()
    rows = con.execute(
        """
        SELECT
          s.id AS site_id,
          s.name AS site_name,
          p.id AS product_id,
          p.product_name,
          p.nc_nummer,
          l.id AS location_id,
          l.shelf,
          l.row
        FROM sites s
        CROSS JOIN products p
        LEFT JOIN product_site_locations psl
          ON psl.site_id = s.id
         AND psl.product_id = p.id
        LEFT JOIN locations l
          ON l.id = psl.location_id
         AND l.site_id = s.id
         AND l.active = 1
        WHERE s.active = 1
          AND p.active = 1
        ORDER BY s.id, p.id
        """
    ).fetchall()
    con.close()
    return rows


def slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^a-z0-9_äöüß]", "", text)
    return text or "site"


def make_qr_image(payload: str):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=1,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").get_image()


def string_width(c, text: str, font: str, size: int) -> float:
    c.setFont(font, size)
    return c.stringWidth(text, font, size)


def ellipsize(c, text: str, font: str, size: int, max_width: float) -> str:
    text = (text or "").strip()
    if not text:
        return ""

    if string_width(c, text, font, size) <= max_width:
        return text

    dots = "..."
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi) // 2
        candidate = text[:mid].rstrip() + dots
        if string_width(c, candidate, font, size) <= max_width:
            lo = mid + 1
        else:
            hi = mid

    out = text[: max(0, lo - 1)].rstrip() + dots
    while out and string_width(c, out, font, size) > max_width:
        out = out[:-1]
    return out


def wrap_text(c, text: str, font: str, size: int, max_width: float, max_lines: int) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []

    c.setFont(font, size)
    words = text.split()
    lines = []
    cur = ""

    for i, word in enumerate(words):
        candidate = word if not cur else f"{cur} {word}"
        if c.stringWidth(candidate, font, size) <= max_width:
            cur = candidate
        else:
            if cur:
                lines.append(cur)
            cur = word
            if len(lines) == max_lines - 1:
                remaining = " ".join([cur] + words[i + 1:])
                lines.append(ellipsize(c, remaining, font, size, max_width))
                return lines

    if cur:
        lines.append(cur)

    if len(lines) > max_lines:
        lines = lines[:max_lines]

    if len(lines) == max_lines:
        lines[-1] = ellipsize(c, lines[-1], font, size, max_width)

    return lines


def draw_label(c, x, y, label_w, label_h, r):
    site_id = int(r["site_id"])
    product_id = int(r["product_id"])
    payload = f"{site_id}-{product_id}"

    left = x + 3 * mm
    top = y + label_h - 2.7 * mm

    c.setFont("Helvetica", 6.8)
    c.drawString(left, top, f"QR: {payload}")

    qr_size = 24.5 * mm
    qr_y = top - 1.8 * mm - qr_size
    qr_x = left

    qr_img = make_qr_image(payload)
    c.drawImage(
        ImageReader(qr_img),
        qr_x,
        qr_y,
        qr_size,
        qr_size,
        mask="auto",
    )

    text_left = left
    text_width_available = label_w - 6 * mm

    product_line = f"{(r['product_name'] or '').strip()} {(r['site_name'] or '').strip()}".strip()
    name_lines = wrap_text(
        c,
        product_line,
        "Helvetica-Bold",
        6.7,
        text_width_available,
        max_lines=3,
    )

    name_y = qr_y - 2.4 * mm
    c.setFont("Helvetica-Bold", 6.7)
    for i, line in enumerate(name_lines):
        c.drawString(text_left, name_y - i * 3.15 * mm, line)

    after_name_y = name_y - max(1, len(name_lines)) * 3.15 * mm - 0.6 * mm

    nc_text = ellipsize(c, r["nc_nummer"] or "-", "Helvetica", 6.0, text_width_available)
    c.setFont("Helvetica", 6.0)
    c.drawString(text_left, after_name_y, nc_text)

    shelf = r["shelf"]
    row = r["row"]
    if shelf is None or row is None:
        loc_text = "Regal - / Fach -"
    else:
        loc_text = f"Regal {shelf} / Fach {row}"

    loc_text = ellipsize(c, loc_text, "Helvetica-Bold", 6.2, text_width_available)
    c.setFont("Helvetica-Bold", 6.2)
    c.drawString(text_left, after_name_y - 3.7 * mm, loc_text)


def draw_grid_lines(c, page_w, page_h, cols_n, rows_per_page, margin_x, margin_y, gap_x, gap_y, label_w, label_h):
    c.setLineWidth(0.25)

    # vertical separator lines between columns
    for col in range(cols_n - 1):
        x_line = margin_x + (col + 1) * label_w + col * gap_x + gap_x / 2
        c.line(x_line, margin_y, x_line, page_h - margin_y)

    # horizontal separator lines between rows
    for row in range(rows_per_page - 1):
        y_top_current = page_h - margin_y - row * (label_h + gap_y) - label_h
        y_line = y_top_current - gap_y / 2
        c.line(margin_x, y_line, page_w - margin_x, y_line)


def generate_for_site(rows: list[sqlite3.Row], out_pdf: Path):
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(out_pdf), pagesize=A4)
    W, H = A4

    cols_n = 4
    rows_per_page = 6

    margin_x = 2.5 * mm
    margin_y = 3.5 * mm

    gap_x = 2.0 * mm
    gap_y = 4.6 * mm

    label_w = (W - 2 * margin_x - (cols_n - 1) * gap_x) / cols_n
    label_h = (H - 2 * margin_y - (rows_per_page - 1) * gap_y) / rows_per_page

    labels_per_page = cols_n * rows_per_page

    for i, r in enumerate(rows):
        idx = i % labels_per_page
        row_i = idx // cols_n
        col_i = idx % cols_n

        if idx == 0:
            draw_grid_lines(
                c, W, H, cols_n, rows_per_page,
                margin_x, margin_y, gap_x, gap_y, label_w, label_h
            )

        x = margin_x + col_i * (label_w + gap_x)
        y = H - margin_y - (row_i + 1) * label_h - row_i * gap_y

        draw_label(c, x, y, label_w, label_h, r)

        if (i + 1) % labels_per_page == 0 and (i + 1) != len(rows):
            c.showPage()

    c.save()
    print(f"Wrote: {out_pdf}")


def main():
    rows = fetch_label_rows()
    if not rows:
        raise SystemExit("No active sites/products found.")

    grouped: dict[tuple[int, str], list[sqlite3.Row]] = {}
    for r in rows:
        key = (int(r["site_id"]), r["site_name"])
        grouped.setdefault(key, []).append(r)

    for (site_id, site_name), site_rows in grouped.items():
        filename = f"qr_{site_id}_{slugify(site_name)}.pdf"
        out_pdf = OUTPUT_DIR / filename
        generate_for_site(site_rows, out_pdf)


if __name__ == "__main__":
    main()