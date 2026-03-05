const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export async function fetchSessions() {
  const res = await fetch(`${BASE_URL}/sessions`);
  if (!res.ok) throw new Error('Failed to fetch sessions');
  const data = await res.json();
  return Array.isArray(data.sessions) ? data.sessions : [];
}

export async function fetchMessages(sessionId) {
  const res = await fetch(`${BASE_URL}/sessions/${sessionId}/messages`);
  if (!res.ok) throw new Error('Failed to fetch messages');
  const data = await res.json();
  return data.messages ?? [];
}

export async function sendMessage(sessionId, prompt) {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, session_id: sessionId }),
  });
  if (!res.ok) throw new Error('Failed to send message');
  const data = await res.json();
  return data.response;
}

export async function deleteSession(sessionId) {
  const res = await fetch(`${BASE_URL}/sessions/${sessionId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete session');
}
