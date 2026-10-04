import { useState } from 'react'

import { login, signup } from '../api/client'

/**
 * Sirf tab dikhti hai jab backend par AUTH_ENABLED on ho. Local single-user
 * setup mein app bina login ke chalti hai.
 */
export default function LoginScreen({ onSignedIn }) {
  const [isSignup, setIsSignup] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  async function submit(event) {
    event.preventDefault()
    setError(null)
    setBusy(true)

    try {
      const session = isSignup
        ? await signup(email, password)
        : await login(email, password)

      onSignedIn(session)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={submit}>
        <h1>AI Developer Assistant</h1>
        <p className="login-sub">
          {isSignup ? 'Create an account to get started.' : 'Sign in to continue.'}
        </p>

        <label>
          <span>Email</span>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            required
            autoFocus
          />
        </label>

        <label>
          <span>Password</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete={isSignup ? 'new-password' : 'current-password'}
            minLength={isSignup ? 8 : undefined}
            required
          />
        </label>

        {error && <p className="login-error">{error}</p>}

        <button type="submit" disabled={busy}>
          {busy ? 'Please wait…' : isSignup ? 'Create account' : 'Sign in'}
        </button>

        <button
          type="button"
          className="login-switch"
          onClick={() => {
            setIsSignup(!isSignup)
            setError(null)
          }}
        >
          {isSignup ? 'Already have an account? Sign in' : 'No account? Create one'}
        </button>
      </form>
    </div>
  )
}
