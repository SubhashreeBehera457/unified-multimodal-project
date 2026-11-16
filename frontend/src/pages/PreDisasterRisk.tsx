import React, { useState, useEffect } from 'react';
import { CloudLightning, Cpu, ShieldAlert, Sliders, RefreshCw, BarChart3, AlertTriangle, Info, CheckCircle2 } from 'lucide-react';
import { RiskPrediction, WeatherData } from '../types';
import { api } from '../services/api';
import { SourceBadge } from '../components/status/SourceBadge';

interface PreDisasterRiskProps {
  weather: WeatherData | null;
}

export const PreDisasterRisk: React.FC<PreDisasterRiskProps> = ({ weather }) => {
  const [rainfall, setRainfall] = useState<number>(45);
  const [wind, setWind] = useState<number>(65);
  const [riverLevel, setRiverLevel] = useState<number>(3.2); // Environmental observation only
  const [prediction, setPrediction] = useState<RiskPrediction | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const runPrediction = async (rainVal: number, windVal: number, sourceLabel = 'SIMULATION') => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.predictRisk(rainVal, windVal, sourceLabel);
      setPrediction(res);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial prediction on load
    runPrediction(rainfall, wind, 'SIMULATION');
  }, []);

  const handleApplyLiveWeather = () => {
    if (weather) {
      const liveRain = weather.precipitation_24h ?? weather.precipitation_now ?? 15;
      const liveWind = weather.windspeed ?? 30;
      setRainfall(Math.round(liveRain));
      setWind(Math.round(liveWind));
      runPrediction(liveRain, liveWind, 'LIVE');
    }
  };

  return (
    <div className="space-y-5 font-mono">
      {/* Top Banner */}
      <div className="p-4 rounded bg-[#111827] border border-[#1F2937] flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <CloudLightning className="w-5 h-5 text-sky-400" />
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Pre-Disaster Hazard & Risk Intelligence
            </h2>
            <SourceBadge source="MODEL GENERATED XGBoost" />
          </div>
          <p className="text-xs text-slate-400">
            Trained on Odisha Daily Rainfall & IBTrACS Historical Cyclone Records with SHAP TreeExplainer.
          </p>
        </div>

        {weather && (
          <button
            onClick={handleApplyLiveWeather}
            className="flex items-center gap-2 px-3 py-1.5 rounded bg-sky-950/60 hover:bg-sky-900/60 border border-sky-600/50 text-sky-300 text-xs transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Load Live Weather ({weather.temperature}°C, {weather.windspeed} km/h)</span>
          </button>
        )}
      </div>

      {/* Grid: Simulator Controls & AI Prediction Card */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Controls Column (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-4 rounded bg-[#111827] border border-[#1F2937] space-y-4">
            <div className="flex items-center justify-between border-b border-[#1F2937] pb-2">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
                <Sliders className="w-4 h-4 text-sky-400" />
                <span>ENVIRONMENTAL TELEMETRY INPUTS</span>
              </div>
              <SourceBadge source="SIMULATION" short={true} />
            </div>

            {/* Slider 1: Rainfall */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300">Daily Rainfall:</span>
                <span className="text-sky-400 font-bold">{rainfall} mm</span>
              </div>
              <input
                type="range"
                min="0"
                max="350"
                step="5"
                value={rainfall}
                onChange={(e) => setRainfall(Number(e.target.value))}
                className="w-full accent-sky-400 bg-slate-800 rounded h-1.5 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-500">
                <span>0 mm (Dry)</span>
                <span>150 mm (Heavy)</span>
                <span>350 mm (Extreme)</span>
              </div>
            </div>

            {/* Slider 2: Wind Speed */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300">Cyclone Sustained Wind:</span>
                <span className="text-sky-400 font-bold">{wind} km/h</span>
              </div>
              <input
                type="range"
                min="0"
                max="250"
                step="5"
                value={wind}
                onChange={(e) => setWind(Number(e.target.value))}
                className="w-full accent-sky-400 bg-slate-800 rounded h-1.5 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-500">
                <span>0 km/h (Calm)</span>
                <span>90 km/h (Gale)</span>
                <span>250 km/h (Super Cyclone)</span>
              </div>
            </div>

            {/* River Level (Context Only) */}
            <div className="p-3 rounded bg-[#161E2E] border border-[#1F2937] space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300">River Gauge Level (Mahanadi River):</span>
                <span className="text-amber-300 font-bold">{riverLevel} m</span>
              </div>
              <input
                type="range"
                min="0"
                max="12"
                step="0.2"
                value={riverLevel}
                onChange={(e) => setRiverLevel(Number(e.target.value))}
                className="w-full accent-amber-400 bg-slate-800 rounded h-1.5 cursor-pointer"
              />
              <p className="text-[10px] text-slate-400 mt-1">
                ℹ️ <em>River Level is logged as local environmental context. The trained XGBoost model uses Rainfall and Cyclone Wind features.</em>
              </p>
            </div>

            <button
              onClick={() => runPrediction(rainfall, wind, 'SIMULATION')}
              disabled={loading}
              className="w-full py-2.5 rounded bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs transition-colors flex items-center justify-center gap-2 shadow-lg shadow-sky-950/50 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>COMPUTING INFERENCE & SHAP...</span>
                </>
              ) : (
                <>
                  <Cpu className="w-3.5 h-3.5" />
                  <span>RUN XGBOOST RISK MODEL</span>
                </>
              )}
            </button>
          </div>

          {/* Model Architecture Specs */}
          <div className="p-4 rounded bg-[#111827] border border-[#1F2937] text-xs space-y-2.5">
            <div className="text-slate-200 font-bold uppercase tracking-wider border-b border-[#1F2937] pb-1.5">
              Model Training Schema
            </div>
            <div className="space-y-1.5 text-[11px] text-slate-400">
              <div className="flex justify-between">
                <span>Model Type:</span>
                <span className="text-slate-200">XGBoost Regressor</span>
              </div>
              <div className="flex justify-between">
                <span>Feature: Daily Rainfall:</span>
                <span className="text-slate-200">{rainfall} mm</span>
              </div>
              <div className="flex justify-between">
                <span>Feature: WMO_WIND:</span>
                <span className="text-slate-200">{wind} km/h</span>
              </div>
              <div className="flex justify-between">
                <span>Synthetic Lag 1-Day:</span>
                <span className="text-slate-200">{(rainfall * 0.8).toFixed(1)} mm</span>
              </div>
              <div className="flex justify-between">
                <span>Synthetic Lag 3-Day:</span>
                <span className="text-slate-200">{(rainfall * 0.7).toFixed(1)} mm</span>
              </div>
              <div className="flex justify-between">
                <span>Synthetic Wind Lag 1-Day:</span>
                <span className="text-slate-200">{(wind * 0.9).toFixed(1)} km/h</span>
              </div>
            </div>
          </div>
        </div>

        {/* Prediction Results Column (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {error ? (
            <div className="p-4 rounded bg-rose-950/30 border border-rose-900/50 text-rose-400 text-xs">
              Error executing risk model: {error}
            </div>
          ) : prediction ? (
            <>
              {/* Primary Risk Output Card */}
              <div className="p-5 rounded bg-[#111827] border border-[#1F2937] space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                    OPERATIONAL HAZARD CLASSIFICATION
                  </span>
                  <SourceBadge source={prediction.data_label} />
                </div>

                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded bg-[#0B0F17] border border-[#1F2937]">
                  <div>
                    <span className="text-[11px] text-slate-400 uppercase tracking-widest block mb-1">
                      RISK SCORE
                    </span>
                    <div className="flex items-baseline gap-2">
                      <span
                        className="text-4xl font-bold tracking-tight"
                        style={{ color: prediction.risk_color }}
                      >
                        {prediction.risk_score.toFixed(1)}
                      </span>
                      <span className="text-xs text-slate-500">/ 100</span>
                    </div>
                  </div>

                  <div className="text-left sm:text-right">
                    <span
                      className="inline-block px-3 py-1 rounded text-sm font-bold tracking-wider mb-1"
                      style={{
                        backgroundColor: `${prediction.risk_color}20`,
                        color: prediction.risk_color,
                        border: `1px solid ${prediction.risk_color}40`,
                      }}
                    >
                      {prediction.risk_level} RISK
                    </span>
                    <div className="text-[11px] text-slate-400">
                      Raw model output: {prediction.raw_score.toFixed(2)}
                    </div>
                  </div>
                </div>

                {/* 70% Operational Threshold Indicator */}
                <div className="p-3 rounded bg-[#161E2E] border border-[#1F2937] flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <AlertTriangle
                      className={`w-4 h-4 ${
                        prediction.operational_threshold_crossed ? 'text-rose-400' : 'text-emerald-400'
                      }`}
                    />
                    <span className="text-slate-300">OPERATIONAL THRESHOLD (70.0):</span>
                  </div>
                  <span
                    className={`font-bold ${
                      prediction.operational_threshold_crossed
                        ? 'text-rose-400'
                        : 'text-emerald-400'
                    }`}
                  >
                    {prediction.operational_threshold_crossed
                      ? 'CRITICAL THRESHOLD BREACHED — EVACUATION PROTOCOL'
                      : 'BELOW CRITICAL EVACUATION THRESHOLD'}
                  </span>
                </div>

                {/* Calibration Notice */}
                <div className="flex items-start gap-2 text-[11px] text-slate-400 bg-slate-900/40 p-2.5 rounded border border-slate-800">
                  <Info className="w-4 h-4 text-sky-400 flex-shrink-0 mt-0.5" />
                  <p>{prediction.calibrated_note}</p>
                </div>
              </div>

              {/* SHAP Feature Contribution Waterfall / Breakdown */}
              <div className="p-5 rounded bg-[#111827] border border-[#1F2937] space-y-4">
                <div className="flex items-center justify-between border-b border-[#1F2937] pb-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
                    <BarChart3 className="w-4 h-4 text-emerald-400" />
                    <span>SHAP EXPLAINABILITY — FEATURE ATTRIBUTIONS</span>
                  </div>
                  <span className="text-[10px] text-slate-500">
                    Base Value: {prediction.base_value?.toFixed(2) || '12.40'} pts
                  </span>
                </div>

                <p className="text-[11px] text-slate-400">
                  Values indicate marginal impact on risk score points (not percentages). Positive values increase risk; negative values suppress risk.
                </p>

                <div className="space-y-2.5">
                  {prediction.shap_contributions.map((shap, idx) => {
                    const isPositive = shap.contribution >= 0;
                    const barWidth = Math.min(100, Math.abs(shap.contribution) * 8);

                    return (
                      <div key={idx} className="p-2 rounded bg-[#161E2E] border border-[#1F2937]/70 text-xs">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-slate-300 font-semibold">{shap.feature}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-slate-500 text-[10px]">val: {shap.value}</span>
                            <span
                              className={`font-mono font-bold ${
                                isPositive ? 'text-rose-400' : 'text-emerald-400'
                              }`}
                            >
                              {isPositive ? '+' : ''}
                              {shap.contribution.toFixed(3)} pts
                            </span>
                          </div>
                        </div>

                        {/* Visual Bar */}
                        <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              isPositive ? 'bg-rose-500' : 'bg-emerald-500'
                            }`}
                            style={{ width: `${Math.max(5, barWidth)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          ) : (
            <div className="p-8 rounded bg-[#111827] border border-[#1F2937] text-center text-slate-500 text-xs">
              INITIALIZING MODEL TELEMETRY...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
