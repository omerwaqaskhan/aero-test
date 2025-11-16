

import { config } from "./config"


class ApiClient {
  baseURL

  constructor() {
    this.baseURL = config.apiUrl
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    
    // Get access token from localStorage
    const token = localStorage.getItem("access_token")
    
    const defaultHeaders = {
      "Content-Type": "application/json",
    }
    
    // Add Authorization header if token exists
    if (token) {
      defaultHeaders["Authorization"] = `Bearer ${token}`
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
      
      // Check if response is JSON
      let data;
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        data = await response.json()
      } else {
        const text = await response.text()
        data = { message: text || "An error occurred" }
      }

      if (!response.ok) {
        throw new ApiError(
          data.detail || data.message || data.error || "An error occurred",
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
        error.message || "Network error. Please check your connection.",
        0,
        error
      )
    }
  }

  async get(endpoint, options = {}) {
    // If options contains params, convert them to query string
    let url = endpoint;
    if (options.params) {
      const queryString = new URLSearchParams(options.params).toString();
      url = `${endpoint}?${queryString}`;
    }
    
    return this.request(url, {
      method: "GET",
      headers: options.headers,
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
