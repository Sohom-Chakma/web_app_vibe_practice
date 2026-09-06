#!/usr/bin/env python3
"""
Fetch current weather and 3-day forecast for 12 major cities from wttr.in (format=j1),
parse the JSON data, and generate an interactive HTML dashboard: 'weather_dashboard.html'.
"""

import json
import urllib.request
import urllib.parse
import datetime
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure UTF-8 output encoding for Windows consoles (supports emoji)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# 12 Major global cities
CITIES = [
    {"name": "London", "flag": "🇬🇧", "query": "London"},
    {"name": "Ankara", "flag": "🇹🇷", "query": "Ankara"},
    {"name": "Tokyo", "flag": "🇯🇵", "query": "Tokyo"},
    {"name": "New York", "flag": "🇺🇸", "query": "New+York"},
    {"name": "Paris", "flag": "🇫🇷", "query": "Paris"},
    {"name": "Berlin", "flag": "🇩🇪", "query": "Berlin"},
    {"name": "Sydney", "flag": "🇦🇺", "query": "Sydney"},
    {"name": "Dubai", "flag": "🇦🇪", "query": "Dubai"},
    {"name": "Singapore", "flag": "🇸🇬", "query": "Singapore"},
    {"name": "Toronto", "flag": "🇨🇦", "query": "Toronto"},
    {"name": "Rome", "flag": "🇮🇹", "query": "Rome"},
    {"name": "Cairo", "flag": "🇪🇬", "query": "Cairo"},
]

def fetch_weather(city_query: str) -> dict:
    url = f"https://wttr.in/{city_query}?format=j1"
    headers = {"User-Agent": "curl/7.68.0"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))

def format_time(t_str: str) -> str:
    """Format time string like '0', '300', '1200' to '12:00 AM', '3:00 AM', '12:00 PM'."""
    val = int(t_str)
    hours = val // 100
    minutes = val % 100
    am_pm = "AM" if hours < 12 else "PM"
    display_hour = 12 if hours in (0, 12) else hours % 12
    return f"{display_hour}:{minutes:02d} {am_pm}"

def get_weather_icon(desc: str, code: str) -> str:
    """Return appropriate weather emoji based on description and code."""
    d = desc.lower()
    c = int(code) if str(code).isdigit() else 0
    
    if "thunder" in d or c in [200, 386, 389, 392, 395]:
        return "⛈️"
    if "snow" in d or "blizzard" in d or "sleet" in d or c in [179, 182, 185, 227, 230, 323, 326, 329, 332, 335, 338, 350, 368, 371, 374, 377]:
        return "❄️"
    if "rain" in d or "drizzle" in d or "shower" in d or c in [176, 263, 266, 293, 296, 299, 302, 305, 308, 311, 314, 353, 356, 359]:
        return "🌧️"
    if "fog" in d or "mist" in d or "haze" in d or c in [143, 248, 260]:
        return "🌫️"
    if "partly cloudy" in d or c == 116:
        return "⛅"
    if "cloudy" in d or "overcast" in d or c in [119, 122]:
        return "☁️"
    if "clear" in d or "sunny" in d or c == 113:
        return "☀️"
    return "🌤️"

