import { create } from 'zustand';
import { Message, Condition } from '../types';

interface ChatState {
  sessionId: string | null;
  messages: Message[];
  conditions: Condition[];
  redFlags: string[];
  isComplete: boolean;
  turnCount: number;
  isLoading: boolean;
  theme: 'dark' | 'light';
  helpModalOpen: boolean;

  setSessionId: (id: string | null) => void;
  addMessage: (msg: Message) => void;
  setConditions: (conditions: Condition[]) => void;
  setRedFlags: (flags: string[]) => void;
  setIsComplete: (complete: boolean) => void;
  setTurnCount: (count: number) => void;
  setIsLoading: (loading: boolean) => void;
  toggleTheme: () => void;
  setHelpModalOpen: (open: boolean) => void;
  reset: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  sessionId: null,
  messages: [],
  conditions: [],
  redFlags: [],
  isComplete: false,
  turnCount: 0,
  isLoading: false,
  theme: 'dark',
  helpModalOpen: false,

  setSessionId: (id) => set({ sessionId: id }),
  addMessage: (msg) => set((state) => {
    if (state.messages.some(m => m.id === msg.id)) return {};
    return { messages: [...state.messages, msg] };
  }),
  setConditions: (conditions) => set({ conditions }),
  setRedFlags: (redFlags) => set({ redFlags }),
  setIsComplete: (isComplete) => set({ isComplete }),
  setTurnCount: (turnCount) => set({ turnCount }),
  setIsLoading: (isLoading) => set({ isLoading }),
  toggleTheme: () => set((state) => {
    const next = state.theme === 'dark' ? 'light' : 'dark';
    if (next === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    return { theme: next };
  }),
  setHelpModalOpen: (helpModalOpen) => set({ helpModalOpen }),
  reset: () => set({
    sessionId: null,
    messages: [
      {
        id: 'initial',
        role: 'assistant',
        content: "Hello, I'm your AI Medical Triage Assistant. Please describe your symptoms and I'll help identify possible conditions.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ],
    conditions: [],
    redFlags: [],
    isComplete: false,
    turnCount: 0,
    isLoading: false,
  })
}));