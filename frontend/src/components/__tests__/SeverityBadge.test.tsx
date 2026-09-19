import { render, screen } from '@testing-library/react'
import { SeverityBadge } from '../common/SeverityBadge'

describe('SeverityBadge', () => {
  it('renders correct level text', () => {
    render(<SeverityBadge level="critical" />)
    expect(screen.getByText(/critical/i)).toBeInTheDocument()
  })
  it('renders low level', () => {
    render(<SeverityBadge level="low" />)
    expect(screen.getByText(/low/i)).toBeInTheDocument()
  })
})
