<template>
  <q-page class="q-pa-lg column" style="min-height:calc(100vh - 64px)">
    <div class="row items-center q-mb-md">
      <div>
        <div class="text-h5 text-weight-bold text-white">Identities</div>
        <div class="text-caption text-grey-6">People under due diligence investigation</div>
      </div>
      <q-space />
      <q-chip v-if="activeFilter" dense removable
        :color="activeFilter === 'flagged' ? 'negative' : 'grey-7'"
        text-color="white"
        :label="`Filter: ${activeFilter}`"
        class="q-mr-sm"
        @remove="router.push({ name: 'identities' })" />
      <q-btn flat unelevated icon="download" label="Export All" class="q-mr-sm" @click="exportAll" />
      <q-btn flat unelevated icon="restart_alt" label="Clear All DD" color="warning" class="q-mr-sm" @click="confirmClearAll = true" />
      <q-btn flat unelevated icon="upload" label="Import CSV" class="q-mr-sm" @click="showImport = true" />
      <q-btn unelevated color="primary" icon="person_add" label="Add Identity" @click="showCreate = true" />
    </div>

    <q-card class="vs-card col column">
      <q-table
        :rows="filteredIdentities"
        :columns="columns"
        row-key="id"
        flat
        dark
        :loading="loading"
        :rows-per-page-options="[0]"
        hide-pagination
        class="vs-table col"
        style="height:100%"
        @row-click="(_, row) => $router.push({ name: 'identity-detail', params: { id: row.id }, query: activeFilter ? { dd_filter: activeFilter } : {} })"
      >
        <template #body-cell-dd_status="props">
          <q-td :props="props">
            <q-badge :color="ddColor(props.value)" :label="ddLabel(props.value)"
              style="font-size:0.78rem; padding:5px 12px; font-weight:600; letter-spacing:0.3px" />
          </q-td>
        </template>
        <template #body-cell-bureaus="props">
          <q-td :props="props">
            <div class="row no-wrap justify-center gap-xs">
              <BureauBadge
                v-for="b in ['equifax','experian','transunion']"
                :key="b"
                :bureau="b"
                :show-name="false"
                size="lg"
                :class="hasBureau(props.row, b) ? '' : 'vs-bureau-missing'"
              />
            </div>
          </q-td>
        </template>
        <template #body-cell-actions="props">
          <q-td :props="props" auto-width>
            <q-btn flat round dense icon="chevron_right"
              :to="{ name: 'identity-detail', params: { id: props.row.id }, query: activeFilter ? { dd_filter: activeFilter } : {} }" />
          </q-td>
        </template>
        <template #no-data>
          <div class="full-width text-center text-grey-6 q-pa-xl">
            No identities yet. Add one or import a CSV.
          </div>
        </template>
      </q-table>
    </q-card>

    <!-- Add Identity dialog -->
    <q-dialog v-model="showCreate" persistent>
      <q-card class="vs-card" style="min-width:480px; max-width:560px">
        <q-card-section>
          <div class="text-h6 text-white">Add Identity</div>
        </q-card-section>
        <q-card-section class="q-pt-none" style="max-height:75vh; overflow-y:auto">
          <q-input v-model="form.full_name" label="Full Name" dark filled class="q-mb-sm"
            :rules="[v => !!v || 'Required']" />
          <div class="row q-gutter-sm q-mb-sm">
            <q-input v-model="form.ssn" label="SSN" dark filled class="col"
              mask="###-##-####" unmasked-value />
            <q-input v-model="form.date_of_birth" label="Date of Birth" dark filled class="col"
              mask="##/##/####" hint="MM/DD/YYYY" />
            <q-select v-model="form.gender" label="Gender" dark filled class="col"
              :options="genderOptions" emit-value map-options clearable />
          </div>

          <!-- Name Variations -->
          <div class="row items-center q-mb-xs">
            <span class="text-caption text-grey-5 text-uppercase" style="letter-spacing:.5px">Name Variations / AKA</span>
            <q-space />
            <q-btn flat dense size="sm" icon="add" color="primary"
              @click="form.name_variations.push({ name:'', note:'' })" />
          </div>
          <div v-for="(v, i) in form.name_variations" :key="i"
            class="row q-gutter-xs q-mb-xs items-center">
            <q-input v-model="v.name" label="Name" dark filled dense class="col" />
            <q-input v-model="v.note" label="Note (optional)" dark filled dense style="max-width:140px" />
            <q-btn flat round dense icon="close" size="xs" color="grey-6"
              @click="form.name_variations.splice(i,1)" />
          </div>

          <!-- Phones -->
          <div class="row items-center q-mb-xs q-mt-sm">
            <span class="text-caption text-grey-5 text-uppercase" style="letter-spacing:.5px">Phone Numbers</span>
            <q-space />
            <q-btn flat dense size="sm" icon="add" color="primary"
              @click="form.phones.push({ number:'', phone_type:'mobile' })" />
          </div>
          <div v-for="(p, i) in form.phones" :key="i"
            class="row q-gutter-xs q-mb-xs items-center">
            <q-input v-model="p.number" label="Number" dark filled dense class="col" />
            <q-select v-model="p.phone_type" :options="phoneTypeOptions"
              emit-value map-options dark filled dense style="max-width:100px" />
            <q-btn flat round dense icon="close" size="xs" color="grey-6"
              @click="form.phones.splice(i,1)" />
          </div>

          <!-- Addresses -->
          <div class="row items-center q-mb-xs q-mt-sm">
            <span class="text-caption text-grey-5 text-uppercase" style="letter-spacing:.5px">Addresses</span>
            <q-space />
            <q-btn flat dense size="sm" icon="add" label="Add" color="primary" @click="addAddress(form)" />
          </div>
          <div v-for="(addr, i) in form.addresses" :key="i"
            class="q-mb-sm q-pa-sm" style="border:1px solid rgba(245,245,247,0.08); border-radius:8px">
            <div class="row items-center q-mb-xs" style="gap:6px">
              <q-select v-model="addr.address_type" :options="addrTypeOptions" emit-value map-options
                dark filled dense style="min-width:110px" />
              <q-space />
              <q-btn flat round dense icon="close" size="xs" color="grey-6"
                @click="removeAddress(form, i)" :disable="form.addresses.length === 1" />
            </div>
            <q-input v-model="addr.street" label="Street" dark filled dense class="q-mb-xs" />
            <div class="row q-gutter-xs">
              <q-input v-model="addr.city" label="City" dark filled dense class="col" />
              <q-input v-model="addr.state" label="State" dark filled dense style="max-width:70px" />
              <q-input v-model="addr.zip_code" label="ZIP" dark filled dense style="max-width:90px" />
            </div>
          </div>

          <!-- Expected FICO Range -->
          <q-select v-model="form.expected_fico_range" label="Expected FICO / Advantage Score Range (optional)"
            dark filled clearable :options="FICO_RANGES" emit-value map-options class="q-mt-sm"
            hint="Used to compare credit score on bureau reports" />

          <!-- Reference Accounts -->
          <div class="row items-center q-mb-xs q-mt-md">
            <span class="text-caption text-grey-5 text-uppercase" style="letter-spacing:.5px">Reference Accounts</span>
            <q-space />
            <q-btn flat dense size="sm" icon="add" color="primary" @click="form.ref_accounts.push(blankAccount())" />
          </div>
          <div v-for="(acct, i) in form.ref_accounts" :key="i"
            class="q-mb-sm q-pa-sm" style="border:1px solid rgba(245,245,247,0.08); border-radius:8px">
            <div class="row items-center q-mb-xs">
              <span class="text-caption text-grey-6">Account {{ i + 1 }}</span>
              <q-space />
              <q-btn flat round dense icon="close" size="xs" color="grey-6" @click="form.ref_accounts.splice(i,1)" />
            </div>
            <div class="row q-gutter-xs q-mb-xs">
              <q-input v-model="acct.creditor_name" label="Creditor" dark filled dense class="col" />
              <q-input v-model="acct.account_type" label="Type" dark filled dense style="max-width:110px" />
            </div>
            <div class="row q-gutter-xs q-mb-xs">
              <q-input v-model="acct.account_number" label="Account #" dark filled dense class="col" />
              <q-input v-model="acct.status" label="Status" dark filled dense style="max-width:110px" />
            </div>
            <div class="row q-gutter-xs q-mb-xs">
              <q-input v-model="acct.balance" label="Balance" dark filled dense class="col" prefix="$" type="number" />
              <q-input v-model="acct.credit_limit" label="Limit" dark filled dense class="col" prefix="$" type="number" />
              <q-input v-model="acct.monthly_payment" label="Mthly Pmt" dark filled dense class="col" prefix="$" type="number" />
            </div>
            <div class="row q-gutter-xs">
              <q-input v-model="acct.highest_balance" label="High Bal" dark filled dense class="col" prefix="$" type="number" />
              <q-input v-model="acct.date_opened" label="Opened" dark filled dense class="col" hint="MM/YYYY" />
            </div>
          </div>

          <q-input v-model="form.notes" label="Notes" dark filled type="textarea" autogrow class="q-mt-sm" />
        </q-card-section>
        <q-card-actions align="right" class="q-px-md q-pb-md">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn unelevated color="primary" label="Add" :loading="creating" @click="createIdentity" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Clear All DD confirmation -->
    <q-dialog v-model="confirmClearAll" persistent>
      <q-card class="vs-card" style="min-width:360px">
        <q-card-section>
          <div class="text-h6 text-white">Clear All DD Results?</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <p style="color:#EBEBED">
            This will archive the current DD results for all identities and detach their reports.
            All history will be preserved and viewable on each identity. New PDFs will be required
            to run a new DD.
          </p>
        </q-card-section>
        <q-card-actions align="right" class="q-pa-md" style="gap:8px">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn unelevated color="warning" label="Clear All" icon="restart_alt"
            :loading="clearingAll" @click="clearAllDD" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Import CSV dialog -->
    <q-dialog v-model="showImport" persistent>
      <q-card class="vs-card" style="min-width:420px">
        <q-card-section>
          <div class="text-h6 text-white">Import Identities from CSV</div>
          <div class="text-caption text-grey-6 q-mt-xs">
            Columns: full_name, ssn, date_of_birth, gender, street, city, state, zip_code, name_variations, phones, notes
          </div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-file v-model="importFile" label="CSV File" dark filled accept=".csv" />
        </q-card-section>
        <q-card-actions align="right" class="q-px-md q-pb-md">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn unelevated color="primary" label="Import" :loading="importing" @click="importCSV" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { api } from 'boot/axios'
