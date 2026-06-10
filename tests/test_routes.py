from types import SimpleNamespace

from fastapi.testclient import TestClient

import main
from astrology.chart import Chart, PlanetPosition, whole_sign_houses


def test_index_route_serves_form():
    client = TestClient(main.app)

    response = client.get("/")

    assert response.status_code == 200
    assert "MOIRA" in response.text
    assert 'action="/reading"' in response.text


def test_static_css_is_served():
    client = TestClient(main.app)

    response = client.get("/static/style.css")

    assert response.status_code == 200
    assert "refined classical UI" in response.text


def test_reading_route_uses_mocked_boundaries(monkeypatch):
    houses = whole_sign_houses("Libra")
    chart = Chart(
        ascendant_degree=15,
        ascendant_sign="Libra",
        mc_degree=10,
        mc_sign="Cancer",
        houses=houses,
        is_day_chart=True,
        planets={
            "Sun": PlanetPosition("Sun", "Helios", 10, "Aries", 10, False, 7),
            "Moon": PlanetPosition("Moon", "Selene", 45, "Taurus", 15, False, 8),
            "Mercury": PlanetPosition("Mercury", "Hermes", 20, "Aries", 20, True, 7),
            "Venus": PlanetPosition("Venus", "Aphrodite", 170, "Virgo", 20, False, 12),
            "Mars": PlanetPosition("Mars", "Ares", 340, "Pisces", 10, False, 6),
            "Jupiter": PlanetPosition("Jupiter", "Zeus", 240, "Sagittarius", 0, False, 3),
            "Saturn": PlanetPosition("Saturn", "Kronos", 300, "Aquarius", 0, False, 5),
        },
    )

    monkeypatch.setattr(main.geolocator, "geocode", lambda place: SimpleNamespace(latitude=41.9, longitude=12.5))
    monkeypatch.setattr(main, "tf", SimpleNamespace(timezone_at=lambda lat, lng: "UTC"))
    monkeypatch.setattr(main, "calculate_chart", lambda *args: chart)
    monkeypatch.setattr(main, "prenatal_syzygy", lambda jd: {"type": "new moon", "sign": "Aries", "degree": 5})
    monkeypatch.setattr(main, "get_reading", lambda data: "# A Reading\n\n## Judgment\n\nA concise reading.")
    monkeypatch.setattr(main, "generate_chart_svg", lambda chart, data: "<svg><text>chart</text></svg>")

    client = TestClient(main.app)

    response = client.post(
        "/reading",
        data={
            "name": "Test Native",
            "gender": "unspecified",
            "date": "1990-05-17",
            "time": "14:35",
            "place": "Rome, Italy",
        },
    )

    assert response.status_code == 200
    assert "<h2>A Reading</h2>" in response.text
    assert "<h3>Judgment</h3>" in response.text
    assert "<svg><text>chart</text></svg>" in response.text
