<template>
  <q-page class="q-pa-lg">
    <div class="row items-center q-mb-lg">
      <div>
        <div class="text-h5 text-weight-bold text-white">Unmatched Reports</div>
        <div class="text-caption text-grey-6">
          Reports that couldn't be automatically linked to an identity
        </div>
      </div>
      <q-badge v-if="unmatched.length" :label="unmatched.length" color="grey-7" class="q-ml-sm" />
      <q-space />
      <q-btn unelevated color="primary" icon="upload_file" label="Upload Reports" :to="{ name: 'upload' }" />
    </div>

    <!-- Empty state -->
    <q-card v-if="!loading && !unmatched.length" class="vs-card">
      <q-card-section class="text-center q-py-xl">
        <q-icon name="check_circle" size="48px" color="positive" class="q-mb-md" />
        <div class="text-h6 text-white q-mb-xs">All reports matched</div>
        <div class="text-caption text-grey-6">Every uploaded report has been linked to an identity.</div>
      </q-card-section>
    </q-card>

    <!-- Loading skeleton -->
    <div v-if="loading">
      <q-card v-for="n in 3" :key="n" class="vs-card q-mb-lg">
        <q-card-section class="row items-center no-wrap q-pb-sm" style="gap:14px">
          <q-skeleton type="circle" size="32px" />
          <div class="col">
            <q-skeleton type="text" width="45%" class="q-mb-xs" />
            <q-skeleton type="text" width="25%" />
          </div>
          <q-skeleton type="QBadge" width="70px" />
        </q-card-section>
        <q-separator dark />
        <q-card-section class="row q-col-gutter-md q-pb-sm">
          <div v-for="i in 3" :key="i" class="col-xs-12 col-sm-4">
            <q-skeleton type="text" width="50%" class="q-mb-xs" />
            <q-skeleton type="text" width="70%" />
          </div>
        </q-card-section>
        <q-separator dark />
        <q-card-section>
          <q-skeleton type="QInput" class="full-width" />
        </q-card-section>
      </q-card>
    </div>

    <!-- Unmatched report cards -->
    <div v-for="r in unmatched" :key="r.id" class="q-mb-lg">
      <q-card class="vs-card">
        <!-- Report header -->
        <q-card-section class="row items-center no-wrap q-pb-sm" style="gap:14px">
          <BureauBadge :bureau="r.bureau" size="md" :show-name="true" />
          <div class="col">
            <div class="text-weight-medium text-white" style="font-size:1rem">{{ r.original_filename }}</div>
            <div class="text-caption text-grey-6">Uploaded {{ formatDate(r.uploaded_at) }}</div>
          </div>
          <q-badge :color="statusColor(r.status)" :label="r.status_display"
            style="font-size:0.75rem; padding:5px 10px" />
          <q-btn flat round icon="open_in_new" size="md" color="grey-5"
            :to="{ name: 'report-detail', params: { id: r.id }, query: { from: 'unmatched' } }" title="View report" />
          <q-btn flat round icon="delete" size="md" color="negative"
            :loading="deleting === r.id" title="Delete report" @click="confirmDelete(r)" />
        </q-card-section>

        <q-separator dark />

        <!-- Extracted data -->
        <q-card-section v-if="r.subject" class="row q-col-gutter-md q-pb-sm">
          <div class="col-xs-12 col-sm-4">
            <div class="unmatched-label">Extracted Name</div>
            <div class="unmatched-value">{{ r.subject.full_name || '—' }}</div>
          </div>
          <div class="col-xs-6 col-sm-3">
            <div class="unmatched-label">Date of Birth</div>
            <div class="unmatched-value">{{ r.subject.date_of_birth || '—' }}</div>
          </div>
          <div class="col-xs-6 col-sm-3">
            <div class="unmatched-label">SSN</div>
            <div class="unmatched-value" style="font-family:monospace">
              {{ r.subject.ssn || (r.subject.ssn_last_four ? `XXX-XX-${r.subject.ssn_last_four}` : '—') }}
            </div>
          </div>
          <div v-if="r.subject.addresses?.length" class="col-xs-12 col-sm-2">
            <div class="unmatched-label">Address</div>
            <div class="unmatched-value" style="font-size:0.78rem">
              {{ r.subject.addresses[0].street }}
            </div>
          </div>
        </q-card-section>

        <q-card-section v-else class="text-caption text-grey-6 q-py-sm">
          Report not yet parsed — no extracted data available.
          <q-btn flat dense size="sm" label="Parse now" color="primary" :loading="reparsing === r.id"
            @click="reparse(r)" />
        </q-card-section>

        <q-separator dark />

        <!-- Assignment row -->
        <q-card-section class="row items-center no-wrap q-py-sm" style="gap:12px">
          <q-icon name="link" color="grey-6" size="18px" />
          <span class="text-caption text-grey-5 text-uppercase" style="letter-spacing:.5px; white-space:nowrap">
            Assign to
          </span>
          <q-select
            v-model="selections[r.id]"
            :options="identityOptions"
            option-value="id"
            option-label="label"
            emit-value
            map-options
            use-input
            input-debounce="0"
            @filter="filterIdentities"
            dark filled dense
            placeholder="Search identities…"
            class="col"
            style="max-width:420px"
            clearable
          >
            <template #option="scope">
              <q-item v-bind="scope.itemProps">
                <q-item-section>
                  <q-item-label>{{ scope.opt.full_name }}</q-item-label>
                  <q-item-label caption>{{ scope.opt.dob }} · SSN {{ scope.opt.ssn_last4 }}</q-item-label>
                </q-item-section>
              </q-item>
            </template>
          </q-select>
          <q-btn unelevated color="primary" label="Assign" size="sm"
            :disable="!selections[r.id]"
            :loading="assigning === r.id"
            @click="assign(r)" />
        </q-card-section>
      </q-card>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { api } from 'boot/axios'
