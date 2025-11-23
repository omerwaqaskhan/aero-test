export const config = {
  apiUrl: import.meta.env.VITE_API_URL || "/api",
  environment: import.meta.env.MODE || "development",
  baseUrl: import.meta.env.VITE_APP_URL || "http://localhost:3000",
}
