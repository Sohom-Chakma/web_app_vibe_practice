# Web App Vibe Practice - Weather Intelligence Dashboard

A modern, interactive weather dashboard comparing **London, UK** and **Ankara, Turkey** using real-time observations and 3-day forecasts from [wttr.in](https://wttr.in) (`format=j1`).

## ✨ Features
- **Real-time Atmospheric Conditions**: Current temperature, feels like, condition badge, humidity, wind speed & direction, UV index, precipitation, pressure, visibility, and cloud cover.
- **3-Day Forecast Breakdown**: Daily high/low ranges, sunrise/sunset, moon phase, sun hours, and chance of rain.
- **Interactive Hourly View**: 24-hour breakdown (3-hour intervals) with weather icons, temperature, precipitation probability, and wind speeds. Click any day to inspect its hourly schedule.
- **Side-by-Side Comparison**: Head-to-head comparison table between London and Ankara across atmospheric and forecast metrics.
- **Metric / Imperial Unit Switcher**: Instant toggle between **°C & km/h** and **°F & mph**.
- **Modern Responsive Glassmorphic UI**: Clean dark theme with smooth gradients, card hover effects, and mobile-friendly responsive layout.

## 🚀 How to Run

1. Run the Python generator script to fetch the latest weather data from wttr.in and generate the dashboard:
   ```bash
   python generate_weather_dashboard.py
   ```

2. Open the generated file in your web browser:
   ```bash
   start weather_dashboard.html
   ```
