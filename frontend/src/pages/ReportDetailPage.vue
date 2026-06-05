<template>
  <q-page class="q-pa-lg">
    <div class="row items-center q-mb-lg">
      <q-btn flat round icon="arrow_back" :to="{ name: 'dashboard' }" class="q-mr-sm" />
      <div>
        <div class="text-h5 text-weight-bold text-white">{{ report?.original_filename || 'Report' }}</div>
        <div class="text-caption text-grey-6">
          {{ report?.bureau_display }} ·
          Uploaded {{ report ? formatDate(report.uploaded_at) : '' }}
        </div>
      </div>
      <q-space />
      <q-badge v-if="report" :color="statusColor(report.status)" :label="report.status_display" class="q-mr-md" />
      <q-btn
        v-if="report?.status !== 'parsed'"
        unelevated
        color="primary"
        icon="refresh"
        label="Re-parse"
        :loading="reparsing"
        @click="reparse"
      />
    </div>

    <div v-if="!report" class="text-center text-grey-6 q-pa-xl">
      <q-spinner color="primary" size="40px" />
    </div>

    <div v-else-if="report.status === 'failed'" class="vs-card q-pa-lg text-negative">
      Parse failed: {{ report.error_message }}
    </div>

    <div v-else-if="subject" class="row q-gutter-lg">
      <!-- Identity -->
      <div class="col-xs-12 col-md-4">
        <div class="text-subtitle1 text-weight-medium text-white q-mb-md">Identity</div>
        <q-card class="vs-card">
          <q-card-section>
            <div class="vs-field q-mb-md">
              <div class="vs-field-label">Full Name</div>
              <div class="vs-field-value">{{ subject.full_name || '—' }}</div>
            </div>
            <div class="vs-field q-mb-md">
              <div class="vs-field-label">SSN</div>
              <div class="vs-field-value font-mono">
                {{ subject.ssn || (subject.ssn_last_four ? `XXX-XX-${subject.ssn_last_four}` : '—') }}
              </div>
            </div>
            <div class="vs-field q-mb-md">
              <div class="vs-field-label">Date of Birth</div>
              <div class="vs-field-value">{{ subject.date_of_birth || '—' }}</div>
            </div>
            <div v-if="subject.alternate_names?.length" class="vs-field">
              <div class="vs-field-label">Alternate Names</div>
              <q-chip
                v-for="n in subject.alternate_names"
                :key="n.id"
                dense
                color="dark"
                text-color="grey-4"
                class="q-mt-xs"
              >
                {{ n.name }}
              </q-chip>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Addresses -->
      <div class="col-xs-12 col-md-4">
        <div class="text-subtitle1 text-weight-medium text-white q-mb-md">
          Addresses ({{ subject.addresses?.length || 0 }})
        </div>
        <q-card class="vs-card">
          <q-list separator>
            <q-item v-if="!subject.addresses?.length">
              <q-item-section class="text-grey-6">No addresses extracted</q-item-section>
            </q-item>
            <q-item v-for="a in subject.addresses" :key="a.id">
              <q-item-section avatar>
                <q-icon name="location_on" color="grey-6" />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ a.street }}</q-item-label>
                <q-item-label caption>{{ a.city }}, {{ a.state }} {{ a.zip_code }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-badge v-if="a.address_type !== 'unknown'" :label="a.address_type" color="dark" />
              </q-item-section>
            </q-item>
          </q-list>
        </q-card>
      </div>

      <!-- Accounts -->
      <div class="col-xs-12">
        <div class="text-subtitle1 text-weight-medium text-white q-mb-md">
          Financial Accounts ({{ subject.financial_accounts?.length || 0 }})
        </div>
        <q-card class="vs-card">
          <q-table
            :rows="subject.financial_accounts || []"
            :columns="accountColumns"
            row-key="id"
            flat
            dark
            dense
            class="vs-table"
          >
            <template #body-cell-status="props">
              <q-td :props="props">
                <q-badge :color="accountStatusColor(props.value)" :label="props.row.status_display" dense />
              </q-td>
            </template>
            <template #body-cell-balance="props">
              <q-td :props="props" class="text-right font-mono">
                {{ props.value != null ? '$' + Number(props.value).toLocaleString() : '—' }}
              </q-td>
            </template>
            <template #no-data>
              <div class="text-grey-6 q-pa-md">No accounts extracted</div>
            </template>
          </q-table>
        </q-card>
      </div>
    </div>

    <div v-else-if="report.status === 'pending' || report.status === 'parsing'" class="text-center text-grey-6 q-pa-xl">
      <q-spinner color="primary" size="40px" class="q-mr-sm" />
      <span>{{ report.status === 'parsing' ? 'Parsing…' : 'Waiting to parse' }}</span>
    </div>

    <div v-else class="text-grey-6 q-pa-xl text-center">No subject data extracted yet.</div>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useQuasar } from 'quasar'
import { api } from 'boot/axios'

const route = useRoute()
const $q = useQuasar()
const report = ref(null)
const subject = ref(null)
const reparsing = ref(false)

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
.vs-field-label {
  font-size: 11px;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: #64748b;
  margin-bottom: 2px;
}
.vs-field-value {
  color: #f1f5f9;
  font-size: 15px;
}
.font-mono { font-family: 'Roboto Mono', monospace; }
</style>
