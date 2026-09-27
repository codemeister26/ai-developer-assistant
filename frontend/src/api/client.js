// Backend ka address — .env mein VITE_API_URL set karke badal sakte ho
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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
 * Message bhejo aur jawab token-by-token receive karo.
 *
 * onChunk har chunk pe call hota hai. Return karta hai conversation id, jo nayi
 * chat ke case mein backend X-Conversation-Id header se deta hai.
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
    headers: {
      'Content-Type': 'application/json',
      // Key header mein jaati hai, body mein nahi — body log ho sakti hai
      ...(apiKey ? { 'X-LLM-Api-Key': apiKey } : {}),
    },
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
  const id = response.headers.get('X-Conversation-Id') || conversationId

  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    onChunk(decoder.decode(value, { stream: true }))
  }

  return id
}

/** Aakhri jawab hatao aur naya banao — user ka sawaal wahi rehta hai */
export async function regenerate({ conversationId, mode, model, apiKey, signal, onChunk }) {
  const response = await fetch(`${API_URL}/api/v1/chat/${conversationId}/regenerate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(apiKey ? { 'X-LLM-Api-Key': apiKey } : {}),
    },
    body: JSON.stringify({ mode: mode ?? 'general', model }),
    signal,
  })

  if (!response.ok) throw new Error(await readError(response))

  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    onChunk(decoder.decode(value, { stream: true }))
  }
}

/** Is message se aage ka sab hatao — edit karke dobara bhejne se pehle */
export async function truncateFrom(conversationId, messageId) {
  const response = await fetch(
    `${API_URL}/api/v1/chat/${conversationId}/messages/${messageId}`,
    { method: 'DELETE' }
  )

  if (!response.ok) throw new Error(await readError(response))
  return response.json()
}

export async function listModels() {
  const response = await fetch(`${API_URL}/api/v1/models`)

  if (!response.ok) throw new Error(await readError(response))
  return response.json()
}

export async function listConversations() {
  const response = await fetch(`${API_URL}/api/v1/conversations`)

  if (!response.ok) throw new Error(await readError(response))
  return response.json()
}

export async function fetchConversation(conversationId) {
  const response = await fetch(`${API_URL}/api/v1/chat/${conversationId}`)

  if (!response.ok) throw new Error(await readError(response))
  return response.json()
}

export async function deleteConversation(conversationId) {
  const response = await fetch(`${API_URL}/api/v1/chat/${conversationId}`, {
    method: 'DELETE',
  })

  if (!response.ok) throw new Error(await readError(response))
  return response.json()
}

export async function checkHealth() {
  const response = await fetch(`${API_URL}/health`)

  if (!response.ok) throw new Error(await readError(response))
  return response.json()
}
