<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated class="vs-header">
      <q-toolbar>
        <q-btn flat dense round icon="menu" @click="drawer = !drawer" />
        <q-toolbar-title class="row items-center no-wrap gap-sm">
          <img src="/logo.svg" height="36" alt="Veriscope" class="q-mr-xs" />
        </q-toolbar-title>
        <q-space />
        <q-btn flat round icon="upload_file" :to="{ name: 'upload' }" title="Upload Report" />
        <q-btn flat round icon="add_box" @click="$emit('new-case')" title="New Case" />
      </q-toolbar>
    </q-header>

    <q-drawer v-model="drawer" show-if-above :width="220" :breakpoint="700" class="vs-drawer">
      <q-scroll-area class="fit">
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

const drawer = ref(false)

const navLinks = [
  { label: 'Dashboard', icon: 'dashboard', to: '/dashboard' },
  { label: 'Cases', icon: 'folder_open', to: '/cases' },
  { label: 'Upload Report', icon: 'upload_file', to: '/upload' },
]
</script>

<style lang="scss">
.vs-header {
  background: #0f172a;
  border-bottom: 1px solid #1e293b;
}

.vs-drawer {
  background: #0d1117;
  border-right: 1px solid #1e293b;
}

.vs-nav-item {
  border-radius: 8px;
  margin: 2px 8px;
  color: #94a3b8;

  &:hover {
    background: #1e293b;
    color: #f1f5f9;
  }
}

.vs-nav-active {
  background: rgba(34, 211, 238, 0.12) !important;
  color: #22d3ee !important;
}

.q-page-container {
  background: #0d1117;
}
</style>
