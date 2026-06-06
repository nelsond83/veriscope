<template>
  <q-page class="q-pa-lg">
    <div class="row items-center q-mb-lg">
      <q-btn flat round icon="arrow_back" :to="{ name: 'cases' }" class="q-mr-sm" />
      <div>
        <div class="text-h5 text-weight-bold text-white">{{ caseData?.name || 'Case' }}</div>
        <div class="text-caption text-grey-6">{{ caseData?.description }}</div>
      </div>
      <q-space />
      <q-badge v-if="caseData" :color="statusColor(caseData.status)" :label="caseData.status_display" />
    </div>

    <q-tabs v-model="tab" dark align="left" class="q-mb-lg" active-color="primary" indicator-color="primary">
      <q-tab name="reports" label="Reports" icon="description" />
      <q-tab name="reference" label="Reference Data" icon="fact_check" />
      <q-tab name="comparisons" label="Comparisons" icon="compare" />
    </q-tabs>

    <!-- Reports tab -->
    <q-tab-panels v-model="tab" dark animated>
      <q-tab-panel name="reports" class="q-pa-none">
        <div class="row items-center q-mb-md">
          <div class="text-subtitle1 text-white">Reports ({{ reports.length }})</div>
          <q-space />
          <q-btn unelevated color="primary" icon="upload_file" label="Upload to Case"
            :to="{ name: 'upload', query: { case: route.params.id } }" />
        </div>
        <q-card class="vs-card">
          <q-list separator>
            <q-item v-if="!reports.length">
              <q-item-section class="text-grey-6 q-py-lg text-center">
                No reports in this case yet
              </q-item-section>
            </q-item>
            <q-item
              v-for="r in reports"
              :key="r.id"
              :to="{ name: 'report-detail', params: { id: r.id } }"
              clickable
              v-ripple
            >
              <q-item-section avatar>
                <BureauBadge :bureau="r.bureau" :show-name="false" size="sm" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="row items-center gap-sm">
                  {{ r.subject?.full_name || r.original_filename }}
                  <BureauBadge :bureau="r.bureau" size="sm" class="q-ml-sm" />
                </q-item-label>
                <q-item-label caption>
                  {{ r.original_filename }}
                </q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-badge :color="rStatusColor(r.status)" :label="r.status_display" />
              </q-item-section>
            </q-item>
          </q-list>
        </q-card>
      </q-tab-panel>

      <!-- Reference data tab -->
      <q-tab-panel name="reference" class="q-pa-none">
        <div class="row items-center q-mb-md">
          <div class="text-subtitle1 text-white">Reference Data ({{ referenceData.length }})</div>
          <q-space />
          <q-btn unelevated color="primary" icon="upload" label="Import CSV" @click="showImport = true" />
        </div>
        <q-card class="vs-card">
          <q-table
            :rows="referenceData"
            :columns="refColumns"
            row-key="id"
            flat
            dark
            class="vs-table"
          >
            <template #no-data>
              <div class="text-grey-6 q-pa-md">No reference data imported yet</div>
            </template>
          </q-table>
        </q-card>
      </q-tab-panel>

      <!-- Comparisons tab -->
      <q-tab-panel name="comparisons" class="q-pa-none">
        <div class="row items-center q-mb-md">
          <div class="text-subtitle1 text-white">Comparison Results ({{ comparisons.length }})</div>
          <q-space />
          <q-btn unelevated color="secondary" icon="compare" label="Run Comparison" @click="showCompare = true" />
        </div>
        <q-card class="vs-card">
          <q-table
            :rows="comparisons"
            :columns="compColumns"
            row-key="id"
            flat
            dark
            class="vs-table"
          >
            <template #body-cell-match_status="props">
              <q-td :props="props">
                <q-badge :color="matchColor(props.value)" :label="props.row.match_status_display" />
              </q-td>
            </template>
            <template #no-data>
              <div class="text-grey-6 q-pa-md">No comparisons run yet</div>
            </template>
          </q-table>
        </q-card>
      </q-tab-panel>
    </q-tab-panels>

    <!-- Import CSV dialog -->
    <q-dialog v-model="showImport" persistent>
      <q-card class="vs-card" style="min-width:420px">
        <q-card-section>
          <div class="text-h6 text-white">Import Reference Data (CSV)</div>
          <div class="text-caption text-grey-6 q-mt-xs">
            CSV columns: full_name, ssn, date_of_birth (MM/DD/YYYY)
          </div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-input v-model="importLabel" label="Label" dark filled class="q-mb-sm"
            placeholder="e.g. Application Form" />
          <q-file v-model="importFile" label="CSV File" dark filled accept=".csv" />
        </q-card-section>
        <q-card-actions align="right" class="q-px-md q-pb-md">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn unelevated color="primary" label="Import" :loading="importing" @click="importCSV" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Run comparison dialog -->
    <q-dialog v-model="showCompare" persistent>
      <q-card class="vs-card" style="min-width:420px">
        <q-card-section>
          <div class="text-h6 text-white">Run Comparison</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-select v-model="compareReport" :options="reportOptions" option-label="original_filename"
            option-value="id" label="Report" dark filled emit-value map-options class="q-mb-sm" />
          <q-select v-model="compareRef" :options="referenceData" option-label="label"
            option-value="id" label="Reference Data" dark filled emit-value map-options />
        </q-card-section>
        <q-card-actions align="right" class="q-px-md q-pb-md">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn unelevated color="secondary" label="Compare" :loading="comparing" @click="runCompare" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useQuasar } from 'quasar'
