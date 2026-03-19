# aspects.py
# Whole-sign aspects — the Hellenistic standard.
# Planets aspect each other by sign relationship, not by degree.
# Source: Ptolemy, Tetrabiblos I.13; Brennan, Hellenistic Astrology ch. 9.

ASPECT_TYPES = {
    1:  None,          # conjunction (same sign) — treated separately
    3:  "sextile",     # 2 signs apart
    4:  "square",      # 3 signs apart
    5:  "trine",       # 4 signs apart
    7:  "opposition",  # 6 signs apart
}

# Ptolemaic aspect qualities
ASPECT_QUALITY = {
    "sextile":   "friendly",
    "trine":     "harmonious",
    "square":    "tense",
    "opposition": "confrontational",
}

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]


def sign_distance(sign_a: str, sign_b: str) -> int:
    """
    Returns the forward distance in signs from sign_a to sign_b (1–12).
    Used to determine aspect type.
    """
    a = SIGNS.index(sign_a)
    b = SIGNS.index(sign_b)
    return ((b - a) % 12) + 1


def aspect_between(sign_a: str, sign_b: str) -> str | None:
    """
    Returns the aspect type between two signs, or None if they don't aspect.
    Conjunction = same sign (distance 1).
    Aversion (no aspect) = distance 2, 6, 8, 11, 12.
    """
    dist = sign_distance(sign_a, sign_b)
    if dist == 1:
        return "conjunction"
    return ASPECT_TYPES.get(dist)


def all_aspects(planets: dict) -> list[dict]:
    """
    Return all whole-sign aspects between the seven traditional planets.
    Each entry: {planet_a, planet_b, aspect, quality}
    """
    planet_names = list(planets.keys())
    aspects = []
    for i, name_a in enumerate(planet_names):
        for name_b in planet_names[i + 1:]:
            sign_a = planets[name_a].sign
            sign_b = planets[name_b].sign
            asp = aspect_between(sign_a, sign_b)
            if asp:
                aspects.append({
                    "planet_a": name_a,
                    "planet_b": name_b,
                    "aspect": asp,
                    "quality": ASPECT_QUALITY.get(asp, "neutral"),
                })
    return aspects
