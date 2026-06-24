import { Settings2, Circle, Clock, Layers } from 'lucide-react';

interface SessionStatusProps {
  sessionId: string | null;
  turnCount: number;
  isComplete: boolean;
}

export default function SessionStatus({
  sessionId,
  turnCount,
  isComplete
}: SessionStatusProps) {
  const displayId = sessionId ? sessionId.slice(0, 10) + (sessionId.length > 10 ? '...' : '') : 'MTAI-PENDING';

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-surface-container-low border border-outline-variant p-3.5 rounded-lg select-none font-mono text-xs text-on-surface-variant shadow-sm" id="session-telemetry-status">
      {/* Session reference indicators */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1" id="status-meta">
        <div className="flex items-center gap-1.5" id="meta-id">
          <Layers className="w-3.5 h-3.5 text-primary" />
          <span className="text-on-surface font-bold">SESSION:</span>
          <span className="text-on-surface select-all tracking-wider font-semibold opacity-90">{displayId}</span>
        </div>
        
        <div className="flex items-center gap-1.5" id="meta-turns">
          <Clock className="w-3.5 h-3.5 text-primary" />
          <span className="text-on-surface font-bold font-mono">TURNS:</span>
          <span className="text-on-surface font-black" id="turn-value">{turnCount} / 10</span>
        </div>
      </div>

      {/* Triage completion status flag badges */}
      <div className="flex items-center gap-2" id="status-badge-wrap">
        <span className="font-sans font-bold text-[10px] sm:text-xs">STATUS:</span>
        <div className={`flex items-center gap-1.5 rounded-full px-2.5 py-0.5 border font-sans font-bold tracking-wider select-none text-[10px] sm:text-xs ${
          isComplete 
            ? 'bg-error-container/10 border-error/30 text-error select-none animate-pulse' 
            : 'bg-primary-container/10 border-primary/30 text-primary'
        }`} id="status-pill">
          <Circle className={`w-2 h-2 fill-current ${
            isComplete ? 'text-error' : 'text-primary'
          }`} />
          <span className="uppercase">{isComplete ? 'Triage Complete' : 'In Progress'}</span>
        </div>
      </div>
    </div>
  );
}
