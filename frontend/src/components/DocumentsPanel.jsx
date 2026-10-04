import { useEffect, useRef, useState } from 'react'

import { deleteDocument, listDocuments, uploadDocument } from '../api/client'

/**
 * Upload kiye documents. Jo yahan hai, uska content har sawaal ke saath
 * automatically dhoondha jaata hai aur relevant hissa AI ko bheja jaata hai.
 */
export default function DocumentsPanel({ onClose }) {
  const [documents, setDocuments] = useState([])
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const fileInput = useRef(null)

  useEffect(() => {
    listDocuments().then(setDocuments).catch((err) => setError(err.message))
  }, [])

  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === 'Escape') onClose()
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  async function handleUpload(event) {
    const files = Array.from(event.target.files ?? [])
    if (files.length === 0) return

    setError(null)
    setBusy(true)

    for (const file of files) {
      try {
        await uploadDocument(file)
      } catch (err) {
        // Ek file fail ho toh baaki rukni nahi chahiye
        setError(`${file.name}: ${err.message}`)
      }
    }

    try {
      setDocuments(await listDocuments())
    } catch (err) {
      setError(err.message)
    }

    setBusy(false)
    if (fileInput.current) fileInput.current.value = ''
  }

  async function handleDelete(id) {
    setError(null)

    try {
      await deleteDocument(id)
      setDocuments(await listDocuments())
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="settings-backdrop" onClick={onClose}>
      <div className="settings-panel" onClick={(event) => event.stopPropagation()}>
        <h2>Documents</h2>

        <p className="settings-note">
          Anything you upload here is searched on every question, and the
          relevant parts are sent to the model. PDFs, Markdown, text and code
          files work.
        </p>

        <input
          ref={fileInput}
          type="file"
          multiple
          onChange={handleUpload}
          disabled={busy}
          accept=".pdf,.txt,.md,.markdown,.rst,.csv,.json,.py,.js,.jsx,.ts,.tsx,.java,.go,.rb,.sql,.yml,.yaml,.html,.css,.sh"
        />

        {busy && <p className="settings-note">Indexing…</p>}
        {error && <p className="login-error">{error}</p>}

        <div className="document-list">
          {documents.length === 0 && !busy && (
            <p className="empty-note">No documents yet.</p>
          )}

          {documents.map((document) => (
            <div key={document.id} className="document-row">
              <span className="document-name">{document.filename}</span>
              <span className="document-chunks">{document.chunk_count} chunks</span>
              <button
                onClick={() => handleDelete(document.id)}
                title="Remove document"
                aria-label={`Remove ${document.filename}`}
              >
                ×
              </button>
            </div>
          ))}
        </div>

        <div className="settings-actions">
          <span className="spacer" />
          <button type="button" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  )
}
