import { CarouselText } from "../ui/carousel"
import { LazyBackground } from "./lazy-background"

export function AuthLayout({ children, title, subtitle }) {
  // Appealing travel-related carousel texts
  const carouselTexts = [
    "Where every journey finds its way",
    "Discover the world, one adventure at a time",
    "Your gateway to extraordinary experiences",
    "Unlock the magic of travel with us"
  ]

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Full Screen Background with gradient fallback and lazy-loaded image */}
      <div className="fixed inset-0 bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900" />
      <LazyBackground key="bg-image" src="/images/bg.jpg" />

      {/* Content Container - Split Layout */}
      <div className="relative z-10 min-h-screen flex">
        {/* Left Side - Branding */}
        <div className="hidden lg:flex lg:w-2/3 flex-col justify-center items-center px-8">
          <div className="text-center max-w-md">
            <h1 className="text-5xl font-bold text-white mb-2">
              WindWays
            </h1>
            <CarouselText 
              texts={carouselTexts}
              interval={4000}
              className="h-14"
            />
            <div className="text-white/80 text-lg">
              <p>Discover amazing destinations, Plan your perfect trip, Create unforgettable memories!</p>
            </div>
          </div>
        </div>

        {/* Right Side - Form */}
        <div className="w-full lg:w-1/2 flex items-center justify-center px-4 py-8 overflow-y-auto">
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
