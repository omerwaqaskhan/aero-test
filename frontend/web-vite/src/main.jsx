import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ToastProvider, useToast } from './hooks/use-toast-context.jsx'
import { ToastContainer } from './components/ui/toast.jsx'
import { AuthProvider } from './contexts/auth-context.jsx'
import App from './App.jsx'
import './index.css'

function AppWithToasts() {
  const { toasts, removeToast } = useToast()
  
  return (
    <>
      <App />
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </>
  )
}

const root = createRoot(document.getElementById('root'))
root.render(
  <BrowserRouter>
    <ToastProvider>
      <AuthProvider>
        <AppWithToasts />
      </AuthProvider>
    </ToastProvider>
  </BrowserRouter>
)