import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { useAuth } from "../../contexts/auth-context"
import { Eye, EyeOff } from "lucide-react"

export function LoginForm() {
  const { login } = useAuth()
  const STORAGE_KEY = "login_form"
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    rememberMe: false,
  })
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  // Load draft (non-sensitive fields only) on mount
  useEffect(() => {
    try {
      const saved = sessionStorage.getItem(STORAGE_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        setFormData(prev => ({
          ...prev,
          email: typeof parsed.email === "string" ? parsed.email : prev.email,
          rememberMe: !!parsed.rememberMe,
        }))
      }
    } catch {}
  }, [])

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value
    }))

    // Persist non-sensitive draft to sessionStorage
    try {
      if (name === "email" || name === "rememberMe") {
        const draft = {
          email: name === "email" ? value : formData.email,
          rememberMe: name === "rememberMe" ? checked : formData.rememberMe,
        }
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(draft))
      }
    } catch {}
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (isLoading) return
    setIsLoading(true)
    
    try {
      await login(formData.email, formData.password, formData.rememberMe)
      // Clear draft on success
      try { sessionStorage.removeItem(STORAGE_KEY) } catch {}
    } catch (error) {
      // Error handling is done in the auth context
      console.error("Login error:", error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-200 mb-2">
          Email Address
        </label>
        <input
          id="email"
          name="email"
          type="email"
          value={formData.email}
          onChange={handleInputChange}
          placeholder="Enter your email"
          className="w-full px-4 py-3 bg-white/10 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-blue-400 focus:outline-none"
          disabled={isLoading}
        />
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-200 mb-2">
          Password
        </label>
        <div className="relative">
          <input
            id="password"
            name="password"
            type={showPassword ? "text" : "password"}
            value={formData.password}
            onChange={handleInputChange}
            placeholder="Enter your password"
            className="w-full px-4 py-3 pr-12 bg-white/10 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-blue-400 focus:outline-none"
            disabled={isLoading}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300 transition-colors"
            disabled={isLoading}
          >
            {showPassword ? (
              <EyeOff className="h-5 w-5" />
            ) : (
              <Eye className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <input
            id="rememberMe"
            name="rememberMe"
            type="checkbox"
            checked={formData.rememberMe}
            onChange={handleInputChange}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-600 rounded bg-white/10"
            disabled={isLoading}
          />
          <label htmlFor="rememberMe" className="ml-2 text-sm text-gray-300">
            Remember me
          </label>
        </div>
        <Link
          to="/forgot-password"
          className="text-sm text-blue-400 hover:text-blue-300"
        >
          Forgot password?
        </Link>
      </div>

      <button
        type="submit"
        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg transition-colors disabled:opacity-50"
        disabled={isLoading}
      >
        {isLoading ? "Signing in..." : "Sign In"}
      </button>
    </form>
  )
}