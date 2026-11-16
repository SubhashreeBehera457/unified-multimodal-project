import React from 'react';
import { CloudRain, Wind, Thermometer, Compass, CloudSun, AlertCircle } from 'lucide-react';
import { WeatherData } from '../../types';
import { SourceBadge } from '../status/SourceBadge';

interface WeatherCardProps {
  weather: WeatherData | null;
  loading?: boolean;
}

export const WeatherCard: React.FC<WeatherCardProps> = ({ weather, loading = false }) => {
  if (loading && !weather) {
    return (
      <div className="p-4 rounded bg-[#111827] border border-[#1F2937] animate-pulse">
        <div className="h-4 w-32 bg-slate-800 rounded mb-4" />
        <div className="grid grid-cols-2 gap-3">
          <div className="h-14 bg-slate-800/60 rounded" />
          <div className="h-14 bg-slate-800/60 rounded" />
        </div>
      </div>
    );
  }

  if (!weather || weather.source === 'UNAVAILABLE') {
    return (
      <div className="p-4 rounded bg-[#111827] border border-slate-800 flex flex-col justify-between">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <CloudSun className="w-4 h-4 text-slate-500" />
            <span className="text-xs font-mono font-semibold text-slate-300 uppercase">
              Weather Telemetry (Bhubaneswar)
            </span>
          </div>
          <SourceBadge source="DATA SOURCE UNAVAILABLE" />
        </div>
        <div className="flex items-center gap-3 p-3 rounded bg-rose-950/20 border border-rose-900/30 text-rose-400 text-xs font-mono">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>Open-Meteo connection unavailable. Check network or server status.</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 rounded bg-[#111827] border border-[#1F2937] flex flex-col justify-between">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <CloudSun className="w-4 h-4 text-sky-400" />
          <span className="text-xs font-mono font-bold text-slate-200 uppercase">
            Weather Telemetry
          </span>
          <span className="text-[10px] font-mono text-slate-500">
            ({weather.lat.toFixed(2)}°N, {weather.lon.toFixed(2)}°E)
          </span>
        </div>
        <SourceBadge source={weather.source === 'LIVE' ? 'LIVE Open-Meteo' : 'DATA SOURCE UNAVAILABLE'} />
      </div>

      {/* Primary Observations Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {/* Temperature */}
        <div className="p-2.5 rounded bg-[#161E2E] border border-[#1F2937]/80">
          <div className="flex items-center justify-between text-slate-400 text-[10px] font-mono mb-1">
            <span>TEMPERATURE</span>
            <Thermometer className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-lg font-bold font-mono text-slate-100">
            {weather.temperature !== null ? `${weather.temperature}°C` : '--'}
          </div>
          <div className="text-[10px] font-mono text-slate-500 truncate">
            {weather.weather_description || 'Condition reported'}
          </div>
        </div>

        {/* Sustained Wind */}
        <div className="p-2.5 rounded bg-[#161E2E] border border-[#1F2937]/80">
          <div className="flex items-center justify-between text-slate-400 text-[10px] font-mono mb-1">
            <span>WIND SPEED</span>
            <Wind className="w-3.5 h-3.5 text-sky-400" />
          </div>
          <div className="text-lg font-bold font-mono text-slate-100">
            {weather.windspeed !== null ? `${weather.windspeed} km/h` : '--'}
          </div>
          <div className="text-[10px] font-mono text-slate-500 truncate">
            Max 24h: {weather.windspeed_max_24h ?? '--'} km/h
          </div>
        </div>

        {/* Current Precipitation */}
        <div className="p-2.5 rounded bg-[#161E2E] border border-[#1F2937]/80">
          <div className="flex items-center justify-between text-slate-400 text-[10px] font-mono mb-1">
            <span>CURRENT PRECIP</span>
            <CloudRain className="w-3.5 h-3.5 text-blue-400" />
          </div>
          <div className="text-lg font-bold font-mono text-slate-100">
            {weather.precipitation_now !== null ? `${weather.precipitation_now} mm` : '0.0 mm'}
          </div>
          <div className="text-[10px] font-mono text-slate-500 truncate">
            Current hour rate
          </div>
        </div>

        {/* 24h Precipitation Accumulation */}
        <div className="p-2.5 rounded bg-[#161E2E] border border-[#1F2937]/80">
          <div className="flex items-center justify-between text-slate-400 text-[10px] font-mono mb-1">
            <span>24H ACCUMULATION</span>
            <Compass className="w-3.5 h-3.5 text-indigo-400" />
          </div>
          <div className="text-lg font-bold font-mono text-sky-300">
            {weather.precipitation_24h !== null ? `${weather.precipitation_24h} mm` : '--'}
          </div>
          <div className="text-[10px] font-mono text-slate-500 truncate">
            Recorded at {weather.fetched_at}
          </div>
        </div>
      </div>
    </div>
  );
};