import BureauBadge from 'components/BureauBadge.vue'

const $q = useQuasar()
const loading = ref(false)
const unmatched = ref([])
const allIdentities = ref([])
const identityOptions = ref([])
const selections = ref({})
const assigning = ref(null)
const reparsing = ref(null)
const deleting = ref(null)

const statusColor = (s) => ({ parsed: 'positive', failed: 'negative', parsing: 'info', pending: 'grey' }[s] || 'grey')
const formatDate = (d) => d ? new Date(d).toLocaleDateString() : ''

function filterIdentities(val, update) {
  const q = val.toLowerCase()
  update(() => {
    identityOptions.value = allIdentities.value.filter(i =>
      i.full_name.toLowerCase().includes(q) ||
      (i.ssn || '').slice(-4).includes(q)
    )
  })
}

async function load() {
  loading.value = true
  try {
    const [unmatchedRes, identitiesRes] = await Promise.all([
      api.get('/reports/', { params: { unmatched: '1' } }),
      api.get('/identities/'),
    ])
    unmatched.value = unmatchedRes.data.results || unmatchedRes.data
    const ids = identitiesRes.data.results || identitiesRes.data
    allIdentities.value = ids.map(i => ({
      ...i,
      label: `${i.full_name}  ···  DOB ${i.date_of_birth || '?'}`,
      dob: i.date_of_birth || '—',
      ssn_last4: i.ssn ? `***-**-${i.ssn.slice(-4)}` : '—',
    }))
    identityOptions.value = allIdentities.value
  } finally {
    loading.value = false
  }
}

async function assign(report) {
  const identityId = selections.value[report.id]
  if (!identityId) return
  assigning.value = report.id
  try {
    await api.post(`/identities/${identityId}/assign-report/`, { report_id: report.id })
    $q.notify({ type: 'positive', message: 'Report assigned and compared.' })
    unmatched.value = unmatched.value.filter(r => r.id !== report.id)
    delete selections.value[report.id]
  } catch {
    $q.notify({ type: 'negative', message: 'Assignment failed.' })
  } finally {
    assigning.value = null
  }
}

function confirmDelete(report) {
  $q.dialog({
    title: 'Delete Report?',
    message: `Remove <strong>${report.original_filename}</strong> permanently? This cannot be undone.`,
    html: true,
    ok: { label: 'Delete', color: 'negative', unelevated: true },
    cancel: { label: 'Cancel', flat: true },
    dark: true,
  }).onOk(() => deleteReport(report))
}

async function deleteReport(report) {
  deleting.value = report.id
  try {
    await api.delete(`/reports/${report.id}/`)
    unmatched.value = unmatched.value.filter(r => r.id !== report.id)
    $q.notify({ type: 'positive', message: 'Report deleted.' })
  } catch {
    $q.notify({ type: 'negative', message: 'Delete failed.' })
  } finally {
    deleting.value = null
  }
}

async function reparse(report) {
  reparsing.value = report.id
  try {
    const res = await api.post(`/reports/${report.id}/parse/`)
    const idx = unmatched.value.findIndex(r => r.id === report.id)
    if (idx !== -1) unmatched.value[idx] = res.data
    $q.notify({ type: 'positive', message: 'Report parsed.' })
  } catch {
    $q.notify({ type: 'negative', message: 'Parse failed.' })
  } finally {
    reparsing.value = null
  }
}

onMounted(load)
</script>

<style scoped>
.unmatched-label {
  color: #AAAAAE;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  margin-bottom: 3px;
}
.unmatched-value {
  color: #D8D8DA;
  font-size: 0.85rem;
  font-weight: 500;
}
</style>
