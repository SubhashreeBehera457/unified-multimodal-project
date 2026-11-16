import {
  DashboardData,
  Incident,
  WeatherData,
  SystemHealthData,
  RiskPrediction,
  MisinfoAnalysis,
  VisionAnalysis,
  FusionResult,
  RouteData,
  RescueTeam,
  SocialReport,
} from '../types';

const API_BASE = '/api';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMsg = `HTTP Error ${res.status}: ${res.statusText}`;
    try {
      const json = await res.json();
      if (json.detail) {
        errorMsg = typeof json.detail === 'string' ? json.detail : JSON.stringify(json.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errorMsg);
  }
  return res.json();
}

export const api = {
  // System Health
  async getSystemHealth(): Promise<SystemHealthData> {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse<SystemHealthData>(res);
  },

  // Dashboard Overview
  async getDashboard(): Promise<DashboardData> {
    const res = await fetch(`${API_BASE}/dashboard`);
    return handleResponse<DashboardData>(res);
  },

  // Incidents
  async getIncidents(status?: string, severity?: string): Promise<Incident[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (severity) params.append('severity', severity);
    const url = `${API_BASE}/incidents${params.toString() ? `?${params.toString()}` : ''}`;
    const res = await fetch(url);
    return handleResponse<Incident[]>(res);
  },

  async createIncident(data: {
    disaster_type: string;
    severity: string;
    latitude: number;
    longitude: number;
    location: string;
    people_at_risk: number;
    description: string;
    source?: string;
  }): Promise<Incident> {
    const res = await fetch(`${API_BASE}/incidents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<Incident>(res);
  },

  async dispatchTeam(team_id: string, incident_id: string): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/incidents/dispatch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ team_id, incident_id }),
    });
    return handleResponse<{ success: boolean; message: string }>(res);
  },

  // Weather Telemetry
  async getWeather(lat?: number, lon?: number, forceRefresh = false): Promise<WeatherData> {
    const params = new URLSearchParams();
    if (lat !== undefined) params.append('lat', lat.toString());
    if (lon !== undefined) params.append('lon', lon.toString());
    if (forceRefresh) params.append('force_refresh', 'true');
    const res = await fetch(`${API_BASE}/weather?${params.toString()}`);
    return handleResponse<WeatherData>(res);
  },

  // GDACS Alerts
  async getGDACS(maxEvents = 250, forceRefresh = false): Promise<{
    source: string;
    fetched_at: string;
    total_events: number;
    incidents: Incident[];
    error?: string | null;
  }> {
    const params = new URLSearchParams({
      max_events: maxEvents.toString(),
      sync_to_incidents: 'true',
    });
    if (forceRefresh) params.append('force_refresh', 'true');
    const res = await fetch(`${API_BASE}/gdacs?${params.toString()}`);
    return handleResponse(res);
  },

  // XGBoost Risk Model & SHAP
  async getLatestRisk(): Promise<RiskPrediction> {
    const res = await fetch(`${API_BASE}/risk/latest`);
    return handleResponse<RiskPrediction>(res);
  },

  async predictRisk(rainfall_mm: number, wind_kmh: number, source = 'SIMULATION'): Promise<RiskPrediction> {
    const res = await fetch(`${API_BASE}/risk/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rainfall_mm, wind_kmh, source }),
    });
    return handleResponse<RiskPrediction>(res);
  },

  // DistilBERT Misinformation & NLP
  async analyzeMisinformation(text: string, source = 'MANUAL_INPUT'): Promise<MisinfoAnalysis> {
    const res = await fetch(`${API_BASE}/misinformation/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, source }),
    });
    return handleResponse<MisinfoAnalysis>(res);
  },

  // ResNet-50 Vision
  async analyzeVision(files: File[]): Promise<VisionAnalysis> {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    const res = await fetch(`${API_BASE}/vision/analyze`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<VisionAnalysis>(res);
  },

  // Decision-Level Multimodal Fusion
  async combineModalities(data: {
    vision_score?: number | null;
    vision_label?: string | null;
    text_prob_genuine?: number | null;
    text_label?: string | null;
  }): Promise<FusionResult> {
    const res = await fetch(`${API_BASE}/fusion/combine`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<FusionResult>(res);
  },

  // OSRM Rescue Routing
  async calculateRoute(
    start_lat: number,
    start_lon: number,
    end_lat: number,
    end_lon: number,
    alternate = false
  ): Promise<RouteData> {
    const res = await fetch(`${API_BASE}/routing/calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        start_lat,
        start_lon,
        end_lat,
        end_lon,
        alternate,
      }),
    });
    return handleResponse<RouteData>(res);
  },

  // Social & News
  async getGDELTNews(maxResults = 15): Promise<{
    source: string;
    reports: SocialReport[];
    error?: string | null;
  }> {
    const res = await fetch(`${API_BASE}/social/gdelt?max_results=${maxResults}`);
    return handleResponse(res);
  },

  async getXReports(): Promise<{
    status: string;
    source: string;
    message?: string;
    reports: SocialReport[];
  }> {
    const res = await fetch(`${API_BASE}/social/x`);
    return handleResponse(res);
  },

  async getRedditReports(): Promise<{
    status: string;
    source: string;
    message?: string;
    reports: SocialReport[];
  }> {
    const res = await fetch(`${API_BASE}/social/reddit`);
    return handleResponse(res);
  },

  async getAllReports(): Promise<{ count: number; reports: SocialReport[] }> {
    const res = await fetch(`${API_BASE}/social/reports`);
    return handleResponse(res);
  },

  // Rescue Teams
  async getTeams(): Promise<RescueTeam[]> {
    const res = await fetch(`${API_BASE}/teams`);
    return handleResponse<RescueTeam[]>(res);
  },
};
