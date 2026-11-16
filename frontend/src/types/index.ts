export type SourceStatus = 'LIVE' | 'MODEL GENERATED' | 'SIMULATION' | 'DATA SOURCE UNAVAILABLE' | 'GDACS' | 'OSRM';

export interface ServiceHealth {
  status: 'ONLINE' | 'DEGRADED' | 'NOT CONFIGURED' | 'UNAVAILABLE';
  message?: string;
  last_checked?: string;
}

export interface SystemHealthData {
  overall_status: 'OPERATIONAL' | 'DEGRADED' | 'OFFLINE';
  timestamp: string;
  services: {
    ai_engine: ServiceHealth;
    data_pipeline: ServiceHealth;
    gdacs: ServiceHealth;
    weather: ServiceHealth;
    gdelt: ServiceHealth;
    osrm: ServiceHealth;
    x_twitter: ServiceHealth;
    reddit: ServiceHealth;
  };
  models: {
    xgboost_risk: string;
    shap_explainer: string;
    distilbert_misinfo: string;
    resnet_vision: string;
    multimodal_fusion: string;
  };
}

export interface Incident {
  incident_id: string;
  disaster_type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'ACTIVE' | 'RESOLVED';
  latitude: number;
  longitude: number;
  location: string;
  people_at_risk: number;
  assigned_team?: string;
  created_at: string;
  updated_at: string;
  source: string;
  verification_status: string;
  description?: string;
  alert_level?: string;
  title?: string;
  event_type_code?: string;
  gdacs_url?: string;
}

export interface WeatherData {
  temperature?: number | null;
  windspeed?: number | null;
  weathercode?: number | null;
  weather_description: string;
  precipitation_now?: number | null;
  precipitation_24h?: number | null;
  windspeed_max_24h?: number | null;
  source: 'LIVE' | 'UNAVAILABLE';
  fetched_at: string;
  lat: number;
  lon: number;
}

export interface ShapContribution {
  feature: string;
  value: number;
  contribution: number;
}

export interface RiskPrediction {
  raw_score: number;
  risk_score: number;
  risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  risk_color: string;
  operational_threshold_crossed: boolean;
  shap_contributions: ShapContribution[];
  base_value?: number;
  input_features: Record<string, number>;
  model_name: string;
  data_label: 'MODEL GENERATED';
  calibrated_note: string;
  timestamp: string;
}

export interface MisinfoAnalysis {
  text: string;
  cleaned_text: string;
  prob_genuine: number;
  prob_misleading: number;
  is_genuine: boolean;
  confidence: number;
  credibility_score: number;
  classification: string;
  verification_status: 'LIKELY GENUINE' | 'UNCERTAIN' | 'LIKELY MISLEADING';
  recommended_action: string;
  model_name: string;
  disclaimer: string;
  data_label: 'MODEL GENERATED';
  timestamp: string;
}

export interface SingleImageVisionResult {
  filename?: string;
  damage_class: 'NO DAMAGE' | 'MILD DAMAGE' | 'SEVERE DAMAGE' | 'INVALID IMAGE' | string;
  class_idx: number;
  confidence: number;
  all_probs: number[];
  damage_score: number;
  is_valid?: boolean;
  risk_level?: 'LOWER RISK' | 'MODERATE RISK' | 'HIGH RISK' | 'INVALID' | string;
  limitation: string;
}

export interface VisionAnalysis {
  image_count: number;
  aggregate_score: number;
  aggregate_class: string;
  aggregate_class_idx: number;
  is_valid?: boolean;
  risk_level?: 'LOWER RISK' | 'MODERATE RISK' | 'HIGH RISK' | 'INVALID' | string;
  severity_summary: Record<string, number>;
  individual_results: SingleImageVisionResult[];
  model_name: string;
  limitation: string;
  data_label: 'MODEL GENERATED';
  timestamp: string;
}

export interface FusionResult {
  fusion_score: number;
  fusion_title: string;
  fusion_color: string;
  fusion_method: string;
  vision_contribution: number;
  text_contribution: number;
  vision_label: string;
  text_label: string;
  recommended_action: string;
  fusion_type: string;
  limitation_notice: string;
  data_label: 'MODEL GENERATED';
  timestamp: string;
}

export interface RouteData {
  success: boolean;
  points?: [number, number][];
  distance_km?: number;
  duration_min?: number;
  route_type: string;
  routing_engine: string;
  hazard_aware: boolean;
  disclaimer: string;
  source: string;
  error?: string;
  fetched_at: string;
}

export interface RescueTeam {
  team_id: string;
  name: string;
  latitude: number;
  longitude: number;
  status: 'AVAILABLE' | 'DISPATCHED' | 'EN_ROUTE';
  capacity: number;
  current_assignment?: string | null;
}

export interface DashboardData {
  kpis: {
    active_incidents: number;
    critical_alerts: number;
    verified_reports: number;
    dispatched_teams: number;
    people_at_risk: number;
    gdacs_incidents: number;
  };
  system_status: string;
  last_synced: string;
  weather?: WeatherData | null;
  recent_incidents: Incident[];
  timeline: Array<{
    time: string;
    description: string;
    type: string;
  }>;
  active_teams: RescueTeam[];
}

export interface SocialReport {
  text: string;
  raw_text?: string;
  source_platform: string;
  created_at?: string;
  ingested_at: string;
  verification_status: string;
  is_genuine?: boolean | null;
  credibility_score?: number | null;
  url?: string;
}
