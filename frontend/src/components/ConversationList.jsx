function formatDate(value) {
  return new Date(value).toLocaleString(undefined, {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Backend title ke roop mein pehla user message bhejta hai. Khaali conversation
// mein wo null hota hai, tab id hi dikhate hain.
function conversationName(conversation) {
  const title = conversation.title?.trim()

  if (!title) return `Untitled · ${conversation.conversation_id.slice(0, 8)}`
  return title
}

export default function ConversationList({
  conversations,
  activeId,
  isOpen,
  onSelect,
  onDelete,
  onNewChat,
  onToggle,
}) {
  if (!isOpen) return null

  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <button className="new-chat" onClick={onNewChat}>
          + New chat
        </button>

        <button className="sidebar-toggle" onClick={onToggle} title="Hide sidebar">
          ‹
        </button>
      </div>

      <div className="conversation-list">
        {conversations.length === 0 && (
          <p className="empty-note">No conversations yet.</p>
        )}

        {conversations.map((conversation) => {
          const id = conversation.conversation_id
          const isActive = id === activeId

          return (
            <div key={id} className={`conversation ${isActive ? 'active' : ''}`}>
              <button className="conversation-open" onClick={() => onSelect(id)}>
                <span className="conversation-title">
                  {conversationName(conversation)}
                </span>
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
