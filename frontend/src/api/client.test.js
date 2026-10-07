import { afterEach, describe, expect, it, vi } from 'vitest'

import { sendMessage } from './client'

/** SSE frames ko aise chunks mein todo jaise network deta hai */
function streamOf(chunks) {
  const encoder = new TextEncoder()
  let index = 0

  return {
    getReader: () => ({
      read: async () =>
        index < chunks.length
          ? { done: false, value: encoder.encode(chunks[index++]) }
          : { done: true, value: undefined },
    }),
  }
}

function mockResponse(chunks, { ok = true, conversationId = 'conv-1' } = {}) {
  return {
    ok,
    status: 200,
    headers: { get: () => conversationId },
    body: streamOf(chunks),
    json: async () => ({ detail: 'boom' }),
  }
}

function frame(event) {
  return `data: ${JSON.stringify(event)}\n\n`
}

afterEach(() => {
  vi.unstubAllGlobals()
})

async function send(chunks, options) {
  vi.stubGlobal('fetch', vi.fn(async () => mockResponse(chunks, options)))

  const received = []
  const { id, usage } = await sendMessage({
    message: 'hi',
    model: 'llama3.2:3b',
    onChunk: (text) => received.push(text),
  })

  return { received, id, usage }
}

describe('SSE parsing', () => {
  it('collects tokens from complete frames', async () => {
    const { received } = await send([
      frame({ type: 'token', text: 'Hello' }),
      frame({ type: 'token', text: ' world' }),
      frame({ type: 'done', conversation_id: 'conv-1' }),
    ])

    expect(received.join('')).toBe('Hello world')
  })

  it('handles a frame split across two network chunks', async () => {
    // Network frame ke beech mein tut sakta hai — buffer isi ke liye hai
    const whole = frame({ type: 'token', text: 'split me' })
    const { received } = await send([whole.slice(0, 12), whole.slice(12)])

    expect(received.join('')).toBe('split me')
  })

  it('handles several frames arriving in one chunk', async () => {
    const { received } = await send([
      frame({ type: 'token', text: 'a' }) + frame({ type: 'token', text: 'b' }),
    ])

    expect(received.join('')).toBe('ab')
  })

  it('keeps newlines inside a token intact', async () => {
    // Code blocks mein newlines hoti hain — yahi SSE ka sabse nazuk case hai
    const code = 'def f():\n    return 1\n\n# done'
    const { received } = await send([frame({ type: 'token', text: code })])

    expect(received.join('')).toBe(code)
  })

  it('takes the conversation id from the done event', async () => {
    const { id } = await send([
      frame({ type: 'done', conversation_id: 'from-done' }),
    ])

    expect(id).toBe('from-done')
  })

  it('reports token usage from the done event', async () => {
    const { usage } = await send([
      frame({
        type: 'done',
        conversation_id: 'c1',
        usage: { input_tokens: 120, output_tokens: 40, cost_usd: 0.0003 },
      }),
    ])

    expect(usage).toEqual({ input_tokens: 120, output_tokens: 40, cost_usd: 0.0003 })
  })

  it('returns null usage when the backend does not send any', async () => {
    const { usage } = await send([frame({ type: 'done', conversation_id: 'c1' })])

    expect(usage).toBeNull()
  })

  it('ignores a malformed frame instead of killing the stream', async () => {
    const { received } = await send([
      'data: {not json}\n\n',
      frame({ type: 'token', text: 'still here' }),
    ])

    expect(received.join('')).toBe('still here')
  })
})

describe('error events', () => {
  it('throws instead of putting the error in the reply text', async () => {
    await expect(
      send([
        frame({ type: 'token', text: 'partial' }),
        frame({ type: 'error', kind: 'unavailable', message: 'service down' }),
      ])
    ).rejects.toThrow('service down')
  })

  it('marks auth errors so the UI can offer Settings', async () => {
    try {
      await send([frame({ type: 'error', kind: 'auth', message: 'bad key' })])
      throw new Error('should have thrown')
    } catch (error) {
      expect(error.kind).toBe('auth')
    }
  })

  it('still delivers tokens received before the error', async () => {
    const received = []
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        mockResponse([
          frame({ type: 'token', text: 'partial answer' }),
          frame({ type: 'error', kind: 'unavailable', message: 'died' }),
        ])
      )
    )

    await expect(
      sendMessage({
        message: 'hi',
        model: 'llama3.2:3b',
        onChunk: (text) => received.push(text),
      })
    ).rejects.toThrow()

    expect(received.join('')).toBe('partial answer')
  })
})

describe('api key handling', () => {
  it('sends the key as a header, never in the body', async () => {
    const fetchMock = vi.fn(async () => mockResponse([frame({ type: 'done' })]))
    vi.stubGlobal('fetch', fetchMock)

    await sendMessage({
      message: 'hi',
      model: 'claude-opus-5',
      apiKey: 'sk-ant-secret',
      onChunk: () => {},
    })

    const [, options] = fetchMock.mock.calls[0]
    expect(options.headers['X-LLM-Api-Key']).toBe('sk-ant-secret')
    expect(options.body).not.toContain('sk-ant-secret')
  })

  it('omits the header when there is no key', async () => {
    const fetchMock = vi.fn(async () => mockResponse([frame({ type: 'done' })]))
    vi.stubGlobal('fetch', fetchMock)

    await sendMessage({ message: 'hi', model: 'llama3.2:3b', onChunk: () => {} })

    const [, options] = fetchMock.mock.calls[0]
    expect(options.headers['X-LLM-Api-Key']).toBeUndefined()
  })
})
