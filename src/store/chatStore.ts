import { create } from 'zustand';
import { Message, Condition, Vitals, SessionHistoryItem } from '../types';

interface ChatState {
  sessionId: string | null;
  messages: Message[];
  conditions: Condition[];
  redFlags: string[];
  isComplete: boolean;
  turnCount: number;
  symptoms: string[];
  isLoading: boolean;
  
  // Custom states for interactive features
  activeTab: 'chat' | 'history' | 'vitals';
  theme: 'dark' | 'light';
  vitals: Vitals;
  historyList: SessionHistoryItem[];
  helpModalOpen: boolean;
  profileModalOpen: boolean;

  // Actions
  setSessionId: (id: string | null) => void;
  addMessage: (msg: Message) => void;
  setMessages: (messages: Message[]) => void;
  setConditions: (conditions: Condition[]) => void;
  setRedFlags: (flags: string[]) => void;
  setIsComplete: (complete: boolean) => void;
  setTurnCount: (count: number) => void;
  setIsLoading: (loading: boolean) => void;
  setSymptoms: (symptoms: string[]) => void;
  
  // Custom Action Methods
  setActiveTab: (tab: 'chat' | 'history' | 'vitals') => void;
  toggleTheme: () => void;
  updateVitals: (vitals: Partial<Vitals>) => void;
  addHistoryItem: (item: SessionHistoryItem) => void;
  setHelpModalOpen: (open: boolean) => void;
  setProfileModalOpen: (open: boolean) => void;
  reset: () => void;
}

const initialVitals: Vitals = {
  heartRate: '72',
  bloodPressure: '120/80',
  temperature: '98.6',
  oxygenSat: '98',
  respiratoryRate: '16',
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
};

export const useChatStore = create<ChatState>((set) => ({
  sessionId: null,
  messages: [],
  conditions: [],
  redFlags: [],
  isComplete: false,
  turnCount: 0,
  symptoms: [],
  isLoading: false,

  activeTab: 'chat',
  theme: 'dark',
  vitals: initialVitals,
  historyList: [],
  helpModalOpen: false,
  profileModalOpen: false,

  setSessionId: (id) => set({ sessionId: id }),
  addMessage: (msg) => set((state) => {
    // Avoid double-adding
    if (state.messages.some(m => m.id === msg.id)) return {};
    return { messages: [...state.messages, msg] };
  }),
  setMessages: (messages) => set({ messages }),
  setConditions: (conditions) => set({ conditions }),
  setRedFlags: (redFlags) => set({ redFlags }),
  setIsComplete: (isComplete) => set({ isComplete }),
  setTurnCount: (turnCount) => set({ turnCount }),
  setIsLoading: (isLoading) => set({ isLoading }),
  setSymptoms: (symptoms) => set({ symptoms }),

  setActiveTab: (activeTab) => set({ activeTab }),
  toggleTheme: () => set((state) => {
    const nextTheme = state.theme === 'dark' ? 'light' : 'dark';
    if (nextTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    return { theme: nextTheme };
  }),
  updateVitals: (vitalsUpdate) => set((state) => ({
    vitals: { 
      ...state.vitals, 
      ...vitalsUpdate,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  })),
  addHistoryItem: (item) => set((state) => ({
    historyList: [item, ...state.historyList]
  })),
  setHelpModalOpen: (helpModalOpen) => set({ helpModalOpen }),
  setProfileModalOpen: (profileModalOpen) => set({ profileModalOpen }),
  reset: () => set({
    sessionId: null,
    messages: [
      {
        id: 'initial',
        role: 'assistant',
        content: "Hello, I am your Clinical AI Triage Assistant. Please describe your symptoms and their duration in detail so I can determine the appropriate level of urgency and prioritize potential causes.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ],
    conditions: [],
    redFlags: [],
    isComplete: false,
    turnCount: 0,
    symptoms: [],
    isLoading: false,
    activeTab: 'chat'
  })
}));
