<template>
  <q-page class="flex flex-center column text-center q-pa-xl">
    <q-icon name="search_off" size="80px" color="grey-8" />
    <div class="text-h4 text-white q-mt-lg">404</div>
    <div class="text-grey-6 q-mt-sm q-mb-xl">Page not found</div>
    <q-btn unelevated color="primary" label="Go to Dashboard" :to="{ name: 'dashboard' }" />
  </q-page>
</template>
