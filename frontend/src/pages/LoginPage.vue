<template>
  <div class="row items-center justify-center" style="min-height: 100vh; background: #1D1D1F;">
    <q-card style="width: 400px; background: #2C2C2E; border: 1px solid rgba(245,245,247,0.1);">
      <q-card-section class="text-center q-pt-xl q-pb-lg">
        <img src="/logo.svg" alt="Veriscope" style="height:80px; width:auto" />
        <div style="margin-top:14px; font-size:0.72rem; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:#9A9A9F">
          Due Diligence Platform
        </div>
      </q-card-section>

      <q-separator dark style="opacity:0.15" />

      <q-card-section class="q-px-xl q-pt-lg q-pb-xl">
        <q-form @submit.prevent="submit">
          <q-input
            v-model="username"
            label="Username"
            dark
            filled
            class="q-mb-md login-input"
            autofocus
            :disable="loading"
          />
          <q-input
            v-model="password"
            label="Password"
            type="password"
            dark
            filled
            class="q-mb-lg login-input"
            :disable="loading"
          />
          <q-btn
            type="submit"
            label="Sign in"
            color="primary"
            class="full-width"
            unelevated
            :loading="loading"
          />
          <div v-if="error" class="text-negative text-caption text-center q-mt-md">
            {{ error }}
          </div>
        </q-form>
      </q-card-section>
    </q-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from 'boot/axios'
import { useAuth } from 'src/composables/useAuth'

const router = useRouter()
const { setUser } = useAuth()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const { data } = await api.post('/auth/login/', {
      username: username.value,
      password: password.value,
    })
    setUser(data)
    router.push({ name: 'dashboard' })
  } catch (err) {
    error.value = err.response?.data?.detail || 'Sign in failed.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* Fix browser autofill overflowing the Quasar input control */
.login-input :deep(input:-webkit-autofill),
.login-input :deep(input:-webkit-autofill:hover),
.login-input :deep(input:-webkit-autofill:focus) {
  -webkit-box-shadow: 0 0 0 1000px #3A3A3C inset !important;
  -webkit-text-fill-color: #ffffff !important;
  transition: background-color 5000s ease-in-out 0s;
  caret-color: #ffffff;
}

.login-input :deep(.q-field__control) {
  height: auto;
  min-height: 56px;
}

.login-input :deep(.q-field__control-container) {
  height: auto;
  min-height: 56px;
}
</style>
