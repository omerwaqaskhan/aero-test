# HTTPS Development Setup for Social Login

## 🚨 Facebook OAuth HTTPS Requirement

Facebook OAuth **requires HTTPS** for security reasons. This means you cannot use Facebook login on `http://localhost` or any non-HTTPS URL.

## 🔧 Development Solutions

### Option 1: Use HTTPS with mkcert (Recommended)

#### Install mkcert
```bash
# macOS
brew install mkcert

# Windows (with Chocolatey)
choco install mkcert

# Linux
# Download from https://github.com/FiloSottile/mkcert/releases
```

#### Generate Local SSL Certificates
```bash
# Install the local CA
mkcert -install

# Generate certificates for localhost
mkcert localhost 127.0.0.1 ::1

# This creates:
# - localhost+2.pem (certificate)
# - localhost+2-key.pem (private key)
```

#### Update Vite Configuration
Create or update `frontend/web-vite/vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'

export default defineConfig({
  plugins: [react()],
  server: {
    https: {
      key: fs.readFileSync('localhost+2-key.pem'),
      cert: fs.readFileSync('localhost+2.pem'),
    },
    port: 3000,
  },
})
```

#### Update Docker Compose for HTTPS
Update `docker-compose.override.yml`:

```yaml
services:
  frontend:
    ports:
      - "3000:3000"  # HTTPS port
    volumes:
      - ./localhost+2.pem:/app/localhost+2.pem:ro
      - ./localhost+2-key.pem:/app/localhost+2-key.pem:ro
```

### Option 2: Use ngrok for HTTPS Tunneling

#### Install ngrok
```bash
# Download from https://ngrok.com/download
# Or use package managers:
brew install ngrok  # macOS
choco install ngrok # Windows
```

#### Create HTTPS Tunnel
```bash
# Expose your local development server
ngrok http 3000

# This will give you an HTTPS URL like:
# https://abc123.ngrok.io -> http://localhost:3000
```

#### Update OAuth Provider Settings
1. **Google OAuth Console**:
   - Add `https://abc123.ngrok.io` to authorized origins
   - Add `https://abc123.ngrok.io` to authorized redirect URIs

2. **Facebook App Settings**:
   - Add `https://abc123.ngrok.io` to Valid OAuth Redirect URIs
   - Add `abc123.ngrok.io` to App Domains

### Option 3: Use localhost with HTTPS (Alternative)

#### Generate Self-Signed Certificates
```bash
# Create certificates directory
mkdir -p ssl

# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

#### Update Vite Configuration
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'

export default defineConfig({
  plugins: [react()],
  server: {
    https: {
      key: fs.readFileSync('ssl/key.pem'),
      cert: fs.readFileSync('ssl/cert.pem'),
    },
    port: 3000,
  },
})
```

## 🎯 Current Implementation Status

### ✅ What Works Now
- **Google OAuth**: Works on both HTTP and HTTPS
- **Facebook OAuth**: Works only on HTTPS (with proper setup)
- **Error Handling**: Graceful fallback when Facebook is not available
- **User Feedback**: Clear indication when Facebook requires HTTPS

### 🔧 What You Need to Do

1. **For Development**:
   - Choose one of the HTTPS setup options above
   - Update your OAuth provider settings with the HTTPS URL
   - Test both Google and Facebook OAuth flows

2. **For Production**:
   - Ensure your production domain uses HTTPS
   - Update OAuth provider settings with production URLs
   - Test the complete OAuth flow

## 🚀 Quick Start with mkcert (Recommended)

```bash
# 1. Install mkcert
brew install mkcert

# 2. Install local CA
mkcert -install

# 3. Generate certificates
mkcert localhost 127.0.0.1 ::1

# 4. Update vite.config.ts (see above)

# 5. Start development server
npm run dev

# 6. Access via HTTPS
# https://localhost:3000
```

## 🔍 Testing OAuth

### Google OAuth
- ✅ Works on HTTP: `http://localhost:3000`
- ✅ Works on HTTPS: `https://localhost:3000`

### Facebook OAuth
- ❌ Does NOT work on HTTP: `http://localhost:3000`
- ✅ Works on HTTPS: `https://localhost:3000`

## 📝 OAuth Provider Configuration

### Google Cloud Console
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to APIs & Services > Credentials
3. Edit your OAuth 2.0 Client ID
4. Add authorized origins:
   - `http://localhost:3000` (for Google OAuth)
   - `https://localhost:3000` (for both Google and Facebook)
5. Add authorized redirect URIs:
   - `http://localhost:3000`
   - `https://localhost:3000`

### Facebook Developers
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Select your app
3. Go to Facebook Login > Settings
4. Add Valid OAuth Redirect URIs:
   - `https://localhost:3000` (HTTPS only)
5. Add App Domains:
   - `localhost` (for HTTPS)

## 🎉 Result

After setting up HTTPS, you'll have:
- ✅ Google OAuth working on both HTTP and HTTPS
- ✅ Facebook OAuth working on HTTPS
- ✅ Clear user feedback when Facebook is not available
- ✅ Graceful fallback behavior
- ✅ No more console errors

The social login implementation is now robust and handles the HTTPS requirement properly! 🚀
