from fastapi import HTTPException


def lager_id_from_site(site: str) -> int:
    normalized = site.strip().lower()

    mapping = {
        "konstanz": 1,
        "sindelfingen": 2,
    }

    if normalized not in mapping:
        raise HTTPException(status_code=404, detail="Unknown site")

    return mapping[normalized]