import { api } from 'boot/axios'
import BureauBadge from 'components/BureauBadge.vue'

const route = useRoute()
const $q = useQuasar()

const caseData = ref(null)
const reports = ref([])
const referenceData = ref([])
const comparisons = ref([])
const tab = ref('reports')

const showImport = ref(false)
const importLabel = ref('')
const importFile = ref(null)
const importing = ref(false)

const showCompare = ref(false)
const compareReport = ref(null)
const compareRef = ref(null)
const comparing = ref(false)

const reportOptions = computed(() => reports.value.filter(r => r.status === 'parsed'))

const statusColor = (s) => ({ open: 'positive', in_review: 'info', closed: 'grey' }[s] || 'grey')
const rStatusColor = (s) => ({ parsed: 'positive', failed: 'negative', parsing: 'info', pending: 'grey' }[s] || 'grey')
const matchColor = (s) => ({ match: 'positive', mismatch: 'negative', partial: 'warning', missing: 'grey' }[s] || 'grey')

const refColumns = [
  { name: 'label', label: 'Label', field: 'label', align: 'left' },
  { name: 'full_name', label: 'Name', field: 'full_name', align: 'left' },
  { name: 'ssn', label: 'SSN', field: 'ssn', align: 'left' },
  { name: 'date_of_birth', label: 'DOB', field: 'date_of_birth', align: 'center' },
  { name: 'source', label: 'Source', field: 'source', align: 'center' },
]

const compColumns = [
  { name: 'field_name', label: 'Field', field: 'field_name', align: 'left' },
  { name: 'report_value', label: 'Report Value', field: 'report_value', align: 'left' },
  { name: 'reference_value', label: 'Reference Value', field: 'reference_value', align: 'left' },
  { name: 'match_status', label: 'Status', field: 'match_status', align: 'center' },
]

async function load() {
  const id = route.params.id
  const [caseRes, reportsRes, refRes, compRes] = await Promise.all([
    api.get(`/cases/${id}/`),
    api.get('/reports/', { params: { case: id } }),
    api.get('/reference-data/', { params: { case: id } }),
    api.get('/comparisons/', { params: { case: id } }),
  ])
  caseData.value = caseRes.data
  reports.value = reportsRes.data.results || reportsRes.data
  referenceData.value = refRes.data.results || refRes.data
  comparisons.value = compRes.data.results || compRes.data
}

async function importCSV() {
  if (!importFile.value) return
  importing.value = true
  const form = new FormData()
  form.append('file', importFile.value)
  form.append('label', importLabel.value || importFile.value.name)
  try {
    await api.post(`/cases/${route.params.id}/import-reference/`, form)
    showImport.value = false
    $q.notify({ type: 'positive', message: 'Reference data imported.' })
    await load()
  } catch {
    $q.notify({ type: 'negative', message: 'Import failed.' })
  } finally {
    importing.value = false
  }
}

async function runCompare() {
  if (!compareReport.value || !compareRef.value) return
  comparing.value = true
  try {
    await api.post(`/cases/${route.params.id}/compare/`, {
      report_id: compareReport.value,
      reference_id: compareRef.value,
    })
    showCompare.value = false
    tab.value = 'comparisons'
    $q.notify({ type: 'positive', message: 'Comparison complete.' })
    await load()
  } catch {
    $q.notify({ type: 'negative', message: 'Comparison failed.' })
  } finally {
    comparing.value = false
  }
}

onMounted(load)
</script>
