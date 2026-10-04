import { useCallback, useEffect, useRef, useState } from 'react'

import {
  checkHealth,
  deleteConversation,
  fetchConversation,
  listConversations,
  listModels,
  regenerate,
  renameConversation,
  sendMessage,
  setPinned,
  truncateFrom,
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
  // "auth" error user khud theek kar sakta hai — uspe Settings ka button dete hain
  const [errorKind, setErrorKind] = useState(null)
  const [health, setHealth] = useState(null)
  const [draft, setDraft] = useState('')
  // Phone par sidebar poori screen dhak leti hai — wahan band se shuru karo
  const [sidebarOpen, setSidebarOpen] = useState(() => window.innerWidth > 700)
  const [mode, setMode] = useState('general')
  const [models, setModels] = useState([])
  const [model, setModel] = useState(() => readStored(MODEL_STORAGE))
  const [apiKey, setApiKey] = useState(() => readStored(KEY_STORAGE))
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [search, setSearch] = useState('')

  // Stop button isse stream beech mein cancel karta hai
  const abortRef = useRef(null)

  function showError(err) {
    const isText = typeof err === 'string'
    setError(isText ? err : err.message)
    setErrorKind(isText ? null : err.kind ?? null)
  }

  function clearError() {
    setError(null)
    setErrorKind(null)
  }

  const loadConversations = useCallback(async (term = '') => {
    try {
      setConversations(await listConversations(term))
    } catch (err) {
      showError(err)
    }
  }, [])

  // Har keystroke par request na jaaye — type rukne ke baad hi search karo
  useEffect(() => {
    const timer = setTimeout(() => loadConversations(search), 250)
    return () => clearTimeout(timer)
  }, [search, loadConversations])

  async function handleRename(id, title) {
    try {
      await renameConversation(id, title)
      await loadConversations(search)
    } catch (err) {
      showError(err)
    }
  }

  async function handleTogglePin(id, pinned) {
    try {
      await setPinned(id, pinned)
      await loadConversations(search)
    } catch (err) {
      showError(err)
    }
  }

  // Mount pe models aur health uthao. Conversations upar wala search effect
  // laata hai, isliye yahan dobara nahi maangte.
  useEffect(() => {
    async function loadInitialData() {
      try {
        const available = await listModels()
        setModels(available)

        // Pehle chuna hua model ab available na ho toh pehle wale par gir jao
        setModel((current) =>
          available.some((m) => m.id === current) ? current : available[0]?.id ?? ''
        )
      } catch (err) {
        showError(err)
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
    clearError()

    try {
      const history = await fetchConversation(id)
      setMessages(history.map(({ id: messageId, role, content }) => ({
        id: messageId,
        role,
        content,
      })))
      setActiveId(id)
    } catch (err) {
      showError(err)
    }
  }

  function startNewChat() {
    if (isStreaming) return

    setActiveId(null)
    setMessages([])
    clearError()
  }

  async function removeConversation(id) {
    clearError()

    try {
      await deleteConversation(id)
      if (id === activeId) startNewChat()
      await loadConversations(search)
    } catch (err) {
      showError(err)
    }
  }

  /**
   * Stream ke baad server se messages dobara lao — taaki unke id mil jayein.
   * Edit-and-resend ko id chahiye hoti hai, aur optimistic bubbles mein wo
   * hoti nahi.
   */
  async function refreshMessages(conversationId) {
    try {
      const history = await fetchConversation(conversationId)
      setMessages(history.map(({ id, role, content }) => ({ id, role, content })))
    } catch {
      // Refresh fail hua toh jo screen par hai wahi rehne do
    }
  }

  async function handleSend(text) {
    clearError()
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
        await loadConversations(search)
      }

      if (id) await refreshMessages(id)
    } catch (err) {
      if (err.name === 'AbortError') {
        // User ne roka — backend jitna jawab bana tha wo save kar leta hai
        showError('Response stopped. Whatever was generated has been saved.')
      } else {
        showError(err)

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

  async function handleRegenerate() {
    if (isStreaming || !activeId) return

    clearError()
    setIsStreaming(true)

    // Purana jawab hata ke khaali bubble lagao — usi mein naya bharega
    setMessages((current) => [
      ...current.slice(0, -1),
      { role: 'assistant', content: '' },
    ])

    const controller = new AbortController()
    abortRef.current = controller

    try {
      await regenerate({
        conversationId: activeId,
        mode,
        model,
        apiKey,
        signal: controller.signal,
        onChunk: (chunk) => {
          setMessages((current) => {
            const updated = [...current]
            const last = updated[updated.length - 1]
            updated[updated.length - 1] = { ...last, content: last.content + chunk }
            return updated
          })
        },
      })

      await refreshMessages(activeId)
    } catch (err) {
      if (err.name === 'AbortError') {
        showError('Response stopped. Whatever was generated has been saved.')
      } else {
        showError(err)
      }
    } finally {
      setIsStreaming(false)
      abortRef.current = null
    }
  }

  async function handleEdit(message) {
    if (isStreaming || !activeId) return
    clearError()

    try {
      // Purana sawaal aur uske baad ka sab hatao, phir naya sawaal bhejenge
      await truncateFrom(activeId, message.id)

      setMessages((current) => {
        const index = current.findIndex((m) => m.id === message.id)
        return index === -1 ? current : current.slice(0, index)
      })
      setDraft(message.content)   // purana text input mein, wahan edit karo
    } catch (err) {
      showError(err)
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
        search={search}
        onSearchChange={setSearch}
        onSelect={selectConversation}
        onDelete={removeConversation}
        onRename={handleRename}
        onTogglePin={handleTogglePin}
        onNewChat={startNewChat}
      />

      {/* Phone par sidebar overlay hoti hai — bahar tap karke band ho jaye.
          Desktop par ye CSS se chhupa rehta hai. */}
      {sidebarOpen && (
        <div className="sidebar-backdrop" onClick={() => setSidebarOpen(false)} />
      )}

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

        <MessageList
          messages={messages}
          isStreaming={isStreaming}
          onRegenerate={handleRegenerate}
          onEdit={handleEdit}
        />

        {error && (
          <div className="error">
            <span>{error}</span>

            {/* Key wali galti user khud theek kar sakta hai — raasta de do */}
            {errorKind === 'auth' && (
              <button onClick={() => setSettingsOpen(true)}>Open Settings</button>
            )}
          </div>
        )}

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
