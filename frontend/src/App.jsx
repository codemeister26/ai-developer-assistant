import { useCallback, useEffect, useRef, useState } from 'react'

import {
  checkHealth,
  deleteConversation,
  fetchConversation,
  listConversations,
  sendMessage,
} from './api/client'
import ConversationList from './components/ConversationList'
import MessageInput from './components/MessageInput'
import MessageList from './components/MessageList'

export default function App() {
  const [conversations, setConversations] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [messages, setMessages] = useState([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState(null)
  const [health, setHealth] = useState(null)
  const [draft, setDraft] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)

  // Stop button isse stream beech mein cancel karta hai
  const abortRef = useRef(null)

  const loadConversations = useCallback(async () => {
    try {
      setConversations(await listConversations())
    } catch (err) {
      setError(err.message)
    }
  }, [])

  // Mount pe backend se conversations aur health uthao
  useEffect(() => {
    async function loadInitialData() {
      await loadConversations()

      try {
        setHealth(await checkHealth())
      } catch {
        setHealth({ status: 'down', database: 'unreachable' })
      }
    }

    loadInitialData()
  }, [loadConversations])

  async function selectConversation(id) {
    if (isStreaming) return
    setError(null)

    try {
      const history = await fetchConversation(id)
      setMessages(history.map(({ role, content }) => ({ role, content })))
      setActiveId(id)
    } catch (err) {
      setError(err.message)
    }
  }

  function startNewChat() {
    if (isStreaming) return

    setActiveId(null)
    setMessages([])
    setError(null)
  }

  async function removeConversation(id) {
    setError(null)

    try {
      await deleteConversation(id)
      if (id === activeId) startNewChat()
      await loadConversations()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleSend(text) {
    setError(null)
    setIsStreaming(true)

    // User ka message aur assistant ka khaali message — usi mein chunks bharte jayenge
    setMessages((current) => [
      ...current,
      { role: 'user', content: text },
      { role: 'assistant', content: '' },
    ])

    const controller = new AbortController()
    abortRef.current = controller

    // Kuch stream hua ya nahi — error hone par isse pata chalta hai ki backend ne
    // message save kiya ya request pehle hi reject ho gayi
    let receivedAnything = false

    try {
      const id = await sendMessage({
        message: text,
        conversationId: activeId,
        signal: controller.signal,
        onChunk: (chunk) => {
          receivedAnything = true
          setMessages((current) => {
            const updated = [...current]
            const last = updated[updated.length - 1]
            updated[updated.length - 1] = { ...last, content: last.content + chunk }
            return updated
          })
        },
      })

      // Nayi chat thi toh ab uska id mil gaya
      if (!activeId && id) {
        setActiveId(id)
        await loadConversations()
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        // User ne roka — backend jitna jawab bana tha wo save kar leta hai
        setError('Response stopped. Whatever was generated has been saved.')
      } else {
        setError(err.message)

        // Kuch aaya hi nahi matlab request reject hui, backend ne kuch save nahi
        // kiya — dono optimistic bubbles hatao warna lagta hai message chala gaya
        if (!receivedAnything) {
          setMessages((current) => current.slice(0, -2))
          setDraft(text)   // jo type kiya tha wo wapas input mein, dobara likhna na pade
        }
        // Partial jawab aaya tha toh wo backend ne save kar liya hai — rehne do
      }
    } finally {
      setIsStreaming(false)
      abortRef.current = null
    }
  }

  function handleStop() {
    abortRef.current?.abort()
  }

  return (
    <div className={`app ${sidebarOpen ? '' : 'sidebar-hidden'}`}>
      <ConversationList
        conversations={conversations}
        activeId={activeId}
        isOpen={sidebarOpen}
        onSelect={selectConversation}
        onDelete={removeConversation}
        onNewChat={startNewChat}
        onToggle={() => setSidebarOpen(false)}
      />

      <main className="chat">
        <header className="chat-header">
          <div className="header-left">
            {!sidebarOpen && (
              <button
                className="sidebar-toggle"
                onClick={() => setSidebarOpen(true)}
                title="Show sidebar"
              >
                ☰
              </button>
            )}
            <h1>AI Developer Assistant</h1>
          </div>
          {health && (
            <span className={`health ${health.database === 'ok' ? 'up' : 'down'}`}>
              database: {health.database}
            </span>
          )}
        </header>

        <MessageList messages={messages} isStreaming={isStreaming} />

        {error && <div className="error">{error}</div>}

        <MessageInput
          text={draft}
          onTextChange={setDraft}
          onSend={handleSend}
          onStop={handleStop}
          isStreaming={isStreaming}
        />
      </main>
    </div>
  )
}
