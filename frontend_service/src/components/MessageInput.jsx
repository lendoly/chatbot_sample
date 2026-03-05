export default function MessageInput({ value, onChange, onSend, disabled }) {
  return (
    <div className="input-area">
      <input
        className="prompt"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Type a message"
        onKeyDown={(e) => e.key === 'Enter' && !disabled && onSend()}
      />
      <button className="send" onClick={onSend} disabled={disabled || !value.trim()}>
        Send
      </button>
    </div>
  );
}
