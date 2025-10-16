import { Link } from "react-router-dom"
import { AuthLayout } from "../components/layout/auth-layout.jsx"
import { RegisterForm } from "../register/components/register-form.jsx"
import { SocialRegister } from "../register/components/social-register.jsx"

export default function RegisterPage() {
  return (
    <AuthLayout
      title="Create Account"
      subtitle="Join WindWays and start your travel journey"
    >
      <RegisterForm />
      <SocialRegister />
      <div className="mt-6 text-center">
        <p className="text-sm text-gray-300">
          Already have an account?{" "}
          <Link
            to="/login"
            className="font-medium text-blue-400 hover:text-blue-300"
          >
            Sign in
          </Link>
        </p>
      </div>
    </AuthLayout>
  )
}
