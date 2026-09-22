// Backend ke ChatMode enum se match karta hai — har mode ka apna system prompt hai
const MODES = [
  { value: 'general', label: 'General', hint: 'Everyday developer questions' },
  { value: 'code_review', label: 'Code review', hint: 'Bugs, security, performance' },
  { value: 'debug', label: 'Debug', hint: 'Find the root cause of an error' },
  { value: 'explain', label: 'Explain', hint: 'Learn a concept step by step' },
  { value: 'architecture', label: 'Architecture', hint: 'System design and tradeoffs' },
  { value: 'code_writing', label: 'Write code', hint: 'Clean, commented code' },
]

export default function ModeSelector({ value, onChange, disabled }) {
  const active = MODES.find((mode) => mode.value === value)

  return (
    <label className="mode-selector" title={active?.hint}>
      <span className="mode-label">Mode</span>

      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
        aria-label="Answer mode"
      >
        {MODES.map((mode) => (
          <option key={mode.value} value={mode.value}>
            {mode.label}
          </option>
        ))}
      </select>
    </label>
  )
}
