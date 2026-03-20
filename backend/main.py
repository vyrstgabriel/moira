# main.py
# FastAPI application entry point.

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz

from astrology.chart import calculate_chart, degree_to_sign
from astrology.dignities import dignities_of
from astrology.lots import lots
from astrology.aspects import all_aspects
from astrology.chart_svg import generate_chart_svg
from reader import get_reading

app = FastAPI()

app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")
templates = Jinja2Templates(directory="../frontend")

geolocator = Nominatim(user_agent="moira")
tf = TimezoneFinder()


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/reading")
async def reading(
    request: Request,
    name: str = Form(default=""),
    date: str = Form(...),
    time: str = Form(...),
    place: str = Form(...),
):
    # Geocode place name → coordinates
    location = geolocator.geocode(place)
    lat = location.latitude
    geo_lon = location.longitude

    # Convert local birth time to UTC
    year, month, day = map(int, date.split("-"))
    hour_local, minute_local = map(int, time.split(":"))

    tz_name = tf.timezone_at(lat=lat, lng=geo_lon)
    tz = pytz.timezone(tz_name)
    local_dt = tz.localize(datetime(year, month, day, hour_local, minute_local))
    utc_dt = local_dt.astimezone(pytz.utc)

    ut_hour = utc_dt.hour + utc_dt.minute / 60.0

    # Calculate natal chart
    chart = calculate_chart(
        utc_dt.year, utc_dt.month, utc_dt.day,
        ut_hour, lat, geo_lon,
    )

    # Dignities, lots, aspects
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

    planet_aspects = all_aspects(chart.planets)

    # Assemble chart data for the reader
    chart_data = {
        "name": name or "the native",
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
        "aspects": planet_aspects,
    }

    reading_text = get_reading(chart_data)
    chart_svg = generate_chart_svg(chart, chart_data)

    # Convert double-newlines to HTML paragraphs
    reading_html = "".join(
        f"<p>{para.strip()}</p>"
        for para in reading_text.split("\n\n")
        if para.strip()
    )

    return templates.TemplateResponse("reading.html", {
        "request": request,
        "reading": reading_html,
        "chart_svg": chart_svg,
    })
