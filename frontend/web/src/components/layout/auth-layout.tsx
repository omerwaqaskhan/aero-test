import { ReactNode } from "react"

interface AuthLayoutProps {
  children: ReactNode
  title: string
  subtitle?: string
}

export function AuthLayout({ children, title, subtitle }: AuthLayoutProps) {
  return (
    <div className="min-h-screen relative">
      {/* Full Screen Background Image */}
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{
          backgroundImage: "url('/images/bg.jpg')"
        }}
      >
        {/* Dark overlay for better contrast */}
        <div className="absolute inset-0 bg-black/50" />
      </div>

      {/* Content Container - Split Layout */}
      <div className="relative z-10 min-h-screen flex">
        {/* Left Side - Branding */}
        <div className="hidden lg:flex lg:w-1/2 flex-col justify-center items-center px-8">
          <div className="text-center max-w-md">
            <h1 className="text-5xl font-bold text-white mb-4">
              WindWays
            </h1>
            <p className="text-white/90 text-xl mb-8">
              Where every journey finds its way
            </p>
            <div className="text-white/80 text-lg space-y-2">
              <p>Discover amazing destinations</p>
              <p>Plan your perfect trip</p>
              <p>Create unforgettable memories</p>
            </div>
          </div>
        </div>

        {/* Right Side - Form */}
        <div className="w-full lg:w-1/2 flex items-center justify-center px-4 py-8">
          <div className="w-full max-w-md">
            {/* Semi-transparent form box */}
            <div className="bg-black/70 backdrop-blur-sm rounded-2xl shadow-2xl p-8">
              <div className="text-center mb-8">
                <h2 className="text-3xl font-bold text-gray-100 mb-2">
                  {title}
                </h2>
                {subtitle && (
                  <p className="text-gray-300 text-lg">
                    {subtitle}
                  </p>
                )}
              </div>
              
              {children}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
