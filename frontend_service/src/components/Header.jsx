export default function Header({ sessionId, onDelete }) {
  return (
    <header>
      Chatbot
      {sessionId && (
        <button className="chat-delete-session" onClick={onDelete}>
          DELETE
        </button>
      )}
    </header>
  );
}
