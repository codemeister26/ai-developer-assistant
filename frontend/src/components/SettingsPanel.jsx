import { useEffect, useState } from 'react'

/**
 * API key yahan daali jaati hai. Key sirf is browser mein rehti hai —
 * server use kabhi save nahi karta, har request ke saath bhej dete hain.
 */
export default function SettingsPanel({ apiKey, onSave, onClose }) {
  const [draft, setDraft] = useState(apiKey)

  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === 'Escape') onClose()
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  function save(event) {
    event.preventDefault()
    onSave(draft.trim())
    onClose()
  }

  return (
    <div className="settings-backdrop" onClick={onClose}>
      <form
        className="settings-panel"
        onClick={(event) => event.stopPropagation()}
        onSubmit={save}
      >
        <h2>Settings</h2>

        <label className="settings-field">
          <span>Anthropic API key</span>
          <input
            type="password"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="sk-ant-..."
            autoFocus
            spellCheck={false}
            autoComplete="off"
          />
        </label>

        <p className="settings-note">
          Needed only for Claude models. The key stays in this browser and is sent
          with each request — the server never stores it. Get one at{' '}
          <a href="https://console.anthropic.com" target="_blank" rel="noreferrer">
            console.anthropic.com
          </a>
          .
        </p>

        <div className="settings-actions">
          {apiKey && (
            <button
              type="button"
              className="settings-clear"
              onClick={() => {
                onSave('')
                onClose()
              }}
            >
              Remove key
            </button>
          )}

          <span className="spacer" />

          <button type="button" className="settings-cancel" onClick={onClose}>
            Cancel
          </button>
          <button type="submit">Save</button>
        </div>
      </form>
    </div>
  )
}
