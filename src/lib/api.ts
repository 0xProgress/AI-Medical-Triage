// src/lib/api.ts
import { ChatResponse } from '../types';

// const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';
const API_BASE = 'https://ai-medical-triage-bk.onrender.com/api/v1';

export async function sendMessage(
  sessionId: string | null,
  message: string,
  history: { role: 'user' | 'assistant' | 'system'; content: string }[]
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      message,
      history,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export async function generateReport(sessionId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE}/report`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to generate report: ${response.status}`);
  }

  return response.blob();
}

export async function getSession(sessionId: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/session/${sessionId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to retrieve session: ${response.status}`);
  }

  return response.json();
}

export async function healthCheck(): Promise<{ status: string }> {
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) throw new Error('Unhealthy');
    return response.json();
  } catch (err) {
    return { status: 'down' };
  }
}
