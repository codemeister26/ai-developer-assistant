import { memo } from 'react'
import ReactMarkdown from 'react-markdown'
import rehypeHighlight from 'rehype-highlight'
import remarkGfm from 'remark-gfm'

import CodeBlock from './CodeBlock'

const components = {
  pre: CodeBlock,
  a: (props) => <a {...props} target="_blank" rel="noreferrer" />,
}

// Language subset karne ka fayda nahi — rehype-highlight lowlight ka "common"
// set statically import karta hai, toh wo bundle mein aata hi hai.
const rehypePlugins = [[rehypeHighlight, { detect: true, ignoreMissing: true }]]
const remarkPlugins = [remarkGfm]

// memo isliye — streaming ke dauran har chunk pe poora markdown dobara parse
// hota hai; content na badle toh re-render skip ho jaata hai
function Markdown({ children }) {
  return (
    <ReactMarkdown
      remarkPlugins={remarkPlugins}
      rehypePlugins={rehypePlugins}
      components={components}
    >
      {children}
    </ReactMarkdown>
  )
}

export default memo(Markdown)
