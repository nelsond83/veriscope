<template>
  <q-page class="q-pa-lg">
    <div class="row items-center q-mb-lg">
      <div>
        <div class="text-h5 text-weight-bold text-white">Cases</div>
        <div class="text-caption text-grey-6">Manage your due diligence investigations</div>
      </div>
      <q-space />
      <q-btn
        unelevated
        color="primary"
        icon="add"
        label="New Case"
        @click="showCreate = true"
      />
    </div>

    <q-card class="vs-card">
      <q-table
        :rows="cases"
        :columns="columns"
        row-key="id"
        flat
        dark
        :loading="loading"
        :rows-per-page-options="[10, 25, 50]"
        class="vs-table"
        @row-click="(_, row) => $router.push({ name: 'case-detail', params: { id: row.id } })"
      >
        <template #body-cell-status="props">
          <q-td :props="props">
            <q-badge :color="statusColor(props.value)" :label="props.row.status_display" />
          </q-td>
        </template>
        <template #body-cell-actions="props">
          <q-td :props="props" auto-width>
            <q-btn flat round dense icon="chevron_right" :to="{ name: 'case-detail', params: { id: props.row.id } }" />
          </q-td>
        </template>
        <template #no-data>
          <div class="full-width text-center text-grey-6 q-pa-xl">
            No cases yet. Create one to get started.
          </div>
        </template>
      </q-table>
    </q-card>

    <!-- Create Case Dialog -->
    <q-dialog v-model="showCreate" persistent>
      <q-card class="vs-card" style="min-width:400px">
        <q-card-section>
          <div class="text-h6 text-white">New Case</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-input
            v-model="newCase.name"
            label="Case Name"
            dark
            filled
            class="q-mb-sm"
            :rules="[v => !!v || 'Required']"
          />
          <q-input
            v-model="newCase.description"
            label="Description (optional)"
            dark
            filled
            type="textarea"
            autogrow
          />
        </q-card-section>
        <q-card-actions align="right" class="q-px-md q-pb-md">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn unelevated color="primary" label="Create" :loading="creating" @click="createCase" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useRoute } from 'vue-router'
import { api } from 'boot/axios'

const $q = useQuasar()
const route = useRoute()
const cases = ref([])
const loading = ref(false)
const showCreate = ref(false)
const creating = ref(false)
const newCase = ref({ name: '', description: '' })

const columns = [
  { name: 'name', label: 'Case Name', field: 'name', align: 'left', sortable: true },
  { name: 'status', label: 'Status', field: 'status', align: 'center', sortable: true },
  { name: 'report_count', label: 'Reports', field: 'report_count', align: 'center', sortable: true },
  { name: 'created_by_username', label: 'Created By', field: 'created_by_username', align: 'left' },
  { name: 'created_at', label: 'Created', field: 'created_at', align: 'left', sortable: true,
    format: (v) => v ? new Date(v).toLocaleDateString() : '' },
  { name: 'actions', label: '', field: 'actions', align: 'right' },
]

const statusColor = (s) => ({ open: 'positive', in_review: 'info', closed: 'grey' }[s] || 'grey')

async function load() {
  loading.value = true
  try {
    const res = await api.get('/cases/')
    cases.value = res.data.results || res.data
  } finally {
    loading.value = false
  }
}

async function createCase() {
  if (!newCase.value.name.trim()) return
  creating.value = true
  try {
    await api.post('/cases/', newCase.value)
    showCreate.value = false
    newCase.value = { name: '', description: '' }
    $q.notify({ type: 'positive', message: 'Case created.' })
    await load()
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to create case.' })
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  load()
  if (route.query.create === '1') showCreate.value = true
})
</script>
