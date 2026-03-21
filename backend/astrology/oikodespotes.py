# oikodespotes.py
# Calculates the Oikodespotes (master of the nativity / patron deity)
# using Ptolemy's method from Tetrabiblos III.10.
#
# Five aphetic points: Sun, Moon, Ascendant, Lot of Fortune, prenatal syzygy.
# For each point, all five essential dignities are tallied with weights.
# The planet accumulating the highest total score is the patron deity.

from __future__ import annotations
from astrology.dignities import DOMICILE, EXALTATION, triplicity_lord, bound_lord, face_lord
from astrology.chart import degree_to_sign, SIGNS

DIGNITY_WEIGHTS = {
    "domicile":   5,
    "exaltation": 4,
    "triplicity": 3,
    "bound":      2,
    "face":       1,
}

PLANETS = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]


def _dignities_at(planet: str, sign: str, degree: float, is_day: bool) -> list[str]:
    """Return the dignities a planet holds over a given zodiac point."""
    result = []
    if DOMICILE.get(sign) == planet:
        result.append("domicile")
    if EXALTATION.get(sign) == planet:
        result.append("exaltation")
    if triplicity_lord(sign, is_day) == planet:
        result.append("triplicity")
    if bound_lord(sign, degree) == planet:
        result.append("bound")
    if face_lord(sign, degree) == planet:
        result.append("face")
    return result


def calculate_oikodespotes(chart, lots: dict, syzygy: dict) -> dict:
    """
    Determine the Oikodespotes using Ptolemy's five aphetic points.

    Args:
        chart:   Chart dataclass from chart.py
        lots:    Dict of lot_name -> ecliptic longitude (from lots.py)
        syzygy:  Dict with keys 'sign', 'degree', 'type' (from chart.py)

    Returns dict with:
        patron  — name of the winning planet
        scores  — {planet: total_score}
        detail  — {planet: {point_name: [dignities]}}
    """
    # Build the five aphetic points as (sign, degree_in_sign)
    points = {
        "Sun":             (chart.planets["Sun"].sign,  chart.planets["Sun"].degree_in_sign),
        "Moon":            (chart.planets["Moon"].sign, chart.planets["Moon"].degree_in_sign),
        "Ascendant":       (chart.ascendant_sign,       chart.ascendant_degree),
        "Lot of Fortune":  degree_to_sign(lots["Fortune"]),
    }

    if syzygy.get("sign") and syzygy["sign"] != "unknown":
        points["Prenatal Syzygy"] = (syzygy["sign"], syzygy["degree"])

    # Tally dignity scores for each planet over each point
    scores = {p: 0 for p in PLANETS}
    detail = {p: {} for p in PLANETS}

    for point_name, (sign, deg) in points.items():
        for planet in PLANETS:
            dignities = _dignities_at(planet, sign, deg, chart.is_day_chart)
            if dignities:
                scores[planet] += sum(DIGNITY_WEIGHTS[d] for d in dignities)
                detail[planet][point_name] = dignities

    # Winner is the planet with the highest score
    patron = max(PLANETS, key=lambda p: scores[p])

    return {
        "patron": patron,
        "scores": scores,
        "detail": detail,
    }
