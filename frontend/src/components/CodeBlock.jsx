import { useState } from 'react'

/**
 * Markdown ka <pre> block — language label aur copy button ke saath.
 * Highlighting rehype-highlight karta hai, ye sirf uske aas-paas ka chrome hai.
 */
export default function CodeBlock({ children, ...props }) {
  const [copied, setCopied] = useState(false)

  // <pre> ke andar <code> hota hai; uski className se language nikalti hai
  const codeElement = children?.props
  const language =
    codeElement?.className?.match(/language-(\w+)/)?.[1] ?? 'code'

  async function copy() {
    const text = extractText(codeElement?.children)

    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // Clipboard permission nahi mili — button bas kuch nahi karega
    }
  }

  return (
    <div className="code-block">
      <div className="code-head">
        <span className="code-lang">{language}</span>
        <button className="code-copy" onClick={copy}>
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>

      <pre {...props}>{children}</pre>
    </div>
  )
}

/** Highlighted code nested elements mein hota hai — saara text nikaalo */
function extractText(node) {
  if (node == null) return ''
  if (typeof node === 'string') return node
  if (Array.isArray(node)) return node.map(extractText).join('')
  if (node.props?.children) return extractText(node.props.children)
  return ''
}
