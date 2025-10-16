import { createContext, useContext, useState, useCallback } from "react"

const ToastContext = createContext(undefined)

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const addToast = useCallback((toast) => {
    const id = Math.random().toString(36).substr(2, 9)
    const newToast = {
      ...toast,
      id,
      duration: toast.duration || 5000, // Default 5 seconds
    }
    setToasts((prev) => [...prev, newToast])
  }, [])

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  const success = useCallback((title, description) => {
    addToast({ type: "success", title, description })
  }, [addToast])

  const error = useCallback((title, description) => {
    addToast({ type: "error", title, description })
  }, [addToast])

  const warning = useCallback((title, description) => {
    addToast({ type: "warning", title, description })
  }, [addToast])

  const info = useCallback((title, description) => {
    addToast({ type: "info", title, description })
  }, [addToast])

  return (
    <ToastContext.Provider
      value={{
        toasts,
        addToast,
        removeToast,
        success,
        error,
        warning,
        info,
      }}
    >
      {children}
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (context === undefined) {
    throw new Error("useToast must be used within a ToastProvider")
  }
  return context
}
