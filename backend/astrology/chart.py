# chart.py
# Calculates planetary positions, Ascendant, and house cusps using Swiss Ephemeris.
# All positions are tropical (geocentric), as per Ptolemy's Tetrabiblos.

from __future__ import annotations
import swisseph as swe
from dataclasses import dataclass
from datetime import datetime

PLANETS = {
    "Sun":     swe.SUN,
    "Moon":    swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus":   swe.VENUS,
    "Mars":    swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn":  swe.SATURN,
}

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Greek/Latin names used in 2nd century CE readings
GREEK_PLANET_NAMES = {
    "Sun":     "Helios",
    "Moon":    "Selene",
    "Mercury": "Hermes",
    "Venus":   "Aphrodite",
    "Mars":    "Ares",
    "Jupiter": "Zeus",
    "Saturn":  "Kronos",
}


@dataclass
class PlanetPosition:
    name: str
    greek_name: str
    longitude: float       # 0–360
    sign: str
    degree_in_sign: float  # 0–30
    retrograde: bool
    house: int             # whole sign house number (1–12)


@dataclass
class Chart:
    ascendant_degree: float
    ascendant_sign: str
    mc_degree: float
    mc_sign: str
    planets: dict[str, PlanetPosition]
    is_day_chart: bool     # Sun above horizon = day chart (sect)
    houses: list[str]      # 12 signs in whole-sign order starting from Asc sign


def degree_to_sign(longitude: float) -> tuple[str, float]:
    """Return (sign_name, degree_within_sign) from ecliptic longitude."""
    sign_index = int(longitude / 30) % 12
    degree_in_sign = longitude % 30
    return SIGNS[sign_index], degree_in_sign


def whole_sign_houses(asc_sign: str) -> list[str]:
    """Return the 12 whole-sign houses as a list of sign names, starting from Asc."""
    start = SIGNS.index(asc_sign)
    return [SIGNS[(start + i) % 12] for i in range(12)]


def prenatal_syzygy(jd_birth: float) -> dict:
    """
    Find the last New or Full Moon before birth.
    Returns sign, degree, and type ("new moon" or "full moon").
    Walking backward in 2-hour steps; elongation = (Moon - Sun) % 360.
    """
    step = 2 / 24  # 2 hours in days

    def elongation(jd):
        sun, _ = swe.calc_ut(jd, swe.SUN)
        moon, _ = swe.calc_ut(jd, swe.MOON)
        return (moon[0] - sun[0]) % 360

    prev = elongation(jd_birth)

    for i in range(1, 362):          # up to ~30 days back
        jd = jd_birth - i * step
        curr = elongation(jd)

        # New moon: elongation wraps from near-0 back to near-360
        if prev < 15 and curr > 345:
            moon_res, _ = swe.calc_ut(jd + step * 0.5, swe.MOON)
            sign, deg = degree_to_sign(moon_res[0])
            return {"type": "new moon", "sign": sign, "degree": round(deg, 2)}

        # Full moon: elongation crosses 180 from above to below (going backward)
        if prev > 175 and curr < 185 and curr < prev:
            moon_res, _ = swe.calc_ut(jd + step * 0.5, swe.MOON)
            sign, deg = degree_to_sign(moon_res[0])
            return {"type": "full moon", "sign": sign, "degree": round(deg, 2)}

        prev = curr

    return {"type": "unknown", "sign": "unknown", "degree": 0.0}


def calculate_chart(
    year: int, month: int, day: int,
    hour: float,           # decimal UT hour (e.g. 14.5 = 14:30)
    latitude: float,
    longitude: float,
) -> Chart:
    """
    Calculate a Hellenistic natal chart.
    All calculations use the tropical zodiac and whole sign houses.
    """
    swe.set_ephe_path(None)  # use bundled ephemeris

    # Julian Day Number (Universal Time)
    jd = swe.julday(year, month, day, hour)

    # House cusps & angles — 'W' = Whole Sign system
    cusps, ascmc = swe.houses(jd, latitude, longitude, b'W')
    asc_lon = ascmc[0]
    mc_lon  = ascmc[1]

    asc_sign, asc_deg = degree_to_sign(asc_lon)
    mc_sign,  mc_deg  = degree_to_sign(mc_lon)
    houses = whole_sign_houses(asc_sign)

    # Planetary positions
    planets = {}
    sun_house = 1  # determined during loop, used for sect
    for name, planet_id in PLANETS.items():
        result, _ = swe.calc_ut(jd, planet_id)
        lon  = result[0]
        speed = result[3]  # deg/day — negative = retrograde

        sign, deg_in_sign = degree_to_sign(lon)
        house = houses.index(sign) + 1  # 1-based

        if name == "Sun":
            sun_house = house

        planets[name] = PlanetPosition(
            name=name,
            greek_name=GREEK_PLANET_NAMES[name],
            longitude=lon,
            sign=sign,
            degree_in_sign=deg_in_sign,
            retrograde=(speed < 0),
            house=house,
        )

    # Sect: day chart if Sun is in houses 7–12 (above horizon)
    is_day_chart = sun_house in range(7, 13)

    return Chart(
        ascendant_degree=asc_deg,
        ascendant_sign=asc_sign,
        mc_degree=mc_deg,
        mc_sign=mc_sign,
        planets=planets,
        is_day_chart=is_day_chart,
        houses=houses,
    )
