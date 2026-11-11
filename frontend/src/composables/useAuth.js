const AUTH_KEY = 'campus_kb_user'
const TOKEN_KEY = 'campus_kb_token'

export const getAuthUser = () => {
  try { return JSON.parse(localStorage.getItem(AUTH_KEY) || 'null') } catch { return null }
}
export const setAuthUser = user => localStorage.setItem(AUTH_KEY, JSON.stringify(user))
export const getAuthToken = () => localStorage.getItem(TOKEN_KEY) || ''
export const setAuthSession = (token, user) => {
  localStorage.setItem(TOKEN_KEY, token)
  setAuthUser(user)
}
export const clearAuthUser = () => {
  localStorage.removeItem(AUTH_KEY)
  localStorage.removeItem(TOKEN_KEY)
}
export const useAuth = () => ({ getAuthUser, getAuthToken, setAuthSession, clearAuthUser })
