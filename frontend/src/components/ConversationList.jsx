function formatDate(value) {
  return new Date(value).toLocaleString(undefined, {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function ConversationList({
  conversations,
  activeId,
  onSelect,
  onDelete,
  onNewChat,
}) {
  return (
    <aside className="sidebar">
      <button className="new-chat" onClick={onNewChat}>
        + New chat
      </button>

      <div className="conversation-list">
        {conversations.length === 0 && (
          <p className="empty-note">Abhi koi conversation nahi hai.</p>
        )}

        {conversations.map((conversation) => {
          const id = conversation.conversation_id
          const isActive = id === activeId

          return (
            <div
              key={id}
              className={`conversation ${isActive ? 'active' : ''}`}
            >
              <button className="conversation-open" onClick={() => onSelect(id)}>
                <span className="conversation-id">{id.slice(0, 8)}</span>
                <span className="conversation-date">
                  {formatDate(conversation.created_at)}
                </span>
              </button>

              <button
                className="conversation-delete"
                title="Delete conversation"
                onClick={() => onDelete(id)}
              >
                ×
              </button>
            </div>
          )
        })}
      </div>
    </aside>
  )
}
