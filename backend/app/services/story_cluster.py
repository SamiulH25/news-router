import re


def _normalize_title(title: str) -> str:
    plain = re.sub(r"[^\w\s]", " ", title.lower())
    return re.sub(r"\s+", " ", plain).strip()


def cluster_key(title: str) -> str:
    """Group near-duplicate headlines by first few significant words."""
    words = [w for w in _normalize_title(title).split() if len(w) > 2][:5]
    return " ".join(words) if words else _normalize_title(title)[:48]
