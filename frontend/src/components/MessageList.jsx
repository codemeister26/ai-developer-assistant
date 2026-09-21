import { useEffect, useRef } from 'react'

import Markdown from './Markdown'

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
          <p>Ask anything about code review, debugging or architecture.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="messages">
      {messages.map((message, index) => {
        const isLast = index === messages.length - 1
        const isAssistant = message.role === 'assistant'
        const showCursor = isStreaming && isLast && isAssistant

        return (
          <div key={index} className={`message ${message.role}`}>
            <div className="role">{isAssistant ? 'Assistant' : 'You'}</div>

            <div className="content">
              {/* Assistant markdown bhejta hai — code blocks, lists, bold.
                  User ne jo type kiya wo waisa ka waisa dikhao. */}
              {isAssistant ? (
                <Markdown>{message.content}</Markdown>
              ) : (
                <span className="plain-text">{message.content}</span>
              )}

              {showCursor && <span className="cursor" />}
            </div>
          </div>
        )
      })}

      <div ref={bottomRef} />
    </div>
  )
}
