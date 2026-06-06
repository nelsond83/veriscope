import { ref } from 'vue'
import { api } from 'boot/axios'

const user = ref(null)
const checked = ref(false)

export function useAuth() {
  async function checkAuth() {
    if (checked.value) return user.value
    try {
      const { data } = await api.get('/auth/me/')
      user.value = data
    } catch {
      user.value = null
    }
    checked.value = true
    return user.value
  }

  function setUser(u) {
    user.value = u
    checked.value = true
  }

  function clearUser() {
    user.value = null
    checked.value = false
  }

  return { user, checkAuth, setUser, clearUser }
}
