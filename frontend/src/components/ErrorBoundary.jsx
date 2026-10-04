import { Component } from 'react'

/**
 * Koi component crash ho jaaye toh poora page blank ho jaata tha. Ab kam se kam
 * kuch dikhta hai aur reload ka raasta milta hai.
 *
 * Class component isliye — React mein error boundary hooks se nahi banti.
 */
export default class ErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error('UI crashed:', error, info.componentStack)
  }

  render() {
    if (!this.state.error) return this.props.children

    return (
      <div className="crash">
        <h2>Something broke</h2>
        <p>The app hit an unexpected error. Your chats are safe on the server.</p>
        <pre>{this.state.error.message}</pre>
        <button onClick={() => window.location.reload()}>Reload</button>
      </div>
    )
  }
}
