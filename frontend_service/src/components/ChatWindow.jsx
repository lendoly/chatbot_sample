import { useEffect, useRef } from 'react';

export default function ChatWindow({ messages, isLoading }) {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="chat-window" ref={ref}>
      {messages.map((msg) => (
        <div key={msg.id} className={`message ${msg.sender}`}>
          {msg.text}
        </div>
      ))}
      {isLoading && <div className="message bot loading">...</div>}
    </div>
  );
}
