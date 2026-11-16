import React, { useState, useRef } from 'react';
import {
  Layers,
  Upload,
  Image as ImageIcon,
  Trash2,
  Cpu,
  RefreshCw,
  Send,
  AlertTriangle,
  Info,
  CheckCircle2,
  ShieldAlert,
} from 'lucide-react';
import { VisionAnalysis, MisinfoAnalysis, FusionResult } from '../types';
import { api } from '../services/api';
import { SourceBadge } from '../components/status/SourceBadge';

export const Multimodal: React.FC = () => {
  // Vision state
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [visionResult, setVisionResult] = useState<VisionAnalysis | null>(null);
  const [analyzingVision, setAnalyzingVision] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Text state
  const [incidentText, setIncidentText] = useState<string>(
    'Urgent: Structural damage to flyover pillar in downtown sector. Water levels rising and partial concrete debris observed on roadway.'
  );
  const [textResult, setTextResult] = useState<MisinfoAnalysis | null>(null);
  const [analyzingText, setAnalyzingText] = useState(false);

  // Fusion state
  const [fusionResult, setFusionResult] = useState<FusionResult | null>(null);
  const [fusing, setFusing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Handle image files selection
  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    const newFiles = Array.from(files).filter((f) => f.type.startsWith('image/'));
    const combined = [...selectedFiles, ...newFiles].slice(0, 4); // max 4 images
    setSelectedFiles(combined);

    // Generate previews
    const newPreviews = combined.map((f) => URL.createObjectURL(f));
    setPreviews(newPreviews);
  };

  const removeFile = (index: number) => {
    const updatedFiles = selectedFiles.filter((_, i) => i !== index);
    setSelectedFiles(updatedFiles);
    const updatedPreviews = updatedFiles.map((f) => URL.createObjectURL(f));
    setPreviews(updatedPreviews);
    setVisionResult(null);
  };

  // Run Vision
  const handleAnalyzeVision = async () => {
    if (selectedFiles.length === 0) return;
    setAnalyzingVision(true);
    setError(null);
    try {
      const res = await api.analyzeVision(selectedFiles);
      setVisionResult(res);
      // Automatically trigger multimodal fusion update
      triggerFusion(res, textResult);
    } catch (err: any) {
      setError(`Vision error: ${err.message}`);
    } finally {
      setAnalyzingVision(false);
    }
  };

  // Run Text
  const handleAnalyzeText = async () => {
    if (!incidentText.trim()) return;
    setAnalyzingText(true);
    setError(null);
    try {
      const res = await api.analyzeMisinformation(incidentText, 'MULTIMODAL_WORKSPACE');
      setTextResult(res);
      triggerFusion(visionResult, res);
    } catch (err: any) {
      setError(`Text analysis error: ${err.message}`);
    } finally {
      setAnalyzingText(false);
    }
  };

  // Trigger Fusion
  const triggerFusion = async (vRes: VisionAnalysis | null, tRes: MisinfoAnalysis | null) => {
    setFusing(true);
    try {
      const res = await api.combineModalities({
        vision_score: vRes ? vRes.aggregate_score : null,
        vision_label: vRes ? vRes.aggregate_class : null,
        text_prob_genuine: tRes ? tRes.prob_genuine : null,
        text_label: tRes ? tRes.classification : null,
      });
      setFusionResult(res);
    } catch (err: any) {
      console.warn('Fusion calculation error:', err);
    } finally {
      setFusing(false);
    }
  };

  return (
    <div className="space-y-5 font-mono">
      {/* Header Banner */}
      <div className="p-4 rounded bg-[#111827] border border-[#1F2937] flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Layers className="w-5 h-5 text-sky-400" />
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Multimodal Intelligence & Damage Assessment Workspace
            </h2>
            <SourceBadge source="MODEL GENERATED Vision + Text" />
          </div>
          <p className="text-xs text-slate-400">
            ResNet-50 Visual Damage Classifier + DistilBERT NLP joined via transparent decision-level fusion.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              handleAnalyzeVision();
              handleAnalyzeText();
            }}
            disabled={analyzingVision || analyzingText || (selectedFiles.length === 0 && !incidentText.trim())}
            className="px-4 py-2 rounded bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {analyzingVision || analyzingText ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>PROCESSING MODALITIES...</span>
              </>
            ) : (
              <>
                <Cpu className="w-3.5 h-3.5" />
                <span>RUN COMPLETE MULTIMODAL INFERENCE</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded bg-rose-950/40 border border-rose-800 text-rose-400 text-xs">
          {error}
        </div>
      )}

      {/* Main Grid: Inputs Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Modality 1: Image Upload & ResNet */}
        <div className="p-4 rounded bg-[#111827] border border-[#1F2937] space-y-4">
          <div className="flex items-center justify-between border-b border-[#1F2937] pb-2">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
              <ImageIcon className="w-4 h-4 text-sky-400" />
              <span>VISION INPUT: DAMAGE IMAGERY (ResNet-50)</span>
            </div>
            <SourceBadge source="MODEL GENERATED ResNet-50" short={true} />
          </div>

          {/* Upload Area */}
          <div
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              handleFiles(e.dataTransfer.files);
            }}
            className="p-6 border-2 border-dashed border-[#1F2937] hover:border-sky-500/50 rounded-lg bg-[#0B0F17] flex flex-col items-center justify-center gap-2 cursor-pointer transition-colors"
          >
            <Upload className="w-6 h-6 text-slate-500" />
            <span className="text-xs text-slate-300 font-semibold">
              Drop incident photos here or browse files
            </span>
            <span className="text-[10px] text-slate-500">
              Supports JPEG, PNG, WebP (Max 4 images for multi-image aggregation)
            </span>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/*"
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
          </div>

          {/* Preview Thumbnails */}
          {previews.length > 0 && (
            <div className="grid grid-cols-4 gap-2">
              {previews.map((src, idx) => (
                <div key={idx} className="relative group rounded border border-[#1F2937] overflow-hidden aspect-video bg-black">
                  <img src={src} alt="Damage sample" className="w-full h-full object-cover" />
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(idx);
                    }}
                    className="absolute top-1 right-1 p-1 rounded bg-black/70 hover:bg-rose-900 text-slate-300 hover:text-white transition-colors"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Vision Trigger */}
          <button
            onClick={handleAnalyzeVision}
            disabled={selectedFiles.length === 0 || analyzingVision}
            className="w-full py-2 rounded bg-[#161E2E] hover:bg-[#1E293B] border border-[#1F2937] text-xs text-slate-200 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {analyzingVision ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>EVALUATING VISUAL FEATURES...</span>
              </>
            ) : (
              <span>ANALYZE IMAGES VIA RESNET-50 ({selectedFiles.length})</span>
            )}
          </button>

          {/* Vision Results Breakdown */}
          {visionResult && (
            <div className="p-3.5 rounded bg-[#0B0F17] border border-[#1F2937] space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">DAMAGE CLASSIFICATION:</span>
                <span
                  className={`px-2 py-0.5 rounded text-xs font-bold ${
                    visionResult.aggregate_class === 'INVALID IMAGE' || visionResult.is_valid === false
                      ? 'bg-slate-800 text-amber-300 border border-amber-600/60'
                      : visionResult.aggregate_class === 'SEVERE DAMAGE'
                      ? 'bg-rose-950 text-rose-300 border border-rose-800'
                      : visionResult.aggregate_class === 'MILD DAMAGE'
                      ? 'bg-amber-950 text-amber-300 border border-amber-800'
                      : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                  }`}
                >
                  {visionResult.aggregate_class === 'INVALID IMAGE'
                    ? 'INVALID IMAGE'
                    : visionResult.aggregate_class === 'NO DAMAGE'
                    ? 'NO DAMAGE (LOWER RISK)'
                    : visionResult.aggregate_class === 'SEVERE DAMAGE'
                    ? 'SEVERE DAMAGE (HIGH RISK)'
                    : 'MILD DAMAGE (MODERATE RISK)'}
                </span>
              </div>

              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Operational Risk Assessment:</span>
                <span
                  className={`font-bold font-mono ${
                    visionResult.aggregate_class === 'INVALID IMAGE' || visionResult.is_valid === false
                      ? 'text-slate-400'
                      : visionResult.aggregate_class === 'SEVERE DAMAGE'
                      ? 'text-rose-400'
                      : visionResult.aggregate_class === 'MILD DAMAGE'
                      ? 'text-amber-400'
                      : 'text-emerald-400'
                  }`}
                >
                  {visionResult.risk_level || (visionResult.is_valid === false ? 'INVALID' : 'LOWER RISK')}
                </span>
              </div>

              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Aggregate Damage Score:</span>
                <span className="font-bold text-sky-400 font-mono">
                  {visionResult.aggregate_score.toFixed(3)} / 1.000
                </span>
              </div>

              {/* Status Context & Guidance */}
              {visionResult.aggregate_class === 'INVALID IMAGE' || visionResult.is_valid === false ? (
                <div className="p-2.5 rounded bg-amber-950/30 border border-amber-800/60 text-[11px] text-amber-200/90 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <strong>Invalid Input Detected:</strong> Uploaded photo does not depict a disaster or outdoor infrastructure scene (e.g. pet, meme, selfie, document, or indoor object).
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      System accepts disaster scenes (wildfire, flood, structural collapse) or environmental baselines (roads, skies, forests).
                    </div>
                  </div>
                </div>
              ) : visionResult.aggregate_class === 'NO DAMAGE' ? (
                <div className="p-2 rounded bg-emerald-950/20 border border-emerald-900/40 text-[11px] text-emerald-300/90 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span>
                    <strong>Safe / Lower Risk:</strong> Clear environment or intact infrastructure verified (clean road, clear sky, green forest, or intact structure).
                  </span>
                </div>
              ) : (
                <div className="p-2 rounded bg-rose-950/20 border border-rose-900/40 text-[11px] text-rose-300/90 flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-rose-400 flex-shrink-0" />
                  <span>
                    <strong>Disaster Hazard Detected:</strong> Active wildfire combustion, flood inundation, or structural debris verified.
                  </span>
                </div>
              )}

              {/* Model context */}
              <div className="p-2 rounded bg-sky-950/20 border border-sky-900/40 text-[10px] text-sky-300/80">
                ⚡ <strong>Model Context:</strong> {visionResult.limitation}
              </div>
            </div>
          )}
        </div>

        {/* Modality 2: Text Report & DistilBERT */}
        <div className="p-4 rounded bg-[#111827] border border-[#1F2937] space-y-4">
          <div className="flex items-center justify-between border-b border-[#1F2937] pb-2">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
              <Cpu className="w-4 h-4 text-emerald-400" />
              <span>TEXT INPUT: SITUATION REPORT (DistilBERT)</span>
            </div>
            <SourceBadge source="MODEL GENERATED DistilBERT" short={true} />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs text-slate-300">Incident Narrative / Dispatch Report:</label>
            <textarea
              rows={4}
              value={incidentText}
              onChange={(e) => setIncidentText(e.target.value)}
              className="w-full p-3 rounded bg-[#0B0F17] border border-[#1F2937] text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-sky-500 leading-relaxed font-sans"
            />
          </div>

          {/* Text Trigger */}
          <button
            onClick={handleAnalyzeText}
            disabled={!incidentText.trim() || analyzingText}
            className="w-full py-2 rounded bg-[#161E2E] hover:bg-[#1E293B] border border-[#1F2937] text-xs text-slate-200 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {analyzingText ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>CLASSIFYING TEXT...</span>
              </>
            ) : (
              <span>ANALYZE TEXT REPORT VIA DISTILBERT</span>
            )}
          </button>

          {/* Text Results Breakdown */}
          {textResult && (
            <div className="p-3.5 rounded bg-[#0B0F17] border border-[#1F2937] space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">CREDIBILITY ASSESSMENT:</span>
                <span
                  className={`px-2 py-0.5 rounded text-xs font-bold ${
                    textResult.is_genuine
                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                      : 'bg-rose-950 text-rose-400 border border-rose-800'
                  }`}
                >
                  {textResult.classification}
                </span>
              </div>

              <div className="flex justify-between text-xs">
                <span className="text-slate-400">P(Real Incident Report):</span>
                <span className="font-bold text-emerald-400 font-mono">
                  {(textResult.prob_genuine * 100).toFixed(1)}%
                </span>
              </div>

              <div className="p-2 rounded bg-slate-900/60 border border-slate-800 text-[10px] text-slate-400">
                Action: {textResult.recommended_action}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Multimodal Decision Fusion Assessment Panel */}
      <div className="p-5 rounded bg-[#111827] border border-[#1F2937] space-y-4">
        <div className="flex items-center justify-between border-b border-[#1F2937] pb-3">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-sky-400" />
            <span className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              MULTIMODAL DECISION FUSION OUTCOME
            </span>
          </div>
          <SourceBadge source="MODEL GENERATED DECISION_LEVEL" />
        </div>

        {fusionResult ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Score Metric */}
              <div className="p-4 rounded bg-[#0B0F17] border border-[#1F2937] flex flex-col justify-between">
                <span className="text-[11px] text-slate-400 uppercase tracking-wider">
                  FUSION CONFIDENCE SCORE
                </span>
                <div className="flex items-baseline gap-2 mt-2">
                  <span
                    className="text-4xl font-bold tracking-tight"
                    style={{ color: fusionResult.fusion_color }}
                  >
                    {(fusionResult.fusion_score * 100).toFixed(1)}%
                  </span>
                  <span className="text-xs text-slate-500">/ 100</span>
                </div>
                <div
                  className="mt-2 text-xs font-bold"
                  style={{ color: fusionResult.fusion_color }}
                >
                  {fusionResult.fusion_title}
                </div>
              </div>

              {/* Modality Contributions */}
              <div className="p-4 rounded bg-[#0B0F17] border border-[#1F2937] space-y-2 text-xs">
                <span className="text-[11px] text-slate-400 uppercase tracking-wider block">
                  MODALITY CONTRIBUTIONS
                </span>
                <div className="flex justify-between pt-1">
                  <span className="text-slate-300">Vision Component (60% wt):</span>
                  <span className="font-bold text-sky-400">
                    {(fusionResult.vision_contribution * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-300">Text Component (40% wt):</span>
                  <span className="font-bold text-emerald-400">
                    {(fusionResult.text_contribution * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="text-[10px] text-slate-500 pt-1 border-t border-[#1F2937]">
                  Formula: {fusionResult.fusion_method}
                </div>
              </div>

              {/* Response Protocol */}
              <div className="p-4 rounded bg-[#0B0F17] border border-[#1F2937] flex flex-col justify-between">
                <span className="text-[11px] text-slate-400 uppercase tracking-wider">
                  OPERATIONAL DISPATCH DECISION
                </span>
                <div className="p-2.5 rounded bg-sky-950/30 border border-sky-800 text-sky-200 text-xs font-bold mt-2">
                  {fusionResult.recommended_action}
                </div>
                <span className="text-[10px] text-slate-500 mt-2">
                  Deterministic tactical escalation rule
                </span>
              </div>
            </div>

            {/* Honest Limitation Notice */}
            <div className="flex items-start gap-2 p-3 rounded bg-slate-900/60 border border-slate-800 text-[11px] text-slate-400">
              <Info className="w-4 h-4 text-sky-400 flex-shrink-0 mt-0.5" />
              <p>
                <strong>Scientific Integrity Note:</strong> {fusionResult.limitation_notice}
              </p>
            </div>
          </div>
        ) : (
          <div className="p-6 text-center text-xs text-slate-500">
            Upload damage photos and enter a situation report above to view combined decision-level fusion.
          </div>
        )}
      </div>
    </div>
  );
};
