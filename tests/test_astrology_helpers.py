import pytest

from astrology.aspects import aspect_between, sign_distance
from astrology.chart import degree_to_sign, whole_sign_houses
from astrology.dignities import bound_lord, dignities_of, face_lord, triplicity_lord
from astrology.lots import calculate_lot


@pytest.mark.parametrize(
    ("longitude", "sign", "degree"),
    [
        (0, "Aries", 0),
        (29.99, "Aries", 29.99),
        (30, "Taurus", 0),
        (359.5, "Pisces", 29.5),
        (390, "Taurus", 0),
    ],
)
def test_degree_to_sign(longitude, sign, degree):
    actual_sign, actual_degree = degree_to_sign(longitude)

    assert actual_sign == sign
    assert actual_degree == pytest.approx(degree)


def test_whole_sign_houses_wrap_from_ascendant():
    assert whole_sign_houses("Libra") == [
        "Libra",
        "Scorpio",
        "Sagittarius",
        "Capricorn",
        "Aquarius",
        "Pisces",
        "Aries",
        "Taurus",
        "Gemini",
        "Cancer",
        "Leo",
        "Virgo",
    ]


@pytest.mark.parametrize(
    ("sign_a", "sign_b", "distance", "aspect"),
    [
        ("Aries", "Aries", 1, "conjunction"),
        ("Aries", "Gemini", 3, "sextile"),
        ("Aries", "Cancer", 4, "square"),
        ("Aries", "Leo", 5, "trine"),
        ("Aries", "Libra", 7, "opposition"),
        ("Aries", "Taurus", 2, None),
    ],
)
def test_whole_sign_aspects(sign_a, sign_b, distance, aspect):
    assert sign_distance(sign_a, sign_b) == distance
    assert sign_distance(sign_b, sign_a) == distance
    assert aspect_between(sign_a, sign_b) == aspect
    assert aspect_between(sign_b, sign_a) == aspect


def test_lot_calculation_normalizes_to_zodiac():
    assert calculate_lot(350, 20, 40) == pytest.approx(330)
    assert calculate_lot(10, 20, 40) == pytest.approx(350)


def test_dignity_helpers_return_expected_lords():
    assert triplicity_lord("Aries", is_day_chart=True) == "Sun"
    assert triplicity_lord("Aries", is_day_chart=False) == "Jupiter"
    assert bound_lord("Aries", 5.99) == "Jupiter"
    assert bound_lord("Aries", 6) == "Venus"
    assert face_lord("Aries", 0) == "Mars"
    assert face_lord("Aries", 10) == "Sun"


def test_dignities_of_collects_multiple_dignities():
    assert dignities_of("Sun", "Aries", 10, is_day_chart=True) == [
        "exaltation",
        "triplicity",
        "face",
    ]
