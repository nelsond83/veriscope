<template>
  <q-page class="q-pa-lg column" style="min-height:calc(100vh - 64px)">
    <div class="row items-center q-mb-md">
      <div>
        <div class="text-h5 text-weight-bold text-white">Corrections</div>
        <div class="text-caption text-grey-6">Active corrections for this session, grouped by bureau</div>
      </div>
      <q-space />
      <q-btn flat unelevated icon="download" label="Export Corrections" class="q-mr-sm" @click="exportCorrections" />
      <q-btn unelevated color="primary" icon="add" label="Add Correction" @click="openAddDialog" />
    </div>

    <q-tabs v-model="tab" dark align="left" class="q-mb-md" active-color="primary" indicator-color="primary">
      <q-tab v-for="b in BUREAUS" :key="b" :name="b" :label="bureauLabel(b)" />
    </q-tabs>

    <q-card v-if="loading" class="vs-card col column">
      <q-list separator>
        <q-item v-for="n in 6" :key="n">
          <q-item-section>
            <q-skeleton type="text" width="20%" />
          </q-item-section>
          <q-item-section>
            <q-skeleton type="text" width="25%" />
          </q-item-section>
          <q-item-section>
            <q-skeleton type="text" width="20%" />
          </q-item-section>
          <q-item-section>
            <q-skeleton type="text" width="50%" />
          </q-item-section>
        </q-item>
      </q-list>
    </q-card>

    <q-card v-else class="vs-card col column">
      <q-table
        :rows="rowsForTab"
        :columns="columns"
        row-key="id"
        flat
        dark
        :filter="filter"
        :rows-per-page-options="[0]"
        hide-pagination
        class="vs-table col"
        style="height:100%"
      >
        <template #top-right>
          <q-input v-model="filter" dense filled dark placeholder="Search…" style="min-width:220px">
            <template #append><q-icon name="search" /></template>
          </q-input>
        </template>

        <template #body-cell-note="props">
          <q-td :props="props">
            {{ props.value }}
            <q-popup-edit v-model="props.row.note" v-slot="scope"
              @save="val => patchCorrection(props.row, { note: val })">
              <q-input v-model="scope.value" type="textarea" autogrow dense autofocus dark filled
                @keyup.enter.stop="scope.set" />
            </q-popup-edit>
          </q-td>
        </template>

        <template #body-cell-actions="props">
          <q-td :props="props" auto-width>
            <q-btn flat round dense icon="delete" color="negative" size="sm" @click="confirmDelete(props.row)" />
          </q-td>
        </template>

        <template #no-data>
          <div class="full-width text-center text-grey-6 q-pa-xl">
            No active corrections for {{ bureauLabel(tab) }}.
          </div>
        </template>
      </q-table>
    </q-card>

    <!-- Add Correction dialog -->
    <q-dialog v-model="showAddDialog" persistent>
      <q-card class="vs-card" style="min-width:420px; max-width:480px">
        <q-card-section>
          <div class="text-h6 text-white">Add Correction</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-select v-model="addForm.identity" :options="identityOptions" option-value="id" option-label="label"
            emit-value map-options use-input input-debounce="0" @filter="filterIdentities"
            dark filled dense label="Identity" class="q-mb-sm" :rules="[v => !!v || 'Required']" />
          <q-select v-model="addForm.bureau" :options="BUREAU_OPTIONS" emit-value map-options
            dark filled dense label="Bureau" class="q-mb-sm" />
          <q-input v-model="addForm.note" label="Correction" type="textarea" autogrow dark filled
            :rules="[v => !!v?.trim() || 'Required']" />
        </q-card-section>
        <q-card-actions align="right" class="q-px-md q-pb-md">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn unelevated color="primary" label="Add" :loading="adding" @click="addCorrection" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { api } from 'boot/axios'

const $q = useQuasar()
const loading = ref(true)
const corrections = ref([])
const filter = ref('')

const BUREAUS = ['equifax', 'experian', 'transunion']
const tab = ref('equifax')

const BUREAU_OPTIONS = [
  { label: 'Equifax', value: 'equifax' },
  { label: 'Experian', value: 'experian' },
  { label: 'TransUnion', value: 'transunion' },
]

function bureauLabel(b) {
  return { equifax: 'Equifax', experian: 'Experian', transunion: 'TransUnion' }[b] || b
}

const columns = [
  { name: 'identity_entity_id', label: 'Entity', field: 'identity_entity_id', align: 'left', sortable: true },
  { name: 'identity_first_name', label: 'First Name', field: 'identity_first_name', align: 'left', sortable: true },
  { name: 'identity_last_name', label: 'Last Name', field: 'identity_last_name', align: 'left', sortable: true },
  { name: 'identity_ssn', label: 'SSN', field: 'identity_ssn', align: 'left' },
  { name: 'identity_current_address', label: 'Current Address', field: 'identity_current_address', align: 'left' },
  { name: 'note', label: 'Correction', field: 'note', align: 'left' },
  { name: 'actions', label: '', field: 'actions', align: 'right' },
]

const rowsForTab = computed(() => corrections.value.filter(c => c.bureau === tab.value))

const allIdentities = ref([])
const identityOptions = ref([])
const showAddDialog = ref(false)
const adding = ref(false)
const addForm = ref({ identity: null, bureau: 'equifax', note: '' })

function filterIdentities(val, update) {
  const q = val.toLowerCase()
  update(() => {
    identityOptions.value = allIdentities.value.filter(i => i.label.toLowerCase().includes(q))
  })
}

function openAddDialog() {
  addForm.value = { identity: null, bureau: tab.value, note: '' }
  showAddDialog.value = true
}

async function addCorrection() {
  if (!addForm.value.identity || !addForm.value.note?.trim()) return
  adding.value = true
  try {
    await api.post('/corrections/', addForm.value)
    showAddDialog.value = false
    $q.notify({ type: 'positive', message: 'Correction added.' })
    await load()
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to add correction.' })
  } finally {
    adding.value = false
  }
}

async function patchCorrection(row, patch) {
  try {
    await api.patch(`/corrections/${row.id}/`, patch)
    $q.notify({ type: 'positive', message: 'Correction updated.' })
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to update correction.' })
    await load()
  }
}

function confirmDelete(row) {
  $q.dialog({
    title: 'Delete Correction?',
    message: `Remove this correction for ${row.identity_first_name} ${row.identity_last_name}?`,
    ok: { label: 'Delete', color: 'negative', unelevated: true },
    cancel: { label: 'Cancel', flat: true },
    dark: true,
  }).onOk(() => deleteCorrection(row))
}

async function deleteCorrection(row) {
  try {
    await api.delete(`/corrections/${row.id}/`)
    corrections.value = corrections.value.filter(c => c.id !== row.id)
    $q.notify({ type: 'positive', message: 'Correction deleted.' })
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to delete correction.' })
  }
}

async function exportCorrections() {
  try {
    const res = await api.get('/identities/export-dd/', { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = 'corrections_all_bureaus.zip'
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    $q.notify({ type: 'negative', message: 'Export failed.' })
  }
}

async function load() {
  loading.value = true
  try {
    const [corrRes, idRes] = await Promise.all([
      api.get('/corrections/'),
      api.get('/identities/'),
    ])
    corrections.value = corrRes.data.results || corrRes.data
    const ids = idRes.data.results || idRes.data
    allIdentities.value = ids.map(i => ({ id: i.id, label: `${i.full_name} (${i.entity_id})` }))
    identityOptions.value = allIdentities.value
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
