import L from 'leaflet';

export type BasemapType = 'tactical-dark' | 'satellite' | 'streets';

export interface BasemapOption {
  id: BasemapType;
  label: string;
  description: string;
}

export const BASEMAP_OPTIONS: BasemapOption[] = [
  { id: 'tactical-dark', label: 'TACTICAL DARK', description: 'High-contrast dark canvas for incident monitoring' },
  { id: 'satellite', label: 'SATELLITE HYBRID', description: 'High-resolution optical satellite imagery' },
  { id: 'streets', label: 'STREETS (OSM)', description: 'OpenStreetMap road and building topography' },
];

/**
 * Creates Leaflet tile layers for the given basemap type.
 * Uses official, unmetered, watermark-free tile endpoints.
 */
export function createBasemapLayers(type: BasemapType = 'tactical-dark'): L.Layer[] {
  const cartoKey = (import.meta as any).env?.VITE_CARTO_API_KEY;

  if (type === 'tactical-dark') {
    if (cartoKey) {
      return [
        L.tileLayer(
          `https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png?key=${cartoKey}`,
          {
            maxZoom: 19,
            subdomains: 'abcd',
            attribution: '&copy; CartoDB, &copy; OpenStreetMap',
          }
        ),
      ];
    }

    // High-performance, unwatermarked Esri Dark Gray Canvas
    const base = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      {
        maxNativeZoom: 16,
        maxZoom: 19,
        attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
      }
    );

    const labels = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
      {
        maxNativeZoom: 16,
        maxZoom: 19,
        pane: 'tilePane',
      }
    );

    return [base, labels];
  }

  if (type === 'satellite') {
    const satellite = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      {
        maxNativeZoom: 19,
        maxZoom: 19,
        attribution: 'Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics',
      }
    );

    const labels = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
      {
        maxNativeZoom: 16,
        maxZoom: 19,
        opacity: 0.9,
      }
    );

    return [satellite, labels];
  }

  // OpenStreetMap standard streets
  return [
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }),
  ];
}
