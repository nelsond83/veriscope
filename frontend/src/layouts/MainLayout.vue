<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated class="vs-header">
      <q-toolbar>
        <q-btn flat dense round icon="menu" @click="drawer = !drawer" />
        <q-toolbar-title class="row items-center no-wrap gap-sm">
          <img src="/logo.svg" height="56" alt="Veriscope" class="q-mr-xs" />
        </q-toolbar-title>
        <q-space />
        <q-btn flat round icon="upload_file" :to="{ name: 'upload' }" title="Upload Report" />
        <q-btn flat round icon="person_add" :to="{ name: 'identities' }" title="Add Identity" />
        <q-btn flat round icon="logout" title="Sign out" @click="signOut" />
      </q-toolbar>
    </q-header>

    <q-drawer v-model="drawer" show-if-above :width="220" :breakpoint="700" class="vs-drawer">
      <q-scroll-area class="fit">
        <!-- Drawer logo -->
        <div class="vs-drawer-logo">
          <img src="/logo.svg" alt="Veriscope" />
        </div>
        <div class="q-py-md">
          <q-list padding>
            <q-item-label header class="text-caption text-weight-medium text-grey-6 q-px-md q-pb-xs">
              NAVIGATION
            </q-item-label>

            <q-item
              v-for="link in navLinks"
              :key="link.name"
              :to="link.to"
              exact
              clickable
              v-ripple
              active-class="vs-nav-active"
              class="vs-nav-item"
            >
              <q-item-section avatar>
                <q-icon :name="link.icon" size="sm" />
              </q-item-section>
              <q-item-section>{{ link.label }}</q-item-section>
            </q-item>
          </q-list>
        </div>
      </q-scroll-area>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from 'boot/axios'
import { useAuth } from 'src/composables/useAuth'

const drawer = ref(false)
const router = useRouter()
const { clearUser } = useAuth()

async function signOut() {
  try { await api.post('/auth/logout/') } catch { /* ignore */ }
  clearUser()
  router.push({ name: 'login' })
}

const navLinks = [
  { label: 'Dashboard',       icon: 'dashboard',   to: '/dashboard' },
  { label: 'Identities',      icon: 'people',      to: '/identities' },
  { label: 'Unmatched',       icon: 'link_off',    to: '/unmatched' },
  { label: 'Upload Reports',  icon: 'upload_file', to: '/upload' },
]
</script>

<style lang="scss">
.vs-header {
  background: #0F0F11;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.04) inset;
}

.vs-drawer {
  background: #0F0F11;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
}

.vs-nav-item {
  border-radius: 8px;
  margin: 2px 8px;
  color: #9A9A9F;   // was rgba(245,245,247,0.45) = 3.7:1 ✗ → now 6.4:1 ✓
  transition: background 0.12s ease, color 0.12s ease;

  .q-icon { transition: opacity 0.12s ease; }

  &:hover {
    background: rgba(255, 255, 255, 0.07);
    color: #FFFFFF;
  }
}

.vs-drawer-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 20px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);

  img {
    height: 52px;
    width: auto;
  }
}

.vs-nav-active {
  background: rgba(200, 16, 46, 0.15) !important;
  color: #FFFFFF !important;
  border: 1px solid rgba(200, 16, 46, 0.3) !important;

  .q-icon { color: #C8102E !important; }
}
</style>
