import { useState, useEffect, useCallback, useRef } from 'react';
import './App.css';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import MessageInput from './components/MessageInput';
import * as api from './api';

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState('');
  const [messages, setMessages] = useState([]);
  const [prompt, setPrompt] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState('');
  const msgId = useRef(0);

  useEffect(() => {
    api.fetchSessions()
      .then(setSessions)
      .catch(() => setError('Could not load sessions.'));
  }, []);

  const createSession = useCallback(() => {
    const id = crypto.randomUUID();
    setSessions((prev) => [...prev, id]);
    setCurrentSession(id);
    setMessages([]);
    setError('');
  }, []);

  const selectSession = useCallback(async (id) => {
    setCurrentSession(id);
    setError('');
    try {
      const msgs = await api.fetchMessages(id);
      setMessages(msgs.map((m) => ({ id: m.timestamp, sender: m.sender, text: m.text })));
    } catch {
      setError('Could not load messages for this session.');
      setMessages([]);
    }
  }, []);

  const deleteSession = useCallback(async (id) => {
    if (!window.confirm(`Delete session ${id}? This cannot be undone.`)) return;
    try {
      await api.deleteSession(id);
      setSessions((prev) => prev.filter((s) => s !== id));
      if (currentSession === id) {
        setCurrentSession('');
        setMessages([]);
      }
    } catch {
      setError('Could not delete session.');
    }
  }, [currentSession]);

  const sendPrompt = useCallback(async () => {
    if (!currentSession) {
      setError('Please select or create a session first.');
      return;
    }
    if (!prompt.trim() || isSending) return;

    const userMsg = { id: msgId.current++, sender: 'user', text: prompt };
    setMessages((prev) => [...prev, userMsg]);
    setPrompt('');
    setIsSending(true);
    setError('');

    try {
      const response = await api.sendMessage(currentSession, userMsg.text);
      const botMsg = { id: msgId.current++, sender: 'bot', text: response };
      setMessages((prev) => [...prev, botMsg]);
    } catch {
      setError('Failed to send message. Please try again.');
    } finally {
      setIsSending(false);
    }
  }, [currentSession, prompt, isSending]);

  return (
    <div className="App">
      <Header sessionId={currentSession} onDelete={() => deleteSession(currentSession)} />
      {error && <div className="error">{error}</div>}
      <div className="chat-container">
        <Sidebar
          sessions={sessions}
          currentSession={currentSession}
          onSelect={selectSession}
          onCreate={createSession}
        />
        <ChatWindow messages={messages} isLoading={isSending} />
      </div>
      <MessageInput
        value={prompt}
        onChange={setPrompt}
        onSend={sendPrompt}
        disabled={isSending}
      />
    </div>
  );
}