import BureauBadge from 'components/BureauBadge.vue'

const route = useRoute()
const router = useRouter()
const $q = useQuasar()
const identities = ref([])
const loading = ref(false)

const activeFilter = computed(() => route.query.dd_status || null)
const filteredIdentities = computed(() =>
  activeFilter.value ? identities.value.filter(i => i.dd_status === activeFilter.value) : identities.value
)
const showCreate = ref(false)
const showImport = ref(false)
const confirmClearAll = ref(false)
const creating = ref(false)
const importing = ref(false)
const clearingAll = ref(false)
const importFile = ref(null)
const FICO_RANGES = [
  { label: '800-850 (Exceptional)', value: '800-850' },
  { label: '740-799 (Very Good)', value: '740-799' },
  { label: '670-739 (Good)', value: '670-739' },
  { label: '580-669 (Fair)', value: '580-669' },
  { label: '300-579 (Poor)', value: '300-579' },
]
const genderOptions = [
  { label: 'Male', value: 'male' },
  { label: 'Female', value: 'female' },
  { label: 'Other', value: 'other' },
  { label: 'Unknown', value: 'unknown' },
]
const addrTypeOptions = [
  { label: 'Current', value: 'current' },
  { label: 'Previous', value: 'previous' },
  { label: 'Other', value: 'other' },
]
const phoneTypeOptions = [
  { label: 'Mobile', value: 'mobile' },
  { label: 'Home', value: 'home' },
  { label: 'Work', value: 'work' },
  { label: 'Other', value: 'other' },
]
function blankAddress() { return { street: '', city: '', state: '', zip_code: '', address_type: 'current' } }
function addAddress(f) { f.addresses.push({ ...blankAddress(), address_type: 'previous' }) }
function removeAddress(f, i) { f.addresses.splice(i, 1) }
function blankAccount() {
  return { creditor_name: '', account_type: '', account_number: '', status: '',
           balance: null, credit_limit: null, highest_balance: null, monthly_payment: null, date_opened: '' }
}
function blankForm() {
  return { full_name: '', ssn: '', date_of_birth: '', gender: '', expected_fico_range: '',
           notes: '', addresses: [blankAddress()], name_variations: [], phones: [], ref_accounts: [] }
}

