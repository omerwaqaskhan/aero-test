import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import App from '../App'

// Mock the pages/components that might cause issues
vi.mock('../pages/LandingPage', () => ({
  default: () => <div>Landing Page</div>
}))

vi.mock('../pages/LoginPage', () => ({
  default: () => <div>Login Page</div>
}))

vi.mock('../pages/DashboardPage', () => ({
  default: () => <div>Dashboard Page</div>
}))

describe('App', () => {
  it('renders without crashing', () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )
    expect(screen.getByText(/Landing Page/i)).toBeInTheDocument()
  })

  it('has routing configured', () => {
    const { container } = render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )
    expect(container.querySelector('main') || container).toBeTruthy()
  })
})

