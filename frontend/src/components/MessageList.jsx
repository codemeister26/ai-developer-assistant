import { useEffect, useRef } from 'react'

export default function MessageList({ messages, isStreaming }) {
  const bottomRef = useRef(null)

  // Naya content aane par apne aap neeche scroll karo
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="messages empty">
        <div className="welcome">
          <h2>AI Developer Assistant</h2>
          <p>Code review, debugging ya architecture ke baare mein kuch bhi poocho.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="messages">
      {messages.map((message, index) => {
        const isLast = index === messages.length - 1
        const showCursor = isStreaming && isLast && message.role === 'assistant'

        return (
          <div key={index} className={`message ${message.role}`}>
            <div className="role">{message.role === 'user' ? 'You' : 'Assistant'}</div>
            <div className="content">
              {message.content}
              {showCursor && <span className="cursor" />}
            </div>
          </div>
        )
      })}

      <div ref={bottomRef} />
    </div>
  )
}
