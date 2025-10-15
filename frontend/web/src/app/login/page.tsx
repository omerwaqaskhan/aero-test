import Link from "next/link"
import { AuthLayout } from "@/components/layout/auth-layout"
import { LoginForm } from "@/login/components/login-form"
import { SocialLogin } from "@/login/components/social-login"

export default function LoginPage() {
  return (
    <AuthLayout
      title="Welcome Back"
      subtitle="Sign in to your account to continue your journey"
    >
      <LoginForm />
      <SocialLogin />

      <div className="mt-6 text-center">
        <p className="text-sm text-gray-300">
          Don't have an account?{" "}
          <Link
            href="/register"
            className="font-medium text-blue-400 hover:text-blue-300"
          >
            Sign up
          </Link>
        </p>
      </div>
    </AuthLayout>
  )
}