import os
import datetime as dt

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import requests
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
DEFAULT_CITY = os.getenv("WEATHER_CITY", "Moscow")
DEFAULT_LANG = "ru"

app = FastAPI(title="PyQt → Web UI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/healthz")
def healthz():
    return {"ok": True, "time": dt.datetime.utcnow().isoformat()}


@app.get("/api/weather")
def api_weather(city: str = DEFAULT_CITY):
    """Простой аналог WeatherWidget: отдать погоду."""
    if not OPENWEATHER_API_KEY:
        return {
            "city": city,
            "temp_c": None,
            "description": "NO OPENWEATHER_API_KEY in .env",
            "icon_url": None,
        }

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang={DEFAULT_LANG}"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
    except Exception as e:
        return {
            "city": city,
            "temp_c": None,
            "description": f"Error: {e}",
            "icon_url": None,
        }

    data = r.json()
    temp_c = data.get("main", {}).get("temp")
    desc = (data.get("weather") or [{}])[0].get("description")
    icon = (data.get("weather") or [{}])[0].get("icon")
    icon_url = f"https://openweathermap.org/img/wn/{icon}@2x.png" if icon else None

    return {
        "city": data.get("name", city),
        "temp_c": temp_c,
        "description": desc,
        "icon_url": icon_url,
    }
