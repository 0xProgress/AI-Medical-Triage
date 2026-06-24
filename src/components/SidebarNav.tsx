import { motion } from 'motion/react';
import { useChatStore } from '../store/chatStore';
import { 
  Plus, 
  Download, 
  MessageSquare, 
  History, 
  Flame, 
  ActivitySquare, 
  FileCheck,
  HeartOff,
  HeartPulse
} from 'lucide-react';

export default function SidebarNav() {
  const {
    activeTab,
    setActiveTab,
    reset,
    messages,
    conditions,
    redFlags,
    vitals,
    isComplete,
    sessionId
  } = useChatStore();

  const handleExport = () => {
    // Generate static clinical markdown summary
    const timestampStr = new Date().toISOString();
    const conditionStr = conditions.length > 0 
      ? conditions.map((c, i) => `${i+1}. ${c.name} (${c.match_percentage}% match, ${c.urgency} risk)\n   - Precautions: ${c.precautions.join(', ')}`).join('\n')
      : 'None identified yet';

    const redFlagsStr = redFlags.length > 0
      ? redFlags.map(rf => `- ${rf}`).join('\n')
      : 'None flagged during current evaluation';

    const transcript = messages
      .filter(m => m.role !== 'system')
      .map(m => `[${m.role.toUpperCase()}]: ${m.content}`)
      .join('\n\n');

    const markdown = `
# MEDTRIAGE CLINICAL AI EVALUATION SUMMARY
==================================================
REF ID: ${sessionId || 'PENDING'}
EXPORTED AT: ${timestampStr}
STATUS: ${isComplete ? 'TRIAGE COMPLETE' : 'IN PROGRESS'}

## COMPLETED PHYSIOLOGICAL VITALS
--------------------------------------------------
- Heart Rate: ${vitals.heartRate} bpm
- Blood Pressure: ${vitals.bloodPressure} mmHg
- Oral Temperature: ${vitals.temperature} °F
- SpO2 Oxygen Sat: ${vitals.oxygenSat}%
- Respiratory Rate: ${vitals.respiratoryRate} /min

## CRITICAL RISK FLAGS IDENTIFIED
--------------------------------------------------
${redFlagsStr}

## EVALUATED DIAGNOSTIC PRIORITIES
--------------------------------------------------
${conditionStr}

## EVALUATION TRANSCRIPT LOGS
--------------------------------------------------
${transcript}

==================================================
⚠️ NOT A SUBSTITUTE FOR PROFESSIONAL MEDICAL ADVICE
Developed strictly for physiological clinical sorting.
    `.trim();

    // Download file
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `medtriage-assessment-${sessionId || 'session'}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full bg-[#141829] p-4 border-r border-[#434654] select-none justify-between gap-5 text-on-surface" id="sidebar-nav-container">
      <div className="space-y-6" id="sidebar-main-group">
        {/* Brand Header */}
        <div className="flex items-center gap-2.5 px-1 py-2 border-b border-[#434654]" id="sidebar-brand">
          <div className="p-2 bg-[#c4d2ff] text-[#0a0e1a] rounded-lg shadow-md shrink-0 animate-pulse" id="brand-logo-box">
            <HeartPulse className="w-5 h-5 text-sans" />
          </div>
          <div id="brand-names">
            <h1 className="text-sm font-black uppercase tracking-wider text-on-surface font-sans leading-none">
              MedTriage <span className="text-[#c4d2ff]">AI</span>
            </h1>
            <span className="text-[10px] text-[#c3c6d6]/80 font-mono tracking-tight font-bold">
              v1.4 Clinical Diagnostic
            </span>
          </div>
        </div>

        {/* Action button trigger stack */}
        <div className="space-y-2.5" id="nav-actions-stack">
          {/* Create new triage session button */}
          <button
            onClick={() => reset()}
            className="flex items-center justify-center gap-2 w-full bg-[#c4d2ff] text-[#0a0e1a] hover:bg-[#b0c0f8] text-xs font-bold py-3 px-4 rounded-lg cursor-pointer transform transition-all active:scale-95 shadow-md shadow-[#c4d2ff1a] select-none"
            id="new-session-button"
          >
            <Plus className="w-4 h-4 shrink-0" />
            <span>New Session</span>
          </button>
        </div>

        {/* Primary Tab Navigation Lists */}
        <div className="space-y-1.5" id="nav-items-list">
          <span className="text-[9px] font-black text-[#c3c6d6] uppercase tracking-widest block px-1.5 mb-1 bg-[#1a1e2e] px-2 py-1 rounded inline-block font-sans">
            Diagnostic Telepresence
          </span>
          
          {/* Active assessment link */}
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex items-center gap-2.5 w-full text-left px-3 py-2.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'chat'
                ? 'bg-[#1a1e2e] text-[#c4d2ff] border-l-2 border-l-[#c4d2ff]'
                : 'text-[#c3c6d6] hover:text-[#c4d2ff] hover:bg-[#1a1e2e]'
            }`}
            id="nav-chat-btn"
          >
            <MessageSquare className="w-4 h-4 text-[#c4d2ff] shrink-0" />
            <span>Current Chat Triage</span>
          </button>

          {/* Patient History link */}
          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-2.5 w-full text-left px-3 py-2.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'history'
                ? 'bg-[#1a1e2e] text-[#c4d2ff] border-l-2 border-l-[#c4d2ff]'
                : 'text-[#c3c6d6] hover:text-[#c4d2ff] hover:bg-[#1a1e2e]'
            }`}
            id="nav-history-btn"
          >
            <History className="w-4 h-4 text-[#c4d2ff] shrink-0" />
            <span>Patient Case History</span>
          </button>

          {/* Vital signs configuration */}
          <button
            onClick={() => setActiveTab('vitals')}
            className={`flex items-center gap-2.5 w-full text-left px-3 py-2.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'vitals'
                ? 'bg-[#1a1e2e] text-[#c4d2ff] border-l-2 border-l-[#c4d2ff]'
                : 'text-[#c3c6d6] hover:text-[#c4d2ff] hover:bg-[#1a1e2e]'
            }`}
            id="nav-vitals-btn"
          >
            <ActivitySquare className="w-4 h-4 text-[#c4d2ff] shrink-0" />
            <span>Somatic Vitals Register</span>
          </button>
        </div>
      </div>

      {/* Export / Utilities section */}
      <div className="border-t border-[#434654] pt-4 space-y-2.5" id="sidebar-utilities-section">
        {messages.length > 1 && (
          <button
            onClick={handleExport}
            className="flex items-center justify-center gap-2 w-full p-2.5 rounded-lg border border-[#434654] bg-[#1a1e2e] text-[#c3c6d6] hover:text-[#c4d2ff] transition-colors text-xs font-medium cursor-pointer"
            id="export-nav-button"
          >
            <Download className="w-4 h-4 shrink-0 text-[#c4d2ff]" />
            <span>Export Diagnostic</span>
          </button>
        )}
        
        {/* Compliance Footer Shield */}
        <div className="bg-[#1a1e2e] p-2.5 rounded border border-[#434654]/60 flex items-center gap-2" id="compliance-shield">
          <FileCheck className="w-4 h-4 text-[#c4d2ff] shrink-0" />
          <p className="text-[9px] text-[#c3c6d6] leading-tight font-sans">
            HIPAA-Grade Security enabled. Data is filtered on server node.
          </p>
        </div>
      </div>
    </div>
  );
}
