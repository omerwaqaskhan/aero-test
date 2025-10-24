import { createContext, useContext, useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { authApi } from "../lib/auth-api"
import { useToast } from "../hooks/use-toast-context"

const AuthContext = createContext(undefined)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()
  const { success, error } = useToast()

  const isAuthenticated = !!user

  useEffect(() => {
    // Check for existing session on mount
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem("access_token")
      if (token) {
        // Verify token with backend
        // For now, we'll just check if token exists
        // In a real app, you'd validate the token
        const userData = localStorage.getItem("user_data")
        if (userData) {
          setUser(JSON.parse(userData))
        }
      }
    } catch (err) {
      console.error("Auth check failed:", err)
      localStorage.removeItem("access_token")
      localStorage.removeItem("refresh_token")
      localStorage.removeItem("user_data")
    } finally {
      setIsLoading(false)
    }
  }

         const login = async (email, password, rememberMe = false) => {
           try {
             setIsLoading(true)
             const response = await authApi.login({
               email,
               password,
               remember_me: rememberMe,
             })
             if (response) {
               localStorage.setItem("access_token", response.access_token)
               localStorage.setItem("refresh_token", response.refresh_token)
               localStorage.setItem("user_data", JSON.stringify(response.user))
               setUser(response.user)
               success("Welcome back!", "You have successfully logged in.", 4000)
               navigate("/dashboard")
             }
           } catch (err) {
             error("Login Failed", err.message || "Invalid credentials. Please try again.", 4000)
             throw err
           } finally {
             setIsLoading(false)
           }
         }

         const register = async (userData) => {
           try {
             setIsLoading(true)
             const response = await authApi.register(userData)
             if (response) {
               localStorage.setItem("access_token", response.access_token)
               localStorage.setItem("refresh_token", response.refresh_token)
               localStorage.setItem("user_data", JSON.stringify(response.user))
               setUser(response.user)
               success("Account Created!", "Welcome to LuftWay! Your account has been created successfully.", 4000)
               navigate("/dashboard")
             }
           } catch (err) {
             console.log("Registration error:", err.message) // Debug log
             error("Registration Failed", err.message || "Failed to create account. Please try again.", 4000)
             throw err
           } finally {
             setIsLoading(false)
           }
         }

  const socialLogin = async (provider, accessToken, deviceInfo = null) => {
    try {
      setIsLoading(true)
      const response = await authApi.socialLogin(provider, accessToken, deviceInfo)
      if (response) {
        localStorage.setItem("access_token", response.access_token)
        localStorage.setItem("refresh_token", response.refresh_token)
        localStorage.setItem("user_data", JSON.stringify(response.user))
        setUser(response.user)
        success("Welcome!", `You have successfully signed in with ${provider.charAt(0).toUpperCase() + provider.slice(1)}.`, 4000)
        navigate("/dashboard")
      }
    } catch (err) {
      error("Social Login Failed", err.message || `Failed to sign in with ${provider}. Please try again.`, 4000)
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      setIsLoading(true)
      await authApi.logout()
    } catch (err) {
      console.error("Logout error:", err)
    } finally {
      // Clear local storage regardless of API call success
      localStorage.removeItem("access_token")
      localStorage.removeItem("refresh_token")
      localStorage.removeItem("user_data")
      setUser(null)
      setIsLoading(false)
      success("Logged Out", "You have been successfully logged out.")
          navigate("/login")
    }
  }

  const forgotPassword = async (email) => {
    try {
      setIsLoading(true)
      await authApi.forgotPassword({ email })
      success("Reset Link Sent", "Please check your email for password reset instructions.")
    } catch (err) {
      error("Failed to Send Reset Link", err.message || "Please try again.")
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const resetPassword = async (token, password, confirmPassword) => {
    try {
      setIsLoading(true)
      await authApi.resetPassword({ token, password, confirm_password: confirmPassword })
      success("Password Reset", "Your password has been successfully reset. Please log in with your new password.")
          navigate("/login")
    } catch (err) {
      error("Password Reset Failed", err.message || "Please try again.")
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const verifyEmail = async (token) => {
    try {
      setIsLoading(true)
      await authApi.verifyEmail({ token })
      success("Email Verified", "Your email has been successfully verified.")
    } catch (err) {
      error("Email Verification Failed", err.message || "Please try again.")
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated,
        login,
        register,
        socialLogin,
        logout,
        forgotPassword,
        resetPassword,
        verifyEmail,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
