import { useEffect, useState } from 'react'

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
}) {
  // Kis conversation ka delete confirm hona baaki hai — delete permanent hai,
  // isliye ek baar poochte hain
  const [confirmingId, setConfirmingId] = useState(null)

  // Escape se confirmation cancel ho jaaye
  useEffect(() => {
    if (!confirmingId) return

    function handleKeyDown(event) {
      if (event.key === 'Escape') setConfirmingId(null)
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [confirmingId])

  function confirmDelete(id) {
    setConfirmingId(null)
    onDelete(id)
  }

  // Sidebar mount rehti hai taaki width smoothly animate ho sake. Band hone par
  // inert isse keyboard tab order aur screen readers se hata deta hai.
  return (
    <aside className="sidebar" inert={!isOpen || undefined}>
      {/* Fixed width — warna band hote waqt content sikudta hai, slide nahi hota */}
      <div className="sidebar-inner">
        <button className="new-chat" onClick={onNewChat}>
          + New chat
        </button>

        <div className="conversation-list">
          {conversations.length === 0 && (
            <p className="empty-note">No conversations yet.</p>
          )}

          {conversations.map((conversation) => {
            const id = conversation.conversation_id
            const isActive = id === activeId

            if (id === confirmingId) {
              return (
                <div key={id} className="conversation confirming">
                  <p className="confirm-text">Delete this chat?</p>

                  {/* Naam dikhana zaruri hai — warna pata nahi chalta kaun si
                      chat delete ho rahi hai */}
                  <p className="confirm-name">{conversationName(conversation)}</p>

                  <div className="confirm-actions">
                    <button
                      className="confirm-yes"
                      onClick={() => confirmDelete(id)}
                      autoFocus
                    >
                      Delete
                    </button>
                    <button
                      className="confirm-no"
                      onClick={() => setConfirmingId(null)}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )
            }

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
                  aria-label={`Delete conversation: ${conversationName(conversation)}`}
                  onClick={() => setConfirmingId(id)}
                >
                  ×
                </button>
              </div>
            )
          })}
        </div>
      </div>
    </aside>
  )
}
