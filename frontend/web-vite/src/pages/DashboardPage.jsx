import { useAuth } from "../contexts/auth-context"
import { Button } from "../components/ui/button"

export default function DashboardPage() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          Welcome to LuftWay!
        </h1>
        <p className="text-gray-600 mb-6">
          Hello, {user?.first_name || user?.email}! You have successfully logged in.
        </p>
        <Button
          onClick={logout}
          className="w-full"
        >
          Logout
        </Button>
      </div>
    </div>
  )
}
