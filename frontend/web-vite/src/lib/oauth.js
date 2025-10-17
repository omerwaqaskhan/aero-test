/**
 * OAuth utility functions for Google and Facebook login
 */

// Google OAuth configuration
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || 'your-google-client-id'
const FACEBOOK_APP_ID = import.meta.env.VITE_FACEBOOK_APP_ID || 'your-facebook-app-id'

/**
 * Initialize Google OAuth
 */
export function initializeGoogleOAuth() {
  return new Promise((resolve, reject) => {
    if (window.google) {
      resolve()
      return
    }

    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.defer = true
    script.onload = () => {
      if (window.google) {
        // Initialize both ID and OAuth2 clients
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleGoogleCallback,
          auto_select: false,
          cancel_on_tap_outside: true
        })
        resolve()
      } else {
        reject(new Error('Failed to load Google OAuth'))
      }
    }
    script.onerror = () => reject(new Error('Failed to load Google OAuth script'))
    document.head.appendChild(script)
  })
}

/**
 * Initialize Facebook OAuth
 */
export function initializeFacebookOAuth() {
  return new Promise((resolve, reject) => {
    // Check if we're on HTTPS or localhost (localhost allows HTTP for development)
    const isSecure = window.location.protocol === 'https:' || 
                     window.location.hostname === 'localhost' || 
                     window.location.hostname === '127.0.0.1'
    
    
    if (!isSecure) {
      console.warn('Facebook OAuth requires HTTPS or localhost. Skipping Facebook initialization.')
      resolve(false) // Return false to indicate Facebook is not available
      return
    }

    if (window.FB) {
      resolve(true)
      return
    }

    // Clear any existing fbAsyncInit
    window.fbAsyncInit = function() {
      window.FB.init({
        appId: FACEBOOK_APP_ID,
        cookie: true,
        xfbml: true,
        version: 'v18.0'
      })
      resolve(true)
    }

    const script = document.createElement('script')
    script.src = 'https://connect.facebook.net/en_US/sdk.js'
    script.async = true
    script.defer = true
    script.onerror = () => {
      console.error('Failed to load Facebook OAuth script')
      resolve(false) // Return false instead of rejecting
    }
    document.head.appendChild(script)
  })
}

/**
 * Handle Google OAuth callback
 */
function handleGoogleCallback(response) {
  // This will be called by Google OAuth
  if (response.credential) {
    // The credential is a JWT token that contains user info
    // We'll send this to our backend for verification
    window.googleOAuthCallback?.(response.credential)
  }
}

/**
 * Sign in with Google
 */
export function signInWithGoogle() {
  return new Promise((resolve, reject) => {
    if (!window.google) {
      reject(new Error('Google OAuth not initialized'))
      return
    }

    // Use popup-based OAuth for better reliability
    try {
      const client = window.google.accounts.oauth2.initCodeClient({
        client_id: GOOGLE_CLIENT_ID,
        scope: 'openid email profile',
        ux_mode: 'popup',
        callback: (response) => {
          if (response.code) {
            // For now, we'll use the authorization code
            // In production, you'd exchange this code for tokens on the backend
            resolve(response.code)
          } else {
            reject(new Error('Google sign-in was cancelled'))
          }
        }
      })
      
      client.requestCode()
    } catch (error) {
      reject(new Error('Google sign-in failed. Please try again or check your browser settings.'))
    }
  })
}

/**
 * Sign in with Facebook
 */
export function signInWithFacebook() {
  return new Promise((resolve, reject) => {
    // Check if we're on HTTPS or localhost (localhost allows HTTP for development)
    const isSecure = window.location.protocol === 'https:' || 
                     window.location.hostname === 'localhost' || 
                     window.location.hostname === '127.0.0.1'
    
    if (!isSecure) {
      reject(new Error('Facebook OAuth requires HTTPS or localhost. Please use HTTPS or localhost.'))
      return
    }

    if (!window.FB) {
      reject(new Error('Facebook OAuth not initialized'))
      return
    }

    // Check if FB is properly initialized
    if (!window.FB.getLoginStatus) {
      reject(new Error('Facebook SDK not properly initialized'))
      return
    }

    window.FB.login((response) => {
      if (response.authResponse) {
        // User logged in successfully
        resolve(response.authResponse.accessToken)
      } else {
        // User cancelled login or did not fully authorize
        reject(new Error('Facebook login was cancelled'))
      }
    }, {
      scope: 'email',
      return_scopes: true
    })
  })
}

/**
 * Get device info for OAuth requests
 */
export function getDeviceInfo() {
  return {
    user_agent: navigator.userAgent,
    platform: navigator.platform,
    language: navigator.language,
    screen_resolution: `${screen.width}x${screen.height}`,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    timestamp: new Date().toISOString()
  }
}

/**
 * Initialize all OAuth providers
 */
export async function initializeOAuth() {
  try {
    const [googleResult, facebookResult] = await Promise.allSettled([
      initializeGoogleOAuth(),
      initializeFacebookOAuth()
    ])
    
    const googleSuccess = googleResult.status === 'fulfilled'
    const facebookSuccess = facebookResult.status === 'fulfilled' && facebookResult.value === true
    
    if (!googleSuccess) {
      console.error('Failed to initialize Google OAuth:', googleResult.reason)
    }
    
    if (!facebookSuccess) {
      console.warn('Facebook OAuth not available (requires HTTPS or localhost)')
    }
    
    // Return true if at least one provider is available
    return googleSuccess || facebookSuccess
  } catch (error) {
    console.error('Failed to initialize OAuth providers:', error)
    return false
  }
}

/**
 * Check if Facebook OAuth is available
 */
export function isFacebookAvailable() {
  const isSecure = window.location.protocol === 'https:' || 
                   window.location.hostname === 'localhost' || 
                   window.location.hostname === '127.0.0.1'
  
  
  return isSecure && window.FB && window.FB.getLoginStatus
}
