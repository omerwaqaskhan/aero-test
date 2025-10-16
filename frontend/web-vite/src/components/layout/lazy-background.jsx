

import { useEffect, useState } from "react"

export function LazyBackground({ src = "/images/bg.jpg", className = "" }) {
  const [isLoaded, setIsLoaded] = useState(false)

  useEffect(() => {
    const image = new Image()
    image.src = src
    image.decode?.().then(() => setIsLoaded(true)).catch(() => setIsLoaded(true))
    image.onload = () => setIsLoaded(true)
  }, [src])

  return (
    <div
      aria-hidden
      className={`absolute inset-0 bg-cover bg-center bg-no-repeat transition-opacity duration-700 ${isLoaded ? "opacity-100" : "opacity-0"} ${className}`}
      style={isLoaded ? { backgroundImage: `url('${src}')` } : undefined}
    >
      <div className="absolute inset-0 bg-black/50" />
    </div>
  )
}


