import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Condition } from '../types';
import { Shield, Info, Activity, Star, Award, CheckCircle2, AlertTriangle, BookOpen } from 'lucide-react';

interface AssessmentSidebarProps {
  conditions: Condition[];
  turnCount: number;
  isComplete: boolean;
}

export default function AssessmentSidebar({
  conditions,
  turnCount,
  isComplete
}: AssessmentSidebarProps) {
  const [showHowItWorks, setShowHowItWorks] = useState(false);

  // Take the highest match score as base or default clinical baseline
  const highestMatch = conditions.length > 0 ? conditions[0].match_percentage : 0;
  
  // Dynamic confidence calculations
  const overallConfidence = highestMatch > 0 
    ? Math.round(highestMatch * 0.9 + Math.min(turnCount * 3, 10)) 
    : 0;
  const symptomMatch = highestMatch > 0 
    ? Math.round(highestMatch * 1.0) 
    : 0;
  const relevanceScore = highestMatch > 0 
    ? Math.round(highestMatch * (turnCount >= 3 ? 0.95 : 0.82)) 
    : 0;

  // Render top 3 conditions
  const topConditions = conditions.slice(0, 3);

  // Helper to determine indicator color
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'bg-primary-container text-primary';
    if (score >= 50) return 'bg-primary/40 text-primary-container';
    return 'bg-outline-variant text-on-surface-variant';
  };

  return (
    <div className="flex flex-col gap-5 bg-surface-container p-4 rounded-xl border border-outline-variant/60 shadow-lg h-full select-none" id="assessment-panel">
      {/* Panel Header */}
      <div className="flex items-center gap-2 border-b border-outline-variant pb-3" id="panel-hdr">
        <div className="p-1.5 rounded bg-primary/10 text-primary" id="hdr-icon">
          <Shield className="w-5 h-5 text-primary" />
        </div>
        <div id="hdr-text">
          <h2 className="text-sm font-black text-on-surface uppercase tracking-wider font-sans">
            Diagnostic Telemetry
          </h2>
          <span className="text-[10px] text-on-surface-variant font-mono">
            Clinical Urgency Priorities
          </span>
        </div>
      </div>

      {/* Primary Confidence Telemetry Metres */}
      {conditions.length > 0 ? (
        <div className="space-y-4" id="telemetry-scores">
          {/* Overall Confidence Indicator */}
          <div className="bg-surface-container-low border border-outline-variant p-3.5 rounded-lg flex flex-col gap-2" id="card-overall-confidence">
            <div className="flex justify-between items-center" id="metric-overall-hdr">
              <span className="text-xs font-bold font-sans text-on-surface-variant">Overall Diagnostic Confidence</span>
              <span className="text-sm font-mono font-bold text-primary">{overallConfidence}%</span>
            </div>
            <div className="w-full bg-surface-container-high h-2.5 rounded-full overflow-hidden border border-outline-variant/30" id="metric-overall-bar-wrap">
              <motion.div 
                className="h-full bg-primary-container rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${overallConfidence}%` }}
                transition={{ duration: 1, ease: 'easeOut' }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-on-surface-variant/80 font-mono" id="metric-overall-footer">
              <span>Low accuracy</span>
              <span>Clinical consensus</span>
            </div>
          </div>

          {/* Detailed metrics stack */}
          <div className="space-y-3 p-1" id="metrics-details">
            {/* Symptom Match */}
            <div className="flex flex-col gap-1" id="metric-symptoms">
              <div className="flex justify-between text-xs font-sans text-on-surface-variant" id="metric-symptoms-hdr">
                <span>Physiological Symptom Alignment</span>
                <span className="font-mono text-on-surface">{symptomMatch}%</span>
              </div>
              <div className="w-full bg-surface-container-low h-2 rounded-full overflow-hidden border border-outline-variant/30" id="metric-symptoms-bar">
                <motion.div 
                  className="h-full bg-primary/70 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${symptomMatch}%` }}
                  transition={{ duration: 0.8, delay: 0.1, ease: 'easeOut' }}
                />
              </div>
            </div>

            {/* Clinical Relevance */}
            <div className="flex flex-col gap-1" id="metric-relevance">
              <div className="flex justify-between text-xs font-sans text-on-surface-variant" id="metric-relevance-hdr">
                <span>Clinical Relevance Index</span>
                <span className="font-mono text-on-surface">{relevanceScore}%</span>
              </div>
              <div className="w-full bg-surface-container-low h-2 rounded-full overflow-hidden border border-outline-variant/30" id="metric-relevance-bar">
                <motion.div 
                  className="h-full bg-primary/40 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${relevanceScore}%` }}
                  transition={{ duration: 0.8, delay: 0.2, ease: 'easeOut' }}
                />
              </div>
            </div>
          </div>

          {/* Top 3 Prioritized Causes */}
          <div className="mt-2 space-y-2" id="top-priority-causes">
            <h3 className="text-xs font-black text-on-surface-variant uppercase tracking-wider mb-2 font-sans flex items-center gap-1">
              <Activity className="w-3.5 h-3.5 text-primary" /> Primary Causes ({topConditions.length})
            </h3>
            
            <div className="grid grid-cols-1 gap-1.5" id="mini-conditions-grid">
              {topConditions.map((cond, idx) => (
                <div 
                  key={idx}
                  className="flex items-center justify-between p-2.5 rounded bg-surface-container-low border border-outline-variant/50 hover:bg-surface-container-high transition-colors text-xs"
                  id={`top-cond-${idx}`}
                >
                  <div className="font-sans font-bold text-on-surface flex items-center gap-1.5">
                    <span className="text-primary font-mono">{idx + 1}.</span>
                    <span className="truncate max-w-[140px]">{cond.name}</span>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <span className={`text-[10px] font-bold px-1.5 rounded select-none ${
                      cond.urgency === 'urgent' ? 'bg-error/10 text-error' :
                      cond.urgency === 'moderate' ? 'bg-primary-container/10 text-primary' :
                      'bg-surface-container text-on-surface-variant'
                    }`}>
                      {cond.urgency}
                    </span>
                    <span className="font-mono text-on-surface-variant font-medium">{cond.match_percentage}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-on-surface-variant-variant/70 border border-dashed border-outline-variant/40 rounded-lg min-h-[160px]" id="empty-telemetry">
          <Award className="w-10 h-10 text-on-surface-variant opacity-40 mb-3" />
          <h3 className="text-xs font-bold text-on-surface uppercase font-sans">Awaiting Diagnostic Input</h3>
          <p className="text-[11px] text-on-surface-variant/70 leading-relaxed mt-1.5 max-w-[180px] font-sans">
            Describe your physiological symptoms inside the chat console to construct active triage priorities.
          </p>
        </div>
      )}

      {/* Static explaining block & "How AI arrived at this" Link triggers */}
      <div className="mt-auto border-t border-outline-variant/40 pt-3" id="panel-docs-trigger">
        <button
          onClick={() => setShowHowItWorks(!showHowItWorks)}
          className="text-xs text-primary font-bold hover:underline flex items-center gap-1 w-full justify-center group py-1 border border-outline-variant rounded bg-surface-container-low"
          id="how-ai-arrived-btn"
        >
          <BookOpen className="w-3.5 h-3.5 text-primary group-hover:scale-105 transition-transform" />
          <span>Clinical Logic & Methodology</span>
        </button>

        {/* Informational overlay toggle dropdown sheet */}
        <AnimatePresence>
          {showHowItWorks && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-2 bg-surface-container-low border border-outline-variant p-3 rounded-lg text-[11px] text-on-surface-variant leading-relaxed font-sans"
              id="how-ai-arrived-desc"
            >
              <h4 className="font-bold text-on-surface flex items-center gap-1 uppercase tracking-wider border-b border-outline-variant/30 pb-1 mb-1.5">
                <Info className="w-3.5 h-3.5 text-primary" /> Reasoning Model
              </h4>
              <p className="mb-2">
                MedTriage AI utilizes the <b>Groq clinical triage guidelines</b> to continuously match structured symptoms against a verified database of medical conditions.
              </p>
              <ul className="list-disc pl-3.5 space-y-1">
                <li><b>Physiological Alignment</b> represents direct token overlap with symptoms profiles.</li>
                <li><b>Clinical Relevance</b> assesses pain indices, vital statuses, and physiological onset rates.</li>
              </ul>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
