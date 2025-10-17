

import { apiClient, ApiError } from "./api-client"


export class AuthApi {
  async login(credentials) {
    try {
      const response = await apiClient.post("/v1/auth/login", {
        ...credentials,
        tenant_slug: "windways" // Default tenant for now
      })
      
      // Extract nested data from backend response
      if (response.data && response.data.data) {
        return {
          user: response.data.data.user,
          access_token: response.data.data.tokens.access_token,
          refresh_token: response.data.data.tokens.refresh_token,
          expires_in: response.data.data.tokens.expires_in
        }
      }
      
      return response.data
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(this.getErrorMessage(error))
      }
      throw error
    }
  }

  async register(userData) {
    try {
      const response = await apiClient.post("/v1/auth/register", {
        ...userData,
        tenant_slug: "windways" // Default tenant for now
      })
      
      // Extract nested data from backend response
      if (response.data && response.data.data) {
        return {
          user: response.data.data.user,
          access_token: response.data.data.tokens.access_token,
          refresh_token: response.data.data.tokens.refresh_token,
          expires_in: response.data.data.tokens.expires_in
        }
      }
      
      return response.data
    } catch (error) {
      if (error instanceof ApiError) {
        const errorMessage = this.getErrorMessage(error)
        console.log("Register API error message:", errorMessage) // Debug log
        throw new Error(errorMessage)
      }
      throw error
    }
  }

  async forgotPassword(data) {
    try {
      const response = await apiClient.post("/v1/auth/forgot-password", data)
      return response.data
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(this.getErrorMessage(error))
      }
      throw error
    }
  }

  async resetPassword(data) {
    try {
      const response = await apiClient.post("/v1/auth/reset-password", data)
      return response.data
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(this.getErrorMessage(error))
      }
      throw error
    }
  }

  async verifyEmail(data) {
    try {
      const response = await apiClient.post("/v1/auth/verify-email", data)
      return response.data
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(this.getErrorMessage(error))
      }
      throw error
    }
  }

  async refreshToken(refreshToken) {
    try {
      const response = await apiClient.post("/v1/auth/refresh", {
        refresh_token: refreshToken,
      })
      return response.data
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(this.getErrorMessage(error))
      }
      throw error
    }
  }

  async logout() {
    try {
      const response = await apiClient.post("/v1/auth/logout")
      return response.data
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(this.getErrorMessage(error))
      }
      throw error
    }
  }

  getErrorMessage(error) {
    // Try to extract specific error message from API response
    // First, support fetch-based ApiError (our ApiClient) via error.details
    if (error.details) {
      const responseData = error.details
      
      // Handle nested error structure from backend
      if (responseData.detail && responseData.detail.error) {
        const apiError = responseData.detail.error
        let errorMessage = apiError.message || "An error occurred"
        
        // Handle specific password validation errors
        if (apiError.code === "VALIDATION_ERROR" && apiError.details) {
          // Forbidden pattern already specific
          if (errorMessage.includes("cannot contain")) return errorMessage
          // Length style
          if (errorMessage.includes("must be at least") || errorMessage.includes("should have at least")) return errorMessage
          if (errorMessage.includes("Password doesn't meet strength requirements")) {
            return "Password must be at least 8 characters long and cannot contain common words like 'password', '123456', 'qwerty', or 'admin'"
          }
        }
        return errorMessage
      }
      
      // Handle Pydantic validation errors (array format)
      if (responseData.detail && Array.isArray(responseData.detail)) {
        const validationErrors = responseData.detail
        const errorMessages = validationErrors.map(err => {
          const field = err.loc ? err.loc.join('.') : 'field'
          return `${field}: ${err.msg}`
        })
        return errorMessages.join(', ')
      }
      
      // Handle direct error message
      if (responseData.message) return responseData.message
      
      // Handle validation errors (string format)
      if (responseData.detail && typeof responseData.detail === 'string') {
        return responseData.detail
      }
    }

    // Also support axios-style errors if present
    if (error.response && error.response.data) {
      const responseData = error.response.data
      
      // Handle nested error structure from backend
      if (responseData.detail && responseData.detail.error) {
        const apiError = responseData.detail.error
        let errorMessage = apiError.message || "An error occurred"
        
        // Handle specific password validation errors
        if (apiError.code === "VALIDATION_ERROR" && apiError.details) {
          // Check if it's a forbidden pattern error (already specific)
          if (errorMessage.includes("cannot contain")) {
            return errorMessage
          }
          
          // Check if it's a length error
          if (errorMessage.includes("must be at least") || errorMessage.includes("should have at least")) {
            return errorMessage
          }
          
          // For other password validation errors, provide helpful message
          if (errorMessage.includes("Password doesn't meet strength requirements")) {
            return "Password must be at least 8 characters long and cannot contain common words like 'password', '123456', 'qwerty', or 'admin'"
          }
        }
        
        return errorMessage
      }
      
      // Handle Pydantic validation errors (array format)
      if (responseData.detail && Array.isArray(responseData.detail)) {
        const validationErrors = responseData.detail
        const errorMessages = validationErrors.map(err => {
          const field = err.loc ? err.loc.join('.') : 'field'
          return `${field}: ${err.msg}`
        })
        return errorMessages.join(', ')
      }
      
      // Handle direct error message
      if (responseData.message) {
        return responseData.message
      }
      
      // Handle validation errors (string format)
      if (responseData.detail && typeof responseData.detail === 'string') {
        return responseData.detail
      }
    }
    
    // Fallback to status-based messages
    switch (error.status) {
      case 400:
        return "Invalid request. Please check your input."
      case 401:
        return "Invalid credentials. Please try again."
      case 403:
        return "Access denied. You don't have permission to perform this action."
      case 404:
        return "The requested resource was not found."
      case 409:
        return "A user with this email already exists."
      case 422:
        return "Validation error. Please check your input."
      case 429:
        return "Too many requests. Please try again later."
      case 500:
        return "Server error. Please try again later."
      default:
        return error.message || "An unexpected error occurred."
    }
  }
}

export const authApi = new AuthApi()
