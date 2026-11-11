import axios from 'axios'
import { clearAuthUser, getAuthToken } from '../composables/useAuth'

export const api = axios.create({ baseURL: '/', timeout: 60000 })

api.interceptors.request.use(config => {
  const token = getAuthToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  response => response.data,
  error => {
    const status = error.response?.status
    if (status === 401) {
      clearAuthUser()
      if (window.location.pathname !== '/login') window.location.assign('/login')
    }
    const message = error.response?.data?.message || error.response?.data?.error || error.message || '请求失败'
    return Promise.reject(new Error(message))
  },
)

export const login = (account, password, role) => api.post('/api/auth/login', { account, password, role })
export const logout = () => api.post('/api/auth/logout')
export const getCurrentUser = () => api.get('/api/auth/me')

export const getCourses = () => api.get('/api/courses')
export const getChapters = courseId => api.get(`/api/courses/${courseId}/chapters`)

export const getQuestions = courseId => api.get('/api/practice/questions', { params: { courseId } })
export const submitAnswer = (questionId, answer) => api.post('/api/practice/submit', { questionId, answer })
export const getWrongAnswers = () => api.get('/api/practice/wrong')
export const getPracticeStats = () => api.get('/api/practice/stats')

export const diagnose = error => api.post('/api/diagnose', { error })
export const getErrorCases = () => api.get('/api/diagnose/cases/grouped')

export const startChat = query => api.post('/api/chat', { query })
export const getChatStatus = sessionId => api.get(`/api/chat/${sessionId}`)

export const listDocuments = courseId => api.get('/api/documents', { params: { courseId } })
export const uploadDocument = formData =>
  api.post('/api/documents', formData, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 120000 })
export const deleteDocument = id => api.delete(`/api/documents/${id}`)
