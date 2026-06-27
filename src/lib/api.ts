import { ChatResponse } from '../types';

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
      conversation_history: history,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export async function generateReport(sessionId: string): Promise<string> {
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
    throw new Error(errorData.detail || `Failed to generate report: ${response.status}`);
  }

  const data = await response.json();
  return data.download_url; // base64 data URL
}

export async function getSession(sessionId: string) {
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
  } catch {
    return { status: 'down' };
  }
}