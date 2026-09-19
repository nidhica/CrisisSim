import { Link, useNavigate } from 'react-router-dom'
import { SeverityBadge } from '../common/SeverityBadge'
import type { Scenario } from '../../types'
import { useAuth } from '../../context/AuthContext'

interface Props { scenario?: Scenario | null; mode?: 'citizen' | 'personnel' }

export function Header({ scenario, mode = 'personnel' }: Props) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const isCitizen = mode === 'citizen'
  function leave() { logout(); navigate('/') }
  return <header className="site-header">
    <div className="header-primary"><Link to={isCitizen ? '/citizen' : '/personnel'} className="brand"><span className="brand-mark">C</span>CrisisSim</Link><span className="header-divider" />{scenario && <div className="scenario-label"><small>CURRENT SCENARIO</small><span>{scenario.name}</span><SeverityBadge level={scenario.severity} /><span className="hazard-pill">{(scenario.hazard_type || 'flood').replaceAll('_', ' ')}</span></div>}</div>
    <nav className="header-nav" aria-label="Primary navigation">
      <span className="emergency-status"><i /> Emergency status</span>
      {isCitizen ? <><span className="nav-current">Dashboard</span><span className="nav-muted">Safety &amp; shelters</span></> : <><Link to="/personnel" className="nav-current">Operations</Link><Link to="/personnel" className="nav-muted">Incidents</Link>{scenario && <Link className="header-action secondary" to="/personnel">Switch scenario</Link>}<Link className="header-action" to="/personnel/new">+ New emergency</Link></>}
      <span className="profile-name">{user?.name ?? (isCitizen ? 'Citizen view' : 'Operations')}</span><button onClick={leave} className="logout-button">Logout</button>
    </nav>
  </header>
}
