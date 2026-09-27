import { useCallback, useEffect, useRef, useState } from 'react'

import {
  checkHealth,
  deleteConversation,
  fetchConversation,
  listConversations,
  listModels,
  sendMessage,
} from './api/client'
import ConversationList from './components/ConversationList'
import MessageInput from './components/MessageInput'
import MessageList from './components/MessageList'
import SettingsPanel from './components/SettingsPanel'
import SidebarToggle from './components/SidebarToggle'

const KEY_STORAGE = 'llm-api-key'
const MODEL_STORAGE = 'llm-model'

// localStorage private browsing mein throw kar sakta hai — app usse na ruke
function readStored(name, fallback = '') {
  try {
    return localStorage.getItem(name) ?? fallback
  } catch {
    return fallback
  }
}

function writeStored(name, value) {
  try {
    if (value) localStorage.setItem(name, value)
    else localStorage.removeItem(name)
  } catch {
    // Storage band hai — key sirf is session ke liye memory mein rahegi
  }
}

export default function App() {
  const [conversations, setConversations] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [messages, setMessages] = useState([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState(null)
  const [health, setHealth] = useState(null)
  const [draft, setDraft] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [mode, setMode] = useState('general')
  const [models, setModels] = useState([])
  const [model, setModel] = useState(() => readStored(MODEL_STORAGE))
  const [apiKey, setApiKey] = useState(() => readStored(KEY_STORAGE))
  const [settingsOpen, setSettingsOpen] = useState(false)

  // Stop button isse stream beech mein cancel karta hai
  const abortRef = useRef(null)

  const loadConversations = useCallback(async () => {
    try {
      setConversations(await listConversations())
    } catch (err) {
      setError(err.message)
    }
  }, [])

  // Mount pe backend se conversations, models aur health uthao
  useEffect(() => {
    async function loadInitialData() {
      await loadConversations()

      try {
        const available = await listModels()
        setModels(available)

        // Pehle chuna hua model ab available na ho toh pehle wale par gir jao
        setModel((current) =>
          available.some((m) => m.id === current) ? current : available[0]?.id ?? ''
        )
      } catch (err) {
        setError(err.message)
      }

      try {
        setHealth(await checkHealth())
      } catch {
        setHealth({ status: 'down', database: 'unreachable' })
      }
    }

    loadInitialData()
  }, [loadConversations])

  function saveApiKey(key) {
    setApiKey(key)
    writeStored(KEY_STORAGE, key)
  }

  function changeModel(id) {
    setModel(id)
    writeStored(MODEL_STORAGE, id)
  }

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
        mode,
        model,
        apiKey,
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
      />

      <main className="chat">
        <header className="chat-header">
          <div className="header-left">
            {/* Button hamesha yahin rehta hai — animation ke beech pop nahi karta */}
            <SidebarToggle
              isOpen={sidebarOpen}
              onToggle={() => setSidebarOpen((open) => !open)}
            />
            <h1>AI Developer Assistant</h1>
          </div>

          <div className="header-right">
            {health && (
              <span className={`health ${health.database === 'ok' ? 'up' : 'down'}`}>
                database: {health.database}
              </span>
            )}

            <button
              className="settings-button"
              onClick={() => setSettingsOpen(true)}
              title="Settings"
              aria-label="Settings"
            >
              ⚙
            </button>
          </div>
        </header>

        <MessageList messages={messages} isStreaming={isStreaming} />

        {error && <div className="error">{error}</div>}

        <MessageInput
          text={draft}
          onTextChange={setDraft}
          onSend={handleSend}
          onStop={handleStop}
          isStreaming={isStreaming}
          mode={mode}
          onModeChange={setMode}
          models={models}
          model={model}
          onModelChange={changeModel}
          hasKey={Boolean(apiKey)}
        />
      </main>

      {settingsOpen && (
        <SettingsPanel
          apiKey={apiKey}
          onSave={saveApiKey}
          onClose={() => setSettingsOpen(false)}
        />
      )}
    </div>
  )
}
