from fastapi import HTTPException


def site_id_from_name(con, site: str) -> int:
    normalized = (site or "").strip()

    if not normalized:
        raise HTTPException(status_code=400, detail="Site is required")

    row = con.execute(
        """
        SELECT id
        FROM sites
        WHERE lower(trim(name)) = lower(trim(?))
          AND active = 1
        """,
        (normalized,),
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Unknown site")

    return int(row["id"])