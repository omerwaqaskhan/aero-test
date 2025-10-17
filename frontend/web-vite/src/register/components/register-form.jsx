import { useState, useCallback, useEffect } from "react"
import { Link } from "react-router-dom"
import { useAuth } from "../../contexts/auth-context"
import { Eye, EyeOff } from "lucide-react"

export function RegisterForm() {
  const { register } = useAuth()
  const STORAGE_KEY = "register_form"
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    password: "",
    confirmPassword: "",
    termsAccepted: false,
    newsletterSubscription: false,
  })
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [errors, setErrors] = useState({})

  // Load draft (non-sensitive fields only) on mount
  useEffect(() => {
    try {
      const saved = sessionStorage.getItem(STORAGE_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        setFormData(prev => ({
          ...prev,
          firstName: typeof parsed.firstName === "string" ? parsed.firstName : prev.firstName,
          lastName: typeof parsed.lastName === "string" ? parsed.lastName : prev.lastName,
          email: typeof parsed.email === "string" ? parsed.email : prev.email,
          phone: typeof parsed.phone === "string" ? parsed.phone : prev.phone,
          termsAccepted: !!parsed.termsAccepted,
          newsletterSubscription: !!parsed.newsletterSubscription,
        }))
      }
    } catch {}
  }, [])


  const handleInputChange = useCallback((e) => {
    const { name, value, type, checked } = e.target
    
    setFormData(prev => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value
    }))
    
    // Clear error when user starts typing
    setErrors(prev => {
      if (prev[name]) {
        return {
          ...prev,
          [name]: ""
        }
      }
      return prev
    })

    // Persist non-sensitive draft to sessionStorage (avoid passwords)
    try {
      if (["firstName", "lastName", "email", "phone", "termsAccepted", "newsletterSubscription"].includes(name)) {
        const draft = {
          firstName: name === "firstName" ? value : formData.firstName,
          lastName: name === "lastName" ? value : formData.lastName,
          email: name === "email" ? value : formData.email,
          phone: name === "phone" ? value : formData.phone,
          termsAccepted: name === "termsAccepted" ? checked : formData.termsAccepted,
          newsletterSubscription: name === "newsletterSubscription" ? checked : formData.newsletterSubscription,
        }
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(draft))
      }
    } catch {}
  }, [])

  const validateForm = () => {
    const newErrors = {}
    
    // Required fields
    if (!formData.firstName.trim()) {
      newErrors.firstName = "First name is required"
    }
    if (!formData.lastName.trim()) {
      newErrors.lastName = "Last name is required"
    }
    if (!formData.email.trim()) {
      newErrors.email = "Email is required"
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Please enter a valid email address"
    }
    if (!formData.password) {
      newErrors.password = "Password is required"
    } else if (formData.password.length < 8) {
      newErrors.password = "Password must be at least 8 characters long"
    }
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = "Please confirm your password"
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match"
    }
    if (!formData.termsAccepted) {
      newErrors.termsAccepted = "You must accept the terms and conditions"
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const togglePasswordVisibility = useCallback(() => {
    setShowPassword(prev => !prev)
  }, [])

  const toggleConfirmPasswordVisibility = useCallback(() => {
    setShowConfirmPassword(prev => !prev)
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    
    // Prevent multiple submissions
    if (isLoading) {
      return
    }
    
    if (!validateForm()) {
      return
    }
    
    setIsLoading(true)
    
    try {
      await register({
        first_name: formData.firstName,
        last_name: formData.lastName,
        email: formData.email,
        phone: formData.phone || undefined,
        password: formData.password,
      })
      // Clear draft on success
      try { sessionStorage.removeItem(STORAGE_KEY) } catch {}
    } catch (error) {
      // Error handling is done in the auth context
      console.error("Registration error:", error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="firstName" className="block text-sm font-medium text-gray-200 mb-2">
            First Name
          </label>
          <input
            id="firstName"
            name="firstName"
            type="text"
            value={formData.firstName}
            onChange={handleInputChange}
            placeholder="First name"
            className={`w-full px-4 py-3 bg-white/10 border rounded-lg text-white placeholder-gray-400 focus:outline-none ${
              errors.firstName ? "border-red-500" : "border-gray-600 focus:border-blue-400"
            }`}
            disabled={isLoading}
          />
          {errors.firstName && (
            <p className="mt-1 text-sm text-red-400">{errors.firstName}</p>
          )}
        </div>
        <div>
          <label htmlFor="lastName" className="block text-sm font-medium text-gray-200 mb-2">
            Last Name
          </label>
          <input
            id="lastName"
            name="lastName"
            type="text"
            value={formData.lastName}
            onChange={handleInputChange}
            placeholder="Last name"
            className={`w-full px-4 py-3 bg-white/10 border rounded-lg text-white placeholder-gray-400 focus:outline-none ${
              errors.lastName ? "border-red-500" : "border-gray-600 focus:border-blue-400"
            }`}
            disabled={isLoading}
          />
          {errors.lastName && (
            <p className="mt-1 text-sm text-red-400">{errors.lastName}</p>
          )}
        </div>
      </div>

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
          className={`w-full px-4 py-3 bg-white/10 border rounded-lg text-white placeholder-gray-400 focus:outline-none ${
            errors.email ? "border-red-500" : "border-gray-600 focus:border-blue-400"
          }`}
          disabled={isLoading}
        />
        {errors.email && (
          <p className="mt-1 text-sm text-red-400">{errors.email}</p>
        )}
      </div>

      <div>
        <label htmlFor="phone" className="block text-sm font-medium text-gray-200 mb-2">
          Phone Number <span className="text-gray-400">(Optional)</span>
        </label>
        <input
          id="phone"
          name="phone"
          type="tel"
          value={formData.phone}
          onChange={handleInputChange}
          placeholder="Enter your phone number"
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
            placeholder="Create a password"
            className={`w-full px-4 py-3 pr-12 bg-white/10 border rounded-lg text-white placeholder-gray-400 focus:outline-none ${
              errors.password ? "border-red-500" : "border-gray-600 focus:border-blue-400"
            }`}
            disabled={isLoading}
          />
          <button
            type="button"
            onClick={togglePasswordVisibility}
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
        {errors.password && (
          <p className="mt-1 text-sm text-red-400">{errors.password}</p>
        )}
        <p className="mt-1 text-xs text-gray-400">
          Must be at least 8 characters long. Cannot contain common words like 'password', '123456', 'qwerty', or 'admin'
        </p>
      </div>

      <div>
        <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-200 mb-2">
          Confirm Password
        </label>
        <div className="relative">
          <input
            id="confirmPassword"
            name="confirmPassword"
            type={showConfirmPassword ? "text" : "password"}
            value={formData.confirmPassword}
            onChange={handleInputChange}
            placeholder="Confirm your password"
            className={`w-full px-4 py-3 pr-12 bg-white/10 border rounded-lg text-white placeholder-gray-400 focus:outline-none ${
              errors.confirmPassword ? "border-red-500" : "border-gray-600 focus:border-blue-400"
            }`}
            disabled={isLoading}
          />
          <button
            type="button"
            onClick={toggleConfirmPasswordVisibility}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300 transition-colors"
            disabled={isLoading}
          >
            {showConfirmPassword ? (
              <EyeOff className="h-5 w-5" />
            ) : (
              <Eye className="h-5 w-5" />
            )}
          </button>
        </div>
        {errors.confirmPassword && (
          <p className="mt-1 text-sm text-red-400">{errors.confirmPassword}</p>
        )}
      </div>

      <div className="space-y-3">
        <div className="flex items-start">
          <input
            id="termsAccepted"
            name="termsAccepted"
            type="checkbox"
            checked={formData.termsAccepted}
            onChange={handleInputChange}
            className={`h-4 w-4 text-blue-600 focus:ring-blue-500 border rounded bg-white/10 mt-1 ${
              errors.termsAccepted ? "border-red-500" : "border-gray-600"
            }`}
            disabled={isLoading}
          />
          <label htmlFor="termsAccepted" className="ml-2 text-sm text-gray-300">
            I agree to the{" "}
            <Link to="/terms" className="text-blue-400 hover:text-blue-300 underline">
              Terms of Service
            </Link>{" "}
            and{" "}
            <Link to="/privacy" className="text-blue-400 hover:text-blue-300 underline">
              Privacy Policy
            </Link>
          </label>
        </div>
        {errors.termsAccepted && (
          <p className="text-sm text-red-400">{errors.termsAccepted}</p>
        )}
        <div className="flex items-center">
          <input
            id="newsletterSubscription"
            name="newsletterSubscription"
            type="checkbox"
            checked={formData.newsletterSubscription}
            onChange={handleInputChange}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-600 rounded bg-white/10"
            disabled={isLoading}
          />
          <label htmlFor="newsletterSubscription" className="ml-2 text-sm text-gray-300">
            Subscribe to our newsletter for travel updates
          </label>
        </div>
      </div>

      <button
        type="submit"
        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        disabled={isLoading}
      >
        {isLoading ? "Creating Account..." : "Create Account"}
      </button>

      <div className="text-center">
        <p className="text-sm text-gray-300">
          Already have an account?{" "}
          <Link to="/login" className="text-blue-400 hover:text-blue-300 font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </form>
  )
}