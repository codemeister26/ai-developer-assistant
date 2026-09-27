export default function ModelSelector({ models, value, onChange, disabled, hasKey }) {
  const active = models.find((model) => model.id === value)
  const keyMissing = active?.needs_key && !hasKey

  return (
    <label className="model-selector" title={active?.note}>
      <span className="field-label">Model</span>

      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled || models.length === 0}
        aria-label="Model"
        className={keyMissing ? 'needs-key' : ''}
      >
        {models.map((model) => (
          <option key={model.id} value={model.id}>
            {model.label}
            {model.needs_key ? ' 🔑' : ''}
          </option>
        ))}
      </select>
    </label>
  )
}
