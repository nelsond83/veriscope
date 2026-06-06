<template>
  <div class="row items-center justify-center" style="min-height: 100vh; background: #1D1D1F;">
    <q-card style="width: 380px; background: #2C2C2E; border: 1px solid rgba(245,245,247,0.1);">
      <q-card-section class="text-center q-pt-xl q-pb-md">
        <div class="text-h5 text-weight-bold text-white q-mb-xs">Veriscope</div>
        <div class="text-caption text-grey-6">Due diligence platform</div>
      </q-card-section>

      <q-card-section class="q-px-xl q-pb-xl">
        <q-form @submit.prevent="submit">
          <q-input
            v-model="username"
            label="Username"
            dark
            filled
            class="q-mb-md"
            autofocus
            :disable="loading"
          />
          <q-input
            v-model="password"
            label="Password"
            type="password"
            dark
            filled
            class="q-mb-lg"
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