def parse_city_weather(raw: dict, city_alias: str, country_flag: str) -> dict:
    nearest = raw.get("nearest_area", [{}])[0]
    curr = raw.get("current_condition", [{}])[0]
    
    city_name = nearest.get("areaName", [{}])[0].get("value", city_alias)
    country = nearest.get("country", [{}])[0].get("value", "")
    region = nearest.get("region", [{}])[0].get("value", "")
    
    curr_desc = curr.get("weatherDesc", [{}])[0].get("value", "Clear").strip()
    curr_code = curr.get("weatherCode", "113")
    
    forecast_days = []
    for day_idx, day_data in enumerate(raw.get("weather", [])):
        date_str = day_data.get("date", "")
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        if day_idx == 0:
            day_label = "Today"
        elif day_idx == 1:
            day_label = "Tomorrow"
        else:
            day_label = dt.strftime("%A")
            
        astro = day_data.get("astronomy", [{}])[0]
        
        hourly_list = []
        for h in day_data.get("hourly", []):
            h_desc = h.get("weatherDesc", [{}])[0].get("value", "Clear").strip()
            h_code = h.get("weatherCode", "113")
            hourly_list.append({
                "timeRaw": h.get("time", "0"),
                "timeFormatted": format_time(h.get("time", "0")),
                "tempC": int(h.get("tempC", 0)),
                "tempF": int(h.get("tempF", 32)),
                "feelsLikeC": int(h.get("FeelsLikeC", 0)),
                "feelsLikeF": int(h.get("FeelsLikeF", 32)),
                "desc": h_desc,
                "icon": get_weather_icon(h_desc, h_code),
                "chanceOfRain": int(h.get("chanceofrain", 0)),
                "chanceOfSnow": int(h.get("chanceofsnow", 0)),
                "humidity": int(h.get("humidity", 0)),
                "windSpeedKmph": int(h.get("windspeedKmph", 0)),
                "windSpeedMiles": int(h.get("windspeedMiles", 0)),
                "windDir": h.get("winddir16Point", ""),
                "cloudcover": int(h.get("cloudcover", 0)),
                "uvIndex": int(h.get("uvIndex", 0))
            })
            
        mid_hourly = day_data.get("hourly", [{}])[len(day_data.get("hourly", [])) // 2] if day_data.get("hourly") else {}
        day_desc = mid_hourly.get("weatherDesc", [{}])[0].get("value", "Clear").strip()
        day_code = mid_hourly.get("weatherCode", "113")
        max_rain = max([int(h.get("chanceofrain", 0)) for h in day_data.get("hourly", [])], default=0)
        
        forecast_days.append({
            "dayIndex": day_idx,
            "date": date_str,
            "displayDate": dt.strftime("%b %d, %Y"),
            "dayLabel": day_label,
            "weekday": dt.strftime("%A"),
            "desc": day_desc,
            "icon": get_weather_icon(day_desc, day_code),
            "maxTempC": int(day_data.get("maxtempC", 0)),
            "maxTempF": int(day_data.get("maxtempF", 32)),
            "minTempC": int(day_data.get("mintempC", 0)),
            "minTempF": int(day_data.get("mintempF", 32)),
            "avgTempC": int(day_data.get("avgtempC", 0)),
            "avgTempF": int(day_data.get("avgtempF", 32)),
            "uvIndex": int(day_data.get("uvIndex", 0)),
            "sunHour": float(day_data.get("sunHour", 0.0)),
            "maxRainChance": max_rain,
            "astronomy": {
                "sunrise": astro.get("sunrise", "--"),
                "sunset": astro.get("sunset", "--"),
                "moonrise": astro.get("moonrise", "--"),
                "moonset": astro.get("moonset", "--"),
                "moonPhase": astro.get("moon_phase", "--"),
                "moonIllum": astro.get("moon_illumination", "--")
            },
            "hourly": hourly_list
        })

    city_id = city_alias.lower().replace(" ", "-")
    return {
        "id": city_id,
        "name": city_name,
        "country": country,
        "region": region,
        "flag": country_flag,
        "latitude": nearest.get("latitude", ""),
        "longitude": nearest.get("longitude", ""),
        "current": {
            "tempC": int(curr.get("temp_C", 0)),
            "tempF": int(curr.get("temp_F", 32)),
            "feelsLikeC": int(curr.get("FeelsLikeC", 0)),
            "feelsLikeF": int(curr.get("FeelsLikeF", 32)),
            "desc": curr_desc,
            "icon": get_weather_icon(curr_desc, curr_code),
            "weatherCode": curr_code,
            "humidity": int(curr.get("humidity", 0)),
            "windSpeedKmph": int(curr.get("windspeedKmph", 0)),
            "windSpeedMiles": int(curr.get("windspeedMiles", 0)),
            "windDir": curr.get("winddir16Point", ""),
            "windDirDegree": curr.get("winddirDegree", "0"),
            "pressure": int(curr.get("pressure", 1013)),
            "pressureInches": float(curr.get("pressureInches", 29.92)),
            "visibilityKm": int(curr.get("visibility", 10)),
            "visibilityMiles": int(curr.get("visibilityMiles", 6)),
            "uvIndex": int(curr.get("uvIndex", 0)),
            "cloudcover": int(curr.get("cloudcover", 0)),
            "precipMM": float(curr.get("precipMM", 0.0)),
            "precipInches": float(curr.get("precipInches", 0.0)),
            "obsTime": curr.get("localObsDateTime", "")
        },
        "forecast": forecast_days
    }

def generate_html(weather_data: dict, city_list: list) -> str:
    generated_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    weather_json_str = json.dumps(weather_data, indent=2)
    cities_json_str = json.dumps(city_list, indent=2)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Global Weather Intelligence | 12 World Cities</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-base: #060913;
      --glass-surface: rgba(18, 26, 48, 0.55);
      --glass-surface-hover: rgba(28, 38, 70, 0.72);
      --glass-border: rgba(255, 255, 255, 0.12);
      --glass-border-hover: rgba(255, 255, 255, 0.28);
      --glass-bevel: inset 0 1px 1px 0 rgba(255, 255, 255, 0.2), inset 0 -1px 1px 0 rgba(0, 0, 0, 0.25);
      --glass-shadow: 0 16px 36px -8px rgba(0, 0, 0, 0.55), 0 0 0 1px rgba(255, 255, 255, 0.05);
      --glass-blur: blur(24px) saturate(190%);
      --border-subtle: rgba(255, 255, 255, 0.1);
      --border-glow: rgba(99, 102, 241, 0.35);
      --primary: #6366f1;
      --primary-light: #818cf8;
      --accent-cyan: #06b6d4;
      --accent-amber: #f59e0b;
      --accent-emerald: #10b981;
      --accent-rose: #f43f5e;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-faint: #64748b;
      --radius-xl: 24px;
      --radius-lg: 16px;
      --radius-md: 12px;
      --radius-sm: 8px;
      --transition-smooth: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    /* Light Mode with Google Signature Brand Accents */
    [data-theme="light"] {{
      --bg-base: #f8fafc;
      --glass-surface: rgba(255, 255, 255, 0.74);
      --glass-surface-hover: rgba(255, 255, 255, 0.92);
      --glass-border: rgba(226, 232, 240, 0.9);
      --glass-border-hover: rgba(66, 133, 244, 0.45);
      --glass-bevel: inset 0 1px 1px 0 rgba(255, 255, 255, 0.98), inset 0 -1px 1px 0 rgba(0, 0, 0, 0.04);
      --glass-shadow: 0 14px 32px -8px rgba(15, 23, 42, 0.08), 0 1px 3px 0 rgba(15, 23, 42, 0.04);
      --glass-blur: blur(20px) saturate(180%);
      --border-subtle: rgba(226, 232, 240, 0.9);
      --border-glow: rgba(66, 133, 244, 0.35);

      /* Google Signature Brand Accents (Scoped to Light Mode) */
      --google-blue: #4285F4;
      --google-red: #EA4335;
      --google-yellow: #FBBC05;
      --google-green: #34A853;
      --google-blue-dark: #1a73e8;

      --primary: var(--google-blue);
      --primary-light: var(--google-blue-dark);
      --accent-cyan: var(--google-blue);
      --accent-emerald: var(--google-green);
      --accent-amber: var(--google-yellow);
      --accent-rose: var(--google-red);

      --text-main: #0f172a;
      --text-muted: #475569;
      --text-faint: #94a3b8;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg-base);
      color: var(--text-main);
      min-height: 100vh;
      line-height: 1.5;
      padding: 24px 16px;
      position: relative;
      overflow-x: hidden;
      transition: background 0.3s ease, color 0.3s ease;
    }}

    /* Ambient Background Mesh for Glassmorphic Refraction */
    .ambient-mesh {{
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      overflow: hidden;
      z-index: 0;
      pointer-events: none;
    }}

    .ambient-orb {{
      position: absolute;
      border-radius: 50%;
      filter: blur(85px);
      opacity: 0.45;
      animation: floatOrb 22s ease-in-out infinite alternate;
      transition: background 1.2s ease, opacity 1s ease;
    }}

    .orb-1 {{
      width: 580px;
      height: 580px;
      background: radial-gradient(circle, #4f46e5 0%, rgba(79, 70, 229, 0) 70%);
      top: -120px;
      left: 12%;
    }}

    .orb-2 {{
      width: 620px;
      height: 620px;
      background: radial-gradient(circle, #06b6d4 0%, rgba(6, 182, 212, 0) 70%);
      bottom: -160px;
      right: 8%;
      animation-duration: 26s;
      animation-direction: alternate-reverse;
    }}

    .orb-3 {{
      width: 460px;
      height: 460px;
      background: radial-gradient(circle, #8b5cf6 0%, rgba(139, 92, 246, 0) 70%);
      top: 35%;
      right: 28%;
      animation-duration: 18s;
    }}

    @keyframes floatOrb {{
      0% {{ transform: translate(0, 0) scale(1); }}
      50% {{ transform: translate(55px, 35px) scale(1.1); }}
      100% {{ transform: translate(-45px, 65px) scale(0.94); }}
    }}

    .container {{
      max-width: 1320px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 24px;
      position: relative;
      z-index: 1;
    }}

    /* Top Navigation Header (Frosted Glass Pill) */
    header.dashboard-header {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      padding: 20px 28px;
      background: var(--glass-surface);
      backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      border: 1px solid var(--glass-border);
      border-radius: var(--radius-xl);
      box-shadow: var(--glass-shadow), var(--glass-bevel);
      gap: 16px;
      position: relative;
      z-index: 50;
    }}

    .brand-group {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}

    .brand-icon {{
      width: 48px;
      height: 48px;
      background: linear-gradient(135deg, #6366f1, #06b6d4);
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      box-shadow: var(--shadow-glow);
    }}

    .brand-title {{
      font-size: 20px;
      font-weight: 700;
      letter-spacing: -0.02em;
      background: linear-gradient(to right, #ffffff, #cbd5e1);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}

    .brand-subtitle {{
      font-size: 13px;
      color: var(--text-muted);
    }}

    .controls-group {{
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}

    /* View Modes (Single, All Cities Grid, Head-to-Head) */
    .view-mode-tabs {{
      display: flex;
      background: rgba(15, 23, 42, 0.6);
      padding: 4px;
      border-radius: var(--radius-lg);
      border: 1px solid var(--border-subtle);
      gap: 4px;
    }}

    .mode-tab-btn {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-weight: 600;
      font-size: 13px;
      padding: 7px 14px;
      border-radius: var(--radius-md);
      cursor: pointer;
      transition: var(--transition-smooth);
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .mode-tab-btn:hover {{
      color: var(--text-main);
    }}

    .mode-tab-btn.active {{
      background: linear-gradient(135deg, #4f46e5, #6366f1);
      color: #fff;
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
    }}

    /* Unit Switcher Button */
    .unit-switch {{
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 3px;
      display: inline-flex;
      align-items: center;
      gap: 2px;
    }}

    .unit-toggle-btn {{
      padding: 5px 10px;
      font-size: 12px;
      font-weight: 700;
      border-radius: var(--radius-md);
      border: none;
      background: transparent;
      color: var(--text-muted);
      cursor: pointer;
      transition: var(--transition-smooth);
    }}

    .unit-toggle-btn.active {{
      background: #0ea5e9;
      color: #fff;
      box-shadow: 0 2px 8px rgba(14, 165, 233, 0.4);
    }}

    /* Settings Dropdown & Hamburger Menu */
    .settings-menu-container {{
      position: relative;
      display: inline-flex;
      align-items: center;
    }}

    .hamburger-btn {{
      background: rgba(15, 23, 42, 0.65);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      color: var(--text-muted);
      font-size: 13px;
      font-weight: 600;
      padding: 7px 15px;
      display: inline-flex;
      align-items: center;
      gap: 9px;
      cursor: pointer;
      transition: var(--transition-smooth);
      box-shadow: inset 0 1px 1px 0 rgba(255, 255, 255, 0.1);
      user-select: none;
    }}

    .hamburger-btn:hover {{
      color: var(--text-main);
      background: rgba(255, 255, 255, 0.09);
      border-color: var(--glass-border-hover);
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35), inset 0 1px 1px 0 rgba(255, 255, 255, 0.18);
      transform: translateY(-1px);
    }}

    .hamburger-btn.open {{
      background: linear-gradient(135deg, #4f46e5, #6366f1);
      color: #ffffff;
      border-color: rgba(165, 180, 252, 0.5);
      box-shadow: 0 4px 16px rgba(99, 102, 241, 0.45), inset 0 1px 1px 0 rgba(255, 255, 255, 0.3);
    }}

    .hamburger-icon {{
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 3.5px;
      width: 16px;
      height: 14px;
    }}

    .hamburger-icon span {{
      display: block;
      width: 100%;
      height: 2px;
      background: currentColor;
      border-radius: 2px;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    .hamburger-btn.open .hamburger-icon span:nth-child(1) {{
      transform: translateY(5.5px) rotate(45deg);
    }}

    .hamburger-btn.open .hamburger-icon span:nth-child(2) {{
      opacity: 0;
      transform: scaleX(0);
    }}

    .hamburger-btn.open .hamburger-icon span:nth-child(3) {{
      transform: translateY(-5.5px) rotate(-45deg);
    }}

    .settings-dropdown {{
      position: absolute;
      top: calc(100% + 12px);
      right: 0;
      width: 295px;
      background: rgba(15, 22, 42, 0.96);
      backdrop-filter: blur(28px) saturate(200%);
      -webkit-backdrop-filter: blur(28px) saturate(200%);
      border: 1px solid var(--glass-border);
      border-radius: var(--radius-lg);
      box-shadow: 0 24px 50px -8px rgba(0, 0, 0, 0.75), 0 0 0 1px rgba(255, 255, 255, 0.08), var(--glass-bevel);
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      z-index: 1000;
      opacity: 0;
      pointer-events: none;
      transform: translateY(-8px) scale(0.96);
      transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    .settings-dropdown.open {{
      opacity: 1;
      pointer-events: auto;
      transform: translateY(0) scale(1);
    }}

    .dropdown-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-bottom: 8px;
      margin-bottom: 2px;
      border-bottom: 1px solid var(--border-subtle);
    }}

    .dropdown-header-title {{
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: var(--primary-light);
    }}

    .dropdown-item {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 10px;
      border-radius: var(--radius-md);
      transition: var(--transition-smooth);
      gap: 12px;
      background: rgba(255, 255, 255, 0.02);
    }}

    .dropdown-item:hover {{
      background: rgba(255, 255, 255, 0.05);
    }}

    .dropdown-item-info {{
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}

    .dropdown-item-title {{
      font-size: 13px;
      font-weight: 700;
      color: var(--text-main);
    }}

    .dropdown-item-desc {{
      font-size: 11px;
      color: var(--text-muted);
    }}

    .action-btn-sm {{
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      color: var(--text-main);
      padding: 6px 12px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      transition: var(--transition-smooth);
      display: inline-flex;
      align-items: center;
      gap: 6px;
      white-space: nowrap;
    }}

    .action-btn-sm:hover {{
      background: rgba(255, 255, 255, 0.12);
      border-color: var(--glass-border-hover);
      transform: translateY(-1px);
    }}

    /* City Selector Bar (12 Cities) with Tactile Scroll Snapping */
    .city-nav-bar {{
      background: var(--glass-surface);
      backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      border: 1px solid var(--glass-border);
      border-radius: var(--radius-xl);
      box-shadow: var(--glass-shadow), var(--glass-bevel);
      padding: 12px 18px;
      display: flex;
      align-items: center;
      gap: 10px;
      overflow-x: auto;
      scrollbar-width: none;
      -ms-overflow-style: none;
      scroll-snap-type: x mandatory;
      scroll-behavior: smooth;
      scroll-padding: 0 40px;
      overscroll-behavior-x: contain;
      -webkit-overflow-scrolling: touch;
    }}

    .city-nav-bar::-webkit-scrollbar {{
      display: none;
    }}

    .city-nav-item {{
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 9px 18px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--glass-border);
      border-radius: var(--radius-lg);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      box-shadow: inset 0 1px 1px 0 rgba(255, 255, 255, 0.15);
      color: var(--text-muted);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
      transition: var(--transition-smooth);
      user-select: none;
      scroll-snap-align: center;
      scroll-snap-stop: normal;
      flex-shrink: 0;
    }}

    .city-nav-item:hover {{
      background: rgba(255, 255, 255, 0.12);
      color: var(--text-main);
      border-color: rgba(255, 255, 255, 0.28);
      transform: translateY(-1px);
    }}

    .city-nav-item.active {{
      background: linear-gradient(135deg, rgba(79, 70, 229, 0.95), rgba(99, 102, 241, 0.95));
      color: #fff;
      border-color: rgba(165, 180, 252, 0.5);
      box-shadow: 0 4px 18px rgba(99, 102, 241, 0.45), inset 0 1px 1px 0 rgba(255, 255, 255, 0.3);
    }}

    .city-nav-pill-temp {{
      font-size: 12px;
      opacity: 0.95;
      background: rgba(0, 0, 0, 0.25);
      padding: 2px 8px;
      border-radius: 9999px;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }}

    /* Main City Weather Overview */
    .city-view-container {{
      display: flex;
      flex-direction: column;
      gap: 24px;
    }}

    .hero-weather-card {{
      background: linear-gradient(135deg, rgba(28, 25, 68, 0.65) 0%, rgba(13, 20, 38, 0.72) 100%);
      backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      border: 1px solid var(--glass-border);
      border-radius: var(--radius-xl);
      padding: 32px;
      display: grid;
      grid-template-columns: 1.5fr 1fr;
      gap: 32px;
      position: relative;
      overflow: hidden;
      box-shadow: var(--glass-shadow), var(--glass-bevel);
    }}

    .city-meta {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    .city-badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(99, 102, 241, 0.15);
      border: 1px solid rgba(99, 102, 241, 0.3);
      padding: 6px 14px;
      border-radius: 9999px;
      width: fit-content;
      font-size: 13px;
      font-weight: 600;
      color: var(--primary-light);
    }}

    .city-title-row {{
      display: flex;
      align-items: baseline;
      gap: 14px;
      margin-top: 4px;
    }}

    .city-name {{
      font-size: 42px;
      font-weight: 800;
      letter-spacing: -0.03em;
    }}

    .city-country {{
      font-size: 18px;
      color: var(--text-muted);
      font-weight: 500;
    }}

    .current-temp-block {{
      display: flex;
      align-items: center;
      gap: 20px;
      margin: 16px 0 8px;
    }}

    .temp-large {{
      font-size: 76px;
      font-weight: 800;
      line-height: 1;
      letter-spacing: -0.04em;
    }}

    .weather-condition-badge {{
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}

    .weather-icon-giant {{
      font-size: 48px;
      line-height: 1;
    }}

    .weather-desc {{
      font-size: 20px;
      font-weight: 600;
      color: var(--text-main);
    }}

    .temp-feel-range {{
      display: flex;
      align-items: center;
      gap: 16px;
      font-size: 15px;
      color: var(--text-muted);
    }}

    .temp-feel-range strong {{
      color: var(--text-main);
    }}

    /* Hero Right Column: Astronomy & Highlights */
    .hero-highlights {{
      display: flex;
      flex-direction: column;
      justify-content: space-around;
      background: rgba(15, 23, 42, 0.5);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 20px;
      gap: 16px;
    }}

    .astro-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border-subtle);
    }}

    .astro-item {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .astro-item-icon {{
      font-size: 24px;
    }}

    .astro-label {{
      font-size: 12px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    .astro-value {{
      font-size: 16px;
      font-weight: 700;
      color: var(--text-main);
    }}

    .geo-pill {{
      font-size: 12px;
      color: var(--text-faint);
      display: flex;
      justify-content: space-between;
      margin-top: 4px;
    }}

    /* Metrics Grid */
    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
    }}

    .metric-card {{
      background: var(--glass-surface);
      backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      border: 1px solid var(--glass-border);
      border-radius: var(--radius-lg);
      padding: 18px 20px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      transition: var(--transition-smooth);
      box-shadow: var(--glass-shadow), var(--glass-bevel);
    }}

    .metric-card:hover {{
      transform: translateY(-3px);
      background: var(--glass-surface-hover);
      border-color: var(--glass-border-hover);
      box-shadow: 0 20px 40px -8px rgba(0, 0, 0, 0.6), var(--glass-bevel), 0 0 22px rgba(99, 102, 241, 0.22);
    }}

    .metric-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      color: var(--text-muted);
      font-size: 13px;
      font-weight: 500;
    }}

    .metric-icon {{
      font-size: 18px;
    }}

    .metric-value {{
      font-size: 26px;
      font-weight: 700;
      color: var(--text-main);
    }}

    .metric-subtext {{
      font-size: 12px;
      color: var(--text-muted);
    }}

    .badge-pill {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 9999px;
      font-size: 11px;
      font-weight: 700;
    }}

    .badge-emerald {{ background: rgba(16, 185, 129, 0.2); color: #34d399; }}
    .badge-amber {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; }}
    .badge-rose {{ background: rgba(244, 63, 94, 0.2); color: #fb7185; }}
    .badge-cyan {{ background: rgba(6, 182, 212, 0.2); color: #38bdf8; }}

    /* Forecast Section */
    .section-title {{
      font-size: 20px;
      font-weight: 700;
      letter-spacing: -0.01em;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .forecast-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
    }}

    .forecast-card {{
      background: var(--glass-surface);
      backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      border: 1px solid var(--glass-border);
      border-radius: var(--radius-lg);
      padding: 22px;
      cursor: pointer;
      transition: var(--transition-smooth);
      position: relative;
      overflow: hidden;
      box-shadow: var(--glass-shadow), var(--glass-bevel);
    }}

    .forecast-card:hover {{
      background: var(--glass-surface-hover);
      border-color: var(--glass-border-hover);
      transform: translateY(-3px);
      box-shadow: 0 20px 40px -8px rgba(0, 0, 0, 0.6), var(--glass-bevel), 0 0 22px rgba(99, 102, 241, 0.25);
    }}

    .forecast-card.selected {{
      border: 2px solid var(--primary-light);
      background: rgba(30, 41, 69, 0.85);
      box-shadow: 0 0 25px rgba(99, 102, 241, 0.35), var(--glass-bevel);
    }}

    .forecast-card.selected::after {{
      content: 'Selected Day';
      position: absolute;
      top: 10px;
      right: 12px;
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      background: var(--primary);
      color: #fff;
      padding: 2px 8px;
      border-radius: 9999px;
    }}

    .forecast-day-name {{
      font-size: 18px;
      font-weight: 700;
    }}

    .forecast-date {{
      font-size: 13px;
      color: var(--text-muted);
      margin-bottom: 12px;
    }}

    .forecast-center {{
      display: flex;
      align-items: center;
      gap: 14px;
      margin: 12px 0;
    }}

    .forecast-icon {{
      font-size: 38px;
      line-height: 1;
    }}

    .forecast-temp-range {{
      display: flex;
      flex-direction: column;
    }}

    .forecast-max {{
      font-size: 24px;
      font-weight: 800;
      color: var(--text-main);
    }}

    .forecast-min {{
      font-size: 15px;
      font-weight: 600;
      color: var(--text-muted);
    }}

    .forecast-desc {{
      font-size: 14px;
      font-weight: 500;
      color: var(--text-muted);
      margin-bottom: 10px;
    }}

    .forecast-stats-pill {{
      display: flex;
      justify-content: space-between;
      background: rgba(15, 23, 42, 0.5);
      padding: 8px 12px;
      border-radius: var(--radius-sm);
      font-size: 12px;
      color: var(--text-muted);
    }}

    /* Hourly Breakdown Section */
    .hourly-container {{
      background: var(--glass-surface);
      backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      border: 1px solid var(--glass-border);
      border-radius: var(--radius-xl);
      padding: 24px;
      box-shadow: var(--glass-shadow), var(--glass-bevel);
      margin-top: 8px;
    }}

    .hourly-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }}

    .hourly-scroll {{
      display: grid;
      grid-template-columns: repeat(8, 1fr);
      gap: 12px;
      overflow-x: auto;
      padding-bottom: 8px;
    }}

    .hourly-card {{
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--glass-border);
      border-radius: var(--radius-md);
      padding: 16px 12px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      text-align: center;
      min-width: 105px;
      transition: var(--transition-smooth);
      box-shadow: inset 0 1px 1px 0 rgba(255, 255, 255, 0.1);
    }}

    .hourly-card:hover {{
      background: rgba(255, 255, 255, 0.1);
      border-color: var(--glass-border-hover);
      transform: translateY(-2px);
    }}

    .hourly-time {{
      font-size: 13px;
      font-weight: 600;
      color: var(--text-muted);
    }}

    .hourly-icon {{
      font-size: 28px;
      margin: 4px 0;
    }}

    .hourly-temp {{
      font-size: 19px;
      font-weight: 800;
      color: var(--text-main);
    }}

    .hourly-rain {{
      font-size: 12px;
      color: #38bdf8;
      display: flex;
      align-items: center;
      gap: 2px;
      font-weight: 600;
    }}

    .hourly-wind {{
      font-size: 11px;
      color: var(--text-faint);
    }}

    /* All Cities Overview Grid View */
    .all-cities-view {{
      display: none;
      flex-direction: column;
      gap: 20px;
    }}

    .cities-overview-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 18px;
    }}

    .city-card-item {{
      background: var(--glass-surface);
      backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      border: 1px solid var(--glass-border);
      border-radius: var(--radius-lg);
      padding: 20px;
      cursor: pointer;
      transition: var(--transition-smooth);
      display: flex;
      flex-direction: column;
      gap: 12px;
      box-shadow: var(--glass-shadow), var(--glass-bevel);
    }}

    .city-card-item:hover {{
      transform: translateY(-3px);
      border-color: var(--glass-border-hover);
      background: var(--glass-surface-hover);
      box-shadow: 0 20px 40px -8px rgba(0, 0, 0, 0.6), var(--glass-bevel), 0 0 25px rgba(99, 102, 241, 0.3);
    }}

    .city-card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .city-card-name {{
      font-size: 18px;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .city-card-temp {{
      font-size: 32px;
      font-weight: 800;
    }}

    .city-card-footer {{
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      color: var(--text-muted);
      border-top: 1px solid var(--border-subtle);
      padding-top: 10px;
    }}

    /* Comparison View (Head to Head) */
    .comparison-view {{
      display: none;
      flex-direction: column;
      gap: 24px;
    }}

    .compare-selectors {{
      display: flex;
      gap: 16px;
      align-items: center;
      background: var(--glass-surface);
      backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      padding: 16px 24px;
      border-radius: var(--radius-lg);
      border: 1px solid var(--glass-border);
      box-shadow: var(--glass-shadow), var(--glass-bevel);
      flex-wrap: wrap;
    }}

    .compare-select-group {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex: 1;
      min-width: 240px;
    }}

    .city-select {{
      flex: 1;
      padding: 10px 14px;
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid var(--glass-border);
      border-radius: var(--radius-md);
      color: var(--text-main);
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      outline: none;
      transition: var(--transition-smooth);
    }}

    .city-select:focus {{
      border-color: var(--primary-light);
      box-shadow: 0 0 12px rgba(99, 102, 241, 0.35);
    }}

    .comparison-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
    }}

    .compare-card {{
      background: var(--glass-surface);
      backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      border: 1px solid var(--glass-border);
      border-radius: var(--radius-xl);
      padding: 28px;
      display: flex;
      flex-direction: column;
      gap: 20px;
      box-shadow: var(--glass-shadow), var(--glass-bevel);
    }}

    .compare-title {{
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 24px;
      font-weight: 800;
    }}

    .compare-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 8px;
    }}

    .compare-table tr {{
      border-bottom: 1px solid var(--border-subtle);
    }}

    .compare-table tr:last-child {{
      border-bottom: none;
    }}

    .compare-table td {{
      padding: 12px 6px;
      font-size: 14px;
    }}

    .compare-table td:first-child {{
      color: var(--text-muted);
      font-weight: 500;
    }}

    .compare-table td:last-child {{
      text-align: right;
      font-weight: 700;
      color: var(--text-main);
    }}

    /* Footer */
    footer.dashboard-footer {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      padding: 16px 20px;
      font-size: 13px;
      color: var(--text-faint);
      border-top: 1px solid var(--border-subtle);
      margin-top: 24px;
      gap: 12px;
    }}

    /* Responsive */
    @media (max-width: 960px) {{
      .hero-weather-card {{
        grid-template-columns: 1fr;
      }}
      .forecast-grid {{
        grid-template-columns: 1fr;
      }}
      .comparison-grid {{
        grid-template-columns: 1fr;
      }}
      .hourly-scroll {{
        grid-template-columns: repeat(8, 120px);
      }}
    }}

    /* =========================================================
       LIGHT MODE: Frosted Glassmorphism with Google Signature Accents
       ========================================================= */
    .google-stripe {{
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 4px;
      background: linear-gradient(90deg, #4285F4 25%, #EA4335 25% 50%, #FBBC05 50% 75%, #34A853 75% 100%);
      z-index: 99999;
      box-shadow: 0 1px 8px rgba(66, 133, 244, 0.35);
    }}

    [data-theme="light"] .google-stripe {{
      display: block;
    }}

    [data-theme="light"] .ambient-orb {{
      opacity: 0.22;
      filter: blur(105px);
    }}

    [data-theme="light"] .orb-1 {{
      background: radial-gradient(circle, #4285F4 0%, rgba(66, 133, 244, 0) 70%);
    }}

    [data-theme="light"] .orb-2 {{
      background: radial-gradient(circle, #34A853 0%, rgba(52, 168, 83, 0) 70%);
    }}

    [data-theme="light"] .orb-3 {{
      background: radial-gradient(circle, #FBBC05 0%, rgba(251, 188, 5, 0) 70%);
    }}

    [data-theme="light"] .brand-icon {{
      background: linear-gradient(135deg, #4285F4 0%, #34A853 100%);
      box-shadow: 0 4px 16px rgba(66, 133, 244, 0.3);
    }}

    [data-theme="light"] .brand-title {{
      background: linear-gradient(to right, #0f172a, #334155);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}

    [data-theme="light"] .view-mode-tabs {{
      background: rgba(241, 245, 249, 0.75);
      border-color: rgba(226, 232, 240, 0.95);
    }}

    [data-theme="light"] .mode-tab-btn.active {{
      background: linear-gradient(135deg, #4285F4, #1a73e8);
      color: #ffffff;
      box-shadow: 0 4px 14px rgba(66, 133, 244, 0.35);
    }}

    [data-theme="light"] .unit-switch {{
      background: rgba(241, 245, 249, 0.75);
      border-color: rgba(226, 232, 240, 0.95);
    }}

    [data-theme="light"] .unit-toggle-btn.active {{
      background: #4285F4;
      color: #ffffff;
      box-shadow: 0 2px 8px rgba(66, 133, 244, 0.4);
    }}

    [data-theme="light"] .action-btn {{
      background: rgba(255, 255, 255, 0.85);
      border-color: rgba(226, 232, 240, 0.95);
      color: var(--text-main);
    }}

    [data-theme="light"] .action-btn:hover {{
      background: rgba(255, 255, 255, 1);
      border-color: rgba(66, 133, 244, 0.5);
      box-shadow: 0 4px 14px rgba(66, 133, 244, 0.2);
    }}

    [data-theme="light"] .hamburger-btn {{
      background: rgba(241, 245, 249, 0.75);
      border: 1px solid rgba(226, 232, 240, 0.95);
      color: var(--text-muted);
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
    }}

    [data-theme="light"] .hamburger-btn:hover {{
      color: var(--text-main);
      background: rgba(255, 255, 255, 0.95);
      border-color: rgba(66, 133, 244, 0.45);
      box-shadow: 0 4px 14px rgba(66, 133, 244, 0.18);
    }}

    [data-theme="light"] .hamburger-btn.open {{
      background: linear-gradient(135deg, #4285F4, #1a73e8);
      color: #ffffff;
      border-color: rgba(66, 133, 244, 0.6);
      box-shadow: 0 4px 16px rgba(66, 133, 244, 0.35);
    }}

    [data-theme="light"] .settings-dropdown {{
      background: rgba(255, 255, 255, 0.96);
      border-color: rgba(226, 232, 240, 0.95);
      box-shadow: 0 20px 45px -8px rgba(15, 23, 42, 0.15), var(--glass-bevel);
    }}

    [data-theme="light"] .dropdown-header {{
      border-color: rgba(226, 232, 240, 0.95);
    }}

    [data-theme="light"] .dropdown-header-title {{
      color: #4285F4;
    }}

    [data-theme="light"] .dropdown-item {{
      background: rgba(241, 245, 249, 0.5);
    }}

    [data-theme="light"] .dropdown-item:hover {{
      background: rgba(241, 245, 249, 0.95);
    }}

    [data-theme="light"] .dropdown-item-title {{
      color: #0f172a;
    }}

    [data-theme="light"] .action-btn-sm {{
      background: rgba(255, 255, 255, 0.9);
      border-color: rgba(226, 232, 240, 0.95);
      color: #0f172a;
    }}

    [data-theme="light"] .action-btn-sm:hover {{
      background: #ffffff;
      border-color: rgba(66, 133, 244, 0.5);
      box-shadow: 0 2px 8px rgba(66, 133, 244, 0.2);
    }}

    [data-theme="light"] .city-nav-item {{
      background: rgba(255, 255, 255, 0.55);
      border-color: rgba(226, 232, 240, 0.9);
      color: var(--text-muted);
    }}

    [data-theme="light"] .city-nav-item:hover {{
      background: rgba(255, 255, 255, 0.9);
      border-color: rgba(66, 133, 244, 0.4);
      color: var(--text-main);
    }}

    [data-theme="light"] .city-nav-item.active {{
      background: linear-gradient(135deg, #4285F4, #1a73e8);
      color: #ffffff;
      border-color: rgba(66, 133, 244, 0.6);
      box-shadow: 0 4px 18px rgba(66, 133, 244, 0.35), inset 0 1px 1px 0 rgba(255, 255, 255, 0.4);
    }}

    [data-theme="light"] .city-nav-pill-temp {{
      background: rgba(0, 0, 0, 0.08);
      border-color: rgba(0, 0, 0, 0.06);
    }}

    [data-theme="light"] .hero-weather-card {{
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.88) 0%, rgba(241, 245, 249, 0.82) 100%);
      border-color: rgba(226, 232, 240, 0.95);
      box-shadow: 0 16px 36px -8px rgba(15, 23, 42, 0.08), inset 0 1px 1px 0 rgba(255, 255, 255, 0.95);
    }}

    [data-theme="light"] .hero-badge {{
      background: rgba(66, 133, 244, 0.12);
      border-color: rgba(66, 133, 244, 0.3);
      color: #1a73e8;
    }}

    [data-theme="light"] .hero-highlights {{
      background: rgba(248, 250, 252, 0.85);
      border-color: rgba(226, 232, 240, 0.95);
    }}

    [data-theme="light"] .metric-card:hover {{
      border-color: rgba(66, 133, 244, 0.45);
      box-shadow: 0 16px 36px -8px rgba(66, 133, 244, 0.15), var(--glass-bevel);
    }}

    /* Google Colored Metric Badges in Light Mode */
    [data-theme="light"] .badge-emerald {{
      background: rgba(52, 168, 83, 0.15);
      color: #188038;
      border: 1px solid rgba(52, 168, 83, 0.35);
    }}

    [data-theme="light"] .badge-amber {{
      background: rgba(251, 188, 5, 0.18);
      color: #b45309;
      border: 1px solid rgba(251, 188, 5, 0.38);
    }}

    [data-theme="light"] .badge-rose {{
      background: rgba(234, 67, 53, 0.15);
      color: #c5221f;
      border: 1px solid rgba(234, 67, 53, 0.35);
    }}

    [data-theme="light"] .badge-cyan {{
      background: rgba(66, 133, 244, 0.15);
      color: #1967d2;
      border: 1px solid rgba(66, 133, 244, 0.35);
    }}

    [data-theme="light"] .forecast-card:hover {{
      border-color: rgba(66, 133, 244, 0.45);
      box-shadow: 0 16px 36px -8px rgba(66, 133, 244, 0.15), var(--glass-bevel);
    }}

    [data-theme="light"] .forecast-card.selected {{
      border: 2px solid #4285F4;
      background: rgba(235, 244, 255, 0.88);
      box-shadow: 0 0 25px rgba(66, 133, 244, 0.25), var(--glass-bevel);
    }}

    [data-theme="light"] .forecast-card.selected::after {{
      background: #4285F4;
    }}

    [data-theme="light"] .forecast-max {{
      color: #EA4335;
    }}

    [data-theme="light"] .forecast-min {{
      color: #1a73e8;
    }}

    [data-theme="light"] .forecast-stats-pill {{
      background: rgba(241, 245, 249, 0.85);
      border: 1px solid rgba(226, 232, 240, 0.95);
      color: var(--text-muted);
    }}

    [data-theme="light"] .hourly-card {{
      background: rgba(255, 255, 255, 0.68);
      border-color: rgba(226, 232, 240, 0.9);
      box-shadow: inset 0 1px 1px 0 rgba(255, 255, 255, 0.9);
    }}

    [data-theme="light"] .hourly-card:hover {{
      background: rgba(255, 255, 255, 0.96);
      border-color: rgba(66, 133, 244, 0.45);
    }}

    [data-theme="light"] .hourly-rain {{
      color: #1a73e8;
    }}

    [data-theme="light"] .city-card-item:hover {{
      border-color: rgba(66, 133, 244, 0.45);
      box-shadow: 0 16px 36px -8px rgba(66, 133, 244, 0.15), var(--glass-bevel);
    }}

    [data-theme="light"] .city-select {{
      background: rgba(255, 255, 255, 0.92);
      color: var(--text-main);
      border-color: rgba(226, 232, 240, 0.95);
    }}

    [data-theme="light"] .city-select:focus {{
      border-color: #4285F4;
      box-shadow: 0 0 12px rgba(66, 133, 244, 0.35);
    }}

    /* Real-Time HTML5 Weather Canvas Layer */
    .weather-canvas {{
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      z-index: 0;
      pointer-events: none;
      transition: opacity 0.5s ease;
    }}

    @keyframes spin {{
      from {{ transform: rotate(0deg); }}
      to {{ transform: rotate(360deg); }}
    }}
  </style>
</head>
<body>
  <!-- Google 4-Color Signature Accent Stripe (Active in Light Mode) -->
  <div class="google-stripe" aria-hidden="true"></div>

  <!-- Ambient Glassmorphic Background Mesh -->
  <div class="ambient-mesh" id="ambient-mesh" aria-hidden="true">
    <div class="ambient-orb orb-1"></div>
    <div class="ambient-orb orb-2"></div>
    <div class="ambient-orb orb-3"></div>
  </div>

  <!-- Real-Time HTML5 Canvas Physics Engine -->
  <canvas id="weather-canvas" class="weather-canvas" aria-hidden="true"></canvas>

  <div class="container">
    <!-- Header -->
    <header class="dashboard-header">
      <div class="brand-group">
        <div class="brand-icon">🌐</div>
        <div>
          <h1 class="brand-title">Global Weather Intelligence</h1>
          <p class="brand-subtitle">Real-time Weather & 3-Day Forecast for 12 Major Cities via wttr.in</p>
        </div>
      </div>

      <div class="controls-group">
        <!-- View Mode Tabs -->
        <div class="view-mode-tabs">
          <button class="mode-tab-btn active" onclick="setViewMode('single')" id="btn-mode-single">
            <span>📍</span> City Detail
          </button>
          <button class="mode-tab-btn" onclick="setViewMode('all')" id="btn-mode-all">
            <span>🗺️</span> 12-City Overview
          </button>
          <button class="mode-tab-btn" onclick="setViewMode('compare')" id="btn-mode-compare">
            <span>⚖️</span> Compare
          </button>
        </div>

        <!-- Settings Hamburger Dropdown Container -->
        <div class="settings-menu-container" id="settings-menu-container">
          <button class="action-btn hamburger-btn" id="hamburger-btn" onclick="toggleSettingsMenu(event)" aria-label="Settings Menu" aria-expanded="false" title="Settings & Controls">
            <span class="hamburger-icon" aria-hidden="true">
              <span></span>
              <span></span>
              <span></span>
            </span>
            <span class="hamburger-label">Settings</span>
          </button>

          <!-- Dropdown Menu Card -->
          <div class="settings-dropdown" id="settings-dropdown" onclick="event.stopPropagation()">
            <div class="dropdown-header">
              <span class="dropdown-header-title">⚙️ Preferences</span>
            </div>

            <!-- Option 1: Theme Switcher -->
            <div class="dropdown-item">
              <div class="dropdown-item-info">
                <span class="dropdown-item-title">Appearance</span>
                <span class="dropdown-item-desc">Light or dark theme</span>
              </div>
              <div class="dropdown-item-control">
                <button class="action-btn-sm" id="btn-theme-toggle" onclick="toggleTheme()" title="Switch Light / Dark Theme">
                  <span id="theme-icon">☀️</span> <span id="theme-label">Light</span>
                </button>
              </div>
            </div>

            <!-- Option 2: Measurement Units -->
            <div class="dropdown-item">
              <div class="dropdown-item-info">
                <span class="dropdown-item-title">Units</span>
                <span class="dropdown-item-desc">Temp & wind velocity</span>
              </div>
              <div class="dropdown-item-control">
                <div class="unit-switch" title="Toggle Units">
                  <button class="unit-toggle-btn active" id="btn-celsius" onclick="setUnit('C')">°C</button>
                  <button class="unit-toggle-btn" id="btn-fahrenheit" onclick="setUnit('F')">°F</button>
                </div>
              </div>
            </div>

            <!-- Option 3: Atmospheric Weather FX -->
            <div class="dropdown-item">
              <div class="dropdown-item-info">
                <span class="dropdown-item-title">Weather FX</span>
                <span class="dropdown-item-desc">Canvas particle physics</span>
              </div>
              <div class="dropdown-item-control">
                <button class="action-btn-sm" id="btn-toggle-fx" onclick="toggleWeatherFX()" title="Toggle Weather Particle Canvas Animation">
                  <span>✨</span> <span id="fx-label">FX: On</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- 12 Cities Quick Navigation Bar -->
    <nav class="city-nav-bar" id="city-nav-bar">
      <!-- Populated by JS -->
    </nav>

    <!-- VIEW 1: Single City Detailed View -->
    <main id="city-view" class="city-view-container">
      <!-- Hero Weather Card -->
      <section class="hero-weather-card" id="hero-card">
        <div class="city-meta">
          <div class="city-badge" id="hero-badge">
            <span id="hero-flag">🇬🇧</span> <span id="hero-region">United Kingdom</span>
          </div>
          <div class="city-title-row">
            <h2 class="city-name" id="hero-city-name">London</h2>
            <span class="city-country" id="hero-country">UK</span>
          </div>
          <div class="current-temp-block">
            <div class="temp-large" id="hero-temp">--°</div>
            <div class="weather-condition-badge">
              <span class="weather-icon-giant" id="hero-icon">☀️</span>
              <span class="weather-desc" id="hero-desc">Sunny</span>
            </div>
          </div>
          <div class="temp-feel-range">
            <span>Feels like <strong id="hero-feels-like">--°</strong></span>
            <span>•</span>
            <span>Today's Range: <strong id="hero-temp-range">--° / --°</strong></span>
          </div>
        </div>

        <!-- Right Side: Astronomy & Highlights -->
        <div class="hero-highlights">
          <div class="astro-row">
            <div class="astro-item">
              <span class="astro-item-icon">🌅</span>
              <div>
                <div class="astro-label">Sunrise</div>
                <div class="astro-value" id="hero-sunrise">--:--</div>
              </div>
            </div>
            <div class="astro-item">
              <span class="astro-item-icon">🌇</span>
              <div>
                <div class="astro-label">Sunset</div>
                <div class="astro-value" id="hero-sunset">--:--</div>
              </div>
            </div>
          </div>

          <div class="astro-row">
            <div class="astro-item">
              <span class="astro-item-icon">🌖</span>
              <div>
                <div class="astro-label">Moon Phase</div>
                <div class="astro-value" id="hero-moon-phase">--</div>
              </div>
            </div>
            <div class="astro-item">
              <span class="astro-item-icon">☀️</span>
              <div>
                <div class="astro-label">Sun Hours</div>
                <div class="astro-value" id="hero-sun-hours">-- hrs</div>
              </div>
            </div>
          </div>

          <div class="geo-pill">
            <span>Observed at <strong id="hero-obs-time" style="color:var(--text-main);">--</strong></span>
            <span id="hero-coords">Lat --°, Lon --°</span>
          </div>
        </div>
      </section>

      <!-- Detailed Metrics Grid -->
      <section>
        <h3 class="section-title"><span>📊</span> Atmospheric Conditions</h3>
        <div class="metrics-grid">
          <div class="metric-card">
            <div class="metric-header">
              <span>Humidity</span>
              <span class="metric-icon">💧</span>
            </div>
            <div class="metric-value" id="metric-humidity">--%</div>
            <div class="metric-subtext" id="metric-humidity-sub">Normal comfort</div>
          </div>

          <div class="metric-card">
            <div class="metric-header">
              <span>Wind Speed & Dir</span>
              <span class="metric-icon">💨</span>
            </div>
            <div class="metric-value" id="metric-wind">--</div>
            <div class="metric-subtext" id="metric-wind-dir">Direction: --</div>
          </div>

          <div class="metric-card">
            <div class="metric-header">
              <span>UV Index</span>
              <span class="metric-icon">☀️</span>
            </div>
            <div class="metric-value" id="metric-uv">--</div>
            <div class="metric-subtext"><span class="badge-pill" id="metric-uv-badge">Moderate</span></div>
          </div>

          <div class="metric-card">
            <div class="metric-header">
              <span>Precipitation</span>
              <span class="metric-icon">🌧️</span>
            </div>
            <div class="metric-value" id="metric-precip">--</div>
            <div class="metric-subtext" id="metric-precip-sub">Accumulation</div>
          </div>

          <div class="metric-card">
            <div class="metric-header">
              <span>Cloud Cover</span>
              <span class="metric-icon">☁️</span>
            </div>
            <div class="metric-value" id="metric-cloud">--%</div>
            <div class="metric-subtext" id="metric-cloud-sub">Sky coverage</div>
          </div>

          <div class="metric-card">
            <div class="metric-header">
              <span>Pressure</span>
              <span class="metric-icon">🧭</span>
            </div>
            <div class="metric-value" id="metric-pressure">--</div>
            <div class="metric-subtext">Barometer</div>
          </div>

          <div class="metric-card">
            <div class="metric-header">
              <span>Visibility</span>
              <span class="metric-icon">👁️</span>
            </div>
            <div class="metric-value" id="metric-visibility">--</div>
            <div class="metric-subtext" id="metric-vis-sub">Sight range</div>
          </div>
        </div>
      </section>

      <!-- 3-Day Forecast Cards -->
      <section>
        <h3 class="section-title"><span>📅</span> 3-Day Weather Forecast <span style="font-size: 13px; font-weight: 500; color: var(--text-muted); margin-left: 8px;">(Click any day to view 24h hourly breakdown)</span></h3>
        <div class="forecast-grid" id="forecast-cards-container">
          <!-- Populated by JavaScript -->
        </div>
      </section>

      <!-- Hourly Forecast for Selected Day -->
      <section class="hourly-container">
        <div class="hourly-header">
          <h3 class="section-title" style="margin-bottom: 0;">
            <span>⏱️</span> 24-Hour Forecast Breakdown — <span id="hourly-day-label" style="color: var(--primary-light);">Today</span>
          </h3>
          <span style="font-size: 13px; color: var(--text-muted);" id="hourly-date-label"></span>
        </div>
        <div class="hourly-scroll" id="hourly-list">
          <!-- Populated by JavaScript -->
        </div>
      </section>
    </main>

    <!-- VIEW 2: 12-City Overview Grid -->
    <main id="all-cities-view" class="all-cities-view">
      <h2 class="section-title"><span>🗺️</span> 12 World Cities At-a-Glance</h2>
      <div class="cities-overview-grid" id="cities-overview-grid">
        <!-- Populated via JS -->
      </div>
    </main>

    <!-- VIEW 3: Head-to-Head Comparison View -->
    <main id="compare-view" class="comparison-view">
      <h2 class="section-title"><span>⚖️</span> Head-to-Head Weather Comparison</h2>
      <div class="compare-selectors">
        <div class="compare-select-group">
          <label style="font-size: 13px; color: var(--text-muted); font-weight: 600;">City 1:</label>
          <select id="select-city-1" class="city-select" onchange="updateComparison()">
            <!-- Populated via JS -->
          </select>
        </div>
        <div style="font-size: 20px; font-weight: 700; color: var(--text-muted);">VS</div>
        <div class="compare-select-group">
          <label style="font-size: 13px; color: var(--text-muted); font-weight: 600;">City 2:</label>
          <select id="select-city-2" class="city-select" onchange="updateComparison()">
            <!-- Populated via JS -->
          </select>
        </div>
      </div>

      <div class="comparison-grid">
        <div class="compare-card">
          <div class="compare-title" id="compare-title-1">
            <span>🇬🇧</span> London
          </div>
          <table class="compare-table" id="compare-table-1">
            <!-- Populated via JS -->
          </table>
        </div>

        <div class="compare-card">
          <div class="compare-title" id="compare-title-2">
            <span>🇹🇷</span> Ankara
          </div>
          <table class="compare-table" id="compare-table-2">
            <!-- Populated via JS -->
          </table>
        </div>
      </div>
    </main>

    <!-- Footer -->
    <footer class="dashboard-footer">
      <div>
        Data source: <strong>wttr.in/&lt;location&gt;?format=j1</strong> • 12 Global Cities Tracked
      </div>
      <div>
        Last Updated: <span id="footer-timestamp">{generated_timestamp}</span>
      </div>
    </footer>
  </div>

  <!-- Embedded Live Weather Data -->
  <script>
    const weatherData = {weather_json_str};
    const cityList = {cities_json_str};

    let currentCityId = 'london';
    let currentUnit = 'C'; // 'C' or 'F'
    let selectedDayIndex = 0;
    let currentViewMode = 'single'; // 'single', 'all', 'compare'

    function setUnit(unit) {{
      currentUnit = unit;
      document.getElementById('btn-celsius').classList.toggle('active', unit === 'C');
      document.getElementById('btn-fahrenheit').classList.toggle('active', unit === 'F');
      updateNavTemperatures();
      if (currentViewMode === 'single') renderDashboard();
      if (currentViewMode === 'all') renderAllCitiesGrid();
      if (currentViewMode === 'compare') updateComparison();
    }}

    function setViewMode(mode) {{
      currentViewMode = mode;
      document.getElementById('btn-mode-single').classList.toggle('active', mode === 'single');
      document.getElementById('btn-mode-all').classList.toggle('active', mode === 'all');
      document.getElementById('btn-mode-compare').classList.toggle('active', mode === 'compare');

      document.getElementById('city-view').style.display = mode === 'single' ? 'flex' : 'none';
      document.getElementById('all-cities-view').style.display = mode === 'all' ? 'flex' : 'none';
      document.getElementById('compare-view').style.display = mode === 'compare' ? 'flex' : 'none';

      updateNavActiveState(currentCityId, false);

      if (mode === 'single') renderDashboard();
      if (mode === 'all') renderAllCitiesGrid();
      if (mode === 'compare') updateComparison();
    }}

    function selectCity(cityId, shouldScroll = true) {{
      currentCityId = cityId;
      selectedDayIndex = 0;
      setViewMode('single');
      updateNavActiveState(cityId, shouldScroll);
      renderDashboard();
    }}

    function selectCityByIndex(index, shouldScroll = true) {{
      if (index < 0 || index >= cityList.length) return;
      const city = cityList[index];
      const cid = city.name.toLowerCase().replace(' ', '-');
      selectCity(cid, shouldScroll);
    }}

    function selectDay(index) {{
      selectedDayIndex = index;
      renderForecastCards();
      renderHourly();
    }}

    function getUVBadge(uv) {{
      if (uv <= 2) return {{ text: 'Low', class: 'badge-emerald' }};
      if (uv <= 5) return {{ text: 'Moderate', class: 'badge-amber' }};
      if (uv <= 7) return {{ text: 'High', class: 'badge-rose' }};
      return {{ text: 'Very High', class: 'badge-rose' }};
    }}

    function buildNavBar() {{
      const nav = document.getElementById('city-nav-bar');
      nav.innerHTML = '';

      cityList.forEach((c, idx) => {{
        const cid = c.name.toLowerCase().replace(' ', '-');
        const data = weatherData[cid];
        if (!data) return;

        const tempVal = currentUnit === 'C' ? data.current.tempC : data.current.tempF;
        const btn = document.createElement('div');
        btn.className = `city-nav-item ${{cid === currentCityId && currentViewMode === 'single' ? 'active' : ''}}`;
        btn.setAttribute('data-city-id', cid);
        btn.setAttribute('data-index', idx);
        btn.onclick = () => selectCity(cid, true);
        btn.innerHTML = `
          <span>${{c.flag}}</span>
          <span>${{c.name}}</span>
          <span class="city-nav-pill-temp" id="nav-temp-${{cid}}">${{tempVal}}°${{currentUnit}}</span>
        `;
        nav.appendChild(btn);
      }});
    }}

    function updateNavActiveState(cityId, shouldScroll = false) {{
      const nav = document.getElementById('city-nav-bar');
      if (!nav) return;
      const items = nav.querySelectorAll('.city-nav-item');
      let targetItem = null;
      items.forEach(item => {{
        const isMatch = item.getAttribute('data-city-id') === cityId && currentViewMode === 'single';
        item.classList.toggle('active', isMatch);
        if (isMatch) targetItem = item;
      }});
      if (shouldScroll && targetItem) {{
        targetItem.scrollIntoView({{ behavior: 'smooth', inline: 'center', block: 'nearest' }});
      }}
    }}

    function updateNavTemperatures() {{
      cityList.forEach(c => {{
        const cid = c.name.toLowerCase().replace(' ', '-');
        const data = weatherData[cid];
        const el = document.getElementById(`nav-temp-${{cid}}`);
        if (data && el) {{
          const tempVal = currentUnit === 'C' ? data.current.tempC : data.current.tempF;
          el.textContent = `${{tempVal}}°${{currentUnit}}`;
        }}
      }});
    }}

    function updateAmbientWeatherTheme(desc, code) {{
      const orb1 = document.querySelector('.orb-1');
      const orb2 = document.querySelector('.orb-2');
      const orb3 = document.querySelector('.orb-3');
      if (!orb1 || !orb2) return;

      if (!desc && window.currentCityId && weatherData[window.currentCityId]) {{
        desc = weatherData[window.currentCityId].current.desc;
        code = weatherData[window.currentCityId].current.weatherCode;
      }}
      if (!desc) return;

      const isLight = document.documentElement.getAttribute('data-theme') === 'light';
      const d = desc.toLowerCase();
      const c = parseInt(code) || 0;

      let c1, c2, c3;

      if (isLight) {{
        // Google Signature Brand Accents in Light Mode
        if (d.includes('clear') || d.includes('sunny') || c === 113) {{
          c1 = '#FBBC05'; // Google Yellow
          c2 = '#EA4335'; // Google Red
          c3 = '#4285F4'; // Google Blue
        }} else if (d.includes('rain') || d.includes('shower') || d.includes('drizzle')) {{
          c1 = '#4285F4'; // Google Blue
          c2 = '#1a73e8'; // Google Blue Dark
          c3 = '#34A853'; // Google Green
        }} else if (d.includes('snow') || d.includes('ice') || d.includes('sleet')) {{
          c1 = '#8ab4f8';
          c2 = '#d2e3fc';
          c3 = '#4285F4';
        }} else if (d.includes('thunder')) {{
          c1 = '#EA4335'; // Google Red
          c2 = '#4285F4'; // Google Blue
          c3 = '#FBBC05'; // Google Yellow
        }} else if (d.includes('cloud') || d.includes('overcast')) {{
          c1 = '#94a3b8';
          c2 = '#4285F4';
          c3 = '#cbd5e1';
        }} else {{
          c1 = '#4285F4';
          c2 = '#34A853';
          c3 = '#FBBC05';
        }}
      }} else {{
        // Preserved Original Cosmic Theme in Dark Mode
        if (d.includes('clear') || d.includes('sunny') || c === 113) {{
          c1 = '#d97706';
          c2 = '#6366f1';
          c3 = '#8b5cf6';
        }} else if (d.includes('rain') || d.includes('shower') || d.includes('drizzle')) {{
          c1 = '#0284c7';
          c2 = '#1e3a8a';
          c3 = '#06b6d4';
        }} else if (d.includes('snow') || d.includes('ice') || d.includes('sleet')) {{
          c1 = '#38bdf8';
          c2 = '#9333ea';
          c3 = '#6366f1';
        }} else if (d.includes('thunder')) {{
          c1 = '#7c3aed';
          c2 = '#1e1b4b';
          c3 = '#4f46e5';
        }} else if (d.includes('cloud') || d.includes('overcast')) {{
          c1 = '#475569';
          c2 = '#4338ca';
          c3 = '#334155';
        }} else {{
          c1 = '#4f46e5';
          c2 = '#06b6d4';
          c3 = '#8b5cf6';
        }}
      }}

      orb1.style.background = `radial-gradient(circle, ${{c1}} 0%, rgba(0,0,0,0) 70%)`;
      orb2.style.background = `radial-gradient(circle, ${{c2}} 0%, rgba(0,0,0,0) 70%)`;
      if (orb3) orb3.style.background = `radial-gradient(circle, ${{c3}} 0%, rgba(0,0,0,0) 70%)`;
    }}

    function renderDashboard() {{
      const city = weatherData[currentCityId];
      if (!city) return;

      const curr = city.current;
      const day0 = city.forecast[0];

      // Update atmospheric refractive glow to match city weather
      updateAmbientWeatherTheme(curr.desc, curr.weatherCode);

      // Update real-time HTML5 physics canvas particles
      if (window.canvasEngine) {{
        window.canvasEngine.setWeather(curr.desc, curr.weatherCode, curr.windSpeedKmph, curr.windDirDegree);
      }}

      // Hero Elements
      document.getElementById('hero-flag').textContent = city.flag;
      document.getElementById('hero-region').textContent = `${{city.region || city.country}}`;
      document.getElementById('hero-city-name').textContent = city.name;
      document.getElementById('hero-country').textContent = city.country;

      const tempVal = currentUnit === 'C' ? curr.tempC : curr.tempF;
      const feelsLikeVal = currentUnit === 'C' ? curr.feelsLikeC : curr.feelsLikeF;
      const unitSymbol = `°${{currentUnit}}`;

      document.getElementById('hero-temp').textContent = `${{tempVal}}${{unitSymbol}}`;
      document.getElementById('hero-icon').textContent = curr.icon;
      document.getElementById('hero-desc').textContent = curr.desc;
      document.getElementById('hero-feels-like').textContent = `${{feelsLikeVal}}${{unitSymbol}}`;

      const maxToday = currentUnit === 'C' ? day0.maxTempC : day0.maxTempF;
      const minToday = currentUnit === 'C' ? day0.minTempC : day0.minTempF;
      document.getElementById('hero-temp-range').textContent = `H: ${{maxToday}}${{unitSymbol}} / L: ${{minToday}}${{unitSymbol}}`;

      // Hero Highlights
      document.getElementById('hero-sunrise').textContent = day0.astronomy.sunrise;
      document.getElementById('hero-sunset').textContent = day0.astronomy.sunset;
      document.getElementById('hero-moon-phase').textContent = day0.astronomy.moonPhase;
      document.getElementById('hero-sun-hours').textContent = `${{day0.sunHour}} hrs`;
      document.getElementById('hero-obs-time').textContent = curr.obsTime;
      document.getElementById('hero-coords').textContent = `Lat: ${{city.latitude}}°, Lon: ${{city.longitude}}°`;

      // Atmospheric Metrics
      document.getElementById('metric-humidity').textContent = `${{curr.humidity}}%`;
      document.getElementById('metric-humidity-sub').textContent = curr.humidity > 70 ? 'Humid' : curr.humidity < 30 ? 'Dry' : 'Comfortable';

      const windSpeed = currentUnit === 'C' ? `${{curr.windSpeedKmph}} km/h` : `${{curr.windSpeedMiles}} mph`;
      document.getElementById('metric-wind').textContent = windSpeed;
      document.getElementById('metric-wind-dir').textContent = `Direction: ${{curr.windDir}} (${{curr.windDirDegree}}°)`;

      document.getElementById('metric-uv').textContent = curr.uvIndex;
      const uvInfo = getUVBadge(curr.uvIndex);
      const uvBadge = document.getElementById('metric-uv-badge');
      uvBadge.textContent = uvInfo.text;
      uvBadge.className = `badge-pill ${{uvInfo.class}}`;

      const precip = currentUnit === 'C' ? `${{curr.precipMM}} mm` : `${{curr.precipInches}} in`;
      document.getElementById('metric-precip').textContent = precip;

      document.getElementById('metric-cloud').textContent = `${{curr.cloudcover}}%`;
      document.getElementById('metric-cloud-sub').textContent = curr.cloudcover > 75 ? 'Heavy cover' : curr.cloudcover > 25 ? 'Partially cloudy' : 'Clear skies';

      const pressure = currentUnit === 'C' ? `${{curr.pressure}} hPa` : `${{curr.pressureInches}} inHg`;
      document.getElementById('metric-pressure').textContent = pressure;

      const vis = currentUnit === 'C' ? `${{curr.visibilityKm}} km` : `${{curr.visibilityMiles}} mi`;
      document.getElementById('metric-visibility').textContent = vis;

      renderForecastCards();
      renderHourly();
    }}

    function renderForecastCards() {{
      const city = weatherData[currentCityId];
      const container = document.getElementById('forecast-cards-container');
      container.innerHTML = '';

      city.forecast.forEach((f, idx) => {{
        const card = document.createElement('div');
        card.className = `forecast-card ${{idx === selectedDayIndex ? 'selected' : ''}}`;
        card.onclick = () => selectDay(idx);

        const maxT = currentUnit === 'C' ? f.maxTempC : f.maxTempF;
        const minT = currentUnit === 'C' ? f.minTempC : f.minTempF;
        const unitSymbol = `°${{currentUnit}}`;

        card.innerHTML = `
          <div class="forecast-day-name">${{f.dayLabel}}</div>
          <div class="forecast-date">${{f.displayDate}}</div>
          <div class="forecast-center">
            <span class="forecast-icon">${{f.icon}}</span>
            <div class="forecast-temp-range">
              <span class="forecast-max">${{maxT}}${{unitSymbol}}</span>
              <span class="forecast-min">Low: ${{minT}}${{unitSymbol}}</span>
            </div>
          </div>
          <div class="forecast-desc">${{f.desc}}</div>
          <div class="forecast-stats-pill">
            <span>🌧️ ${{f.maxRainChance}}% rain</span>
            <span>☀️ UV ${{f.uvIndex}}</span>
            <span>🌅 ${{f.astronomy.sunrise}}</span>
          </div>
        `;
        container.appendChild(card);
      }});
    }}

    function renderHourly() {{
      const city = weatherData[currentCityId];
      const day = city.forecast[selectedDayIndex];
      const container = document.getElementById('hourly-list');
      container.innerHTML = '';

      document.getElementById('hourly-day-label').textContent = `${{day.dayLabel}} (${{day.weekday}})`;
      document.getElementById('hourly-date-label').textContent = day.displayDate;

      day.hourly.forEach(h => {{
        const card = document.createElement('div');
        card.className = 'hourly-card';
        const temp = currentUnit === 'C' ? h.tempC : h.tempF;
        const feels = currentUnit === 'C' ? h.feelsLikeC : h.feelsLikeF;
        const wind = currentUnit === 'C' ? `${{h.windSpeedKmph}} km/h` : `${{h.windSpeedMiles}} mph`;
        const unitSymbol = `°${{currentUnit}}`;

        card.innerHTML = `
          <div class="hourly-time">${{h.timeFormatted}}</div>
          <div class="hourly-icon" title="${{h.desc}}">${{h.icon}}</div>
          <div class="hourly-temp">${{temp}}${{unitSymbol}}</div>
          <div style="font-size:11px; color:var(--text-muted);">Feels ${{feels}}°</div>
          <div class="hourly-rain">💧 ${{h.chanceOfRain}}%</div>
          <div class="hourly-wind">${{wind}}</div>
        `;
        container.appendChild(card);
      }});
    }}

    function renderAllCitiesGrid() {{
      const grid = document.getElementById('cities-overview-grid');
      grid.innerHTML = '';
      const unitSym = `°${{currentUnit}}`;

      cityList.forEach(c => {{
        const cid = c.name.toLowerCase().replace(' ', '-');
        const data = weatherData[cid];
        if (!data) return;

        const curr = data.current;
        const f0 = data.forecast[0];
        const temp = currentUnit === 'C' ? curr.tempC : curr.tempF;
        const maxT = currentUnit === 'C' ? f0.maxTempC : f0.maxTempF;
        const minT = currentUnit === 'C' ? f0.minTempC : f0.minTempF;

        const card = document.createElement('div');
        card.className = 'city-card-item';
        card.onclick = () => selectCity(cid);

        card.innerHTML = `
          <div class="city-card-header">
            <div class="city-card-name">
              <span style="font-size: 22px;">${{c.flag}}</span>
              <span>${{c.name}}</span>
            </div>
            <span style="font-size: 28px;">${{curr.icon}}</span>
          </div>
          <div class="city-card-temp">${{temp}}${{unitSym}}</div>
          <div style="font-size: 13px; color: var(--text-muted); font-weight: 500;">
            ${{curr.desc}} • Feels like ${{currentUnit === 'C' ? curr.feelsLikeC : curr.feelsLikeF}}${{unitSym}}
          </div>
          <div class="city-card-footer">
            <span>H: ${{maxT}}${{unitSym}} / L: ${{minT}}${{unitSym}}</span>
            <span>💧 ${{curr.humidity}}% | 💨 ${{currentUnit === 'C' ? curr.windSpeedKmph + ' km/h' : curr.windSpeedMiles + ' mph'}}</span>
          </div>
        `;
        grid.appendChild(card);
      }});
    }}

    function initCompareDropdowns() {{
      const sel1 = document.getElementById('select-city-1');
      const sel2 = document.getElementById('select-city-2');
      sel1.innerHTML = '';
      sel2.innerHTML = '';

      cityList.forEach(c => {{
        const cid = c.name.toLowerCase().replace(' ', '-');
        const opt1 = document.createElement('option');
        opt1.value = cid;
        opt1.textContent = `${{c.flag}} ${{c.name}} (${{c.query}})`;
        if (cid === 'london') opt1.selected = true;
        sel1.appendChild(opt1);

        const opt2 = document.createElement('option');
        opt2.value = cid;
        opt2.textContent = `${{c.flag}} ${{c.name}} (${{c.query}})`;
        if (cid === 'ankara') opt2.selected = true;
        sel2.appendChild(opt2);
      }});
    }}

    function updateComparison() {{
      const id1 = document.getElementById('select-city-1').value || 'london';
      const id2 = document.getElementById('select-city-2').value || 'ankara';
      const c1 = weatherData[id1];
      const c2 = weatherData[id2];
      const unitSym = `°${{currentUnit}}`;

      function makeRows(city) {{
        if (!city) return '';
        const c = city.current;
        const f0 = city.forecast[0];
        const f1 = city.forecast[1];
        const f2 = city.forecast[2];
        const temp = currentUnit === 'C' ? c.tempC : c.tempF;
        const feels = currentUnit === 'C' ? c.feelsLikeC : c.feelsLikeF;
        const wind = currentUnit === 'C' ? `${{c.windSpeedKmph}} km/h` : `${{c.windSpeedMiles}} mph`;
        const f0max = currentUnit === 'C' ? f0.maxTempC : f0.maxTempF;
        const f0min = currentUnit === 'C' ? f0.minTempC : f0.minTempF;
        const f1max = currentUnit === 'C' ? f1.maxTempC : f1.maxTempF;
        const f1min = currentUnit === 'C' ? f1.minTempC : f1.minTempF;
        const f2max = currentUnit === 'C' ? f2.maxTempC : f2.maxTempF;
        const f2min = currentUnit === 'C' ? f2.minTempC : f2.minTempF;

        return `
          <tr><td>Condition</td><td>${{c.icon}} ${{c.desc}}</td></tr>
          <tr><td>Current Temperature</td><td><strong style="color:var(--primary-light); font-size:18px;">${{temp}}${{unitSym}}</strong></td></tr>
          <tr><td>Feels Like</td><td>${{feels}}${{unitSym}}</td></tr>
          <tr><td>Humidity</td><td>${{c.humidity}}%</td></tr>
          <tr><td>Wind</td><td>${{wind}} (${{c.windDir}})</td></tr>
          <tr><td>UV Index</td><td>${{c.uvIndex}} (${{getUVBadge(c.uvIndex).text}})</td></tr>
          <tr><td>Cloud Cover</td><td>${{c.cloudcover}}%</td></tr>
          <tr><td>Today (${{f0.dayLabel}})</td><td>${{f0.icon}} ${{f0max}}${{unitSym}} / ${{f0min}}${{unitSym}} (${{f0.maxRainChance}}% rain)</td></tr>
          <tr><td>Tomorrow (${{f1.dayLabel}})</td><td>${{f1.icon}} ${{f1max}}${{unitSym}} / ${{f1min}}${{unitSym}} (${{f1.maxRainChance}}% rain)</td></tr>
          <tr><td>Day 3 (${{f2.dayLabel}})</td><td>${{f2.icon}} ${{f2max}}${{unitSym}} / ${{f2min}}${{unitSym}} (${{f2.maxRainChance}}% rain)</td></tr>
          <tr><td>Sunrise / Sunset</td><td>🌅 ${{f0.astronomy.sunrise}} / 🌇 ${{f0.astronomy.sunset}}</td></tr>
        `;
      }}

      if (c1) {{
        document.getElementById('compare-title-1').innerHTML = `<span>${{c1.flag}}</span> ${{c1.name}}, ${{c1.country}}`;
        document.getElementById('compare-table-1').innerHTML = makeRows(c1);
      }}
      if (c2) {{
        document.getElementById('compare-title-2').innerHTML = `<span>${{c2.flag}}</span> ${{c2.name}}, ${{c2.country}}`;
        document.getElementById('compare-table-2').innerHTML = makeRows(c2);
      }}
    }}

    function setupNavBarScroll() {{
      const navBar = document.getElementById('city-nav-bar');
      if (!navBar) return;

      let lastWheelTime = 0;
      let isProgrammaticScroll = false;
      let programmaticTimer = null;

      // Mouse wheel listener: single-notch step & rapid spin multi-step with auto-selection
      navBar.addEventListener('wheel', (e) => {{
        // Intercept when hovering over the locations bar and vertical movement is dominant
        if (Math.abs(e.deltaY) >= Math.abs(e.deltaX)) {{
          e.preventDefault(); // Stop main webpage from scrolling vertically

          const now = Date.now();
          const timeDiff = now - lastWheelTime;
          lastWheelTime = now;

          // Find current active city index
          const currentIndex = cityList.findIndex(c => c.name.toLowerCase().replace(' ', '-') === currentCityId);
          if (currentIndex === -1) return;

          const direction = Math.sign(e.deltaY); // 1 = next, -1 = prev
          const absDelta = Math.abs(e.deltaY);

          // Determine step size based on wheel velocity
          let step = 1;
          // Rapid spin detection: rapid successive events (< 80ms) with significant delta
          if (absDelta > 200 || (timeDiff < 80 && absDelta > 70)) {{
            step = Math.min(4, Math.max(1, Math.round(absDelta / 70)));
          }}

          let targetIndex = currentIndex + (direction * step);
          targetIndex = Math.max(0, Math.min(cityList.length - 1, targetIndex));

          if (targetIndex !== currentIndex) {{
            isProgrammaticScroll = true;
            clearTimeout(programmaticTimer);
            programmaticTimer = setTimeout(() => {{ isProgrammaticScroll = false; }}, 400);

            selectCityByIndex(targetIndex, true);
          }}
        }}
      }}, {{ passive: false }});

      // Debounced center-detection for trackpad horizontal scrolling or manual drags
      let scrollDebounceTimer = null;
      navBar.addEventListener('scroll', () => {{
        if (isProgrammaticScroll) return;

        clearTimeout(scrollDebounceTimer);
        scrollDebounceTimer = setTimeout(() => {{
          const navRect = navBar.getBoundingClientRect();
          const navCenter = navRect.left + navRect.width / 2;

          const items = navBar.querySelectorAll('.city-nav-item');
          let closestItem = null;
          let minDistance = Infinity;

          items.forEach(item => {{
            const rect = item.getBoundingClientRect();
            const itemCenter = rect.left + rect.width / 2;
            const dist = Math.abs(navCenter - itemCenter);
            if (dist < minDistance) {{
              minDistance = dist;
              closestItem = item;
            }}
          }});

          if (closestItem) {{
            const cid = closestItem.getAttribute('data-city-id');
            if (cid && cid !== currentCityId && currentViewMode === 'single') {{
              selectCity(cid, false);
            }}
          }}
        }}, 60);
      }}, {{ passive: true }});
    }}

    class WeatherCanvasEngine {{
      constructor(canvasId) {{
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.lightning = {{ active: false, opacity: 0, timer: 0 }};
        this.condition = 'clear';
        this.windAngle = 0;
        this.windSpeed = 10;
        this.enabled = true;
        this.animId = null;

        this.resize();
        window.addEventListener('resize', () => this.resize());

        document.addEventListener('visibilitychange', () => {{
          if (document.hidden) this.stop();
          else if (this.enabled) this.start();
        }});

        this.initParticles();
        this.start();
      }}

      resize() {{
        this.width = window.innerWidth;
        this.height = window.innerHeight;
        this.canvas.width = this.width;
        this.canvas.height = this.height;
      }}

      setWeather(desc, code, windSpeedKmph, windDirDegree) {{
        const d = desc.toLowerCase();
        const c = parseInt(code) || 0;
        const speed = Math.max(5, Math.min(55, parseInt(windSpeedKmph) || 12));
        const deg = (parseInt(windDirDegree) || 0) * (Math.PI / 180);

        this.windSpeed = speed;
        this.windAngle = deg;

        let newCondition = 'clear';
        if (d.includes('thunder') || [200, 386, 389, 392, 395].includes(c)) {{
          newCondition = 'thunder';
        }} else if (d.includes('snow') || d.includes('blizzard') || d.includes('sleet') || d.includes('ice') || [179, 182, 185, 227, 230, 323, 326, 329, 332, 335, 338, 350, 368, 371, 374, 377].includes(c)) {{
          newCondition = 'snow';
        }} else if (d.includes('rain') || d.includes('shower') || d.includes('drizzle') || [176, 263, 266, 293, 296, 299, 302, 305, 308, 311, 314, 353, 356, 359].includes(c)) {{
          newCondition = 'rain';
        }} else if (d.includes('cloud') || d.includes('overcast') || d.includes('fog') || d.includes('mist') || [119, 122, 143, 248, 260].includes(c)) {{
          newCondition = 'cloud';
        }} else {{
          newCondition = 'clear';
        }}

        if (newCondition !== this.condition) {{
          this.condition = newCondition;
          this.initParticles();
        }}
      }}

      initParticles() {{
        this.particles = [];
        const count = this.condition === 'rain' || this.condition === 'thunder' ? 100 :
                      this.condition === 'snow' ? 70 :
                      this.condition === 'cloud' ? 22 : 40;

        for (let i = 0; i < count; i++) {{
          this.particles.push(this.createParticle(true));
        }}
      }}

      createParticle(randomY = false) {{
        const y = randomY ? Math.random() * this.height : -20;
        const x = Math.random() * (this.width + 100) - 50;

        if (this.condition === 'rain' || this.condition === 'thunder') {{
          return {{
            x: x,
            y: y,
            len: 14 + Math.random() * 18,
            speed: 15 + Math.random() * 10 + (this.windSpeed * 0.18),
            opacity: 0.25 + Math.random() * 0.45,
            width: 1 + Math.random() * 1.2
          }};
        }} else if (this.condition === 'snow') {{
          return {{
            x: x,
            y: y,
            radius: 1.5 + Math.random() * 3,
            speed: 1.2 + Math.random() * 2.2,
            swaySpeed: 0.02 + Math.random() * 0.03,
            swayOffset: Math.random() * Math.PI * 2,
            opacity: 0.35 + Math.random() * 0.55
          }};
        }} else if (this.condition === 'cloud') {{
          return {{
            x: x,
            y: Math.random() * (this.height * 0.65),
            radius: 90 + Math.random() * 140,
            speed: 0.25 + Math.random() * 0.5 + (this.windSpeed * 0.015),
            opacity: 0.035 + Math.random() * 0.04
          }};
        }} else {{
          return {{
            x: x,
            y: y,
            radius: 1.2 + Math.random() * 2.8,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5 - 0.2,
            opacity: 0.2 + Math.random() * 0.4,
            pulse: Math.random() * Math.PI * 2
          }};
        }}
      }}

      update() {{
        const slantX = Math.sin(this.windAngle) * (this.windSpeed * 0.16);

        if (this.condition === 'thunder') {{
          this.lightning.timer++;
          if (this.lightning.timer > 150 && Math.random() < 0.03) {{
            this.lightning.active = true;
            this.lightning.opacity = 0.35 + Math.random() * 0.35;
            this.lightning.timer = 0;
          }}
          if (this.lightning.active) {{
            this.lightning.opacity *= 0.86;
            if (this.lightning.opacity < 0.02) this.lightning.active = false;
          }}
        }}

        for (let p of this.particles) {{
          if (this.condition === 'rain' || this.condition === 'thunder') {{
            p.y += p.speed;
            p.x += slantX;
            if (p.y > this.height || p.x > this.width + 60 || p.x < -60) {{
              Object.assign(p, this.createParticle(false));
            }}
          }} else if (this.condition === 'snow') {{
            p.swayOffset += p.swaySpeed;
            p.y += p.speed;
            p.x += Math.sin(p.swayOffset) * 1.3 + (slantX * 0.5);
            if (p.y > this.height || p.x > this.width + 60 || p.x < -60) {{
              Object.assign(p, this.createParticle(false));
            }}
          }} else if (this.condition === 'cloud') {{
            p.x += p.speed;
            if (p.x - p.radius > this.width + 50) {{
              p.x = -p.radius;
              p.y = Math.random() * (this.height * 0.65);
            }}
          }} else {{
            p.pulse += 0.03;
            p.x += p.vx;
            p.y += p.vy;
            if (p.x < 0 || p.x > this.width || p.y < 0 || p.y > this.height) {{
              Object.assign(p, this.createParticle(true));
            }}
          }}
        }}
      }}

      setTheme(theme) {{
        this.theme = theme;
      }}

      draw() {{
        this.ctx.clearRect(0, 0, this.width, this.height);

        const isLight = document.documentElement.getAttribute('data-theme') === 'light';

        if (this.condition === 'thunder' && this.lightning.active) {{
          this.ctx.fillStyle = isLight ? `rgba(66, 133, 244, ${{this.lightning.opacity * 0.35}})` : `rgba(186, 230, 253, ${{this.lightning.opacity}})`;
          this.ctx.fillRect(0, 0, this.width, this.height);
        }}

        const slantX = Math.sin(this.windAngle) * (this.windSpeed * 0.16);

        for (let p of this.particles) {{
          if (this.condition === 'rain' || this.condition === 'thunder') {{
            // Google Blue in light mode, sky blue in dark mode
            this.ctx.strokeStyle = isLight ? `rgba(66, 133, 244, ${{p.opacity * 0.85}})` : `rgba(186, 230, 253, ${{p.opacity}})`;
            this.ctx.lineWidth = p.width;
            this.ctx.beginPath();
            this.ctx.moveTo(p.x, p.y);
            this.ctx.lineTo(p.x + slantX * 1.4, p.y + p.len);
            this.ctx.stroke();
          }} else if (this.condition === 'snow') {{
            // Soft periwinkle frost in light mode, pure white in dark mode
            this.ctx.fillStyle = isLight ? `rgba(99, 140, 219, ${{p.opacity * 0.75}})` : `rgba(255, 255, 255, ${{p.opacity}})`;
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            this.ctx.fill();
          }} else if (this.condition === 'cloud') {{
            const grad = this.ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.radius);
            if (isLight) {{
              grad.addColorStop(0, `rgba(148, 163, 184, ${{p.opacity * 0.75}})`);
              grad.addColorStop(1, 'rgba(148, 163, 184, 0)');
            }} else {{
              grad.addColorStop(0, `rgba(203, 213, 225, ${{p.opacity}})`);
              grad.addColorStop(1, 'rgba(203, 213, 225, 0)');
            }}
            this.ctx.fillStyle = grad;
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            this.ctx.fill();
          }} else {{
            // Google Yellow in light mode, golden in dark mode
            const alpha = Math.max(0.08, p.opacity * (0.6 + 0.4 * Math.sin(p.pulse)));
            this.ctx.fillStyle = isLight ? `rgba(251, 188, 5, ${{alpha * 0.85}})` : `rgba(251, 191, 36, ${{alpha}})`;
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            this.ctx.fill();
          }}
        }}
      }}

      loop() {{
        if (!this.enabled) return;
        this.update();
        this.draw();
        this.animId = requestAnimationFrame(() => this.loop());
      }}

      start() {{
        if (!this.animId) {{
          this.animId = requestAnimationFrame(() => this.loop());
        }}
      }}

      stop() {{
        if (this.animId) {{
          cancelAnimationFrame(this.animId);
          this.animId = null;
        }}
      }}

      toggle() {{
        this.enabled = !this.enabled;
        if (this.enabled) {{
          this.canvas.style.opacity = '1';
          this.start();
        }} else {{
          this.canvas.style.opacity = '0';
          this.stop();
          this.ctx.clearRect(0, 0, this.width, this.height);
        }}
        return this.enabled;
      }}
    }}

    function toggleWeatherFX() {{
      if (window.canvasEngine) {{
        const isEnabled = window.canvasEngine.toggle();
        const lbl = document.getElementById('fx-label');
        if (lbl) lbl.textContent = isEnabled ? 'FX: On' : 'FX: Off';
      }}
    }}

    function applyTheme(theme) {{
      document.documentElement.setAttribute('data-theme', theme);
      try {{
        localStorage.setItem('weather_theme', theme);
      }} catch (e) {{}}

      const icon = document.getElementById('theme-icon');
      const label = document.getElementById('theme-label');
      if (icon && label) {{
        icon.textContent = theme === 'light' ? '🌙' : '☀️';
        label.textContent = theme === 'light' ? 'Dark' : 'Light';
      }}

      if (window.canvasEngine) {{
        window.canvasEngine.setTheme(theme);
      }}

      updateAmbientWeatherTheme();
    }}

    function toggleTheme() {{
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      applyTheme(current === 'light' ? 'dark' : 'light');
    }}

    function initTheme() {{
      let savedTheme = 'dark';
      try {{
        savedTheme = localStorage.getItem('weather_theme') || 'dark';
      }} catch (e) {{}}
      applyTheme(savedTheme);
    }}

    /* Settings Hamburger Dropdown Controller */
    function toggleSettingsMenu(e) {{
      if (e) e.stopPropagation();
      const dropdown = document.getElementById('settings-dropdown');
      const btn = document.getElementById('hamburger-btn');
      if (!dropdown || !btn) return;

      const isOpen = dropdown.classList.toggle('open');
      btn.classList.toggle('open', isOpen);
      btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    }}

    function closeSettingsMenu() {{
      const dropdown = document.getElementById('settings-dropdown');
      const btn = document.getElementById('hamburger-btn');
      if (dropdown) dropdown.classList.remove('open');
      if (btn) {{
        btn.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      }}
    }}

    // Auto-close settings menu on outside click and Escape key
    document.addEventListener('click', (e) => {{
      const container = document.getElementById('settings-menu-container');
      if (container && !container.contains(e.target)) {{
        closeSettingsMenu();
      }}
    }});

    document.addEventListener('keydown', (e) => {{
      if (e.key === 'Escape') closeSettingsMenu();
    }});

    // Initialize
    initTheme();
    window.canvasEngine = new WeatherCanvasEngine('weather-canvas');
    initCompareDropdowns();
    buildNavBar();
    renderDashboard();
    setupNavBarScroll();
  </script>
</body>
</html>
"""
    return html_content

# Number of concurrent worker threads.
# 4 workers provides a ~70% speedup while remaining polite to public wttr.in rate limits.
MAX_WORKERS = 4

def fetch_and_parse_city(city_info: dict) -> tuple:
    """Worker function to fetch and parse weather data for a single city."""
    name = city_info["name"]
    query = city_info["query"]
    flag = city_info["flag"]
    cid = name.lower().replace(" ", "-")
    
    try:
        raw_data = fetch_weather(query)
        parsed = parse_city_weather(raw_data, name, flag)
        return (cid, name, parsed, None)
    except Exception as e:
        return (cid, name, None, str(e))

def main():
    print(f"Fetching weather data for {len(CITIES)} cities (this may take a moment)... \n")
    
    parsed_data = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks to the thread pool
        future_to_city = {
            executor.submit(fetch_and_parse_city, city): city for city in CITIES
        }
        
        # Process and report results in real-time as each thread finishes
        for future in as_completed(future_to_city):
            cid, name, data, error = future.result()
            if data:
                parsed_data[cid] = data
                print(f"✅ Successfully fetched data for {name}")
            else:
                print(f"❌ Failed to fetch data for {name}: {error}")
    
    print("\nGenerating HTML dashboard...")
    html = generate_html(parsed_data, CITIES)

    output_filename = "weather_dashboard.html"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n🎉 Successfully generated '{output_filename}' with live data for all {len(parsed_data)} cities!")

if __name__ == "__main__":
    main()
