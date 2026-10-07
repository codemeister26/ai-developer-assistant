/**
 * Pichhle jawab ka token usage aur kharcha, aur is session ka total.
 *
 * BYOK ke saath ye zaruri hai — warna pata hi nahi chalta ki har message
 * kitne paise ka pada. Local models par cost 0 hota hai, toh sirf tokens
 * dikhate hain.
 */
function formatCost(usd) {
  // Chhote amounts par 2 decimals "$0.00" dikha dete hain, jo bekaar hai
  if (usd < 0.01) return `$${usd.toFixed(4)}`
  return `$${usd.toFixed(2)}`
}

export default function UsageBar({ last, sessionCost }) {
  if (!last) return null

  const isPaid = last.cost_usd > 0

  return (
    <span className="usage-bar">
      <span title="Tokens sent (your question plus history)">
        {last.input_tokens.toLocaleString()} in
      </span>
      {' · '}
      <span title="Tokens generated">
        {last.output_tokens.toLocaleString()} out
      </span>

      {isPaid && (
        <>
          {' · '}
          <span title="Cost of this message">{formatCost(last.cost_usd)}</span>
        </>
      )}

      {sessionCost > 0 && (
        <>
          {' · '}
          <span className="usage-total" title="Total spent since you opened the app">
            {formatCost(sessionCost)} this session
          </span>
        </>
      )}
    </span>
  )
}
