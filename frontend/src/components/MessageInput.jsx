// Backend ka MAX_MESSAGE_LENGTH — yahan bhi rok lo taaki user ko turant pata chale
const MAX_LENGTH = 4000

// text App mein rehta hai taaki request fail hone par draft wapas laaya ja sake
export default function MessageInput({ text, onTextChange, onSend, onStop, isStreaming }) {
  const trimmed = text.trim()
  const tooLong = text.length > MAX_LENGTH
  const canSend = trimmed.length > 0 && !tooLong && !isStreaming

  function submit(event) {
    event.preventDefault()
    if (!canSend) return

    onSend(trimmed)
    onTextChange('')
  }

  function handleKeyDown(event) {
    // Enter bhejta hai, Shift+Enter nayi line
    if (event.key === 'Enter' && !event.shiftKey) {
      submit(event)
    }
  }

  return (
    <form className="composer" onSubmit={submit}>
      <textarea
        value={text}
        onChange={(event) => onTextChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Apna sawaal likho... (Enter bhejne ke liye, Shift+Enter nayi line)"
        rows={3}
      />

      <div className="composer-actions">
        <span className={`counter ${tooLong ? 'over' : ''}`}>
          {text.length} / {MAX_LENGTH}
        </span>

        {isStreaming ? (
          <button type="button" className="stop" onClick={onStop}>
            Stop
          </button>
        ) : (
          <button type="submit" disabled={!canSend}>
            Send
          </button>
        )}
      </div>
    </form>
  )
}
