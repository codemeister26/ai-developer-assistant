import { useCallback, useEffect, useRef, useState } from 'react'

import {
  authStatus,
  checkHealth,
  deleteConversation,
  fetchConversation,
  listConversations,
  generateTitle,
  listModels,
  logout as logoutRequest,
  regenerate,
  renameConversation,
  sendMessage,
  setPinned,
  setSessionToken,
  truncateFrom,
} from './api/client'
import ConversationList from './components/ConversationList'
import DocumentsPanel from './components/DocumentsPanel'
import LoginScreen from './components/LoginScreen'
import MessageInput from './components/MessageInput'
import MessageList from './components/MessageList'
import SettingsPanel from './components/SettingsPanel'
import UsageBar from './components/UsageBar'
import SidebarToggle from './components/SidebarToggle'

const KEY_STORAGE = 'llm-api-key'
const SESSION_STORAGE = 'session-token'
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
  const [documentsOpen, setDocumentsOpen] = useState(false)
  const [lastUsage, setLastUsage] = useState(null)
  const [sessionCost, setSessionCost] = useState(0)
  const [search, setSearch] = useState('')
  // null = abhi pata nahi (status aa raha hai), uske baad {enabled, email}
  const [auth, setAuth] = useState(null)

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

  // Auth status aane se pehle koi request mat bhejo, warna sign-in se pehle
  // har call 401 degi aur error banner bhar jayega
  const signedIn = auth !== null && (!auth.enabled || Boolean(auth.email))

  // Mount par pata karo ki auth on hai ya nahi, aur saved token valid hai ya nahi
  useEffect(() => {
    setSessionToken(readStored(SESSION_STORAGE))

    authStatus()
      .then(setAuth)
      .catch(() => setAuth({ enabled: false }))   // backend band — login se mat roko
  }, [])

  // Har keystroke par request na jaaye — type rukne ke baad hi search karo
  useEffect(() => {
    if (!signedIn) return

    const timer = setTimeout(() => loadConversations(search), 250)
    return () => clearTimeout(timer)
  }, [search, loadConversations, signedIn])

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
    if (!signedIn) return

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
  }, [loadConversations, signedIn])

  function handleSignedIn(session) {
    setSessionToken(session.token)
    writeStored(SESSION_STORAGE, session.token)
    setAuth({ enabled: true, email: session.email })
  }

  async function handleSignOut() {
    await logoutRequest()
    writeStored(SESSION_STORAGE, '')
    setAuth({ enabled: true, email: null })
    setConversations([])
    setMessages([])
    setActiveId(null)
  }

  function recordUsage(usage) {
    if (!usage) return

    setLastUsage(usage)
    setSessionCost((total) => total + (usage.cost_usd ?? 0))
  }

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
      const { id, usage } = await sendMessage({
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

      recordUsage(usage)

      // Nayi chat thi toh ab uska id mil gaya
      const isNewChat = !activeId && id

      if (isNewChat) setActiveId(id)
      if (id) await refreshMessages(id)

      if (isNewChat) {
        // Pehle exchange ke baad chat ko chhota naam dilwao. Fail ho jaye toh
        // koi baat nahi — pehla message title ki tarah dikhta rahega.
        try {
          await generateTitle(id, model, apiKey)
        } catch {
          // chup-chaap chhod do
        }
      }

      if (id) await loadConversations(search)
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
      const { usage } = await regenerate({
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

      recordUsage(usage)
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

  // Auth status aane tak kuch mat dikhao — warna ek pal ko galat screen flash hoti hai
  if (auth === null) return null

  if (auth.enabled && !auth.email) {
    return <LoginScreen onSignedIn={handleSignedIn} />
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
              onClick={() => setDocumentsOpen(true)}
              title="Documents"
              aria-label="Documents"
            >
              📎
            </button>

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

        <UsageBar last={lastUsage} sessionCost={sessionCost} />

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

      {documentsOpen && (
        <DocumentsPanel onClose={() => setDocumentsOpen(false)} />
      )}

      {settingsOpen && (
        <SettingsPanel
          apiKey={apiKey}
          email={auth.enabled ? auth.email : null}
          onSignOut={handleSignOut}
          onSave={saveApiKey}
          onClose={() => setSettingsOpen(false)}
        />
      )}
    </div>
  )
}
