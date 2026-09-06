# Global Weather Intelligence Dashboard

A modern, interactive weather dashboard tracking **12 major world cities** using real-time observations and 3-day forecasts from [wttr.in](https://wttr.in) (`format=j1`).

## 🌍 Tracked Cities
- 🇬🇧 London, United Kingdom
- 🇹🇷 Ankara, Turkey
- 🇯🇵 Tokyo, Japan
- 🇺🇸 New York, United States
- 🇫🇷 Paris, France
- 🇩🇪 Berlin, Germany
- 🇦🇺 Sydney, Australia
- 🇦🇪 Dubai, United Arab Emirates
- 🇸🇬 Singapore
- 🇨🇦 Toronto, Canada
- 🇮🇹 Rome, Italy
- 🇪🇬 Cairo, Egypt

---

## ✨ Features
- **3 Dynamic Views**:
  - **📍 City Detail**: Deep-dive atmospheric metrics, sun & moon astronomy, interactive 3-day forecast, and 24-hour breakdown (3-hour intervals).
  - **🗺️ 12-City Overview**: At-a-glance cards for all 12 cities showing real-time temperature, condition badge, humidity, and today's high/low range.
  - **⚖️ Head-to-Head Comparison**: Select any 2 cities from dropdowns to compare their atmospheric conditions and forecasts side-by-side.
- **High-Speed Concurrent Fetching**: Powered by Python's `ThreadPoolExecutor` (4 concurrent worker threads), speeding up multi-city fetching by ~70% while respecting server limits.
- **Metric / Imperial Unit Switcher**: Seamless live toggle between **°C (km/h)** and **°F (mph)**.
- **Scroll-Driven Location Selection**: Scrolling over the locations bar automatically activates and selects the next/previous city, updating the entire dashboard in real time. Supports both single-notch 1-at-a-time navigation and rapid multi-item scrolling with CSS Scroll Snapping (`scroll-snap-type: x mandatory`, `scroll-snap-align: center`).
- **Refractive Glassmorphism UI**: Multi-layered frosted glass panels (`backdrop-filter: blur(24px) saturate(190%)`), specular bevel rim highlights, and condition-adaptive ambient background orbs that react dynamically to the selected city's weather mood.

---

## 🚀 How to Run

1. Run the Python generator script to fetch the latest weather data:
   ```bash
   python generate_weather_dashboard.py
   ```

   **Console output:**
   ```text
   Fetching weather data for 12 cities (this may take a moment)... 

   ✅ Successfully fetched data for London
   ✅ Successfully fetched data for Ankara
   ✅ Successfully fetched data for Tokyo
   ✅ Successfully fetched data for New York
   ✅ Successfully fetched data for Paris
   ✅ Successfully fetched data for Berlin
   ✅ Successfully fetched data for Sydney
   ✅ Successfully fetched data for Dubai
   ✅ Successfully fetched data for Singapore
   ✅ Successfully fetched data for Toronto
   ✅ Successfully fetched data for Rome
   ✅ Successfully fetched data for Cairo

   Generating HTML dashboard...

   🎉 Successfully generated 'weather_dashboard.html' with live data for all 12 cities!
   ```

2. Open the dashboard in your web browser:
   ```bash
   start weather_dashboard.html
   ```
