const AUTH_KEY = 'javacourse_user'
const TOKEN_KEY = 'javacourse_token'

export const getAuthUser = () => {
  try { return JSON.parse(localStorage.getItem(AUTH_KEY) || 'null') } catch { return null }
}
export const getAuthToken = () => localStorage.getItem(TOKEN_KEY) || ''
export const setAuthSession = (token, user) => {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(AUTH_KEY, JSON.stringify(user))
}
export const clearAuthUser = () => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(AUTH_KEY)
}
export const useAuth = () => ({ getAuthUser, getAuthToken, setAuthSession, clearAuthUser })
