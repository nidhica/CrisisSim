import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { CITIZEN_HAZARD_OPTIONS } from '../constants/hazardDisplay'
import type { HazardType } from '../types'

/** Hardcoded presentation-only values for the landing demo preview — not live simulation output. */
const DEMO_PREVIEW = {
  avgRisk: '43.2',
  responseTime: '44.2 min',
  topZone: 'Zone 1',
  bottleneck: 'Resource constraint',
  recommended: 'Resource Reallocation',
}

const WORKFLOW_STEPS = ['Report', 'Assess', 'Simulate', 'Analyze', 'Respond'] as const

const HAZARD_CHIP_CLASS: Record<HazardType, string> = {
  fire: 'landing-hazard-chip--fire',
  flood: 'landing-hazard-chip--flood',
  earthquake: 'landing-hazard-chip--earthquake',
  cyclone: 'landing-hazard-chip--cyclone',
  industrial_accident: 'landing-hazard-chip--industrial',
}

export function LandingPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const enterCitizen = () => {
    login('citizen')
    navigate('/citizen')
  }
  return (
    <div className="landing-shell landing-v2 landing-premium">
      <nav className="landing-nav">
        <Link to="/" className="brand">
          <span className="brand-mark">C</span>CrisisSim
        </Link>
        <Link className="nav-link" to="/personnel/login">
          Personnel access
        </Link>
      </nav>

      <main className="landing-main landing-premium-main">
        <section className="landing-hero-premium">
          <div className="landing-hero-copy">
            <p className="eyebrow">EMERGENCY DECISION SUPPORT FOR A COMPLEX WORLD</p>
            <h1 className="landing-hero-title">CRISISSIM</h1>
            <p className="landing-lead">
              From citizen reports to simulated response strategies. Deterministic multi-hazard
              prototype — not live emergency operations.
            </p>
            <div className="landing-hero-actions">
              <Link className="button button-primary landing-cta-primary" to="/personnel/login">
                Open operations center <span>→</span>
              </Link>
              <button
                type="button"
                className="button button-secondary landing-cta-secondary"
                onClick={enterCitizen}
              >
                Citizen reporting <span>→</span>
              </button>
            </div>
          </div>

          <figure className="landing-dashboard-preview" aria-labelledby="landing-preview-title">
            <div className="landing-preview-header">
              <span className="landing-demo-badge">Demo preview</span>
              <p id="landing-preview-title" className="landing-preview-kicker">Simulation preview</p>
              <p className="landing-preview-disclaimer">Example deterministic output — not live data</p>
            </div>

            <div className="landing-preview-brief">
              <p className="landing-preview-brief-title">🚨 Response command brief</p>
              <div className="landing-preview-metrics">
                <div>
                  <span className="landing-preview-label">Avg risk</span>
                  <span className="landing-preview-value">{DEMO_PREVIEW.avgRisk}</span>
                </div>
                <div>
                  <span className="landing-preview-label">Response time</span>
                  <span className="landing-preview-value">{DEMO_PREVIEW.responseTime}</span>
                </div>
                <div>
                  <span className="landing-preview-label">Highest-risk zone</span>
                  <span className="landing-preview-value landing-preview-value-sm">{DEMO_PREVIEW.topZone}</span>
                </div>
              </div>
              <div className="landing-preview-row">
                <span className="landing-preview-label">Primary bottleneck</span>
                <span className="landing-preview-row-value">{DEMO_PREVIEW.bottleneck}</span>
              </div>
              <div className="landing-preview-row landing-preview-recommended">
                <span className="landing-preview-label">Recommended</span>
                <span className="landing-preview-row-value">{DEMO_PREVIEW.recommended}</span>
              </div>
            </div>

            <div className="landing-preview-map-panel">
              <div className="landing-preview-map-head">
                <span className="landing-preview-label">Simulation map</span>
                <span className="landing-preview-map-note">Real geography · simulated zones</span>
              </div>
              <div className="landing-preview-map-frame">
                <div className="landing-preview-map-zones">
                  <span className="zone-high" title="Example high-risk zone" />
                  <span className="zone-elevated" title="Example elevated zone" />
                  <span className="zone-med" title="Example medium zone" />
                  <span className="zone-low" title="Example lower-risk zone" />
                </div>
                <span className="landing-preview-map-pin" aria-hidden>📍</span>
              </div>
            </div>
          </figure>
        </section>

        <ol className="landing-workflow-steps" aria-label="Core workflow">
          {WORKFLOW_STEPS.map((step, index) => (
            <li key={step} className="landing-workflow-step">
              <span className="landing-workflow-num">{String(index + 1).padStart(2, '0')}</span>
              <span className="landing-workflow-name">{step}</span>
              {index < WORKFLOW_STEPS.length - 1 && (
                <span className="landing-workflow-arrow" aria-hidden>→</span>
              )}
            </li>
          ))}
        </ol>

        <section className="landing-hazards-section">
          <p className="eyebrow">MULTI-HAZARD COVERAGE</p>
          <div className="landing-hazard-strip" aria-label="Supported hazards">
            {CITIZEN_HAZARD_OPTIONS.map(option => (
              <div
                key={option.type}
                className={`landing-hazard-chip ${HAZARD_CHIP_CLASS[option.type]}`}
              >
                <div className="landing-hazard-chip-title">
                  {option.emoji} {option.label.toUpperCase()}
                </div>
                <div className="hazard-card-sub">{option.subtitle}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="landing-features">
          <article className="landing-feature-card">
            <p className="section-kicker">CITIZEN REPORTING</p>
            <h2>Real geography, prototype workflow</h2>
            <p>Capture hazard, location, and severity for authority review — not a live dispatch system.</p>
          </article>
          <article className="landing-feature-card">
            <p className="section-kicker">OPERATIONS DASHBOARD</p>
            <h2>Command brief &amp; simulation map</h2>
            <p>Deterministic zones, bottlenecks, and intervention comparison in one command view.</p>
          </article>
          <article className="landing-feature-card">
            <p className="section-kicker">WHAT-IF ANALYSIS</p>
            <h2>Explore assumptions</h2>
            <p>Adjust scenario parameters and compare projected outcomes before diving into tables.</p>
          </article>
        </section>

        <div className="landing-aws-strip" aria-label="Technology stack">
          <span>AWS Amplify</span>
          <span>API Gateway</span>
          <span>Lambda</span>
          <span>DynamoDB</span>
          <span>Amazon Bedrock</span>
        </div>
      </main>

      <footer className="landing-footer">
        <span>Decision support grounded in deterministic simulation results.</span>
        <span>Hackathon prototype · not a live emergency-control system</span>
      </footer>
    </div>
  )
}
