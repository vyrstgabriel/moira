# lots.py
# Greek Lots (Klēroi) — also called Arabic Parts in later tradition.
# Source: Paulus Alexandrinus; Brennan, Hellenistic Astrology ch. 12.
# Formula: Lot = Ascendant + Planet A - Planet B
# Day/night charts reverse the Fortune formula; others vary by source.

from __future__ import annotations


def calculate_lot(asc: float, planet_a: float, planet_b: float) -> float:
    """Generic lot calculation, result normalized to 0–360."""
    return (asc + planet_a - planet_b) % 360


def lots(chart) -> dict[str, float]:
    """
    Calculate the seven Hermetic Lots for a chart.
    Returns a dict of lot_name -> ecliptic longitude.
    """
    asc  = chart.ascendant_degree + _sign_offset(chart.ascendant_sign)
    sun  = chart.planets["Sun"].longitude
    moon = chart.planets["Moon"].longitude
    mer  = chart.planets["Mercury"].longitude
    ven  = chart.planets["Venus"].longitude
    mar  = chart.planets["Mars"].longitude
    jup  = chart.planets["Jupiter"].longitude
    sat  = chart.planets["Saturn"].longitude

    day = chart.is_day_chart

    return {
        # Lot of Fortune (Tyche) — material life, body
        "Fortune": calculate_lot(asc, moon, sun) if day else calculate_lot(asc, sun, moon),

        # Lot of Spirit (Daimon) — soul, actions, father
        "Spirit":  calculate_lot(asc, sun, moon) if day else calculate_lot(asc, moon, sun),

        # Lot of Eros — desire, what one loves
        "Eros":    calculate_lot(asc, ven, _spirit_raw(asc, sun, moon, day)),

        # Lot of Necessity (Ananke) — compulsion, obstacles
        "Necessity": calculate_lot(asc, _fortune_raw(asc, sun, moon, day), mer),

        # Lot of Courage (Tolma) — boldness, daring
        "Courage": calculate_lot(asc, _fortune_raw(asc, sun, moon, day), mar),

        # Lot of Victory (Nike) — success, allies
        "Victory": calculate_lot(asc, jup, _spirit_raw(asc, sun, moon, day)),

        # Lot of Nemesis — punishment, what undermines
        "Nemesis": calculate_lot(asc, sat, _fortune_raw(asc, sun, moon, day)),
    }


# --- Internal helpers ---

def _sign_offset(sign: str) -> float:
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer",
        "Leo", "Virgo", "Libra", "Scorpio",
        "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    return signs.index(sign) * 30


def _fortune_raw(asc, sun, moon, day):
    return (asc + moon - sun) % 360 if day else (asc + sun - moon) % 360


def _spirit_raw(asc, sun, moon, day):
    return (asc + sun - moon) % 360 if day else (asc + moon - sun) % 360
