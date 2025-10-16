

import { useState, useEffect } from "react"
import { cn } from "../../lib/utils"

export function CarouselText({ texts, className, interval = 3000 }) {
  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIndex((prevIndex) => (prevIndex + 1) % texts.length)
    }, interval)

    return () => clearInterval(timer)
  }, [texts.length, interval])

  return (
    <div className={cn("relative overflow-hidden", className)}>
      <div
        className="flex transition-transform duration-500 ease-in-out"
        style={{
          transform: `translateX(-${currentIndex * 100}%)`,
        }}
      >
        {texts.map((text, index) => (
          <div
            key={index}
            className="w-full flex-shrink-0 text-center"
          >
            <p className="text-white/90 text-xl mb-8 animate-fade-in">
              {text}
            </p>
          </div>
        ))}
      </div>
      
      {/* Dots indicator */}
      <div className="flex justify-center space-x-2 mt-4">
        {texts.map((_, index) => (
          <button
            key={index}
            className={cn(
              "w-2 h-2 rounded-full transition-all duration-300",
              index === currentIndex
                ? "bg-white scale-125"
                : "bg-white/40 hover:bg-white/60"
            )}
            onClick={() => setCurrentIndex(index)}
            aria-label={`Go to slide ${index + 1}`}
          />
        ))}
      </div>
    </div>
  )
}
