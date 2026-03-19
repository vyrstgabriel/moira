# dignities.py
# Essential dignities: domicile, exaltation, triplicity, bounds (Egyptian), face/decan.
# Source: Ptolemy, Tetrabiblos I; Brennan, Hellenistic Astrology ch. 4–7.

# --- Domicile rulerships ---
DOMICILE = {
    "Aries":       "Mars",
    "Taurus":      "Venus",
    "Gemini":      "Mercury",
    "Cancer":      "Moon",
    "Leo":         "Sun",
    "Virgo":       "Mercury",
    "Libra":       "Venus",
    "Scorpio":     "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn":   "Saturn",
    "Aquarius":    "Saturn",
    "Pisces":      "Jupiter",
}

# --- Exaltations (sign: planet) ---
EXALTATION = {
    "Aries":       "Sun",
    "Taurus":      "Moon",
    "Cancer":      "Jupiter",
    "Virgo":       "Mercury",
    "Libra":       "Saturn",
    "Scorpio":     "Moon",   # fall of Moon is actually Scorpio — exalt is Taurus. TODO: verify
    "Capricorn":   "Mars",
    "Pisces":      "Venus",
}

# --- Triplicity lords (by day / by night) ---
# Source: Ptolemy Tetrabiblos I.18; Dorotheus via Brennan
TRIPLICITY = {
    "Aries":       ("Sun",     "Jupiter"),
    "Leo":         ("Sun",     "Jupiter"),
    "Sagittarius": ("Sun",     "Jupiter"),
    "Taurus":      ("Venus",   "Moon"),
    "Virgo":       ("Venus",   "Moon"),
    "Capricorn":   ("Venus",   "Moon"),
    "Gemini":      ("Saturn",  "Mercury"),
    "Libra":       ("Saturn",  "Mercury"),
    "Aquarius":    ("Saturn",  "Mercury"),
    "Cancer":      ("Venus",   "Mars"),
    "Scorpio":     ("Venus",   "Mars"),
    "Pisces":      ("Venus",   "Mars"),
}

# --- Egyptian bounds (terms) — longitude ranges within each sign ---
# Format: list of (upper_bound_degree, ruler) within the sign (0–30)
BOUNDS = {
    "Aries":       [(6, "Jupiter"), (12, "Venus"), (20, "Mercury"), (25, "Mars"), (30, "Saturn")],
    "Taurus":      [(8, "Venus"),   (14, "Mercury"),(22, "Jupiter"), (27, "Saturn"), (30, "Mars")],
    "Gemini":      [(6, "Mercury"), (12, "Jupiter"), (17, "Venus"),  (24, "Mars"),  (30, "Saturn")],
    "Cancer":      [(7, "Mars"),    (13, "Venus"),   (19, "Mercury"), (26, "Jupiter"), (30, "Saturn")],
    "Leo":         [(6, "Jupiter"), (11, "Venus"),   (18, "Saturn"), (24, "Mercury"), (30, "Mars")],
    "Virgo":       [(7, "Mercury"), (17, "Venus"),   (21, "Jupiter"), (28, "Mars"),   (30, "Saturn")],
    "Libra":       [(6, "Saturn"),  (14, "Mercury"), (21, "Jupiter"), (28, "Venus"),  (30, "Mars")],
    "Scorpio":     [(7, "Mars"),    (11, "Venus"),   (19, "Mercury"), (24, "Jupiter"), (30, "Saturn")],
    "Sagittarius": [(12, "Jupiter"),(17, "Venus"),   (21, "Mercury"), (26, "Saturn"), (30, "Mars")],
    "Capricorn":   [(7, "Mercury"), (14, "Jupiter"), (22, "Venus"),   (26, "Saturn"), (30, "Mars")],
    "Aquarius":    [(7, "Mercury"), (13, "Venus"),   (20, "Jupiter"), (25, "Mars"),   (30, "Saturn")],
    "Pisces":      [(12, "Venus"),  (16, "Jupiter"), (19, "Mercury"), (28, "Mars"),   (30, "Saturn")],
}

# --- Face/decan lords (10° divisions, Chaldean order) ---
# Each sign has three faces: 0–10, 10–20, 20–30
FACE_ORDER = ["Mars", "Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter"]

def face_lord(sign: str, degree_in_sign: float) -> str:
    """Return the decan/face lord for a given sign and degree."""
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer",
        "Leo", "Virgo", "Libra", "Scorpio",
        "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    sign_index = signs.index(sign)
    face_index = int(degree_in_sign / 10)
    # Chaldean order starts with Mars for Aries 0–10
    chaldean_start = sign_index * 3
    return FACE_ORDER[(chaldean_start + face_index) % 7]


def bound_lord(sign: str, degree_in_sign: float) -> str:
    """Return the Egyptian bounds (terms) lord."""
    for upper, ruler in BOUNDS[sign]:
        if degree_in_sign < upper:
            return ruler
    return BOUNDS[sign][-1][1]


def triplicity_lord(sign: str, is_day_chart: bool) -> str:
    """Return the triplicity lord for the given sect."""
    day_lord, night_lord = TRIPLICITY[sign]
    return day_lord if is_day_chart else night_lord


def dignities_of(planet: str, sign: str, degree_in_sign: float, is_day_chart: bool) -> list[str]:
    """Return a list of dignities the planet holds in this position."""
    dignities = []
    if DOMICILE.get(sign) == planet:
        dignities.append("domicile")
    if EXALTATION.get(sign) == planet:
        dignities.append("exaltation")
    if triplicity_lord(sign, is_day_chart) == planet:
        dignities.append("triplicity")
    if bound_lord(sign, degree_in_sign) == planet:
        dignities.append("bound")
    if face_lord(sign, degree_in_sign) == planet:
        dignities.append("face")
    return dignities
