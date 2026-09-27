import { useState } from 'react'

export default function MessageActions({ content, onRegenerate, onEdit, disabled }) {
  const [copied, setCopied] = useState(false)

  async function copy() {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // Clipboard permission nahi mili — button chup rahega
    }
  }

  return (
    <div className="message-actions">
      <button onClick={copy} title="Copy">
        {copied ? 'Copied' : 'Copy'}
      </button>

      {onEdit && (
        <button onClick={onEdit} disabled={disabled} title="Edit and resend">
          Edit
        </button>
      )}

      {onRegenerate && (
        <button onClick={onRegenerate} disabled={disabled} title="Regenerate reply">
          Regenerate
        </button>
      )}
    </div>
  )
}
