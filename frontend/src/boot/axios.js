import { boot } from 'quasar/wrappers'
import axios from 'axios'

const api = axios.create({ baseURL: '/api', withCredentials: true })

function getCsrfToken() {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)
  return match ? match[1] : null
}

api.interceptors.request.use((config) => {
  const method = config.method?.toLowerCase()
  if (method && !['get', 'head', 'options'].includes(method)) {
    const token = getCsrfToken()
    if (token) config.headers['X-CSRFToken'] = token
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !window.location.hash.includes('/login')) {
      window.location.href = '/#/login'
    }
    const msg = error.response?.data?.detail || error.message || 'An error occurred'
    console.error('API error:', msg)
    return Promise.reject(error)
  }
)

export default boot(({ app }) => {
  app.config.globalProperties.$axios = axios
  app.config.globalProperties.$api = api
})

export { api }
