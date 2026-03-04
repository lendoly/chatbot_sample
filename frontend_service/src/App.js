import React, { useState, useRef } from 'react';
import './App.css';

function App() {
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState('');
  const [error, setError] = useState('');

  // show popup when error changes
  React.useEffect(() => {
    if (error) {
      alert(error);
      setError('');
    }
  }, [error]);
  const chatWindowRef = useRef(null);

  const createNewSession = () => {
    const newId = (window.crypto && crypto.randomUUID && crypto.randomUUID()) ||
      Math.random().toString(36).substring(2, 10);
    setSessions(prev => [...prev, newId]);
    setCurrentSession(newId);
    setMessages([]);
  };

  const sendPrompt = async () => {
    if (!currentSession) {
      setError('Please select or create a session first.');
      return;
    }
    if (!prompt.trim()) return;
    setError('');
    const userMsg = { text: prompt, sender: 'user' };
    setMessages(prev => [...prev, userMsg]);
    setPrompt('');

    const res = await fetch('http://localhost:5000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: userMsg.text, session_id: currentSession }),
    });
    const data = await res.json();
    const botMsg = { text: data.response, sender: 'bot' };
    setMessages(prev => [...prev, botMsg]);

    // scroll to bottom
    setTimeout(() => {
      if (chatWindowRef.current) {
        chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
      }
    }, 100);
  };

  // load session list on mount
  React.useEffect(() => {
    fetch('http://localhost:5000/sessions')
      .then(res => res.json())
      .then(data => {
        const list = data && Array.isArray(data.sessions) ? data.sessions : [];
        setSessions(list);
        // leave currentSession empty until user selects or creates one
      })
      .catch(err => {
        console.error('failed to load sessions', err);
        setSessions([]);
      });
  }, []);

  const selectSession = async (id) => {
    setCurrentSession(id);
    // fetch previous messages from backend
    try {
      const res = await fetch(`http://localhost:5000/sessions/${id}/messages`);
      const data = await res.json();
      if (data.messages) {
        setMessages(data.messages.map(m => ({ text: m.text, sender: m.sender })));
      } else {
        setMessages([]);
      }
    } catch (err) {
      console.error('failed to load session messages', err);
      setMessages([]);
    }
  };

  return (
    <div className="App">
      <header>
        Chatbot
        {currentSession && (
          <button
            className="chat-delete-session"
            onClick={() => {
              if (!window.confirm(`Delete session ${currentSession}? This cannot be undone.`)) return;
              window.fetch(`http://localhost:5000/sessions/${currentSession}`, { method: 'DELETE' })
                .then(res => {
                  if (res.ok) {
                    setSessions(prev => prev.filter(s => s !== currentSession));
                    setCurrentSession('');
                    setMessages([]);
                  }
                })
                .catch(console.error);
            }}
          >DELETE</button>
        )}
      </header>
      <div className="chat-container">
        <div className="sidebar">
          <h2>Sessions</h2>
          <ul>
            {(sessions || []).map(id => (
              <li
                key={id}
                className={id === currentSession ? 'active' : ''}
              >
                <span onClick={() => selectSession(id)}>{id}</span>
                <button
                  className="delete-session"
                  onClick={() => {
                    if (!window.confirm(`Delete session ${id}? This cannot be undone.`)) return;
                    window.fetch(`http://localhost:5000/sessions/${id}`, { method: 'DELETE' })
                      .then(res => {
                        if (res.ok) {
                          setSessions(prev => prev.filter(s => s !== id));
                          if (currentSession === id) {
                            setCurrentSession('');
                            setMessages([]);
                          }
                        }
                      })
                      .catch(console.error);
                  }}
                >DELETE</button>
              </li>
            ))}
          </ul>
          <button className="new-session" onClick={createNewSession}>
            + New Session
          </button>
        </div>
        <div className="chat-window" ref={chatWindowRef}>
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.sender}`}>
              {msg.text}
            </div>
          ))}
        </div>
      </div>
      <div className="input-area">
        <input
          className="prompt"
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          placeholder="Type a message"
          onKeyDown={e => e.key === 'Enter' && sendPrompt()}
        />
        <button className="send" onClick={sendPrompt} disabled={!prompt.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}

export default App;
