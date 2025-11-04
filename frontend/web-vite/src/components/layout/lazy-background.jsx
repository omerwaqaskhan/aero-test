
import { useEffect, useState } from "react"

// Global cache to prevent reloading the same image
const imageCache = new Map()

export function LazyBackground({ src = "/images/background.jpg", className = "" }) {
  const [isLoaded, setIsLoaded] = useState(imageCache.has(src))

  useEffect(() => {
    // If already cached, set loaded immediately
    if (imageCache.has(src)) {
      setIsLoaded(true)
      return
    }

    const image = new Image()
    image.src = src
    
    const handleLoad = () => {
      imageCache.set(src, true)
      setIsLoaded(true)
    }

    const handleError = () => {
      // Still cache to prevent retries
      imageCache.set(src, false)
      setIsLoaded(true)
    }

    image.onload = handleLoad
    image.onerror = handleError
    
    // Cleanup
    return () => {
      image.onload = null
      image.onerror = null
    }
  }, [src])

  return (
    <div
      aria-hidden
      className={`fixed inset-0 bg-cover bg-center bg-no-repeat transition-opacity duration-500 ease-in-out ${isLoaded ? "opacity-100" : "opacity-0"} ${className}`}
      style={isLoaded ? { backgroundImage: `url('${src}')` } : undefined}
    >
      <div className="absolute inset-0 bg-black/50" />
    </div>
  )
}


