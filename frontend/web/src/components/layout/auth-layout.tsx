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

      {/* Content Container */}
      <div className="relative z-10 min-h-screen flex items-center justify-center px-4 py-8">
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

          {/* Branding below the form */}
          <div className="text-center mt-8">
            <h1 className="text-4xl font-bold text-white mb-2">
              WindWays
            </h1>
            <p className="text-white/90 text-lg">
              Where every journey finds its way
            </p>
            <div className="mt-4 text-white/80 text-sm">
              <p>Discover amazing destinations</p>
              <p>Plan your perfect trip</p>
              <p>Create unforgettable memories</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
