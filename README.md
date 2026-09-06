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
- **Consolidated Settings Hamburger Dropdown Menu**:
  - A modern, tactile **☰ Settings** button in the header with an animated 3-bar icon that transitions into a close icon (`✕`).
  - Opens a refractive frosted glass dropdown card consolidating all three configuration toggles:
    1. **Appearance / Theme**: Seamless toggle between **Dark Mode** and **Light Mode** (with scoped Google Signature Accents).
    2. **Measurement Units**: Switch between **Metric (°C, km/h)** and **Imperial (°F, mph)**.
    3. **Weather Canvas FX**: Toggle live particle physics simulation On and Off.
  - Features click-outside auto-dismiss, Escape key support, and `localStorage` persistence.
- **Light & Dark Mode with Scoped Google Signature Accents**:
  - **Dark Mode**: Retains the original cyber/cosmic glassmorphism aesthetic with deep navy background (`#060913`), indigo/cyan ambient glows, and dark frosted glass.
  - **Light Mode**: Exclusively unlocks **Google Signature Brand Accents**:
    - Signature 4-color Google stripe at top (`#4285F4`, `#EA4335`, `#FBBC05`, `#34A853`).
    - Google Blue (`#4285F4`) primary active states, tabs, and navigation pills.
    - Google-tinted metric badges, astronomy highlights, and high/low indicators.
    - High-contrast white frosted glass surfaces (`rgba(255, 255, 255, 0.74)`).
- **Adaptive Data-Driven HTML5 Canvas Physics Engine**:
  - Real-time particle simulation running behind glass cards on a fixed hardware-accelerated canvas.
  - **Theme-Adaptive Particle Hues**: Rain droplets render as Google Blue (`#4285F4`) in Light Mode and sky blue in Dark Mode; snowflakes render as soft periwinkle frost on light backgrounds; sun motes pulse in Google Yellow (`#FBBC05`).
  - Rain particles angle and slant based on live wind direction (`windDirDegree`) and velocity (`windSpeedKmph`).
  - Snowflakes drift with sinusoidal swaying physics and wind slant.
  - Atmospheric cloud puffs drift softly across overcast skies.
  - Lightning flash simulation triggers dynamically for thunderstorm conditions.
  - Header controls include an interactive **✨ FX: On / Off** toggle button.

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
