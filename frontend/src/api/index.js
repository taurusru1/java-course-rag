import axios from 'axios'
import { clearAuthUser, getAuthToken } from '../composables/useAuth'

export const api = axios.create({ baseURL: '', withCredentials: false, timeout: 30000 })

api.interceptors.request.use(config => {
  const token = getAuthToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  response => response,
  error => {
    const status = error.response?.status
    if (status === 401 || status === 403) {
      clearAuthUser()
      if (window.location.pathname !== '/login') window.location.assign(`/login?redirect=${encodeURIComponent(window.location.pathname + window.location.search)}`)
    }
    else if (status >= 500) console.error('服务端异常', error)
    else if (error.code === 'ECONNABORTED') console.error('请求超时', error)
    else if (!error.response) console.error('网络连接失败', error)
    return Promise.reject(error)
  },
)

export const getCourses = () => api.get('/api/courses')
export const createCourse = (data) => api.post('/api/courses', data)
export const updateCourse = (id, data) => api.put(`/api/courses/${id}`, data)
export const getCourse = (id) => api.get(`/api/courses/${id}`)
export const deleteCourse = (id) => api.delete(`/api/courses/${id}`)
export const uploadDocument = (formData, onUploadProgress) => api.post('/api/documents', formData, { onUploadProgress })
export const getDocuments = (courseId) => api.get('/api/documents', { params: { courseId } })
export const getDocument = (id) => api.get(`/api/documents/${id}`)
export const deleteDocument = (id) => api.delete(`/api/documents/${id}`)
export const getTeacherDashboard = () => api.get('/api/teacher/dashboard')
export const startChat = (query, courseId) => api.post('/api/chat', { query, courseId })
export const getChatResult = (sessionId) => api.get(`/api/chat/${sessionId}`)
export const chatStreamUrl = (sessionId) => `/api/chat/${sessionId}/stream?access_token=${encodeURIComponent(getAuthToken())}`
export const login = (data) => api.post('/api/auth/login', data)
export const getCurrentUser = () => api.get('/api/auth/me')
export const logout = () => api.post('/api/auth/logout')
export const getChatSessions = () => api.get('/api/chat/sessions')
export const getChatMessages = (sessionId) => api.get(`/api/chat/sessions/${sessionId}/messages`)
export const deleteChatSession = (sessionId) => api.delete(`/api/chat/sessions/${sessionId}`)
export const submitFeedback = (sessionId, messageIndex, type) => api.post('/api/chat/feedback', { sessionId, messageIndex, type })
export const getPortalCategories = () => api.get('/api/portal/categories')
export const getPortalNotices = (category) => api.get('/api/portal/notices', { params: category ? { category } : {} })
export const getStudentProfile = (id = 1) => api.get(`/api/student/${id}/profile`)
export const updateStudentProfile = (id = 1, data) => api.put(`/api/student/${id}/profile`, data)
export const getStudentSummary = (id = 1) => api.get(`/api/student/${id}/summary`)
export const getStudentHistory = (id = 1, category) => api.get(`/api/student/${id}/history`, { params: category && category !== '全部' ? { category } : {} })
export const saveStudentHistory = (id = 1, data) => api.post(`/api/student/${id}/history`, data)
export const getStudentFavorites = (id = 1) => api.get(`/api/student/${id}/favorites`)
export const addStudentFavorite = (id = 1, data) => api.post(`/api/student/${id}/favorites`, data)
export const removeStudentFavorite = (studentId = 1, favoriteId) => api.delete(`/api/student/${studentId}/favorites/${favoriteId}`)
