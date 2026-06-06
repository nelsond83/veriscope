<template>
  <q-page class="q-pa-lg">
    <!-- Header -->
    <div class="row items-center q-mb-lg">
      <q-btn flat round icon="arrow_back" @click="goBack" class="q-mr-sm" />
      <div class="row items-center" style="gap:12px">
        <BureauBadge v-if="report" :bureau="report.bureau" size="lg" />
        <div>
          <div class="text-h5 text-weight-bold text-white">{{ report?.original_filename || 'Report' }}</div>
          <div class="text-caption text-grey-6">
            Uploaded {{ report ? formatDate(report.uploaded_at) : '' }}
          </div>
        </div>
      </div>
      <q-space />
      <div class="row items-center" style="gap:8px">
        <q-btn v-if="report?.file" flat icon="open_in_new" label="Open PDF" size="sm" color="grey-5"
          :href="report.file" target="_blank" />
        <q-badge v-if="report" :color="statusColor(report.status)" :label="report.status_display" />
        <q-btn v-if="report?.status !== 'parsed'" unelevated color="primary" icon="refresh" label="Re-parse"
          :loading="reparsing" @click="reparse" />
      </div>
    </div>

    <!-- Loading -->
    <div v-if="!report" class="text-center text-grey-6 q-pa-xl">
      <q-spinner color="primary" size="40px" />
    </div>

    <!-- Failed -->
    <div v-else-if="report.status === 'failed'" class="vs-card q-pa-lg text-negative">
      Parse failed: {{ report.error_message }}
    </div>

    <!-- Parsed -->
    <template v-else-if="subject">
      <div class="row q-col-gutter-md q-mb-lg">
        <!-- Identity card -->
        <div class="col-xs-12 col-md-4">
          <div class="text-subtitle2 text-grey-5 q-mb-sm text-uppercase" style="letter-spacing:.5px; font-size:.65rem">Extracted Identity</div>
          <q-card class="vs-card">
            <q-card-section class="q-py-sm">
              <div class="parsed-field">
                <span class="parsed-label">Full Name</span>
                <span class="parsed-value">{{ subject.full_name || '—' }}</span>
              </div>
              <div class="parsed-field">
                <span class="parsed-label">SSN</span>
                <span class="parsed-value" style="font-family:monospace">
                  {{ subject.ssn || (subject.ssn_last_four ? `XXX-XX-${subject.ssn_last_four}` : '—') }}
                </span>
              </div>
              <div class="parsed-field">
                <span class="parsed-label">Date of Birth</span>
                <span class="parsed-value">{{ subject.date_of_birth || '—' }}</span>
              </div>
              <template v-if="subject.alternate_names?.length">
                <div class="parsed-label q-mb-xs">Alternate Names</div>
                <div class="row q-gutter-xs">
                  <q-chip v-for="n in subject.alternate_names" :key="n.id" dense dark color="dark" text-color="grey-4">
                    {{ n.name }}
                  </q-chip>
                </div>
              </template>
            </q-card-section>
          </q-card>
        </div>

        <!-- Addresses -->
        <div class="col-xs-12 col-md-4">
          <div class="text-subtitle2 text-grey-5 q-mb-sm text-uppercase" style="letter-spacing:.5px; font-size:.65rem">
            Addresses ({{ subject.addresses?.length || 0 }})
          </div>
          <q-card class="vs-card">
            <q-list separator dense>
              <q-item v-if="!subject.addresses?.length">
                <q-item-section class="text-grey-6 text-caption">No addresses extracted</q-item-section>
              </q-item>
              <q-item v-for="a in subject.addresses" :key="a.id" class="q-py-sm">
                <q-item-section avatar style="min-width:28px">
                  <q-icon name="location_on" color="grey-7" size="16px" />
                </q-item-section>
                <q-item-section>
                  <q-item-label style="font-size:0.82rem; color:rgba(245,245,247,0.85)">{{ a.street }}</q-item-label>
                  <q-item-label caption>{{ a.city }}, {{ a.state }} {{ a.zip_code }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-badge v-if="a.address_type !== 'unknown'" dense :label="a.address_type" color="blue-grey-9"
                    style="font-size:0.6rem" />
                </q-item-section>
              </q-item>
            </q-list>
          </q-card>
        </div>

        <!-- Page count / meta -->
        <div class="col-xs-12 col-md-4">
          <div class="text-subtitle2 text-grey-5 q-mb-sm text-uppercase" style="letter-spacing:.5px; font-size:.65rem">Report Info</div>
          <q-card class="vs-card">
            <q-card-section class="q-py-sm">
              <div class="parsed-field">
                <span class="parsed-label">Bureau</span>
                <span class="parsed-value" style="text-transform:capitalize">{{ report.bureau_display }}</span>
              </div>
              <div class="parsed-field">
                <span class="parsed-label">Pages</span>
                <span class="parsed-value">{{ report.page_count || '—' }}</span>
              </div>
              <div class="parsed-field">
                <span class="parsed-label">Parsed</span>
                <span class="parsed-value">{{ report.parsed_at ? formatDate(report.parsed_at) : '—' }}</span>
              </div>
              <div class="parsed-field">
                <span class="parsed-label">Match</span>
                <span class="parsed-value" style="text-transform:capitalize">{{ report.match_confidence_display || '—' }}</span>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Accounts table -->
      <div class="q-mb-lg">
        <div class="text-subtitle2 text-grey-5 q-mb-sm text-uppercase" style="letter-spacing:.5px; font-size:.65rem">
          Financial Accounts ({{ subject.financial_accounts?.length || 0 }})
        </div>
        <q-card class="vs-card">
          <q-table :rows="subject.financial_accounts || []" :columns="accountColumns" row-key="id"
            flat dark dense class="vs-table" :rows-per-page-options="[0]">
            <template #body-cell-status="props">
              <q-td :props="props">
                <q-badge :color="accountStatusColor(props.value)" :label="props.row.status_display" dense
                  style="font-size:0.65rem" />
              </q-td>
            </template>
            <template #body-cell-balance="props">
              <q-td :props="props" class="text-right" style="font-family:monospace; font-size:0.8rem">
                {{ props.value != null ? '$' + Number(props.value).toLocaleString() : '—' }}
              </q-td>
            </template>
            <template #no-data>
              <div class="text-grey-6 q-pa-md text-caption">No accounts extracted</div>
            </template>
          </q-table>
        </q-card>
      </div>

      <!-- Raw document text -->
      <div class="q-mb-lg">
        <div class="row items-center q-mb-sm">
          <div class="text-subtitle2 text-grey-5 text-uppercase" style="letter-spacing:.5px; font-size:.65rem">Raw Document Text</div>
          <q-space />
          <q-btn flat dense size="sm" :icon="showRaw ? 'expand_less' : 'expand_more'"
            :label="showRaw ? 'Hide' : 'Show'" color="grey-6" @click="showRaw = !showRaw" />
        </div>
        <q-card v-if="showRaw" class="vs-card">
          <q-card-section class="q-pa-sm">
            <pre class="raw-text">{{ report.raw_text || 'No text extracted.' }}</pre>
          </q-card-section>
        </q-card>
      </div>
    </template>

    <!-- Parsing -->
    <div v-else-if="report?.status === 'pending' || report?.status === 'parsing'"
      class="text-center text-grey-6 q-pa-xl">
      <q-spinner color="primary" size="40px" class="q-mr-sm" />
      <span>{{ report.status === 'parsing' ? 'Parsing…' : 'Waiting to parse' }}</span>
    </div>

    <div v-else class="text-grey-6 q-pa-xl text-center">No subject data extracted yet.</div>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { api } from 'boot/axios'
import BureauBadge from 'components/BureauBadge.vue'

const route = useRoute()
const router = useRouter()
const $q = useQuasar()
const report = ref(null)
const subject = ref(null)
const reparsing = ref(false)
const showRaw = ref(false)

function goBack() {
  const fromIdentity = route.query.from
  if (fromIdentity) {
    router.push({ name: 'identity-detail', params: { id: fromIdentity } })
  } else {
    router.push({ name: 'identities' })
  }
}

const statusColor = (s) =>
  ({ parsed: 'positive', failed: 'negative', parsing: 'info', pending: 'grey' }[s] || 'grey')

const accountStatusColor = (s) =>
  ({ open: 'positive', closed: 'grey', derogatory: 'negative', collection: 'negative', charged_off: 'negative' }[s] || 'grey')

const formatDate = (d) => d ? new Date(d).toLocaleDateString() : ''

const accountColumns = [
  { name: 'creditor_name', label: 'Creditor', field: 'creditor_name', align: 'left', sortable: true },
  { name: 'account_type_display', label: 'Type', field: 'account_type_display', align: 'left' },
  { name: 'account_number', label: 'Account #', field: 'account_number', align: 'left' },
  { name: 'status', label: 'Status', field: 'status', align: 'center' },
  { name: 'balance', label: 'Balance', field: 'balance', align: 'right', sortable: true },
  { name: 'date_opened', label: 'Opened', field: 'date_opened', align: 'center' },
]

async function load() {
  try {
    const res = await api.get(`/reports/${route.params.id}/`)
    report.value = res.data
    subject.value = res.data.subject || null
  } catch {
    $q.notify({ type: 'negative', message: 'Report not found.' })
  }
}

async function reparse() {
  reparsing.value = true
  try {
    const res = await api.post(`/reports/${route.params.id}/parse/`)
    report.value = res.data
    subject.value = res.data.subject || null
    $q.notify({ type: 'positive', message: 'Report re-parsed.' })
  } catch (e) {
    $q.notify({ type: 'negative', message: e.response?.data?.detail || 'Parse failed.' })
  } finally {
    reparsing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.parsed-field {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid rgba(245, 245, 247, 0.06);
}
.parsed-field:last-child {
  border-bottom: none;
}
.parsed-label {
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  color: rgba(245, 245, 247, 0.35);
  min-width: 80px;
  flex-shrink: 0;
}
.parsed-value {
  font-size: 0.85rem;
  color: rgba(245, 245, 247, 0.85);
  font-weight: 500;
}
.raw-text {
  font-family: 'Roboto Mono', 'Courier New', monospace;
  font-size: 0.72rem;
  line-height: 1.6;
  color: rgba(245, 245, 247, 0.6);
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  max-height: 600px;
  overflow-y: auto;
}
</style>
