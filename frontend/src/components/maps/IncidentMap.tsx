import React, { useEffect, useRef, useState, useMemo } from 'react';
import L from 'leaflet';
import { Incident, RescueTeam } from '../../types';
import { Layers, MapPin, Globe, Compass, Flame, Waves, Zap, Wind } from 'lucide-react';
import { BasemapType, createBasemapLayers } from '../../utils/mapLayers';

interface IncidentMapProps {
  incidents: Incident[];
  teams?: RescueTeam[];
  selectedIncident?: Incident | null;
  onSelectIncident?: (inc: Incident) => void;
  center?: [number, number];
  zoom?: number;
}

function getDisasterVisuals(type: string, severity: string) {
  const t = (type || '').toUpperCase();
  if (t.includes('FIRE') || t.includes('WILDFIRE')) {
    return {
      fillColor: '#FF5722',
      glowColor: '#F4511E',
      iconEmoji: '🔥',
      label: 'WILDFIRE',
    };
  }
  if (t.includes('FLOOD')) {
    return {
      fillColor: '#06B6D4',
      glowColor: '#0891B2',
      iconEmoji: '🌊',
      label: 'FLOOD',
    };
  }
  if (t.includes('EARTHQUAKE')) {
    return {
      fillColor: '#EAB308',
      glowColor: '#CA8A04',
      iconEmoji: '⚡',
      label: 'EARTHQUAKE',
    };
  }
  if (t.includes('CYCLONE') || t.includes('STORM') || t.includes('TYPHOON')) {
    return {
      fillColor: '#A855F7',
      glowColor: '#9333EA',
      iconEmoji: '🌀',
      label: 'CYCLONE',
    };
  }
  if (t.includes('DROUGHT')) {
    return {
      fillColor: '#F59E0B',
      glowColor: '#D97706',
      iconEmoji: '🏜️',
      label: 'DROUGHT',
    };
  }
  if (severity === 'CRITICAL') {
    return {
      fillColor: '#EF4444',
      glowColor: '#DC2626',
      iconEmoji: '🚨',
      label: type,
    };
  }
  return {
    fillColor: '#38BDF8',
    glowColor: '#0284C7',
    iconEmoji: '📍',
    label: type,
  };
}

