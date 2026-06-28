# main.py
# FastAPI application entry point.

from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import swisseph as swe
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from timezonefinder import TimezoneFinder
from datetime import datetime
from functools import lru_cache
from html import escape
from pathlib import Path
import os
import pytz

from astrology.chart import calculate_chart, degree_to_sign, prenatal_syzygy
from astrology.dignities import dignities_of
from astrology.lots import lots
from astrology.aspects import all_aspects
from astrology.chart_svg import generate_chart_svg
from astrology.oikodespotes import calculate_oikodespotes
from quota import ReadingQuota, VisitorQuotaExceeded
from reader import get_reading, ReadingUnavailable

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DEMO_READING_PATH = BASE_DIR / "backend" / "demo" / "augustus.md"
READING_QUOTA_COOKIE = "moira_reading_quota"

# Suetonius records 23 September 63 BCE, just before sunrise, in Rome.
# 05:40 local mean time is represented as approximately 04:50 UT here.
AUGUSTUS_BIRTH = {
    "year": -62,  # astronomical year numbering: -62 == 63 BCE
    "month": 9,
    "day": 23,
    "hour": 4 + 50 / 60,
    "latitude": 41.9028,
    "longitude": 12.4964,
}

app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")
templates = Jinja2Templates(directory=FRONTEND_DIR)

geolocator = Nominatim(
    user_agent=os.getenv(
        "NOMINATIM_USER_AGENT",
        f"moira-natal-chart/1.0 ({os.getenv('RENDER_EXTERNAL_HOSTNAME', 'local')})",
    ),
    domain=os.getenv("NOMINATIM_DOMAIN", "nominatim.openstreetmap.org"),
)
rate_limited_geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
tf = TimezoneFinder()


@lru_cache(maxsize=512)
def geocode_place(place: str):
    """Geocode a visitor-entered place while respecting the public service limits."""
    return rate_limited_geocode(place.strip())


def reading_to_html(text: str) -> str:
    """Render the model's lightweight Markdown-ish output as escaped HTML."""
    blocks = []
    for raw in text.split("\n\n"):
        block = raw.strip()
        if not block:
            continue

        if set(block) <= {"-"} and len(block) >= 3:
            blocks.append("<hr>")
            continue

        if block.startswith("## "):
            blocks.append(f"<h3>{escape(block[3:].strip())}</h3>")
            continue

        if block.startswith("# "):
            blocks.append(f"<h2>{escape(block[2:].strip())}</h2>")
            continue

        paragraph = "<br>".join(escape(line.strip()) for line in block.splitlines())
        blocks.append(f"<p>{paragraph}</p>")

    return "".join(blocks)


def get_reading_quota() -> ReadingQuota:
    visitor_limit = int(os.getenv("MOIRA_VISITOR_MONTHLY_LIMIT", "5"))
    signing_secret = os.getenv("MOIRA_COOKIE_SECRET") or os.getenv("ANTHROPIC_API_KEY", "")
    return ReadingQuota(signing_secret, visitor_monthly_limit=visitor_limit)


def set_reading_quota_cookie(response, value: str) -> None:
    response.set_cookie(
        READING_QUOTA_COOKIE,
        value,
        max_age=60 * 60 * 24 * 400,
        httponly=True,
        samesite="lax",
        secure=os.getenv("MOIRA_SECURE_COOKIES", "").lower() in {"1", "true", "yes"},
    )


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "personal_readings_enabled": bool(os.getenv("ANTHROPIC_API_KEY")),
        "visitor_monthly_limit": int(os.getenv("MOIRA_VISITOR_MONTHLY_LIMIT", "5")),
    })


def assemble_chart_data(chart, *, name: str, gender: str, place: str, jd: float) -> dict:
    """Build the shared model/SVG payload for live and pre-generated readings."""
    planet_dignities = {
        pname: dignities_of(pname, p.sign, p.degree_in_sign, chart.is_day_chart)
        for pname, p in chart.planets.items()
    }

    greek_lots = lots(chart)
    lot_details = {}
    for lot_name, lot_lon in greek_lots.items():
        lot_sign, lot_deg = degree_to_sign(lot_lon)
        lot_house = chart.houses.index(lot_sign) + 1
        lot_details[lot_name] = {
            "sign": lot_sign,
            "degree": round(lot_deg, 2),
            "house": lot_house,
        }

    syzygy = prenatal_syzygy(jd)

    return {
        "name": name or "the native",
        "gender": gender,
        "place": place,
        "ascendant": {
            "sign": chart.ascendant_sign,
            "degree": round(chart.ascendant_degree, 2),
        },
        "mc": {
            "sign": chart.mc_sign,
            "degree": round(chart.mc_degree, 2),
        },
        "sect": "day" if chart.is_day_chart else "night",
        "planets": {
            pname: {
                "sign": p.sign,
                "house": p.house,
                "degree": round(p.degree_in_sign, 2),
                "retrograde": p.retrograde,
                "dignities": planet_dignities[pname],
            }
            for pname, p in chart.planets.items()
        },
        "lots": lot_details,
        "aspects": all_aspects(chart.planets),
        "prenatal_syzygy": syzygy,
        "oikodespotes": calculate_oikodespotes(chart, greek_lots, syzygy),
    }


