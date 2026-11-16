import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  AlertOctagon,
  ShieldCheck,
  Send,
  RefreshCw,
  Info,
  Radio,
  Newspaper,
  Twitter,
  Globe,
} from 'lucide-react';
import { MisinfoAnalysis, SocialReport } from '../types';
import { api } from '../services/api';
import { SourceBadge } from '../components/status/SourceBadge';
import { KpiCard } from '../components/cards/KpiCard';

const SAMPLE_TEXTS = [
  'Massive flash flood inundating Janpath Road in Bhubaneswar! Cars floating and water rising fast, rescue teams urgently needed!',
  'The entire district of Puri has been completely destroyed and 50,000 people are dead. The government is covering this up!',
  'Emergency alert: Severe waterlogging reported in low-lying areas near Old Town following 120mm rainfall. Citizens advised to stay indoors.',
  'Just saw alien spaceships flying over the cyclone eye wall in Odisha! Retweet before government deletes!',
];

export const Misinformation: React.FC = () => {
  const [inputText, setInputText] = useState<string>(SAMPLE_TEXTS[0]);
  const [analysis, setAnalysis] = useState<MisinfoAnalysis | null>(null);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Social feeds
  const [gdeltNews, setGdeltNews] = useState<SocialReport[]>([]);
  const [gdeltLoading, setGdeltLoading] = useState<boolean>(false);
  const [xStatus, setXStatus] = useState<{ status: string; message?: string }>({ status: 'CHECKING' });
  const [redditStatus, setRedditStatus] = useState<{ status: string; message?: string }>({ status: 'CHECKING' });
  const [analyzedHistory, setAnalyzedHistory] = useState<MisinfoAnalysis[]>([]);

  const handleAnalyze = async (textToRun: string) => {
    if (!textToRun.trim()) return;
    setAnalyzing(true);
    setError(null);
    try {
      const res = await api.analyzeMisinformation(textToRun, 'MANUAL_DISPATCH_CONSOLE');
      setAnalysis(res);
      setAnalyzedHistory((prev) => [res, ...prev].slice(0, 10));
    } catch (err: any) {
      setError(err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const loadSocialIntelligence = async () => {
    // 1. GDELT Live News
    setGdeltLoading(true);
    try {
      const gdeltRes = await api.getGDELTNews(10);
      setGdeltNews(gdeltRes.reports || []);
    } catch {
      // GDELT unavailable
    } finally {
      setGdeltLoading(false);
    }

    // 2. X/Twitter Status
    try {
      const xRes = await api.getXReports();
      setXStatus({ status: xRes.status, message: xRes.message });
    } catch {
      setXStatus({ status: 'UNAVAILABLE' });
    }

    // 3. Reddit Status
    try {
      const rRes = await api.getRedditReports();
      setRedditStatus({ status: rRes.status, message: rRes.message });
    } catch {
      setRedditStatus({ status: 'UNAVAILABLE' });
    }
  };

  useEffect(() => {
    handleAnalyze(SAMPLE_TEXTS[0]);
    loadSocialIntelligence();
  }, []);

  const totalAnalyzed = analyzedHistory.length;
  const genuineCount = analyzedHistory.filter((a) => a.is_genuine).length;
  const misleadingCount = totalAnalyzed - genuineCount;

  return (
    <div className="space-y-5 font-mono">
      {/* Top Banner */}
      <div className="p-4 rounded bg-[#111827] border border-[#1F2937] flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Misinformation Intelligence & Social Verification
            </h2>
            <SourceBadge source="MODEL GENERATED DistilBERT" />
          </div>
          <p className="text-xs text-slate-400">
            Fine-tuned DistilBERT classifier evaluating disaster communication patterns and linguistic credibility signals.
          </p>
        </div>

        <button
          onClick={loadSocialIntelligence}
          disabled={gdeltLoading}
          className="flex items-center gap-2 px-3 py-1.5 rounded bg-[#161E2E] hover:bg-[#1E293B] border border-[#1F2937] text-xs text-slate-300 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${gdeltLoading ? 'animate-spin' : ''}`} />
          <span>Refresh News Intelligence</span>
        </button>
      </div>

      {/* Top Telemetry KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <KpiCard
          label="Incoming Reports"
          value={gdeltNews.length + totalAnalyzed}
          accent="accent"
          icon={Radio}
          subtext="GDELT + Dispatch Feed"
        />
        <KpiCard
          label="Reports Analyzed"
          value={totalAnalyzed}
          accent="default"
          icon={CheckCircle2}
          subtext="Session evaluations"
        />
        <KpiCard
          label="Likely Genuine"
          value={genuineCount}
          accent="safe"
          icon={ShieldCheck}
          subtext="P(genuine) >= 0.50"
        />
        <KpiCard
          label="Potentially Misleading"
          value={misleadingCount}
          accent="critical"
          icon={AlertOctagon}
          subtext="Flagged by model"
        />
      </div>

      {/* Main Workspace: Classifier Input & Detailed Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Input Workspace (6 cols) */}
        <div className="lg:col-span-6 space-y-4">
          <div className="p-4 rounded bg-[#111827] border border-[#1F2937] space-y-4">
            <div className="flex items-center justify-between border-b border-[#1F2937] pb-2">
              <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                DISTILBERT TEXT CLASSIFIER
              </span>
              <SourceBadge source="MODEL GENERATED" short={true} />
            </div>

            {/* Presets */}
            <div>
              <span className="text-[11px] text-slate-400 block mb-1.5">
                Load Preset Test Report:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {SAMPLE_TEXTS.map((sample, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setInputText(sample);
                      handleAnalyze(sample);
                    }}
                    className="px-2 py-1 rounded bg-[#161E2E] hover:bg-[#1E293B] border border-[#1F2937] text-[11px] text-slate-300 transition-colors"
                  >
                    Sample {idx + 1}
                  </button>
                ))}
              </div>
            </div>

            {/* Text Area */}
            <div className="space-y-1.5">
              <label className="text-xs text-slate-300">Incident Report Text:</label>
              <textarea
                rows={4}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Enter eyewitness tweet, radio dispatch, or incident message..."
                className="w-full p-3 rounded bg-[#0B0F17] border border-[#1F2937] text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-sky-500 leading-relaxed font-sans"
              />
            </div>

            <button
              onClick={() => handleAnalyze(inputText)}
              disabled={analyzing || !inputText.trim()}
              className="w-full py-2.5 rounded bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {analyzing ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>ANALYZING TEXT VIA DISTILBERT...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>ANALYZE INCIDENT REPORT</span>
                </>
              )}
            </button>
          </div>

          {/* Social Sources Status Cards */}
          <div className="p-4 rounded bg-[#111827] border border-[#1F2937] space-y-3">
            <div className="text-xs font-bold text-slate-200 uppercase tracking-wider border-b border-[#1F2937] pb-1.5">
              Configured External Streams
            </div>

            {/* GDELT Stream */}
            <div className="p-2.5 rounded bg-[#161E2E] border border-[#1F2937] flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <Newspaper className="w-4 h-4 text-emerald-400" />
                <span>GDELT Global News Feed:</span>
              </div>
              <SourceBadge source="LIVE GDELT" />
            </div>

            {/* X / Twitter Stream */}
            <div className="p-2.5 rounded bg-[#161E2E] border border-[#1F2937] flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <Twitter className="w-4 h-4 text-slate-500" />
                <span>X (Twitter) API v2:</span>
              </div>
              <SourceBadge source={xStatus.status === 'ONLINE' ? 'LIVE' : 'UNAVAILABLE X/Twitter'} />
            </div>

            {/* Reddit Stream */}
            <div className="p-2.5 rounded bg-[#161E2E] border border-[#1F2937] flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4 text-slate-500" />
                <span>Reddit Subreddit Feed:</span>
              </div>
              <SourceBadge source={redditStatus.status === 'ONLINE' ? 'LIVE' : 'UNAVAILABLE Reddit'} />
            </div>
          </div>
        </div>

        {/* Right Output Workspace (6 cols) */}
        <div className="lg:col-span-6 space-y-4">
          {error ? (
            <div className="p-4 rounded bg-rose-950/30 border border-rose-900/50 text-rose-400 text-xs">
              Analysis error: {error}
            </div>
          ) : analysis ? (
            <div className="p-5 rounded bg-[#111827] border border-[#1F2937] space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  CLASSIFICATION ASSESSMENT
                </span>
                <SourceBadge source={analysis.data_label} />
              </div>

              {/* Primary Classification Result */}
              <div className="p-4 rounded bg-[#0B0F17] border border-[#1F2937] space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400 uppercase">PREDICTED CLASS</span>
                  <span
                    className={`px-2.5 py-1 rounded text-xs font-bold tracking-wider ${
                      analysis.is_genuine
                        ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800'
                        : 'bg-rose-950/80 text-rose-400 border border-rose-800'
                    }`}
                  >
                    {analysis.classification}
                  </span>
                </div>

                {/* Probabilities */}
                <div className="space-y-1.5 pt-2 border-t border-[#1F2937]">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">P(Real Disaster Pattern):</span>
                    <span className="text-emerald-400 font-bold font-mono">
                      {(analysis.prob_genuine * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-900 rounded-full h-1.5">
                    <div
                      className="bg-emerald-500 h-1.5 rounded-full"
                      style={{ width: `${analysis.prob_genuine * 100}%` }}
                    />
                  </div>

                  <div className="flex justify-between text-xs pt-1">
                    <span className="text-slate-400">P(Not Real / Misleading Pattern):</span>
                    <span className="text-rose-400 font-bold font-mono">
                      {(analysis.prob_misleading * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-900 rounded-full h-1.5">
                    <div
                      className="bg-rose-500 h-1.5 rounded-full"
                      style={{ width: `${analysis.prob_misleading * 100}%` }}
                    />
                  </div>
                </div>

                <div className="flex justify-between text-xs pt-2 border-t border-[#1F2937]">
                  <span className="text-slate-400">Credibility Signal:</span>
                  <span className="text-sky-300 font-bold">{analysis.credibility_score} / 100</span>
                </div>
              </div>

              {/* Operational Action Recommendation */}
              <div className="p-3 rounded bg-[#161E2E] border border-[#1F2937] text-xs">
                <span className="text-[10px] text-slate-400 block mb-1 uppercase font-bold tracking-wider">
                  RECOMMENDED DISPATCH PROTOCOL
                </span>
                <span className="text-slate-200 font-bold">{analysis.recommended_action}</span>
              </div>

              {/* Honest AI Limitation Note */}
              <div className="flex items-start gap-2 p-3 rounded bg-amber-950/20 border border-amber-900/40 text-amber-300/90 text-[11px]">
                <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <p>
                  <strong>Disclaimer:</strong> {analysis.disclaimer}
                </p>
              </div>
            </div>
          ) : (
            <div className="p-8 rounded bg-[#111827] border border-[#1F2937] text-center text-slate-500 text-xs">
              READY TO ANALYZE INCIDENT REPORT
            </div>
          )}

          {/* Live GDELT News Feed stream */}
          <div className="p-4 rounded bg-[#111827] border border-[#1F2937] space-y-3">
            <div className="flex items-center justify-between border-b border-[#1F2937] pb-2">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
                <Newspaper className="w-4 h-4 text-emerald-400" />
                <span>LIVE GDELT DISASTER NEWS FEED</span>
              </div>
              <SourceBadge source="LIVE" short={true} />
            </div>

            <div className="space-y-2 max-h-[220px] overflow-y-auto custom-scrollbar pr-1">
              {gdeltNews.length === 0 ? (
                <div className="text-xs text-slate-500 text-center py-4">
                  {gdeltLoading ? 'Fetching live news...' : 'No news articles ingested currently.'}
                </div>
              ) : (
                gdeltNews.map((news, idx) => (
                  <div
                    key={idx}
                    onClick={() => {
                      setInputText(news.text);
                      handleAnalyze(news.text);
                    }}
                    className="p-2.5 rounded bg-[#161E2E] hover:bg-[#1E293B] border border-[#1F2937] cursor-pointer transition-colors text-xs"
                  >
                    <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
                      <span className="text-emerald-400 font-semibold">{news.source_platform}</span>
                      <span>{news.created_at || news.ingested_at}</span>
                    </div>
                    <p className="text-slate-200 line-clamp-2">{news.text}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
