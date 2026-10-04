// Backend ka address — .env mein VITE_API_URL set karke badal sakte ho
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Session token. Module mein isliye rakha hai taaki har call mein pass na
// karna pade — auth band ho toh ye khaali rehta hai aur header jaata hi nahi.
let sessionToken = ''

export function setSessionToken(token) {
  sessionToken = token || ''
}

function authHeaders(extra = {}) {
  return {
    ...extra,
    ...(sessionToken ? { Authorization: `Bearer ${sessionToken}` } : {}),
  }
}

// ─── Auth ─────────────────────────────────────────────────────────────────

export async function authStatus() {
  const response = await fetch(`${API_URL}/api/v1/auth/status`, {
    headers: authHeaders(),
  })

  if (!response.ok) throw new Error(await readError(response))
  return response.json()
}

export async function signup(email, password) {
  return postCredentials('signup', email, password)
}

export async function login(email, password) {
  return postCredentials('login', email, password)
}

async function postCredentials(path, email, password) {
  const response = await fetch(`${API_URL}/api/v1/auth/${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })

  if (!response.ok) throw new Error(await readError(response))
  return response.json()
}

export async function logout() {
  await fetch(`${API_URL}/api/v1/auth/logout`, {
    method: 'POST',
    headers: authHeaders(),
  }).catch(() => {})   // token waise bhi client se hata rahe hain
  setSessionToken('')
}

/**
 * Backend ke error ko padhne layak message mein badlo.
 * Validation errors FastAPI se {detail: [{msg, loc}]} format mein aate hain.
 */
async function readError(response) {
  try {
    const body = await response.json()

    if (Array.isArray(body.detail)) {
      return body.detail.map((item) => item.msg).join(', ')
    }
    return body.detail || `Request failed (${response.status})`
  } catch {
    return `Request failed (${response.status})`
  }
}

/**
 * SSE stream padho aur har event onEvent ko do.
 *
 * Network chunk aur SSE frame ek cheez nahi hain — ek frame do chunks mein
 * aa sakti hai, isliye buffer rakhna padta hai.
 */
async function readEvents(response, onEvent) {
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    // Frames "\n\n" se alag hoti hain; aakhri aadhi frame buffer mein rukti hai
    const frames = buffer.split('\n\n')
    buffer = frames.pop() ?? ''

    for (const frame of frames) {
      const line = frame.trim()
      if (!line.startsWith('data:')) continue

      try {
        onEvent(JSON.parse(line.slice(5).trim()))
      } catch {
        // Adhuri ya kharab frame — usse poori stream nahi rukni chahiye
      }
    }
  }
}

/**
 * Message bhejo aur jawab token-by-token receive karo.
 *
 * onChunk har token pe call hota hai. Return karta hai conversation id, jo nayi
 * chat ke case mein backend X-Conversation-Id header se deta hai.
 * Backend error ko alag event mein bhejta hai, isliye wo throw hota hai —
 * jawab ke text mein ghusta nahi.
 */
export async function sendMessage({
  message,
  conversationId,
  mode,
  model,
  apiKey,
  signal,
  onChunk,
}) {
  const response = await fetch(`${API_URL}/api/v1/chat`, {
    method: 'POST',
    headers: authHeaders({
      'Content-Type': 'application/json',
      // Key header mein jaati hai, body mein nahi — body log ho sakti hai
      ...(apiKey ? { 'X-LLM-Api-Key': apiKey } : {}),
    }),
    body: JSON.stringify({
      message,
      conversation_id: conversationId ?? null,
      mode: mode ?? 'general',
      model,
    }),
    signal,
  })

  if (!response.ok) {
    throw new Error(await readError(response))
  }

  // Ye header CORS ke expose_headers mein hai — warna browser ise padhne nahi deta
  let id = response.headers.get('X-Conversation-Id') || conversationId
  let streamError = null

  await readEvents(response, (event) => {
    if (event.type === 'token') onChunk(event.text)
    else if (event.type === 'done') id = event.conversation_id || id
    else if (event.type === 'error') streamError = event
  })

  if (streamError) {
    const error = new Error(streamError.message)
    error.kind = streamError.kind   // "auth" ya "unavailable"
    throw error
  }

  return id
}

/** Aakhri jawab hatao aur naya banao — user ka sawaal wahi rehta hai */
export async function regenerate({ conversationId, mode, model, apiKey, signal, onChunk }) {
  const response = await fetch(`${API_URL}/api/v1/chat/${conversationId}/regenerate`, {
    method: 'POST',
    headers: authHeaders({
      'Content-Type': 'application/json',
      ...(apiKey ? { 'X-LLM-Api-Key': apiKey } : {}),
    }),
    body: JSON.stringify({ mode: mode ?? 'general', model }),
    signal,
  })

  if (!response.ok) throw new Error(await readError(response))

  let streamError = null

  await readEvents(response, (event) => {
    if (event.type === 'token') onChunk(event.text)
    else if (event.type === 'error') streamError = event
  })

  if (streamError) {
    const error = new Error(streamError.message)
    error.kind = streamError.kind
    throw error
  }
}

/** Is message se aage ka sab hatao — edit karke dobara bhejne se pehle */
export async function truncateFrom(conversationId, messageId) {
  const response = await fetch(
    `${API_URL}/api/v1/chat/${conversationId}/messages/${messageId}`,
    { method: 'DELETE', headers: authHeaders() }
  )

  if (!response.ok) throw new Error(await readError(response))
  return response.json()
}

export async function listModels() {
  const response = await fetch(`${API_URL}/api/v1/models`, {
    headers: authHeaders(),
  })

  if (!response.ok) throw new Error(await readError(response))
  return response.json()
}

export async function listConversations(search = '') {
  const query = search ? `?search=${encodeURIComponent(search)}` : ''
  const response = await fetch(`${API_URL}/api/v1/conversations${query}`, {
    headers: authHeaders(),
  })

  if (!response.ok) throw new Error(await readError(response))
  return response.json()
}

export async function renameConversation(conversationId, title) {
  const response = await fetch(`${API_URL}/api/v1/conversations/${conversationId}`, {
    method: 'PATCH',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ title }),   // null bhejo toh auto-title wapas
  })

  if (!response.ok) throw new Error(await readError(response))
  return response.json()
}

/** Chat ko chhota naam dilwao (LLM se). Fail ho toh chup-chaap chhod do. */
export async function generateTitle(conversationId, model, apiKey) {
  const response = await fetch(
    `${API_URL}/api/v1/conversations/${conversationId}/title`,
    {
      method: 'POST',
      headers: authHeaders({
        'Content-Type': 'application/json',
        ...(apiKey ? { 'X-LLM-Api-Key': apiKey } : {}),
      }),
      body: JSON.stringify({ model }),
    }
  )

  if (!response.ok) throw new Error(await readError(response))
  return response.json()
}

export async function setPinned(conversationId, pinned) {
  const response = await fetch(
    `${API_URL}/api/v1/conversations/${conversationId}/pin`,
    {
      method: 'PATCH',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ pinned }),
    }
  )

  if (!response.ok) throw new Error(await readError(response))
  return response.json()
}

export async function fetchConversation(conversationId) {
  const response = await fetch(`${API_URL}/api/v1/chat/${conversationId}`, {
    headers: authHeaders(),
  })

  if (!response.ok) throw new Error(await readError(response))
  return response.json()
}

export async function deleteConversation(conversationId) {
  const response = await fetch(`${API_URL}/api/v1/chat/${conversationId}`, {
    method: 'DELETE',
    headers: authHeaders(),
  })

  if (!response.ok) throw new Error(await readError(response))
  return response.json()
}

export async function checkHealth() {
  const response = await fetch(`${API_URL}/health`)

  if (!response.ok) throw new Error(await readError(response))
  return response.json()
}
