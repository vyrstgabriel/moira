from types import SimpleNamespace

from fastapi.testclient import TestClient

import main
from astrology.chart import Chart, PlanetPosition, whole_sign_houses
from quota import VisitorQuotaExceeded


class AllowReadingQuota:
    def reserve(self, cookie_value):
        return "signed-next-quota"


class RejectReadingQuota:
    def reserve(self, cookie_value):
        raise VisitorQuotaExceeded


def test_index_route_serves_form():
    client = TestClient(main.app)

    response = client.get("/")

    assert response.status_code == 200
    assert "MOIRA" in response.text
    assert 'action="/chart"' in response.text
    assert 'formaction="/reading"' in response.text
    assert 'href="/demo"' in response.text
    assert "5 sponsored Sonnet readings" in response.text


def test_index_supports_demo_only_deployment(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = TestClient(main.app)

    response = client.get("/")

    assert response.status_code == 200
    assert 'href="/demo"' in response.text
    assert 'action="/chart"' in response.text
    assert 'formaction="/reading"' not in response.text
    assert "public demo includes personal charts" in response.text


def test_demo_uses_checked_in_reading_without_network(monkeypatch, tmp_path):
    fixture = tmp_path / "augustus.md"
    fixture.write_text("# A Reading of the Nativity\n\n## Augustus\n\nA fixed reading.")
    monkeypatch.setattr(main, "DEMO_READING_PATH", fixture)
    monkeypatch.setattr(
        main,
        "get_reading",
        lambda data: (_ for _ in ()).throw(AssertionError("demo called Claude")),
    )
    monkeypatch.setattr(
        main,
        "geocode_place",
        lambda place: (_ for _ in ()).throw(AssertionError("demo geocoded")),
    )
    client = TestClient(main.app)

    response = client.get("/demo")

    assert response.status_code == 200
    assert "The Nativity of Augustus" in response.text
    assert "A fixed reading." in response.text
    assert "No AI request is made" in response.text


def test_live_reading_is_unavailable_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
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

    assert response.status_code == 503


def test_personal_chart_does_not_call_claude(monkeypatch):
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
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(main, "geocode_place", lambda place: SimpleNamespace(latitude=41.9, longitude=12.5))
    monkeypatch.setattr(main, "tf", SimpleNamespace(timezone_at=lambda lat, lng: "UTC"))
    monkeypatch.setattr(main, "calculate_chart", lambda *args: chart)
    monkeypatch.setattr(main, "prenatal_syzygy", lambda jd: {"type": "new moon", "sign": "Aries", "degree": 5})
    monkeypatch.setattr(main, "generate_chart_svg", lambda chart, data: "<svg><text>chart</text></svg>")
    monkeypatch.setattr(
        main,
        "get_reading",
        lambda data: (_ for _ in ()).throw(AssertionError("chart called Claude")),
    )
    client = TestClient(main.app)

    response = client.post(
        "/chart",
        data={
            "name": "Test Native",
            "gender": "unspecified",
            "date": "1990-05-17",
            "time": "14:35",
            "place": "Rome, Italy",
        },
    )

    assert response.status_code == 200
    assert "Test Native's Chart" in response.text
    assert "No AI request or API credits were used" in response.text
    assert "Planetary positions" in response.text


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

    monkeypatch.setattr(main, "geocode_place", lambda place: SimpleNamespace(latitude=41.9, longitude=12.5))
    monkeypatch.setattr(main, "tf", SimpleNamespace(timezone_at=lambda lat, lng: "UTC"))
    monkeypatch.setattr(main, "calculate_chart", lambda *args: chart)
    monkeypatch.setattr(main, "prenatal_syzygy", lambda jd: {"type": "new moon", "sign": "Aries", "degree": 5})
    monkeypatch.setattr(main, "get_reading", lambda data: "# A Reading\n\n## Judgment\n\nA concise reading.")
    monkeypatch.setattr(main, "get_reading_quota", lambda: AllowReadingQuota())
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
    assert "moira_reading_quota=signed-next-quota" in response.headers["set-cookie"]


def test_reading_route_stops_before_claude_when_visitor_quota_is_used(monkeypatch):
    monkeypatch.setattr(
        main,
        "personal_chart_data",
        lambda **kwargs: (object(), {
            "name": "Test Native",
            "ascendant": {"sign": "Libra", "degree": 15},
            "mc": {"sign": "Cancer", "degree": 10},
            "sect": "day",
            "oikodespotes": {"master": "Venus"},
            "planets": {},
            "lots": {},
        }),
    )
    monkeypatch.setattr(main, "get_reading_quota", lambda: RejectReadingQuota())
    monkeypatch.setattr(
        main,
        "get_reading",
        lambda data: (_ for _ in ()).throw(AssertionError("quota should stop Claude")),
    )
    monkeypatch.setattr(main, "generate_chart_svg", lambda chart, data: "<svg></svg>")
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

    assert response.status_code == 429
    assert "five sponsored Claude readings" in response.text
    assert "calculated chart remains available" not in response.text


def test_reading_route_keeps_chart_when_sponsored_budget_is_unavailable(monkeypatch):
    monkeypatch.setattr(
        main,
        "personal_chart_data",
        lambda **kwargs: (object(), {
            "name": "Test Native",
            "ascendant": {"sign": "Libra", "degree": 15},
            "mc": {"sign": "Cancer", "degree": 10},
            "sect": "day",
            "oikodespotes": {"master": "Venus"},
            "planets": {},
            "lots": {},
        }),
    )
    monkeypatch.setattr(main, "get_reading_quota", lambda: AllowReadingQuota())
    monkeypatch.setattr(
        main,
        "get_reading",
        lambda data: (_ for _ in ()).throw(main.ReadingUnavailable()),
    )
    monkeypatch.setattr(main, "generate_chart_svg", lambda chart, data: "<svg></svg>")
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

    assert response.status_code == 503
    assert "sponsored monthly budget" in response.text
    assert "Planetary positions" in response.text
