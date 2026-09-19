import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function PersonnelLoginPage() {
  const [name, setName] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()
  function submit(event: FormEvent) { event.preventDefault(); login('emergency_personnel', name.trim() || undefined); navigate('/personnel') }
  return <main className="auth-shell"><section className="auth-card"><Link to="/" className="brand brand-dark"><span className="brand-mark">C</span>CrisisSim</Link><p className="eyebrow">OPERATIONS ACCESS</p><h1>Personnel sign in</h1><p className="auth-copy">This is a frontend demonstration login. It does not provide security controls and is designed to be replaced by Amazon Cognito.</p><form onSubmit={submit}><label htmlFor="display-name">Display name <span>(optional)</span></label><input id="display-name" value={name} onChange={e => setName(e.target.value)} placeholder="Operations user" autoComplete="name" /><button className="button button-primary auth-button" type="submit">Enter operations center</button></form></section></main>
}
