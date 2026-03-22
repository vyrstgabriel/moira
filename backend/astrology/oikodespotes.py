# oikodespotes.py
# Master of the Nativity algorithm.
# Source: Porphyry, Introduction ch. 30, via Brennan (Astrology Podcast ep. 205).
#
# Method: determine which luminary "predominates" by angularity, easterness,
# and sect; the domicile lord of that luminary's sign is the master.

from __future__ import annotations
from astrology.dignities import DOMICILE
from astrology.chart import SIGNS


ANGULAR   = {1, 4, 7, 10}
SUCCEDENT = {2, 5, 8, 11}
EASTERN   = {1, 2, 3, 4, 5, 6}


def _angularity_rank(house: int) -> int:
    if house in ANGULAR:   return 3
    if house in SUCCEDENT: return 2
    return 1


def _angularity_label(house: int) -> str:
    if house in ANGULAR:   return "ANGULAR"
    if house in SUCCEDENT: return "SUCCEDENT"
    return "CADENT"


def calculate_oikodespotes(chart, lots: dict, syzygy: dict) -> dict:
    """
    Determine the Oikodespotes (Master of the Nativity).
    Source: Porphyry, Introduction ch. 30.

    Args:
        chart:  Chart dataclass from chart.py
        lots:   Dict of lot_name -> ecliptic longitude (unused here, kept for API consistency)
        syzygy: Dict with 'sign', 'degree', 'type' (unused here, kept for API consistency)

    Returns a dict with sect, luminary positions, predominator, master, and flags.
    """
    sun  = chart.planets["Sun"]
    moon = chart.planets["Moon"]

    asc_lon = SIGNS.index(chart.ascendant_sign) * 30 + chart.ascendant_degree
    sun_lon  = SIGNS.index(sun.sign)  * 30 + sun.degree_in_sign
    moon_lon = SIGNS.index(moon.sign) * 30 + moon.degree_in_sign

    sun_offset = (sun_lon - asc_lon) % 360
    sect = "DAY" if sun_offset < 180 else "NIGHT"

    # Twilight: Sun within 3° of ASC or DSC
    twilight = sun_offset < 3 or 177 < sun_offset < 183 or sun_offset > 357

    sun_house  = sun.house
    moon_house = moon.house

    sun_ang  = _angularity_rank(sun_house)
    moon_ang = _angularity_rank(moon_house)

    easterness_decided = False
    ambiguous          = False

    # Both cadent → Ascendant is the default predominator
    if sun_ang == 1 and moon_ang == 1:
        predominator    = "ASCENDANT"
        pred_sign       = chart.ascendant_sign
        decision_reason = "both luminaries cadent — Ascendant is default"

    # Criterion 1: Angularity
    elif sun_ang != moon_ang:
        predominator    = "SUN" if sun_ang > moon_ang else "MOON"
        pred_sign       = sun.sign if predominator == "SUN" else moon.sign
        decision_reason = "angularity"

    else:
        sun_east  = 1 if sun_house  in EASTERN else 0
        moon_east = 1 if moon_house in EASTERN else 0

        # Criterion 2: Easterness
        if sun_east != moon_east:
            predominator       = "SUN" if sun_east > moon_east else "MOON"
            pred_sign          = sun.sign if predominator == "SUN" else moon.sign
            decision_reason    = "easterness"
            easterness_decided = True

        else:
            sun_sect  = 1 if sect == "DAY"   else 0
            moon_sect = 1 if sect == "NIGHT" else 0

            # Criterion 3: Sect
            if sun_sect != moon_sect:
                predominator    = "SUN" if sun_sect > moon_sect else "MOON"
                pred_sign       = sun.sign if predominator == "SUN" else moon.sign
                decision_reason = "sect"

            else:
                # Full tie — default to sect light
                predominator    = "SUN" if sect == "DAY" else "MOON"
                pred_sign       = sun.sign if sect == "DAY" else moon.sign
                decision_reason = "full tie — defaulting to sect light"
                ambiguous       = True

    master = DOMICILE[pred_sign]

    return {
        "sect":              sect,
        "sun_house":         sun_house,
        "moon_house":        moon_house,
        "sun_angularity":    _angularity_label(sun_house),
        "moon_angularity":   _angularity_label(moon_house),
        "predominator":      predominator,
        "predominator_sign": pred_sign,
        "decision_reason":   decision_reason,
        "master":            master,
        "flags": {
            "twilight_birth":     twilight,
            "easterness_decided": easterness_decided,
            "ambiguous":          ambiguous,
        },
    }
