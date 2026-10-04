import { useEffect, useState } from 'react'

function formatDate(value) {
  return new Date(value).toLocaleString(undefined, {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Backend title ke roop mein custom naam deta hai, warna pehla user message.
// Khaali conversation mein wo null hota hai, tab id dikhate hain.
function conversationName(conversation) {
  const title = conversation.title?.trim()

  if (!title) return `Untitled · ${conversation.conversation_id.slice(0, 8)}`
  return title
}

export default function ConversationList({
  conversations,
  activeId,
  isOpen,
  search,
  onSearchChange,
  onSelect,
  onDelete,
  onRename,
  onTogglePin,
  onNewChat,
}) {
  // Kis conversation ka delete confirm hona baaki hai — delete permanent hai,
  // isliye ek baar poochte hain
  const [confirmingId, setConfirmingId] = useState(null)
  const [renamingId, setRenamingId] = useState(null)
  const [draftName, setDraftName] = useState('')

  // Escape se confirmation ya rename cancel ho jaaye
  useEffect(() => {
    if (!confirmingId && !renamingId) return

    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        setConfirmingId(null)
        setRenamingId(null)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [confirmingId, renamingId])

  function confirmDelete(id) {
    setConfirmingId(null)
    onDelete(id)
  }

  function startRename(conversation) {
    setRenamingId(conversation.conversation_id)
    setDraftName(conversationName(conversation))
  }

  function saveRename(event, id) {
    event.preventDefault()
    setRenamingId(null)
    onRename(id, draftName.trim() || null)   // khaali chhodo toh auto-title wapas
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

        <input
          className="search-box"
          type="search"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Search chats..."
          aria-label="Search conversations"
        />

        <div className="conversation-list">
          {conversations.length === 0 && (
            <p className="empty-note">
              {search ? 'No chats match that search.' : 'No conversations yet.'}
            </p>
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

            if (id === renamingId) {
              return (
                <form
                  key={id}
                  className="conversation renaming"
                  onSubmit={(event) => saveRename(event, id)}
                >
                  <input
                    value={draftName}
                    onChange={(event) => setDraftName(event.target.value)}
                    onBlur={(event) => saveRename(event, id)}
                    autoFocus
                    maxLength={200}
                    aria-label="Conversation name"
                  />
                </form>
              )
            }

            return (
              <div key={id} className={`conversation ${isActive ? 'active' : ''}`}>
                <button className="conversation-open" onClick={() => onSelect(id)}>
                  <span className="conversation-title">
                    {conversation.pinned && <span className="pin-mark">📌 </span>}
                    {conversationName(conversation)}
                  </span>
                  <span className="conversation-date">
                    {formatDate(conversation.created_at)}
                  </span>
                </button>

                <div className="conversation-actions">
                  <button
                    title={conversation.pinned ? 'Unpin' : 'Pin to top'}
                    aria-label={conversation.pinned ? 'Unpin' : 'Pin to top'}
                    onClick={() => onTogglePin(id, !conversation.pinned)}
                  >
                    {conversation.pinned ? '📌' : '📍'}
                  </button>

                  <button
                    title="Rename"
                    aria-label="Rename conversation"
                    onClick={() => startRename(conversation)}
                  >
                    ✎
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
              </div>
            )
          })}
        </div>
      </div>
    </aside>
  )
}
