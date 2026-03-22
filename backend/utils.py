def compute_tags(dims: dict, review_count: int) -> list:
    """Derive human-readable tags from dimension averages.

    Uses `or 0` guard to safely handle SQL AVG() returning None
    (Python None > float raises TypeError without this guard).
    Tags are only computed when there are at least 3 reviews.
    """
    if review_count < 3:
        return []
    we = dims.get("worship_energy") or 0
    cw = dims.get("community_warmth") or 0
    sd = dims.get("sermon_depth") or 0
    cp = dims.get("childrens_programs") or 0
    to_ = dims.get("theological_openness") or 0
    fac = dims.get("facilities") or 0

    tags = []
    if we > 4.5:
        tags.append("Vibrant worship")
    if cw > 4.5:
        tags.append("Strong community")
    if sd > 4.3:
        tags.append("Deep sermons")
    if cp > 4.0:
        tags.append("Kids programs")
    if to_ > 4.0:
        tags.append("Progressive")
    # Only tag Traditional when we have actual ratings (not a 0-guard default)
    if dims.get("theological_openness") is not None and to_ < 2.5:
        tags.append("Traditional")
    if fac > 4.3:
        tags.append("Beautiful facilities")
    return tags
