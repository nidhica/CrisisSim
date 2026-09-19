import { render, screen } from '@testing-library/react'
import { BottleneckAlert } from '../dashboard/BottleneckAlert'
import type { Bottleneck } from '../../types'

const bottleneck: Bottleneck = {
  type: 'resource_shortage',
  zone_id: 'zone-1',
  facility_id: null,
  description: 'Resource shortage in zone zone-1',
  severity_score: 0.83,
}

describe('BottleneckAlert', () => {
  it('shows no bottleneck message when empty', () => {
    render(<BottleneckAlert bottlenecks={[]} />)
    expect(screen.getByText(/no critical bottlenecks/i)).toBeInTheDocument()
  })
  it('shows primary bottleneck description', () => {
    render(<BottleneckAlert bottlenecks={[bottleneck]} />)
    expect(screen.getByText(/resource shortage in zone zone-1/i)).toBeInTheDocument()
  })
})
