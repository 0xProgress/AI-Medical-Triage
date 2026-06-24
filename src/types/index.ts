// types/index.ts

export interface Message {
  id: string; // Unique message ID
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface Condition {
  name: string;
  description: string;
  match_percentage: number;
  urgency: 'urgent' | 'moderate' | 'low';
  precautions: string[];
  medications: string[];
  diet: string[];
  workouts: string[];
}

export interface ChatResponse {
  session_id: string;
  message: string;
  conditions: Condition[];
  follow_up_question?: string;
  red_flags: string[];
  is_complete: boolean;
  turn: number;
}

export interface Vitals {
  heartRate: string;
  bloodPressure: string;
  temperature: string;
  oxygenSat: string;
  respiratoryRate: string;
  timestamp: string;
}

export interface SessionHistoryItem {
  sessionId: string;
  date: string;
  chiefComplaint: string;
  urgency: 'urgent' | 'moderate' | 'low';
  turnCount: number;
  isComplete: boolean;
}