export const IncidentMap: React.FC<IncidentMapProps> = ({
  incidents,
  teams = [],
  selectedIncident,
  onSelectIncident,
  center = [20.2961, 85.8245],
  zoom = 6,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);
  const basemapLayersRef = useRef<L.Layer[]>([]);
  const [activeBasemap, setActiveBasemap] = useState<BasemapType>('tactical-dark');

  // Breakdown of disaster types
  const counts = useMemo(() => {
    let wildfire = 0;
    let flood = 0;
    let earthquake = 0;
    let cyclone = 0;

    incidents.forEach((inc) => {
      const t = (inc.disaster_type || '').toUpperCase();
      if (t.includes('FIRE') || t.includes('WILDFIRE')) wildfire++;
      else if (t.includes('FLOOD')) flood++;
      else if (t.includes('EARTHQUAKE')) earthquake++;
      else if (t.includes('CYCLONE') || t.includes('STORM') || t.includes('TYPHOON')) cyclone++;
    });

    return { wildfire, flood, earthquake, cyclone };
  }, [incidents]);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: center,
      zoom: zoom,
      zoomControl: false,
      attributionControl: false,
    });

    // High-performance basemap layers
    const initialLayers = createBasemapLayers(activeBasemap);
    initialLayers.forEach((layer) => layer.addTo(map));
    basemapLayersRef.current = initialLayers;

    // Zoom control at top-right
    L.control.zoom({ position: 'topright' }).addTo(map);

    // Layer group for dynamic markers
    const markersLayer = L.layerGroup().addTo(map);
    markersLayerRef.current = markersLayer;
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

  // Update Markers
  useEffect(() => {
    if (!markersLayerRef.current || !mapInstanceRef.current) return;
    markersLayerRef.current.clearLayers();

    // 1. Render Incidents
    incidents.forEach((inc) => {
      if (inc.latitude == null || inc.longitude == null) return;

      const isCritical = inc.severity === 'CRITICAL';
      const visuals = getDisasterVisuals(inc.disaster_type, inc.severity);

      // Custom pulsing HTML marker with disaster icon
      const markerHtml = `
        <div style="position: relative; width: 26px; height: 26px; cursor: pointer; display: flex; align-items: center; justify-content: center;">
          <div style="
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background-color: ${visuals.fillColor};
            opacity: ${isCritical ? '0.75' : '0.35'};
            animation: ${isCritical ? 'ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite' : 'none'};
          "></div>
          <div style="
            position: absolute;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background-color: ${visuals.fillColor};
            border: 2px solid #0B0F17;
            box-shadow: 0 0 10px ${visuals.glowColor};
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
          ">
            <span>${visuals.iconEmoji}</span>
          </div>
        </div>
      `;

      const customIcon = L.divIcon({
        className: 'custom-incident-marker',
        html: markerHtml,
        iconSize: [26, 26],
        iconAnchor: [13, 13],
      });

      const marker = L.marker([inc.latitude, inc.longitude], { icon: customIcon });

      const popupContent = `
        <div style="
          background-color: #111827;
          color: #F1F5F9;
          font-family: monospace;
          font-size: 11px;
          padding: 8px 12px;
          border-radius: 6px;
          border: 1px solid #1F2937;
          min-width: 220px;
        ">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span style="font-weight: bold; color: ${visuals.fillColor}; font-size: 12px;">
              ${visuals.iconEmoji} ${inc.disaster_type}
            </span>
            <span style="padding: 1px 4px; border-radius: 3px; background-color: #1F2937; font-size: 10px; color: #94A3B8;">
              ${inc.severity}
            </span>
          </div>
          <div style="color: #E2E8F0; font-weight: bold; margin-bottom: 4px;">${inc.location}</div>
          ${inc.description ? `<div style="color: #94A3B8; font-size: 10px; margin-bottom: 6px; line-height: 1.4;">${inc.description}</div>` : ''}
          <div style="border-top: 1px solid #1F2937; padding-top: 6px; line-height: 1.5;">
            <div>SOURCE: <strong>${inc.source}</strong></div>
            <div>STATUS: <span style="color: #10B981;">${inc.status}</span></div>
            <div>PEOPLE AT RISK: <strong>${inc.people_at_risk?.toLocaleString() || 0}</strong></div>
            <div>ASSIGNED: ${inc.assigned_team || 'Unassigned'}</div>
            <div style="font-size: 10px; color: #64748B; margin-top: 4px;">ID: ${inc.incident_id}</div>
          </div>
        </div>
      `;

      marker.bindPopup(popupContent, {
        className: 'dark-leaflet-popup',
        closeButton: true,
      });

      marker.on('click', () => {
        if (onSelectIncident) onSelectIncident(inc);
      });

      markersLayerRef.current?.addLayer(marker);
    });

    // 2. Render Rescue Teams
    teams.forEach((team) => {
      if (team.latitude == null || team.longitude == null) return;

      const teamHtml = `
        <div style="
          background-color: #0284C7;
          color: white;
          padding: 2px 5px;
          border-radius: 4px;
          font-family: monospace;
          font-size: 10px;
          font-weight: bold;
          border: 1px solid #38BDF8;
          box-shadow: 0 2px 6px rgba(0,0,0,0.5);
          white-space: nowrap;
        ">
          🚑 ${team.team_id}
        </div>
      `;

      const teamIcon = L.divIcon({
        className: 'team-marker',
        html: teamHtml,
        iconSize: [50, 20],
        iconAnchor: [25, 10],
      });

      const teamMarker = L.marker([team.latitude, team.longitude], { icon: teamIcon });
      teamMarker.bindPopup(`
        <div style="background-color: #111827; color: #F1F5F9; font-family: monospace; font-size: 11px; padding: 6px 10px; border-radius: 4px;">
          <div style="font-weight: bold; color: #38BDF8;">${team.name}</div>
          <div>STATUS: ${team.status}</div>
          <div>CAPACITY: ${team.capacity} personnel</div>
          <div>ASSIGNMENT: ${team.current_assignment || 'Standby'}</div>
        </div>
      `);

      markersLayerRef.current?.addLayer(teamMarker);
    });
  }, [incidents, teams, onSelectIncident]);

  // Center on selected incident if provided
  useEffect(() => {
    if (selectedIncident && mapInstanceRef.current && selectedIncident.latitude && selectedIncident.longitude) {
      mapInstanceRef.current.setView([selectedIncident.latitude, selectedIncident.longitude], 10, {
        animate: true,
      });
    }
  }, [selectedIncident]);

  // Navigation handlers
  const handleFitGlobal = () => {
    if (!mapInstanceRef.current || incidents.length === 0) return;
    const validCoords = incidents
      .filter((i) => i.latitude != null && i.longitude != null)
      .map((i) => [i.latitude, i.longitude] as [number, number]);

    if (validCoords.length > 0) {
      const bounds = L.latLngBounds(validCoords);
      mapInstanceRef.current.fitBounds(bounds, { padding: [40, 40] });
    }
  };

  const handleFocusOdisha = () => {
    if (!mapInstanceRef.current) return;
    mapInstanceRef.current.setView([20.2961, 85.8245], 7, { animate: true });
  };

  return (
    <div className="relative w-full h-full min-h-[420px] rounded bg-[#111827] border border-[#1F2937] overflow-hidden flex flex-col">
      {/* Map Header Overlay */}
      <div className="absolute top-3 left-3 z-[1000] flex flex-wrap items-center gap-2 px-3 py-1.5 rounded bg-[#0B0F17]/95 backdrop-blur border border-[#1F2937] text-xs font-mono shadow-xl">
        <MapPin className="w-3.5 h-3.5 text-sky-400" />
        <span className="font-semibold text-slate-200">TACTICAL DISASTER MAP</span>
        <span className="text-slate-600">|</span>
        <span className="text-sky-400 font-bold">{incidents.length} PLOTTED</span>

        {/* Quick disaster breakdown tags */}
        {counts.wildfire > 0 && (
          <span className="px-1.5 py-0.2 rounded bg-orange-950/80 text-orange-300 border border-orange-800 text-[10px]">
            🔥 {counts.wildfire} Wildfires
          </span>
        )}
        {counts.flood > 0 && (
          <span className="px-1.5 py-0.2 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-800 text-[10px]">
            🌊 {counts.flood} Floods
          </span>
        )}
        {counts.earthquake > 0 && (
          <span className="px-1.5 py-0.2 rounded bg-amber-950/80 text-amber-300 border border-amber-800 text-[10px]">
            ⚡ {counts.earthquake} Quakes
          </span>
        )}

        {/* Quick Zoom Presets */}
        <div className="flex items-center gap-1 ml-2 border-l border-[#1F2937] pl-2">
          <button
            type="button"
            onClick={handleFitGlobal}
            className="px-2 py-0.5 rounded bg-sky-950 text-sky-300 hover:bg-sky-900 border border-sky-800 text-[10px] flex items-center gap-1 transition-colors"
            title="Fit map view to all plotted global alerts"
          >
            <Globe className="w-3 h-3" />
            <span>GLOBAL ALERTS</span>
          </button>
          <button
            type="button"
            onClick={handleFocusOdisha}
            className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700 text-[10px] flex items-center gap-1 transition-colors"
            title="Focus map on Odisha / Bay of Bengal monitoring sector"
          >
            <Compass className="w-3 h-3 text-sky-400" />
            <span>ODISHA SECTOR</span>
          </button>
        </div>
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

      {/* Actual Leaflet Map Canvas */}
      <div ref={mapContainerRef} className="w-full h-full flex-1" />
    </div>
  );
};
