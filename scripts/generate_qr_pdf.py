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
OUT_PDF = ROOT / "data" / "qr_labels.pdf"


def get_conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def table_columns(con: sqlite3.Connection, table: str) -> set[str]:
    cur = con.cursor()
    cols = cur.execute(f"PRAGMA table_info({table})").fetchall()
    return {c["name"] for c in cols}


def fetch_products():
    con = get_conn()
    cols = table_columns(con, "products")

    want = ["id", "kind", "nc_nummer", "materialkurztext", "product_name", "name", "active"]
    select_cols = [c for c in want if c in cols]
    if "id" not in select_cols:
        con.close()
        raise SystemExit("products table must have an id column")

    where = []
    if "active" in cols:
        where.append("active = 1")
    if "kind" in cols:
        where.append("lower(kind) = 'netcom'")

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    q = f"""
    SELECT {", ".join(select_cols)}
    FROM products
    {where_sql}
    ORDER BY id
    """

    rows = con.cursor().execute(q).fetchall()
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


def main():
    rows = fetch_products()
    if not rows:
        raise SystemExit("No matching products found (active netcom).")

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(OUT_PDF), pagesize=A4)
    W, H = A4

    # Table-like grid: no internal gaps
    cols_n = 3
    rows_per_page = 6

    margin_x = 8 * mm
    margin_y = 10 * mm
    gap_x = 0 * mm
    gap_y = 0 * mm

    label_w = (W - 2 * margin_x - (cols_n - 1) * gap_x) / cols_n
    label_h = (H - 2 * margin_y - (rows_per_page - 1) * gap_y) / rows_per_page

    def best_name(r):
        for k in ("materialkurztext", "product_name", "name"):
            if k in r.keys() and r[k]:
                return str(r[k]).strip()
        return ""

    def best_nc(r):
        if "nc_nummer" in r.keys() and r["nc_nummer"]:
            return str(r["nc_nummer"]).strip()
        return ""

    def sw(s: str, font: str, size: int) -> float:
        return c.stringWidth(s, font, size)

    def ellipsize(s: str, font: str, size: int, max_w: float) -> str:
        s = (s or "").strip()
        if not s:
            return ""
        if sw(s, font, size) <= max_w:
            return s
        dots = "..."
        if sw(dots, font, size) > max_w:
            return ""
        lo, hi = 0, len(s)
        while lo < hi:
            mid = (lo + hi) // 2
            cand = s[:mid].rstrip() + dots
            if sw(cand, font, size) <= max_w:
                lo = mid + 1
            else:
                hi = mid
        out = s[: max(0, lo - 1)].rstrip() + dots
        while out and sw(out, font, size) > max_w:
            out = out[:-1]
        return out

    def split_long_token(token: str, font: str, size: int, max_w: float):
        token = (token or "").strip()
        if not token:
            return []
        if sw(token, font, size) <= max_w:
            return [token]

        out = []
        i = 0
        n = len(token)

        while i < n:
            j = i + 1
            best = i + 1
            while j <= n:
                chunk = token[i:j]
                if sw(chunk, font, size) <= max_w:
                    best = j
                    j += 1
                else:
                    break

            chunk = token[i:best]
            if best < n:
                while chunk and sw(chunk + "-", font, size) > max_w:
                    best -= 1
                    chunk = token[i:best]
                if not chunk:
                    chunk = token[i:i+1]
                    best = i + 1
                out.append(chunk + "-")
            else:
                out.append(chunk)

            i = best

        return out

    def wrap_mixed(text: str, font: str, size: int, max_w: float):
        text = (text or "").strip()
        if not text:
            return []
        c.setFont(font, size)

        words = text.split()
        lines = []
        cur = ""

        for w in words:
            parts = split_long_token(w, font, size, max_w)
            for part in parts:
                if not cur:
                    test = part
                else:
                    test = cur + " " + part
                if sw(test, font, size) <= max_w:
                    cur = test
                else:
                    if cur:
                        lines.append(cur)
                    cur = part

        if cur:
            lines.append(cur)
        return lines

    def lead(size: int) -> float:
        if size >= 10:
            return 5.8 * mm
        if size == 9:
            return 5.2 * mm
        if size == 8:
            return 4.6 * mm
        return 4.0 * mm

    def draw_label(x, y, r):
        pid = int(r["id"])
        payload = str(pid)

        pad = 4 * mm
        gap = 4 * mm

        # QR (left)
        qr_side = label_h - 2 * pad
        qr_img = make_qr_image(payload)
        c.drawImage(ImageReader(qr_img), x + pad, y + pad, qr_side, qr_side, mask="auto")

        # text box (right)
        text_x = x + pad + qr_side + gap
        text_w = (x + label_w - pad) - text_x

        top_y = y + label_h - pad
        bottom_reserved = 7.5 * mm  # keep QR line safe
        min_y = y + pad + bottom_reserved
        available_h = max(0.0, top_y - min_y)

        name = best_name(r)
        nc = best_nc(r)

        # fixed sizes -> predictable, consistent printing
        name_font = ("Helvetica-Bold", 9)
        nc_font = ("Helvetica", 8)

        name_lead = lead(name_font[1])
        nc_lead = lead(nc_font[1])
        gap_between = 1.5 * mm

        # wrap to width first
        name_lines = wrap_mixed(name, name_font[0], name_font[1], text_w) or [""]
        nc_lines = wrap_mixed(nc, nc_font[0], nc_font[1], text_w) or [""]

        # HARD RESERVE space for NC: at least 2 lines if possible, else 1
        want_nc_lines = 2 if available_h >= (2 * nc_lead + gap_between + name_lead) else 1
        max_nc_lines = max(1, int(available_h // nc_lead)) if nc_lead > 0 else 1
        use_nc_lines = min(want_nc_lines, max_nc_lines, len(nc_lines))

        nc_block_h = use_nc_lines * nc_lead
        remaining_for_name = max(0.0, available_h - nc_block_h - gap_between)

        # allocate remaining to name
        max_name_lines = max(1, int(remaining_for_name // name_lead)) if name_lead > 0 else 1
        use_name_lines = min(max_name_lines, len(name_lines))

        draw_name = name_lines[:use_name_lines]
        if len(name_lines) > use_name_lines:
            draw_name[-1] = ellipsize(draw_name[-1], name_font[0], name_font[1], text_w)
        else:
            draw_name[-1] = ellipsize(draw_name[-1], name_font[0], name_font[1], text_w)

        draw_nc = nc_lines[:use_nc_lines]
        if len(nc_lines) > use_nc_lines:
            draw_nc[-1] = ellipsize(draw_nc[-1], nc_font[0], nc_font[1], text_w)
        else:
            draw_nc[-1] = ellipsize(draw_nc[-1], nc_font[0], nc_font[1], text_w)

        # draw with a small top padding so text doesn't start immediately at the border
        cursor = top_y - 2.5 * mm

        c.setFont(*name_font)
        for line in draw_name:
            if cursor - name_lead < min_y:
                break
            c.drawString(text_x, cursor, ellipsize(line, name_font[0], name_font[1], text_w))
            cursor -= name_lead

        if cursor - gap_between >= min_y:
            cursor -= gap_between

        c.setFont(*nc_font)
        for line in draw_nc:
            if cursor - nc_lead < min_y:
                break
            c.drawString(text_x, cursor, ellipsize(line, nc_font[0], nc_font[1], text_w))
            cursor -= nc_lead

        # QR payload bottom-right
        c.setFont("Helvetica", 8)
        c.drawRightString(x + label_w - pad, y + pad, f"QR: {payload}")

        # border
        c.setLineWidth(0.6)
        c.rect(x, y, label_w, label_h)

    labels_per_page = cols_n * rows_per_page

    for i, r in enumerate(rows):
        idx = i % labels_per_page
        row_i = idx // cols_n
        col_i = idx % cols_n

        x = margin_x + col_i * (label_w + gap_x)
        y = H - margin_y - (row_i + 1) * label_h - row_i * gap_y

        draw_label(x, y, r)

        if (i + 1) % labels_per_page == 0 and (i + 1) != len(rows):
            c.showPage()

    c.save()
    print(f"Wrote: {OUT_PDF}")


if __name__ == "__main__":
    main()
