import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { apiClient } from '../lib/api-client'

// Mock fetch
global.fetch = vi.fn()

describe('ApiClient', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('makes GET request successfully', async () => {
    const mockData = { data: 'test' }
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
      headers: new Headers(),
    })

    const result = await apiClient.get('/test')
    expect(result).toEqual(mockData)
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/test'),
      expect.objectContaining({ method: 'GET' })
    )
  })

  it('handles 401 Unauthorized and clears tokens', async () => {
    localStorage.setItem('access_token', 'token')
    
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ error: 'Unauthorized' }),
      headers: new Headers(),
    })

    // Mock window.dispatchEvent
    const dispatchEventSpy = vi.spyOn(window, 'dispatchEvent')

    await expect(apiClient.get('/test')).rejects.toThrow()
    
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(dispatchEventSpy).toHaveBeenCalled()
  })

  it('includes authorization header when token exists', async () => {
    localStorage.setItem('access_token', 'test-token')
    
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
      headers: new Headers(),
    })

    await apiClient.get('/test')
    
    expect(fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
        }),
      })
    )
  })

  it('handles query parameters correctly', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
      headers: new Headers(),
    })

    await apiClient.get('/test', {
      params: { page: 1, limit: 10 }
    })
    
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/test?page=1&limit=10'),
      expect.any(Object)
    )
  })
})