def augustus_demo_data():
    """Return Augustus's fixed chart and its reading payload without network I/O."""
    birth = AUGUSTUS_BIRTH
    chart = calculate_chart(
        birth["year"], birth["month"], birth["day"], birth["hour"],
        birth["latitude"], birth["longitude"], calendar=swe.JUL_CAL,
    )
    jd = swe.julday(
        birth["year"], birth["month"], birth["day"], birth["hour"], swe.JUL_CAL,
    )
    chart_data = assemble_chart_data(
        chart,
        name="Gaius Octavius (Augustus)",
        gender="male",
        place="Rome",
        jd=jd,
    )
    return chart, chart_data


def personal_chart_data(*, name: str, gender: str, date: str, time: str, place: str):
    """Calculate a visitor's chart. This performs no generative-AI work."""
    location = geocode_place(place)
    if location is None:
        raise HTTPException(status_code=422, detail="That birth place could not be found.")

    lat = location.latitude
    geo_lon = location.longitude
    year, month, day = map(int, date.split("-"))
    hour_local, minute_local = map(int, time.split(":"))

    tz_name = tf.timezone_at(lat=lat, lng=geo_lon)
    if tz_name is None:
        raise HTTPException(status_code=422, detail="The birth place's timezone could not be determined.")

    tz = pytz.timezone(tz_name)
    local_dt = tz.localize(datetime(year, month, day, hour_local, minute_local))
    utc_dt = local_dt.astimezone(pytz.utc)
    ut_hour = utc_dt.hour + utc_dt.minute / 60.0

    chart = calculate_chart(
        utc_dt.year, utc_dt.month, utc_dt.day,
        ut_hour, lat, geo_lon,
    )
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, ut_hour)
    chart_data = assemble_chart_data(
        chart,
        name=name,
        gender=gender,
        place=place,
        jd=jd,
    )
    return chart, chart_data


def chart_response(
    request: Request,
    chart,
    chart_data: dict,
    *,
    birth_input: dict | None = None,
    reading_notice: str | None = None,
    reading_available: bool | None = None,
    status_code: int = 200,
):
    enabled = bool(os.getenv("ANTHROPIC_API_KEY"))
    return templates.TemplateResponse(
        request,
        "chart.html",
        {
            "chart": chart_data,
            "chart_svg": generate_chart_svg(chart, chart_data),
            "birth_input": birth_input,
            "personal_readings_enabled": enabled,
            "reading_available": enabled if reading_available is None else reading_available,
            "reading_notice": reading_notice,
            "visitor_monthly_limit": int(os.getenv("MOIRA_VISITOR_MONTHLY_LIMIT", "5")),
        },
        status_code=status_code,
    )


@app.get("/demo")
async def demo(request: Request):
    chart, chart_data = augustus_demo_data()
    reading_text = DEMO_READING_PATH.read_text(encoding="utf-8")

    return templates.TemplateResponse(request, "reading.html", {
        "reading": reading_to_html(reading_text),
        "chart_svg": generate_chart_svg(chart, chart_data),
        "page_title": "The Nativity of Augustus",
        "subtitle": "The nativity of Augustus",
        "demo": True,
    })


@app.post("/chart")
async def personal_chart(
    request: Request,
    name: str = Form(default=""),
    gender: str = Form(default="unspecified"),
    date: str = Form(...),
    time: str = Form(...),
    place: str = Form(...),
):
    chart, chart_data = personal_chart_data(
        name=name,
        gender=gender,
        date=date,
        time=time,
        place=place,
    )
    return chart_response(
        request,
        chart,
        chart_data,
        birth_input={
            "name": name,
            "gender": gender,
            "date": date,
            "time": time,
            "place": place,
        },
    )


@app.post("/reading")
async def reading(
    request: Request,
    name: str = Form(default=""),
    gender: str = Form(default="unspecified"),
    date: str = Form(...),
    time: str = Form(...),
    place: str = Form(...),
):
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="Personal readings are unavailable in this demo deployment.",
        )

    chart, chart_data = personal_chart_data(
        name=name,
        gender=gender,
        date=date,
        time=time,
        place=place,
    )

    try:
        next_quota_cookie = get_reading_quota().reserve(
            request.cookies.get(READING_QUOTA_COOKIE)
        )
    except VisitorQuotaExceeded:
        return chart_response(
            request,
            chart,
            chart_data,
            reading_notice=(
                "You have used your five sponsored Claude readings for this month. "
                "Your chart is still available, and the allowance resets next month."
            ),
            reading_available=False,
            status_code=429,
        )

    try:
        reading_text = get_reading(chart_data)
    except ReadingUnavailable:
        return chart_response(
            request,
            chart,
            chart_data,
            reading_notice=(
                "Claude readings are resting for now. The sponsored monthly budget may "
                "have been reached, but your calculated chart remains available below."
            ),
            reading_available=False,
            status_code=503,
        )
    chart_svg = generate_chart_svg(chart, chart_data)

    reading_html = reading_to_html(reading_text)

    response = templates.TemplateResponse(request, "reading.html", {
        "reading": reading_html,
        "chart_svg": chart_svg,
        "page_title": "Your Reading",
        "subtitle": "The nativity unfolded",
        "demo": False,
    })
    set_reading_quota_cookie(response, next_quota_cookie)
    return response
