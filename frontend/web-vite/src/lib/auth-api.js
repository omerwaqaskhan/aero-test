

import { apiClient, ApiError } from "./api-client"


export class AuthApi {
  async login(credentials) {
    try {
      const response = await apiClient.post("/api/v1/auth/login", {
        ...credentials,
        tenant_slug: "windways" // Default tenant for now
      })
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
      const response = await apiClient.post("/api/v1/auth/register", {
        ...userData,
        tenant_slug: "windways" // Default tenant for now
      })
      return response.data
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(this.getErrorMessage(error))
      }
      throw error
    }
  }

  async forgotPassword(data) {
    try {
      const response = await apiClient.post("/api/v1/auth/forgot-password", data)
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
      const response = await apiClient.post("/api/v1/auth/reset-password", data)
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
      const response = await apiClient.post("/api/v1/auth/verify-email", data)
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
      const response = await apiClient.post("/api/v1/auth/refresh", {
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
      const response = await apiClient.post("/api/v1/auth/logout")
      return response.data
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(this.getErrorMessage(error))
      }
      throw error
    }
  }

  getErrorMessage(error) {
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
