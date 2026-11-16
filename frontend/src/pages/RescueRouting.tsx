import React, { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import { Navigation, Compass, MapPin, Truck, AlertTriangle, Send, RefreshCw, Info, CheckCircle2, Layers } from 'lucide-react';
import { Incident, RescueTeam, RouteData } from '../types';
import { api } from '../services/api';
import { SourceBadge } from '../components/status/SourceBadge';
import { BasemapType, createBasemapLayers } from '../utils/mapLayers';

interface RescueRoutingProps {
  incidents: Incident[];
  teams: RescueTeam[];
  onTeamDispatched: () => void;
}

export const RescueRouting: React.FC<RescueRoutingProps> = ({
  incidents,
  teams,
  onTeamDispatched,
}) => {
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>('');
  const [selectedTeamId, setSelectedTeamId] = useState<string>('');
  const [useAlternate, setUseAlternate] = useState<boolean>(false);
  const [routeData, setRouteData] = useState<RouteData | null>(null);
  const [calculating, setCalculating] = useState<boolean>(false);
  const [dispatching, setDispatching] = useState<boolean>(false);
  const [dispatchSuccess, setDispatchSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeBasemap, setActiveBasemap] = useState<BasemapType>('tactical-dark');

  // Map refs
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const routeLayerRef = useRef<L.LayerGroup | null>(null);
  const basemapLayersRef = useRef<L.Layer[]>([]);

  // Set initial selections
  useEffect(() => {
    if (incidents.length > 0 && !selectedIncidentId) {
      setSelectedIncidentId(incidents[0].incident_id);
    }
    if (teams.length > 0 && !selectedTeamId) {
      setSelectedTeamId(teams[0].team_id);
    }
  }, [incidents, teams]);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [20.2961, 85.8245],
      zoom: 12,
      zoomControl: false,
      attributionControl: false,
    });

    // High-performance basemap layers (unwatermarked Esri Dark / Satellite / Streets)
    const initialLayers = createBasemapLayers(activeBasemap);
    initialLayers.forEach((layer) => layer.addTo(map));
    basemapLayersRef.current = initialLayers;

    L.control.zoom({ position: 'topright' }).addTo(map);

    const routeLayer = L.layerGroup().addTo(map);
    routeLayerRef.current = routeLayer;
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update Basemap Layers dynamically when switched
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const map = mapInstanceRef.current;

    basemapLayersRef.current.forEach((layer) => {
      if (map.hasLayer(layer)) {
        map.removeLayer(layer);
      }
    });

    const newLayers = createBasemapLayers(activeBasemap);
    newLayers.forEach((layer) => {
      layer.addTo(map);
      if ((layer as any).bringToBack) {
        (layer as any).bringToBack();
      }
    });
    basemapLayersRef.current = newLayers;
  }, [activeBasemap]);

  const handleCalculateRoute = async () => {
    const inc = incidents.find((i) => i.incident_id === selectedIncidentId);
    const team = teams.find((t) => t.team_id === selectedTeamId);

    if (!inc || !team) {
      setError('Please select both a rescue team origin and incident destination.');
      return;
    }

    setCalculating(true);
    setError(null);
    setDispatchSuccess(null);

    try {
      const data = await api.calculateRoute(
        team.latitude,
        team.longitude,
        inc.latitude,
        inc.longitude,
        useAlternate
      );

      if (!data.success) {
        setError(data.error || 'OSRM failed to find a valid road path.');
        setRouteData(null);
        return;
      }

      setRouteData(data);

      // Render polyline on map
      if (routeLayerRef.current && mapInstanceRef.current && data.points && data.points.length > 0) {
        routeLayerRef.current.clearLayers();

        // 1. Origin Marker
        const originMarker = L.marker([team.latitude, team.longitude], {
          icon: L.divIcon({
            className: 'origin-marker',
            html: `<div style="background-color: #38BDF8; color: black; font-weight: bold; font-family: monospace; font-size: 11px; padding: 2px 6px; border-radius: 4px; border: 2px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.8);">ORIGIN: ${team.team_id}</div>`,
            iconSize: [80, 20],
            iconAnchor: [40, 10],
          }),
        });
        routeLayerRef.current.addLayer(originMarker);

        // 2. Destination Marker
        const destMarker = L.marker([inc.latitude, inc.longitude], {
          icon: L.divIcon({
            className: 'dest-marker',
            html: `<div style="background-color: #EF4444; color: white; font-weight: bold; font-family: monospace; font-size: 11px; padding: 2px 6px; border-radius: 4px; border: 2px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.8);">INCIDENT: ${inc.disaster_type}</div>`,
            iconSize: [120, 20],
            iconAnchor: [60, 10],
          }),
        });
        routeLayerRef.current.addLayer(destMarker);

        // 3. OSRM Polyline
        const latlngs: L.LatLngExpression[] = data.points.map((p) => [p[0], p[1]]);
        const polyline = L.polyline(latlngs, {
          color: useAlternate ? '#F59E0B' : '#38BDF8',
          weight: 4,
          opacity: 0.9,
          dashArray: useAlternate ? '8, 8' : undefined,
        });
        routeLayerRef.current.addLayer(polyline);

        // Fit bounds
        mapInstanceRef.current.fitBounds(polyline.getBounds(), { padding: [50, 50] });
      }
    } catch (err: any) {
      setError(`Routing error: ${err.message}`);
    } finally {
      setCalculating(false);
    }
  };

  const handleDispatch = async () => {
    if (!selectedTeamId || !selectedIncidentId) return;
    setDispatching(true);
    try {
      await api.dispatchTeam(selectedTeamId, selectedIncidentId);
      setDispatchSuccess(`Team ${selectedTeamId} successfully ordered to deploy to ${selectedIncidentId}.`);
      onTeamDispatched();
    } catch (err: any) {
      setError(`Dispatch failed: ${err.message}`);
    } finally {
      setDispatching(false);
    }
  };

  const currentInc = incidents.find((i) => i.incident_id === selectedIncidentId);
  const currentTeam = teams.find((t) => t.team_id === selectedTeamId);

  return (
    <div className="space-y-5 font-mono">
      {/* Top Banner */}
      <div className="p-4 rounded bg-[#111827] border border-[#1F2937] flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Navigation className="w-5 h-5 text-sky-400" />
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Emergency Rescue Routing & Deployment
            </h2>
            <SourceBadge source="LIVE OSRM" />
          </div>
          <p className="text-xs text-slate-400">
            Open Source Routing Machine (OSRM) road network navigation engine.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="px-2.5 py-1 rounded bg-[#161E2E] border border-[#1F2937] text-slate-300">
            ENGINE: <strong>OSRM v5</strong>
          </span>
        </div>
      </div>

      {/* Main Grid: Controls & Route Details vs Interactive Map */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column: Route Controls (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-5 rounded bg-[#111827] border border-[#1F2937] space-y-4">
            <div className="flex items-center justify-between border-b border-[#1F2937] pb-2">
              <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                TACTICAL ROUTE CONFIGURATION
              </span>
              <SourceBadge source="OSRM" short={true} />
            </div>

            {/* Team Origin Selector */}
            <div className="space-y-1.5">
              <label className="text-xs text-slate-300 flex items-center gap-1.5">
                <Truck className="w-3.5 h-3.5 text-sky-400" />
                <span>Origin (Rescue Team Base):</span>
              </label>
              <select
                value={selectedTeamId}
                onChange={(e) => setSelectedTeamId(e.target.value)}
                className="w-full px-3 py-2 rounded bg-[#0B0F17] border border-[#1F2937] text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              >
                {teams.map((t) => (
                  <option key={t.team_id} value={t.team_id}>
                    {t.name} [{t.status}] — ({t.latitude.toFixed(2)}, {t.longitude.toFixed(2)})
                  </option>
                ))}
              </select>
            </div>

            {/* Incident Destination Selector */}
            <div className="space-y-1.5">
              <label className="text-xs text-slate-300 flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-rose-400" />
                <span>Destination (Target Incident):</span>
              </label>
              <select
                value={selectedIncidentId}
                onChange={(e) => setSelectedIncidentId(e.target.value)}
                className="w-full px-3 py-2 rounded bg-[#0B0F17] border border-[#1F2937] text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              >
                {incidents.map((inc) => (
                  <option key={inc.incident_id} value={inc.incident_id}>
                    {inc.incident_id} — {inc.disaster_type} ({inc.location})
                  </option>
                ))}
              </select>
            </div>

            {/* Alternate Route Checkbox */}
            <div className="flex items-center gap-2 p-2.5 rounded bg-[#161E2E] border border-[#1F2937] text-xs">
              <input
                type="checkbox"
                id="altRoute"
                checked={useAlternate}
                onChange={(e) => setUseAlternate(e.target.checked)}
                className="rounded accent-sky-400"
              />
              <label htmlFor="altRoute" className="text-slate-300 cursor-pointer">
                Compute Alternate Waypoint Path (explore secondary corridor)
              </label>
            </div>

            {/* Calculate Button */}
            <button
              onClick={handleCalculateRoute}
              disabled={calculating || !selectedIncidentId || !selectedTeamId}
              className="w-full py-2.5 rounded bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {calculating ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>CALCULATING OSRM ROAD ROUTE...</span>
                </>
              ) : (
                <>
                  <Compass className="w-3.5 h-3.5" />
                  <span>CALCULATE ROUTE</span>
                </>
              )}
            </button>
          </div>

          {/* Route Telemetry Card */}
          {routeData && (
            <div className="p-5 rounded bg-[#111827] border border-[#1F2937] space-y-4">
              <div className="flex items-center justify-between border-b border-[#1F2937] pb-2">
                <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                  ROUTE TELEMETRY SUMMARY
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] bg-sky-950 text-sky-400 border border-sky-800">
                  {routeData.route_type}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded bg-[#0B0F17] border border-[#1F2937]">
                  <span className="text-[10px] text-slate-400 uppercase block mb-1">
                    TOTAL DISTANCE
                  </span>
                  <div className="text-xl font-bold text-slate-100 font-mono">
                    {routeData.distance_km} <span className="text-xs text-slate-500">km</span>
                  </div>
                </div>

                <div className="p-3 rounded bg-[#0B0F17] border border-[#1F2937]">
                  <span className="text-[10px] text-slate-400 uppercase block mb-1">
                    ESTIMATED TRANSIT TIME
                  </span>
                  <div className="text-xl font-bold text-sky-300 font-mono">
                    {routeData.duration_min} <span className="text-xs text-slate-500">min</span>
                  </div>
                </div>
              </div>

              {/* Crucial Hazard Disclaimer as requested in user prompt */}
              <div className="p-3 rounded bg-amber-950/20 border border-amber-900/40 text-[11px] text-amber-300/90 space-y-1">
                <div className="flex items-center gap-1.5 font-bold">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>STANDARD ROAD ROUTING</span>
                </div>
                <p className="text-[10px] text-slate-400">
                  {routeData.disclaimer}
                </p>
              </div>

              {/* Dispatch Action */}
              <button
                onClick={handleDispatch}
                disabled={dispatching || currentTeam?.status === 'DISPATCHED'}
                className="w-full py-2.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {dispatching ? (
                  <span>CONFIRMING ORDERS...</span>
                ) : currentTeam?.status === 'DISPATCHED' ? (
                  <span>UNIT ALREADY DISPATCHED</span>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    <span>DISPATCH {currentTeam?.name} TO INCIDENT</span>
                  </>
                )}
              </button>

              {dispatchSuccess && (
                <div className="p-2.5 rounded bg-emerald-950/40 border border-emerald-800 text-emerald-400 text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                  <span>{dispatchSuccess}</span>
                </div>
              )}
            </div>
          )}

          {error && (
            <div className="p-3 rounded bg-rose-950/40 border border-rose-800 text-rose-400 text-xs">
              {error}
            </div>
          )}
        </div>

        {/* Right Column: Route Leaflet Map (7 cols) */}
        <div className="lg:col-span-7 h-[560px] rounded bg-[#111827] border border-[#1F2937] overflow-hidden relative">
          <div className="absolute top-3 left-3 z-[1000] px-3 py-1.5 rounded bg-[#0B0F17]/90 backdrop-blur border border-[#1F2937] text-xs font-mono flex items-center gap-2">
            <Compass className="w-3.5 h-3.5 text-sky-400" />
            <span className="font-semibold text-slate-200">OSRM ROUTE MAP</span>
            {routeData && (
              <span className="text-emerald-400">| {routeData.distance_km} km ({routeData.duration_min} min)</span>
            )}
          </div>

          {/* Interactive Basemap Layer Selector */}
          <div className="absolute bottom-3 left-3 z-[1000] flex items-center gap-1 p-1 rounded bg-[#0B0F17]/95 backdrop-blur border border-[#1F2937] text-xs font-mono shadow-xl">
            <div className="flex items-center gap-1.5 px-2 py-0.5 text-[10px] text-slate-400 font-semibold border-r border-[#1F2937]">
              <Layers className="w-3 h-3 text-sky-400" />
              <span>LAYER:</span>
            </div>
            <button
              type="button"
              onClick={() => setActiveBasemap('tactical-dark')}
              className={`px-2 py-0.5 rounded text-[10px] transition-all ${
                activeBasemap === 'tactical-dark'
                  ? 'bg-sky-500/20 text-sky-300 border border-sky-500/50 font-bold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              TACTICAL DARK
            </button>
            <button
              type="button"
              onClick={() => setActiveBasemap('satellite')}
              className={`px-2 py-0.5 rounded text-[10px] flex items-center gap-1 transition-all ${
                activeBasemap === 'satellite'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 font-bold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${activeBasemap === 'satellite' ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
              SATELLITE
            </button>
            <button
              type="button"
              onClick={() => setActiveBasemap('streets')}
              className={`px-2 py-0.5 rounded text-[10px] transition-all ${
                activeBasemap === 'streets'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50 font-bold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              STREETS
            </button>
          </div>

          <div ref={mapContainerRef} className="w-full h-full" />
        </div>
      </div>
    </div>
  );
};
