"use client"

import { useState, useRef } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Form, FormField } from "@/components/ui/form"
import { Eye, EyeOff, Mail, Lock, User, Phone } from "lucide-react"

export function RegisterForm() {
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const passwordRef = useRef<HTMLInputElement>(null)
  const confirmPasswordRef = useRef<HTMLInputElement>(null)

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword)
    if (passwordRef.current) {
      passwordRef.current.type = !showPassword ? "password" : "text"
    }
  }

  const toggleConfirmPasswordVisibility = () => {
    setShowConfirmPassword(!showConfirmPassword)
    if (confirmPasswordRef.current) {
      confirmPasswordRef.current.type = !showConfirmPassword ? "password" : "text"
    }
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setIsLoading(true)
    
    // TODO: Implement registration logic
    console.log("Registration form submitted")
    
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false)
    }, 2000)
  }

  return (
    <Form onSubmit={handleSubmit}>
      <div className="grid grid-cols-2 gap-4">
        <FormField>
          <Label htmlFor="firstName">First Name</Label>
          <div className="relative">
            <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              id="firstName"
              type="text"
              placeholder="John"
              className="pl-10"
              required
            />
          </div>
        </FormField>

        <FormField>
          <Label htmlFor="lastName">Last Name</Label>
          <div className="relative">
            <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              id="lastName"
              type="text"
              placeholder="Doe"
              className="pl-10"
              required
            />
          </div>
        </FormField>
      </div>

      <FormField>
        <Label htmlFor="email">Email Address</Label>
        <div className="relative">
          <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            id="email"
            type="email"
            placeholder="john.doe@example.com"
            className="pl-10"
            required
          />
        </div>
      </FormField>

      <FormField>
        <Label htmlFor="phone">Phone Number</Label>
        <div className="relative">
          <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            id="phone"
            type="tel"
            placeholder="+1 (555) 123-4567"
            className="pl-10"
            required
          />
        </div>
      </FormField>

      <FormField>
        <Label htmlFor="password">Password</Label>
        <div className="relative">
          <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            ref={passwordRef}
            id="password"
            type="password"
            placeholder="Create a strong password"
            className="pl-10 pr-10"
            required
          />
          <button
            type="button"
            onClick={togglePasswordVisibility}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
      </FormField>

      <FormField>
        <Label htmlFor="confirmPassword">Confirm Password</Label>
        <div className="relative">
          <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            ref={confirmPasswordRef}
            id="confirmPassword"
            type="password"
            placeholder="Confirm your password"
            className="pl-10 pr-10"
            required
          />
          <button
            type="button"
            onClick={toggleConfirmPasswordVisibility}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
      </FormField>

      <div className="flex items-start space-x-2">
        <input
          id="terms"
          type="checkbox"
          className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          required
        />
        <Label htmlFor="terms" className="text-sm leading-relaxed text-gray-200">
          I agree to the{" "}
          <Link href="/terms" className="text-blue-400 hover:text-blue-300">
            Terms of Service
          </Link>{" "}
          and{" "}
          <Link href="/privacy" className="text-blue-400 hover:text-blue-300">
            Privacy Policy
          </Link>
        </Label>
      </div>

      <div className="flex items-start space-x-2">
        <input
          id="newsletter"
          type="checkbox"
          className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <Label htmlFor="newsletter" className="text-sm leading-relaxed text-gray-200">
          I'd like to receive travel deals and updates via email
        </Label>
      </div>

      <Button
        type="submit"
        className="w-full"
        disabled={isLoading}
      >
        {isLoading ? "Creating Account..." : "Create Account"}
      </Button>
    </Form>
  )
}
