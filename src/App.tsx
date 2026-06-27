import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useChatStore } from './store/chatStore';
import { sendMessage, generateReport } from './lib/api';
import { Message } from './types';

import SidebarNav from './components/SidebarNav';
import SessionStatus from './components/SessionStatus';
import ChatMessage from './components/ChatMessage';
import ConditionCard from './components/ConditionCard';
import RedFlagAlert from './components/RedFlagAlert';
import ChatInput from './components/ChatInput';
import AssessmentSidebar from './components/AssessmentSidebar';
import TypingIndicator from './components/TypingIndicator';

import { 
  HeartPulse, 
  Sun, 
  Moon, 
  HelpCircle, 
  ShieldAlert, 
  Stethoscope, 
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
    theme,
    helpModalOpen,
    setSessionId,
    addMessage,
    setConditions,
    setRedFlags,
    setIsComplete,
    setTurnCount,
    setIsLoading,
    toggleTheme,
    setHelpModalOpen,
    reset
  } = useChatStore();

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messages.length === 0) {
      reset();
    }
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async (userText: string) => {
    if (!userText.trim() || isLoading || isComplete) return;

    const userMsg: Message = {
      id: `usr-${Date.now()}`,
      role: 'user',
      content: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    addMessage(userMsg);
    setIsLoading(true);

    try {
      const historyPayload = messages
        .filter(m => m.role !== 'system')
        .map(m => ({ role: m.role, content: m.content }));

      const result = await sendMessage(sessionId, userText, historyPayload);

      if (result.session_id && !sessionId) {
        setSessionId(result.session_id);
      }

      setTurnCount(result.turn);

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

    } catch (err: any) {
      console.error(err);
      addMessage({
        id: `err-${Date.now()}`,
        role: 'system',
        content: `Error: ${err.message || "Connection failed. Please try again."}`
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!sessionId) return;
    setIsLoading(true);
    try {
      const base64Url = await generateReport(sessionId);
      
      const link = document.createElement('a');
      link.href = base64Url;
      link.download = `medical-triage-report-${sessionId.slice(0, 8)}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      addMessage({
        id: `sys-report-${Date.now()}`,
        role: 'system',
        content: "Report downloaded successfully."
      });
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`flex flex-col h-screen overflow-hidden ${theme === 'dark' ? 'bg-surface text-on-surface' : 'light bg-slate-50 text-slate-900'}`}>
      
      {/* Disclaimer Banner */}
      <div className="bg-red-600 text-white text-xs py-2 px-4 text-center font-semibold shrink-0 flex items-center justify-center gap-2">
        <ShieldAlert className="w-4 h-4" />
        <span>This is not a substitute for professional medical advice. Call 911 in emergencies.</span>
      </div>

      {/* Top Bar */}
      <header className="flex items-center justify-between px-6 h-16 bg-[#141829] border-b border-[#434654] shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-[#c4d2ff] rounded-lg flex items-center justify-center">
            <Stethoscope className="w-5 h-5 text-[#0a0e1a]" />
          </div>
          <span className="text-xl font-semibold text-white">
            MedTriage <span className="text-[#c4d2ff]">AI</span>
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <button onClick={toggleTheme} className="p-2 text-gray-400 hover:text-white rounded-lg transition-colors">
            {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
          <button onClick={() => setHelpModalOpen(true)} className="p-2 text-gray-400 hover:text-white rounded-lg transition-colors">
            <HelpCircle className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        
        {/* Left Sidebar */}
        <aside className="hidden lg:block w-64 h-full shrink-0">
          <SidebarNav />
        </aside>

        {/* Center Chat */}
        <main className="flex-1 flex flex-col h-full overflow-hidden bg-surface">
          <div className="flex flex-col h-full p-4 sm:p-5 gap-3">
            <SessionStatus sessionId={sessionId} turnCount={turnCount} isComplete={isComplete} />

            {redFlags.length > 0 && <RedFlagAlert redFlags={redFlags} />}

            <div className="flex-1 overflow-y-auto space-y-4 min-h-0">
              {conditions.length > 0 && (
                <div className="bg-surface-container-low border border-outline-variant p-4 rounded-xl space-y-3">
                  <div className="flex items-center gap-1.5 border-b border-outline-variant/40 pb-2">
                    <Sparkle className="w-4 h-4 text-primary" />
                    <span className="text-xs font-bold uppercase text-on-surface-variant">
                      Possible Conditions ({conditions.length})
                    </span>
                  </div>
                  
                  <motion.div 
                    className="grid grid-cols-1 md:grid-cols-2 gap-3"
                    initial="hidden"
                    animate="visible"
                    variants={{
                      hidden: { opacity: 0 },
                      visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
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

              {messages.map((message, idx) => (
                <ChatMessage key={message.id || idx} message={message} index={idx} />
              ))}

              {isLoading && <TypingIndicator />}
              <div ref={chatEndRef} />
            </div>

            <div className="mt-auto shrink-0">
              <ChatInput 
                onSend={handleSendMessage} 
                onGenerateReport={handleGenerateReport}
                isComplete={isComplete}
                isLoading={isLoading}
                hasMessages={messages.length > 1}
              />
            </div>
          </div>
        </main>

        {/* Right Sidebar */}
        <aside className="hidden xl:block w-80 h-full shrink-0 border-l border-[#434654]">
          <AssessmentSidebar conditions={conditions} turnCount={turnCount} isComplete={isComplete} />
        </aside>
      </div>

      {/* Help Modal */}
      <AnimatePresence>
        {helpModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="bg-surface-container border border-outline w-full max-w-md p-5 rounded-xl space-y-4 shadow-2xl"
            >
              <h3 className="text-base font-bold uppercase text-on-surface border-b border-outline pb-2 flex items-center gap-2">
                <HelpCircle className="w-5 h-5 text-primary" /> How It Works
              </h3>
              
              <div className="space-y-3 text-sm text-on-surface-variant">
                <p>MedTriage AI helps identify possible medical conditions based on your reported symptoms.</p>
                <div className="bg-surface-container-low border border-outline rounded p-3 space-y-2">
                  <p><span className="font-bold text-primary">1.</span> Describe your symptoms in the chat.</p>
                  <p><span className="font-bold text-primary">2.</span> Answer follow-up questions to narrow down possibilities.</p>
                  <p><span className="font-bold text-primary">3.</span> Download a report to share with your doctor.</p>
                </div>
                <p className="text-xs text-red-500 font-semibold">This is not a diagnosis. Always consult a licensed healthcare provider.</p>
              </div>

              <button
                onClick={() => setHelpModalOpen(false)}
                className="w-full bg-primary text-white text-sm font-bold py-2.5 rounded hover:opacity-90 transition-opacity"
              >
                Got it
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}