const form = ref(blankForm())

const columns = [
  { name: 'full_name', label: 'Name', field: 'full_name', align: 'left', sortable: true },
  { name: 'ssn', label: 'SSN', field: 'ssn', align: 'left' },
  { name: 'date_of_birth', label: 'Date of Birth', field: 'date_of_birth', align: 'left', sortable: true },
  { name: 'bureaus', label: 'Bureaus', field: 'bureaus', align: 'center' },
  { name: 'dd_status', label: 'DD Status', field: 'dd_status', align: 'center', sortable: true },
  { name: 'actions', label: '', field: 'actions', align: 'right' },
]

const ddColor = (s) => ({ clear: 'positive', flagged: 'negative', review: 'warning', pending: 'grey' }[s] || 'grey')
const ddLabel = (s) => ({ clear: 'Clear', flagged: 'Flagged', review: 'Review', pending: 'Pending' }[s] || s)

function hasBureau(row, bureau) {
  return (row.reports_by_bureau || {})[bureau] !== undefined
}

async function load() {
  loading.value = true
  try {
    const res = await api.get('/identities/')
    identities.value = res.data.results || res.data
  } finally {
    loading.value = false
  }
}

async function createIdentity() {
  if (!form.value.full_name.trim()) return
  creating.value = true
  try {
    // Convert DOB from MM/DD/YYYY to YYYY-MM-DD for the API
    const payload = { ...form.value }
    if (payload.date_of_birth && payload.date_of_birth.length === 10) {
      const [m, d, y] = payload.date_of_birth.split('/')
      payload.date_of_birth = `${y}-${m}-${d}`
    } else {
      delete payload.date_of_birth
    }
    await api.post('/identities/', payload)
    showCreate.value = false
    form.value = blankForm()
    $q.notify({ type: 'positive', message: 'Identity added.' })
    await load()
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to add identity.' })
  } finally {
    creating.value = false
  }
}

async function clearAllDD() {
  clearingAll.value = true
  try {
    const res = await api.post('/identities/clear-all-dd/')
    confirmClearAll.value = false
    $q.notify({ type: 'positive', message: res.data.detail })
    await load()
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to clear DD.' })
  } finally {
    clearingAll.value = false
  }
}

async function exportAll() {
  try {
    const res = await api.get('/identities/export-dd/', { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = 'dd_export.csv'
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    $q.notify({ type: 'negative', message: 'Export failed.' })
  }
}

async function importCSV() {
  if (!importFile.value) return
  importing.value = true
  const fd = new FormData()
  fd.append('file', importFile.value)
  try {
    const res = await api.post('/identities/import-csv/', fd)
    showImport.value = false
    importFile.value = null
    $q.notify({ type: 'positive', message: `Imported ${res.data.created} identities.` })
    await load()
  } catch {
    $q.notify({ type: 'negative', message: 'Import failed.' })
  } finally {
    importing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.vs-bureau-missing { opacity: 0.2; }
.gap-xs { gap: 4px; }
</style>
