import React, { useState } from 'react';
import { useLiveData } from './hooks/useLiveData';
import { useSystemHealth } from './hooks/useSystemHealth';
import { TopHeader } from './components/layout/TopHeader';
import { Sidebar, PageId } from './components/layout/Sidebar';
import { CommandCenter } from './pages/CommandCenter';
import { PreDisasterRisk } from './pages/PreDisasterRisk';
import { Misinformation } from './pages/Misinformation';
import { Multimodal } from './pages/Multimodal';
import { RescueRouting } from './pages/RescueRouting';
import { AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<PageId>('command-center');
  const { dashboard, connectionStatus, lastSync, loading, error, refreshNow } = useLiveData();
  const { health, refreshHealth } = useSystemHealth();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    refreshNow();
    await refreshHealth();
    setTimeout(() => setIsRefreshing(false), 600);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#0B0F17] text-[#F1F5F9]">
      {/* Fixed Operational Top Header */}
      <TopHeader
        lastSync={lastSync}
        connectionStatus={connectionStatus}
        systemStatus={health?.overall_status || 'OPERATIONAL'}
        onRefresh={handleManualRefresh}
        isRefreshing={isRefreshing}
      />

      {/* Main Body: Sidebar + Dynamic Workspace Page */}
      <div className="flex-1 flex flex-row overflow-hidden">
        {/* Left Operational Sidebar */}
        <Sidebar
          activePage={activePage}
          onSelectPage={(page) => setActivePage(page)}
          health={health}
        />

        {/* Dynamic Page Content */}
        <main className="flex-1 overflow-y-auto p-5 custom-scrollbar">
          {error && (
            <div className="mb-4 p-3 rounded bg-rose-950/30 border border-rose-900/60 text-rose-400 text-xs font-mono flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>Telemetry sync warning: {error}. Working with cached telemetry state.</span>
            </div>
          )}

          {activePage === 'command-center' && (
            <CommandCenter
              dashboard={dashboard}
              health={health}
              loading={loading}
              onRefresh={handleManualRefresh}
            />
          )}

          {activePage === 'pre-disaster-risk' && (
            <PreDisasterRisk weather={dashboard?.weather || null} />
          )}

          {activePage === 'misinformation' && <Misinformation />}

          {activePage === 'multimodal' && <Multimodal />}

          {activePage === 'rescue-routing' && (
            <RescueRouting
              incidents={dashboard?.recent_incidents || []}
              teams={dashboard?.active_teams || []}
              onTeamDispatched={handleManualRefresh}
            />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
