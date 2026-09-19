import { render, screen } from '@testing-library/react'
import { SimMapLegend } from '../SimMapLegend'

describe('SimMapLegend', () => {
  it('renders simulation map legend', () => {
    render(<SimMapLegend showCitizenPin />)
    expect(screen.getByText(/simulation map/i)).toBeInTheDocument()
    expect(screen.getByText(/citizen report/i)).toBeInTheDocument()
    expect(screen.getByText(/HIGH RISK/i)).toBeInTheDocument()
    expect(screen.getByText(/simulated boundaries/i)).toBeInTheDocument()
  })
})
