/**
 * Sidebar kholne/band karne ka ek hi button — jaisa Claude/ChatGPT mein hota hai.
 * Icon wahi rehta hai dono states mein, sirf label badalta hai.
 */
export default function SidebarToggle({ isOpen, onToggle }) {
  const label = isOpen ? 'Hide sidebar' : 'Show sidebar'

  return (
    <button
      className="sidebar-toggle"
      onClick={onToggle}
      title={label}
      aria-label={label}
      aria-expanded={isOpen}
    >
      <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <path d="M9 3v18" />
      </svg>
    </button>
  )
}
