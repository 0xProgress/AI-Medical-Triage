import { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useChatStore } from './store/chatStore';
import { sendMessage, generateReport } from './lib/api';
import { Message } from './types';

// Component Imports
import SidebarNav from './components/SidebarNav';
import SessionStatus from './components/SessionStatus';
import ChatMessage from './components/ChatMessage';
import ConditionCard from './components/ConditionCard';
import RedFlagAlert from './components/RedFlagAlert';
import ChatInput from './components/ChatInput';
import AssessmentSidebar from './components/AssessmentSidebar';
import TypingIndicator from './components/TypingIndicator';

// Icon Imports
import { 
  HeartPulse, 
  Sun, 
  Moon, 
  HelpCircle, 
  User, 
  Award, 
  HeartHandshake, 
  History, 
  ShieldAlert, 
  Activity, 
  Stethoscope, 
  ActivitySquare, 
  MessageSquare,
  Sparkle
} from 'lucide-react';

export default function App() {
  const {
    sessionId,
    messages,
    conditions,
    redFlags,
    isComplete,
    turnCount,
    isLoading,
    activeTab,
    theme,
    vitals,
    historyList,
    helpModalOpen,
    profileModalOpen,
    setSessionId,
    addMessage,
    setMessages,
    setConditions,
    setRedFlags,
    setIsComplete,
    setTurnCount,
    setIsLoading,
    setActiveTab,
    toggleTheme,
    updateVitals,
    addHistoryItem,
    setHelpModalOpen,
    setProfileModalOpen,
    reset
  } = useChatStore();

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Initialize store on mount if empty
  useEffect(() => {
    if (messages.length === 0) {
      reset();
    }
  }, []);

  // Scroll to bottom of chat when messages update
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Handle user input dispatch
  const handleSendMessage = async (userText: string) => {
    if (!userText.trim() || isLoading || isComplete) return;

    // Create unique user message Object
    const userMsg: Message = {
      id: `usr-${Date.now()}`,
      role: 'user',
      content: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    addMessage(userMsg);
    setIsLoading(true);

    try {
      // Build history payloads excluding HIPAA system triggers
      const activeHistoryPayload = messages
        .filter(m => m.id !== 'initial' && m.role !== 'system')
        .map(m => ({ role: m.role, content: m.content }));

      // Append somatic vitals context directly to prompt so backend knows latest telemetry meters
      const vitalsPrompt = `
[PATIENT SOMATIC VITALS UPDATE]
- Heart Rate: ${vitals.heartRate} bpm
- Blood Pressure: ${vitals.bloodPressure} mmHg
- Oral Temperature: ${vitals.temperature} °F
- Oxygen Saturation: ${vitals.oxygenSat}%
- Respiratory Rate: ${vitals.respiratoryRate}/min

[PATIENT CHIEF COMPLAINT]
${userText}
      `.trim();

      // Call Express API endpoint
      const result = await sendMessage(sessionId, vitalsPrompt, activeHistoryPayload);

      // Set state based on response
      if (result.session_id && !sessionId) {
        setSessionId(result.session_id);
      }

      setTurnCount(result.turn);

      // Create bot response Object
      const botMsg: Message = {
        id: `bot-${Date.now()}`,
        role: 'assistant',
        content: result.message,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      
      addMessage(botMsg);

      setConditions(result.conditions || []);
      setRedFlags(result.red_flags || []);
      setIsComplete(result.is_complete || false);

      // If clinical complete is reached, append System HIPAA notice pill
      if (result.is_complete) {
        const sysMsg: Message = {
          id: `sys-${Date.now()}`,
          role: 'system',
          content: "Triage parameters complete. Self-care protocols or Emergency CTA outlined."
        };
        addMessage(sysMsg);

        // Record to interactive history logs
        addHistoryItem({
          sessionId: result.session_id,
          date: new Date().toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' }),
          chiefComplaint: userText.slice(0, 48) + (userText.length > 48 ? '...' : ''),
          urgency: result.conditions?.[0]?.urgency || 'low',
          turnCount: result.turn,
          isComplete: true
        });
      }

    } catch (err: any) {
      console.error(err);
      const errSys: Message = {
        id: `err-${Date.now()}`,
        role: 'system',
        content: `Diagnostic failure: ${err.message || "Network lost"}. Checking offline triage nodes.`
      };
      addMessage(errSys);
    } finally {
      setIsLoading(false);
    }
  };

  // Generate Report action
  const handleGenerateReport = async () => {
    if (!sessionId) return;
    setIsLoading(true);
    try {
      const blob = await generateReport(sessionId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `medtriage-clinical-report-${sessionId}.md`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      const sysMsg: Message = {
        id: `sys-report-${Date.now()}`,
        role: 'system',
        content: "Clinical evaluation report downloaded successfully."
      };
      addMessage(sysMsg);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`flex flex-col h-screen overflow-hidden ${theme === 'dark' ? 'bg-surface text-on-surface' : 'light bg-slate-50 text-slate-900'}`} id="application-container">
      
      {/* 1. LAYOUT DISCLAIMER BANNER */}
      <div 
        className="bg-error text-white font-black text-[10px] sm:text-xs py-2 px-4 shadow-md text-center tracking-wider shrink-0 select-none animate-pulse flex items-center justify-center gap-2 border-b border-error/20"
        id="medical-disclaimer-banner"
      >
        <ShieldAlert className="w-4 h-4 text-white animate-spin shrink-0" />
        <span>⚠️ CRITICAL DIRECTIVE: NOT A SUBSTITUTE FOR PROFESSIONAL MEDICAL ADVICE. CALL 911 IMMEDIATELY IN EMERGENCIES.</span>
      </div>

      {/* 2. TOP APP BAR */}
      <header className="flex items-center justify-between px-6 h-16 bg-[#141829] border-b border-[#434654] shadow-sm shrink-0" id="top-app-bar">
        <div className="flex items-center gap-3 select-none" id="app-logo-section">
          <div className="w-8 h-8 bg-[#c4d2ff] rounded-lg flex items-center justify-center text-[#0a0e1a] shrink-0 shadow-md">
            <Stethoscope className="w-5 h-5 text-sans" />
          </div>
          <span className="text-xl font-semibold tracking-tight text-on-surface font-sans">
            MedTriage <span className="text-[#c4d2ff]">AI</span>
          </span>
          <span className="hidden sm:inline-block rounded px-1.5 py-0.5 text-[8px] font-bold bg-[#c4d2ff]/10 border border-[#c4d2ff]/20 text-[#c4d2ff] font-mono select-none">
            TELE_SECURE v1.4
          </span>
        </div>

        {/* Action icons stack */}
        <div className="flex items-center gap-1.5" id="app-controls">
          {/* Support Theme Toggle */}
          <button
            onClick={() => toggleTheme()}
            className="p-2 text-on-surface-variant hover:text-on-surface rounded-lg hover:bg-surface-container-high transition-colors cursor-pointer"
            id="theme-toggler"
            aria-label="Toggle visual theme"
          >
            {theme === 'dark' ? <Sun className="w-4.5 h-4.5 text-primary" /> : <Moon className="w-4.5 h-4.5 text-indigo-700" />}
          </button>

          {/* Help overlay toggler */}
          <button
            onClick={() => setHelpModalOpen(true)}
            className="p-2 text-on-surface-variant hover:text-on-surface rounded-lg hover:bg-surface-container-high transition-colors cursor-pointer"
            id="help-button"
            aria-label="How does this work"
          >
            <HelpCircle className="w-4.5 h-4.5 text-primary" />
          </button>

          {/* Profile overview toggler */}
          <button
            onClick={() => setProfileModalOpen(true)}
            className="p-2 text-on-surface-variant hover:text-on-surface rounded-lg hover:bg-surface-container-high transition-colors cursor-pointer"
            id="profile-button"
            aria-label="Patient credentials profile"
          >
            <User className="w-4.5 h-4.5 text-primary" />
          </button>
        </div>
      </header>

      {/* 3. TRIPLE-COLUMN CONTAINER */}
      <div className="flex flex-1 overflow-hidden relative" id="main-content-panels">
        
        {/* LEFT COLUMN: Sidebar Navigation (Desktop only) */}
        <aside className="hidden lg:block w-64 h-full shrink-0" id="left-sidebar-navigation">
          <SidebarNav />
        </aside>

        {/* CENTER COLUMN: Core Dynamic Workspace Canvas */}
        <main className="flex-1 flex flex-col h-full overflow-hidden bg-surface relative" id="center-chat-canvas">
          
          {/* Inner view dispatcher */}
          <AnimatePresence mode="wait">
            {activeTab === 'chat' && (
              <motion.div
                key="chat-view"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col h-full overflow-hidden p-3.5 sm:p-5 gap-3.5"
                id="chat-active-tab-panel"
              >
                {/* Session telemetry ribbon */}
                <SessionStatus sessionId={sessionId} turnCount={turnCount} isComplete={isComplete} />

                {/* Red flags alerts if found */}
                {redFlags.length > 0 && (
                  <RedFlagAlert redFlags={redFlags} />
                )}

                {/* Primary Chat Dialogue Canvas scroll frame */}
                <div 
                  className="flex-1 overflow-y-auto pr-1 space-y-4 min-h-0" 
                  id="chat-messages-scroll-area"
                >
                  {/* Conditions Cards Grid shown dynamically when items exist */}
                  {conditions.length > 0 && (
                    <div className="bg-surface-container-low border border-outline-variant p-4 rounded-xl space-y-3" id="conditions-canvas-block">
                      <div className="flex items-center justify-between select-none border-b border-outline-variant/40 pb-2 mb-2" id="conditions-canvas-hdr">
                        <span className="text-xs font-black uppercase text-on-surface-variant tracking-wider flex items-center gap-1.5 font-sans">
                          <Sparkle className="w-4 h-4 text-primary shrink-0 animate-spin" /> Live Diagnostics Profiles ({conditions.length})
                        </span>
                        <span className="text-[10px] text-on-surface-variant font-mono">
                          Click cards to review supportive action plans
                        </span>
                      </div>
                      
                      <motion.div 
                        className="grid grid-cols-1 md:grid-cols-2 gap-3" 
                        id="conditions-stagger-layout"
                        initial="hidden"
                        animate="visible"
                        variants={{
                          hidden: { opacity: 0 },
                          visible: {
                            opacity: 1,
                            transition: { staggerChildren: 0.1 }
                          }
                        }}
                      >
                        {conditions.map((cond, idx) => (
                          <ConditionCard 
                            key={idx}
                            name={cond.name}
                            description={cond.description}
                            matchPercentage={cond.match_percentage}
                            urgency={cond.urgency}
                            precautions={cond.precautions}
                            medications={cond.medications}
                            diet={cond.diet ? (Array.isArray(cond.diet) ? cond.diet.join(', ') : cond.diet) : ''}
                            workouts={cond.workouts ? (Array.isArray(cond.workouts) ? cond.workouts.join(', ') : cond.workouts) : ''}
                          />
                        ))}
                      </motion.div>
                    </div>
                  )}

                  {/* Standard Message loops */}
                  {messages.map((message, idx) => (
                    <ChatMessage key={message.id || idx} message={message} index={idx} />
                  ))}

                  {/* Loading typed bubbles */}
                  {isLoading && (
                    <TypingIndicator />
                  )}

                  {/* Invisible anchor for dynamic scrolling */}
                  <div ref={chatEndRef} />
                </div>

                {/* Bottom Input Drawer */}
                <div className="mt-auto shrink-0" id="bottom-chat-composer">
                  <ChatInput 
                    onSend={handleSendMessage} 
                    onGenerateReport={handleGenerateReport}
                    isComplete={isComplete}
                    isLoading={isLoading}
                    hasMessages={messages.length > 1}
                  />
                </div>
              </motion.div>
            )}

            {/* TAB 2: Patient Case History Dashboard */}
            {activeTab === 'history' && (
              <motion.div
                key="history-view"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5"
                id="patient-case-history-view"
              >
                <div className="border-b border-outline-variant pb-3 select-none" id="vitals-header-desc">
                  <h2 className="text-lg font-black uppercase text-on-surface font-sans flex items-center gap-2">
                    <History className="w-5.5 h-5.5 text-primary" /> Historic Patient Case Files
                  </h2>
                  <p className="text-xs text-on-surface-variant leading-relaxed mt-1 font-sans">
                    View previous clinical triage certifications recorded under current patient context profile.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4" id="case-history-list-grid">
                  {historyList.map((item, idx) => (
                    <div 
                      key={item.sessionId || idx}
                      className="bg-surface-container border border-outline-variant hover:border-outline p-4 rounded-xl text-xs space-y-3 shadow-md"
                      id={`history-item-${idx}`}
                    >
                      <div className="flex justify-between items-center" id="history-item-top">
                        <span className="font-mono text-primary font-bold uppercase select-none">{item.sessionId}</span>
                        <span className="font-mono text-on-surface-variant">{item.date}</span>
                      </div>

                      <div id="history-item-complaint">
                        <span className="text-[10px] text-on-surface-variant font-bold block uppercase tracking-wide">Chief Complaint</span>
                        <p className="text-on-surface font-sans text-sm mt-0.5 line-clamp-2">{item.chiefComplaint}</p>
                      </div>

                      <div className="flex justify-between items-center border-t border-outline-variant/30 pt-3" id="history-item-footer">
                        <div className="flex items-center gap-1.5" id="history-item-urn">
                          <span className="text-[10px] text-on-surface-variant uppercase font-bold">Risk priority:</span>
                          <span className={`text-[10px] font-black uppercase py-0.5 px-2 rounded-full ${
                            item.urgency === 'urgent' ? 'bg-error/15 text-error' :
                            item.urgency === 'moderate' ? 'bg-primary/20 text-primary' :
                            'bg-surface-container-high text-on-surface-variant'
                          }`}>
                            {item.urgency}
                          </span>
                        </div>
                        <span className="font-mono text-on-surface-variant font-medium">Turns: {item.turnCount}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* TAB 3: Somatic Vitals configuration form */}
            {activeTab === 'vitals' && (
              <motion.div
                key="vitals-view"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5"
                id="somatic-vitals-editor-view"
              >
                <div className="border-b border-outline-variant pb-3 select-none" id="vitals-header-sec">
                  <h2 className="text-lg font-black uppercase text-on-surface font-sans flex items-center gap-2">
                    <ActivitySquare className="w-5.5 h-5.5 text-primary" /> Dynamic Somatic Vitals Register
                  </h2>
                  <p className="text-xs text-on-surface-variant leading-relaxed mt-1 font-sans">
                    Configure real-time biological telemetry. These metric parameters are dynamically integrated with outgoing diagnostic chat prompts to Ground AI calculations.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-5" id="vitals-dashboard-group">
                  {/* HR Slider */}
                  <div className="bg-surface-container border border-outline-variant/80 p-4 rounded-xl space-y-3" id="vital-box-hr">
                    <div className="flex justify-between items-center select-none" id="vital-hdr-hr">
                      <span className="font-sans font-bold text-xs uppercase text-on-surface-variant">Pulse / Heart Rate</span>
                      <span className="font-mono text-base font-bold text-primary">{vitals.heartRate} <span className="text-xs">bpm</span></span>
                    </div>
                    <input 
                      type="range" 
                      min="40" 
                      max="180" 
                      value={vitals.heartRate} 
                      onChange={(e) => updateVitals({ heartRate: e.target.value })}
                      className="w-full accent-primary bg-surface-container-low border border-outline/20 h-2 rounded cursor-pointer"
                      id="vital-slider-hr"
                    />
                    <div className="flex justify-between text-[10px] text-on-surface-variant/80 font-mono" id="vital-footer-hr">
                      <span>Bradycardic</span>
                      <span>Resting (60-100)</span>
                      <span>Tachycardic</span>
                    </div>
                  </div>

                  {/* Oral Temperation Slider */}
                  <div className="bg-surface-container border border-outline-variant/80 p-4 rounded-xl space-y-3" id="vital-box-temp">
                    <div className="flex justify-between items-center select-none" id="vital-hdr-temp">
                      <span className="font-sans font-bold text-xs uppercase text-on-surface-variant">Oral Temperature</span>
                      <span className="font-mono text-base font-bold text-primary">{vitals.temperature} <span className="text-xs">°F</span></span>
                    </div>
                    <input 
                      type="range" 
                      min="95" 
                      max="106" 
                      step="0.1"
                      value={vitals.temperature} 
                      onChange={(e) => updateVitals({ temperature: e.target.value })}
                      className="w-full accent-primary bg-surface-container-low border border-outline/20 h-2 rounded cursor-pointer"
                      id="vital-slider-temp"
                    />
                    <div className="flex justify-between text-[10px] text-on-surface-variant/80 font-mono" id="vital-footer-temp">
                      <span>Hypothermia</span>
                      <span>Physiological Normal</span>
                      <span>Hyperpyrexia (Fever)</span>
                    </div>
                  </div>

                  {/* SaO2 Oxygen saturation Slider */}
                  <div className="bg-surface-container border border-outline-variant/80 p-4 rounded-xl space-y-3" id="vital-box-spo2">
                    <div className="flex justify-between items-center select-none" id="vital-hdr-spo2">
                      <span className="font-sans font-bold text-xs uppercase text-on-surface-variant">SpO2 Oxygen Saturation</span>
                      <span className="font-mono text-base font-bold text-primary">{vitals.oxygenSat} <span className="text-xs">%</span></span>
                    </div>
                    <input 
                      type="range" 
                      min="80" 
                      max="100" 
                      value={vitals.oxygenSat} 
                      onChange={(e) => updateVitals({ oxygenSat: e.target.value })}
                      className="w-full accent-primary bg-surface-container-low border border-outline/20 h-2 rounded cursor-pointer"
                      id="vital-slider-spo2"
                    />
                    <div className="flex justify-between text-[10px] text-on-surface-variant/80 font-mono" id="vital-footer-spo2">
                      <span>Critical Hypoxia</span>
                      <span>Target Sat Range (95-100)</span>
                    </div>
                  </div>

                  {/* Respiratory rate Slider */}
                  <div className="bg-surface-container border border-outline-variant/80 p-4 rounded-xl space-y-3" id="vital-box-rr">
                    <div className="flex justify-between items-center select-none" id="vital-hdr-rr">
                      <span className="font-sans font-bold text-xs uppercase text-on-surface-variant">Respiratory Frequency</span>
                      <span className="font-mono text-base font-bold text-primary">{vitals.respiratoryRate} <span className="text-xs">/min</span></span>
                    </div>
                    <input 
                      type="range" 
                      min="8" 
                      max="40" 
                      value={vitals.respiratoryRate} 
                      onChange={(e) => updateVitals({ respiratoryRate: e.target.value })}
                      className="w-full accent-primary bg-surface-container-low border border-outline/20 h-2 rounded cursor-pointer"
                      id="vital-slider-rr"
                    />
                    <div className="flex justify-between text-[10px] text-on-surface-variant/80 font-mono" id="vital-footer-rr">
                      <span>Bradypnea</span>
                      <span>Normal (12-16)</span>
                      <span>Tachypnea</span>
                    </div>
                  </div>

                  {/* Blood pressure input */}
                  <div className="bg-surface-container border border-outline-variant/80 p-4 rounded-xl space-y-3 md:col-span-2" id="vital-box-bp">
                    <div className="flex items-center justify-between" id="vital-hdr-bp">
                      <span className="font-sans font-bold text-xs uppercase text-on-surface-variant block">Blood Pressure Telemetry</span>
                      <span className="font-mono text-xs text-primary bg-primary-container/10 px-2 py-0.5 rounded border border-primary/20">Active: {vitals.bloodPressure} mmHg</span>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 pt-1" id="bp-inputs-grid">
                      <div id="bp-systolic">
                        <label className="text-[10px] text-on-surface-variant font-bold block mb-1 font-sans">Systolic Target (e.g. 120)</label>
                        <input 
                          type="text" 
                          placeholder="Systolic" 
                          defaultValue="120"
                          onChange={(e) => {
                            const dia = vitals.bloodPressure.split('/')[1] || '80';
                            updateVitals({ bloodPressure: `${e.target.value || '120'}/${dia}` });
                          }}
                          className="w-full rounded border border-outline bg-surface-container-low px-3 py-2 text-xs text-on-surface focus:outline-none focus:border-primary"
                        />
                      </div>
                      <div id="bp-diastolic">
                        <label className="text-[10px] text-on-surface-variant font-bold block mb-1 font-sans">Diastolic Target (e.g. 80)</label>
                        <input 
                          type="text" 
                          placeholder="Diastolic" 
                          defaultValue="80"
                          onChange={(e) => {
                            const sys = vitals.bloodPressure.split('/')[0] || '120';
                            updateVitals({ bloodPressure: `${sys}/${e.target.value || '80'}` });
                          }}
                          className="w-full rounded border border-outline bg-surface-container-low px-3 py-2 text-xs text-on-surface focus:outline-none focus:border-primary"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </main>

        {/* RIGHT COLUMN: Clinical Assessment Sidebar (Desktop only) */}
        <aside className="hidden xl:block w-80 h-full shrink-0 border-l border-[#434654]" id="right-assessment-sidebar">
          <AssessmentSidebar conditions={conditions} turnCount={turnCount} isComplete={isComplete} />
        </aside>

      </div>

      {/* 4. CLINICAL COMPLIANCE BOTTOM NAV BAR (Mobile and Tablet only) */}
      <nav className="flex items-center justify-around bg-surface-container border-t border-outline-variant/60 py-2 sm:py-3 px-4 shrink-0 lg:hidden shadow-lg select-none" id="mobile-navigation-bar">
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex flex-col items-center gap-1 text-[10px] font-bold ${
            activeTab === 'chat' ? 'text-primary' : 'text-on-surface-variant hover:text-on-surface'
          }`}
          id="mobile-nav-chat"
        >
          <MessageSquare className="w-4.5 h-4.5" />
          <span>Triage Chat</span>
        </button>

        <button
          onClick={() => setActiveTab('history')}
          className={`flex flex-col items-center gap-1 text-[10px] font-bold ${
            activeTab === 'history' ? 'text-primary' : 'text-on-surface-variant hover:text-on-surface'
          }`}
          id="mobile-nav-history"
        >
          <History className="w-4.5 h-4.5" />
          <span>Case History</span>
        </button>

        <button
          onClick={() => setActiveTab('vitals')}
          className={`flex flex-col items-center gap-1 text-[10px] font-bold ${
            activeTab === 'vitals' ? 'text-primary' : 'text-on-surface-variant hover:text-on-surface'
          }`}
          id="mobile-nav-vitals"
        >
          <ActivitySquare className="w-4.5 h-4.5" />
          <span>Somatic Vitals</span>
        </button>
      </nav>

      {/* -------------------------------------------------------------
          MODALS & OVERLAYS
          ------------------------------------------------------------- */}
      
      {/* A. HELP EXPLAINING DIALOG MODAL */}
      <AnimatePresence>
        {helpModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm select-none" id="help-modal-overlay">
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="bg-surface-container border border-outline w-full max-w-md p-5 rounded-xl space-y-4 shadow-2xl relative"
              id="help-modal-box"
            >
              <h3 className="text-base font-black uppercase text-on-surface flex items-center gap-2 border-b border-outline pb-2 font-sans" id="help-modal-title">
                <HelpCircle className="w-5.5 h-5.5 text-primary" /> Clinical AI Help Core
              </h3>
              
              <div className="space-y-3.5 text-xs text-on-surface-variant leading-relaxed font-sans" id="help-modal-body">
                <p>
                  MedTriage AI is an interactive diagnostic companion engineered to streamline somatic complaints, prioritize physiological probabilities, and outline precaution advice parameters.
                </p>
                <div className="bg-surface-container-low border border-outline rounded p-2.5 space-y-2" id="help-step-box">
                  <div className="flex gap-2" id="step-1">
                    <span className="font-mono text-primary font-bold">1.</span>
                    <p>Provide description of any current discomforts, duration, and local pain traits in the chat.</p>
                  </div>
                  <div className="flex gap-2" id="step-2">
                    <span className="font-mono text-primary font-bold">2.</span>
                    <p>Adjust values in your **Somatic Vitals Register** tab to inject precise physiological benchmarks into AI calculations.</p>
                  </div>
                  <div className="flex gap-2" id="step-3">
                    <span className="font-mono text-primary font-bold">3.</span>
                    <p>Export case markdown logs at any turn for diagnostic handoff to licensed physicians.</p>
                  </div>
                </div>
              </div>

              <button
                onClick={() => setHelpModalOpen(false)}
                className="w-full bg-primary-container text-white text-xs font-bold py-2.5 rounded hover:bg-primary-container/90 transition-colors"
                id="close-help-btn"
              >
                Understood
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* B. PROFILE DIALOG OVERLAY */}
      <AnimatePresence>
        {profileModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm select-none" id="profile-modal-overlay">
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="bg-surface-container border border-outline w-full max-w-sm p-5 rounded-xl space-y-4 shadow-2xl relative"
              id="patient-profile-modal"
            >
              <h3 className="text-base font-black uppercase text-on-surface flex items-center gap-2 border-b border-outline pb-2 font-sans" id="profile-modal-title">
                <User className="w-5.5 h-5.5 text-primary" /> Patient Record Card
              </h3>

              <div className="space-y-3.5 text-xs text-on-surface-variant font-sans" id="profile-modal-body">
                <div className="grid grid-cols-2 gap-3" id="patient-data-grid">
                  <div id="patient-age">
                    <span className="text-[10px] text-on-surface-variant font-bold uppercase tracking-wide">Age</span>
                    <p className="text-on-surface mt-0.5">34 Years old</p>
                  </div>
                  <div id="patient-gender">
                    <span className="text-[10px] text-on-surface-variant font-bold uppercase tracking-wide">Sex Assigned</span>
                    <p className="text-on-surface mt-0.5">Male</p>
                  </div>
                  <div id="patient-uid" className="col-span-2">
                    <span className="text-[10px] text-on-surface-variant font-bold uppercase tracking-wide">Patient Reference ID</span>
                    <p className="text-on-surface mt-0.5 font-mono select-all text-xs">MTRAC-9482-BOB3</p>
                  </div>
                </div>

                <div className="bg-surface-container-low border border-outline/30 rounded p-2 text-[10px] leading-relaxed text-on-surface-variant border-l-2 border-l-primary" id="profile-note">
                  <b>Clinical Note:</b> Patient profiles are stored solely inside temporary local workspace contexts. No HIPAA-protected data is persisted persistently.
                </div>
              </div>

              <button
                onClick={() => setProfileModalOpen(false)}
                className="w-full bg-primary-container text-white text-xs font-bold py-2.5 rounded hover:bg-primary-container/90 transition-colors"
                id="close-profile-btn"
              >
                Close Profile
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </div>
  );
}
