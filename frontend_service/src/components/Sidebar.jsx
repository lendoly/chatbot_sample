export default function Sidebar({ sessions, currentSession, onSelect, onCreate }) {
  return (
    <div className="sidebar">
      <h2>Sessions</h2>
      <ul>
        {sessions.map((id) => (
          <li key={id} className={id === currentSession ? 'active' : ''}>
            <span onClick={() => onSelect(id)}>{id}</span>
          </li>
        ))}
      </ul>
      <button className="new-session" onClick={onCreate}>
        + New Session
      </button>
    </div>
  );
}
