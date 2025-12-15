import React, { useState, useEffect, memo } from 'react';

function WeatherWidget() {
  const [weather, setWeather] = useState({
    city: '--',
    temp_c: null,
    description: '--',
    icon_url: null,
  });

  useEffect(() => {
    const loadWeather = async () => {
      try {
        const r = await fetch("/api/weather");
        const data = await r.json();

        setWeather({
          city: data.city || '--',
          temp_c: data.temp_c,
          description: data.description || '--',
          icon_url: data.icon_url || null,
        });
      } catch (e) {
        console.error("Weather error:", e);
      }
    };

    loadWeather();
    const interval = setInterval(loadWeather, 30 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const tempStr = weather.temp_c !== null && weather.temp_c !== undefined
    ? weather.temp_c.toFixed(1) + "°C"
    : "--";

  return (
    <div id="weatherWidget">
      <div id="weatherInfo">
        Город: {weather.city}<br />
        Температура: {tempStr}<br />
        Погода: {weather.description}
      </div>
      <div id="weatherIconBox">
        {weather.icon_url && (
          <img id="weatherIcon" src={weather.icon_url} alt="Погода" />
        )}
      </div>
    </div>
  );
}

export default memo(WeatherWidget);

