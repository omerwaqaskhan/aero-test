

import { config } from "./config"


class ApiClient {
  baseURL

  constructor() {
    this.baseURL = config.apiUrl
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    
    const defaultHeaders = {
      "Content-Type": "application/json",
    }

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    }

    try {
      const response = await fetch(url, config)
      const data = await response.json()

      if (!response.ok) {
        throw new ApiError(
          data.message || data.error || "An error occurred",
          response.status,
          data,
          response
        )
      }

      return {
        data,
        status: response.status,
      }
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }

      // Network or other errors
      throw new ApiError(
        "Network error. Please check your connection.",
        0,
        error
      )
    }
  }

  async get(endpoint, headers) {
    return this.request(endpoint, {
      method: "GET",
      headers,
    })
  }

  async post(endpoint, data, headers) {
    return this.request(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
      headers,
    })
  }

  async put(endpoint, data, headers) {
    return this.request(endpoint, {
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
      headers,
    })
  }

  async delete(endpoint, headers) {
    return this.request(endpoint, {
      method: "DELETE",
      headers,
    })
  }
}

export class ApiError extends Error {
  constructor(message, status, details, response) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.details = details
    this.response = response
  }
}

export const apiClient = new ApiClient()
