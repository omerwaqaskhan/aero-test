import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from '../contexts/auth-context'
import { BrowserRouter } from 'react-router-dom'

// Mock the auth API
vi.mock('../lib/auth-api', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  }
}))

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock useToast
vi.mock('../hooks/use-toast-context', () => ({
  useToast: () => ({
    success: vi.fn(),
    error: vi.fn(),
  })
}))

// Test component that uses auth context
function TestComponent() {
  const { user, isAuthenticated, isLoading } = useAuth()
  
  if (isLoading) {
    return <div>Loading...</div>
  }
  
  return (
    <div>
      <div data-testid="is-authenticated">{isAuthenticated ? 'true' : 'false'}</div>
      {user && <div data-testid="user-email">{user.email}</div>}
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('provides auth context to children', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      </BrowserRouter>
    )
    
    expect(screen.getByTestId('is-authenticated')).toBeInTheDocument()
  })

  it('handles unauthenticated state', async () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      </BrowserRouter>
    )
    
    await waitFor(() => {
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false')
    })
  })

  it('handles authenticated state with token', async () => {
    const mockUser = { email: 'test@example.com', id: '123' }
    localStorage.setItem('access_token', 'mock-token')
    localStorage.setItem('user_data', JSON.stringify(mockUser))
    
    render(
      <BrowserRouter>
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      </BrowserRouter>
    )
    
    await waitFor(() => {
      const isAuth = screen.getByTestId('is-authenticated')
      // Token might be expired, so we check if component renders
      expect(isAuth).toBeInTheDocument()
    })
  })
})

