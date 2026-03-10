from __future__ import annotations

def username_from_worker(first_name: str, last_name: str) -> str:
    first = first_name.strip().lower().replace(" ", "")
    last = last_name.strip().lower().replace(" ", "")
    return f"{first}.{last}"
