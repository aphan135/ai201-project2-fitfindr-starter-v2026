"""
The runs your test needs. ← UNIT 4, MILESTONE 3

`run_eval.py` runs every scenario five times with caching disabled. Each
scenario maps to one numbered acceptance criterion in criteria.md.
"""

SCENARIOS = [
    {
        "name": "matching query completes all tools",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        "name": "impossible query stops before outfit",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        "name": "selected listing reaches outfit tool",
        "query": "90s track jacket in size M",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        "name": "same item fit card includes listing facts",
        "query": "vintage linen blazer in size M under $40",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        "name": "search results obey price ceiling",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 5,
    },
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
