<template>
  <q-page class="q-pa-lg">
    <!-- Header -->
    <div class="row items-center q-mb-lg">
      <q-btn flat round dense icon="arrow_back" :to="{ name: 'templates' }" class="q-mr-sm" />
      <div class="text-h5 text-weight-bold text-white">
        {{ isNew ? 'New Template' : 'Edit Template' }}
      </div>
      <q-space />
      <q-btn unelevated color="primary" icon="save" label="Save Template"
        :loading="saving" @click="saveTemplate" />
    </div>

    <!-- Metadata row -->
    <div class="row q-gutter-md q-mb-lg">
      <q-input v-model="tmpl.name" label="Template Name" outlined dark dense
        class="col-xs-12 col-sm-3" style="min-width:180px" />
      <q-input v-model="tmpl.description" label="Description (optional)" outlined dark dense
        class="col-xs-12 col-sm-4" />
      <div class="col-xs-12 col-sm-4">
        <div class="text-caption text-grey-5 q-mb-xs" style="line-height:1.4">
          Keywords <span class="text-grey-7">(for auto-detection)</span>
        </div>
        <div class="keyword-wrap row items-center q-gutter-xs">
          <q-chip v-for="kw in tmpl.keywords" :key="kw" dense removable
            color="dark" text-color="grey-3" @remove="removeKeyword(kw)">{{ kw }}</q-chip>
          <q-input v-model="keywordInput" outlined dark dense placeholder="Add &amp; press Enter"
            style="width:150px" @keyup.enter="addKeyword" />
        </div>
      </div>
    </div>

    <!-- Main two-panel layout -->
    <div class="row q-gutter-md">
      <!-- Left: Sample text -->
      <div class="col-xs-12 col-md-5">
        <q-card class="vs-card full-height-card">
          <q-card-section class="q-pb-sm">
            <div class="row items-center q-gutter-xs">
              <div class="text-subtitle2 text-grey-4">Sample Text</div>
              <q-space />
              <q-btn flat dense size="sm" icon="picture_as_pdf" label="Upload PDF"
                :loading="extracting" @click="$refs.pdfInput.click()" />
              <q-btn flat dense size="sm" icon="folder_open" label="From Report"
                @click="showLoadDialog = true" />
            </div>
            <div class="text-caption text-grey-7 q-mt-xs">
              Upload a PDF or paste text directly. Use "From Report" to load text from an already-uploaded report.
            </div>
            <input ref="pdfInput" type="file" accept=".pdf" class="hidden" @change="onPdfUpload" />
          </q-card-section>
          <q-card-section class="q-pt-none">
            <div v-if="extracting" class="row items-center justify-center q-pa-xl">
              <q-spinner size="32px" color="primary" />
              <span class="q-ml-sm text-grey-5 text-caption">Extracting text from PDF...</span>
            </div>
            <q-input v-else v-model="tmpl.sample_text" type="textarea" outlined dark dense
              placeholder="Upload a PDF above, load from a report, or paste text here..."
              :rows="20" input-style="font-family: monospace; font-size: 0.78rem; color: #ccc;" />
          </q-card-section>
        </q-card>
      </div>

      <!-- Right: Field patterns -->
      <div class="col">
        <q-card class="vs-card">
          <q-card-section class="q-pb-sm">
            <div class="row items-center">
              <div class="text-subtitle2 text-grey-4">Field Patterns</div>
              <q-space />
              <q-btn flat dense size="sm" icon="add" label="Add Field" @click="addField" />
            </div>
            <div class="text-caption text-grey-7 q-mt-xs">
              Each pattern is a regex. Wrap the value you want to capture in a group: <code class="text-grey-4">(?:Name:)\s+([A-Za-z\s]+)</code>
            </div>
          </q-card-section>

          <q-card-section class="q-pt-none">
            <div v-if="!tmpl.fields.length" class="text-center text-grey-7 text-caption q-pa-lg">
              No fields yet. Click "Add Field" to define your first extraction pattern.
            </div>

            <div v-for="(field, idx) in tmpl.fields" :key="field._key" class="field-block q-mb-md">
              <!-- Row 1: type + label + delete -->
              <div class="row items-center q-gutter-sm q-mb-xs">
                <q-select v-model="field.field_name" :options="FIELD_OPTIONS"
                  emit-value map-options outlined dark dense label="Field Type"
                  style="min-width:160px; flex:0 0 auto" />
                <q-input v-if="field.field_name === 'custom'" v-model="field.custom_label"
                  outlined dark dense placeholder="Custom label..." style="width:130px; flex:0 0 auto" />
                <q-space />
                <q-btn flat round dense size="xs" icon="delete" color="grey-6"
                  @click="removeField(idx)" />
              </div>

              <!-- Row 2: pattern input -->
              <q-input v-model="field.regex_pattern" type="textarea" outlined dark dense
                label="Regex Pattern" :rows="2" class="q-mb-xs"
                input-style="font-family: monospace; font-size: 0.78rem;" />

              <!-- Row 3: options + test -->
              <div class="row items-center q-gutter-sm">
                <q-input v-model.number="field.capture_group" type="number" outlined dark dense
                  label="Capture group" min="0" style="width:120px; flex:0 0 auto" />
                <q-toggle v-model="field.case_insensitive" label="Case insensitive"
                  dense color="primary" class="text-grey-4 text-caption" />
                <q-space />
                <q-btn unelevated size="sm" color="dark" icon="search" label="Test"
                  :loading="field._testing" :disable="!field.regex_pattern || !tmpl.sample_text"
                  @click="testField(field)" />
              </div>

              <!-- Matches -->
              <div v-if="field._tested" class="q-mt-xs">
                <div v-if="field._error" class="text-negative text-caption">
                  <q-icon name="error" size="12px" /> {{ field._error }}
                </div>
                <div v-else-if="!field._matches.length" class="text-grey-7 text-caption">
                  No matches in sample text
                </div>
                <div v-else class="row items-center q-gutter-xs q-mt-xs">
                  <q-chip v-for="(m, mi) in field._matches.slice(0, 8)" :key="mi"
                    dense color="primary" text-color="white" size="sm">{{ m.value }}</q-chip>
                  <span v-if="field._matches.length > 8" class="text-caption text-grey-6">
                    +{{ field._matches.length - 8 }} more
                  </span>
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>

        <!-- Apply section (shown after first save) -->
        <q-card v-if="savedId" class="vs-card q-mt-md">
          <q-card-section class="q-pb-sm">
            <div class="text-subtitle2 text-grey-4">Test Against a Report</div>
            <div class="text-caption text-grey-7 q-mt-xs">
              Select an uploaded report to run this template against its extracted text.
            </div>
          </q-card-section>
          <q-card-section class="q-pt-none">
            <div class="row q-gutter-sm items-end">
              <q-select v-model="applyReportId" :options="reportOptions"
                option-value="id" option-label="label" emit-value map-options
                outlined dark dense label="Select Report" class="col" />
              <q-btn unelevated color="primary" label="Extract"
                :loading="applying" :disable="!applyReportId"
                @click="applyTemplate" />
            </div>
            <div v-if="applyResults" class="q-mt-md">
              <div v-for="(val, key) in applyResults" :key="key"
                class="row items-baseline q-mb-xs apply-result-row">
                <div class="apply-result-label text-caption text-grey-5">{{ key }}</div>
                <div class="text-grey-3 text-body2" :class="val ? '' : 'text-grey-7 text-italic'">
                  {{ val || 'no match' }}
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Load from report dialog -->
    <q-dialog v-model="showLoadDialog">
      <q-card class="vs-card" style="min-width:380px">
        <q-card-section>
          <div class="text-subtitle1 text-white">Load Text from Report</div>
          <div class="text-caption text-grey-6 q-mt-xs">
            The raw extracted text from the selected report will populate the sample text area.
          </div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-select v-model="loadReportId" :options="reportOptions"
            option-value="id" option-label="label" emit-value map-options
            outlined dark dense label="Select Report" />
        </q-card-section>
        <q-card-actions align="right" class="q-px-md q-pb-md">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn unelevated color="primary" label="Load Text"
            :disable="!loadReportId" @click="loadFromReport" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'

const route = useRoute()
const router = useRouter()
const $q = useQuasar()

const FIELD_OPTIONS = [
  { label: 'Full Name',       value: 'full_name' },
  { label: 'SSN / Tax ID',    value: 'ssn' },
  { label: 'Date of Birth',   value: 'date_of_birth' },
  { label: 'Address',         value: 'address' },
  { label: 'Phone',           value: 'phone' },
  { label: 'Email',           value: 'email' },
  { label: 'Employer',        value: 'employer' },
  { label: 'Account Number',  value: 'account_number' },
  { label: 'Custom Field',    value: 'custom' },
]

const isNew = computed(() => !route.params.id || route.params.id === 'new')
const savedId = ref(isNew.value ? null : route.params.id)

const saving = ref(false)
const applying = ref(false)
const extracting = ref(false)
const showLoadDialog = ref(false)
const keywordInput = ref('')
const applyReportId = ref(null)
const loadReportId = ref(null)
const applyResults = ref(null)
const reportOptions = ref([])

const tmpl = ref({
  name: '',
  description: '',
  keywords: [],
  sample_text: '',
  fields: [],
})

let _keyCounter = 0

function newField(overrides = {}) {
  return {
    _key: ++_keyCounter,
    _tested: false,
    _testing: false,
    _matches: [],
    _error: null,
    field_name: 'full_name',
    custom_label: '',
    regex_pattern: '',
    capture_group: 1,
    case_insensitive: true,
    ...overrides,
  }
}

function addField() {
  tmpl.value.fields.push(newField())
}

function removeField(idx) {
  tmpl.value.fields.splice(idx, 1)
}

function addKeyword() {
  const kw = keywordInput.value.trim()
  if (kw && !tmpl.value.keywords.includes(kw)) {
    tmpl.value.keywords.push(kw)
  }
  keywordInput.value = ''
}

function removeKeyword(kw) {
  tmpl.value.keywords = tmpl.value.keywords.filter(k => k !== kw)
}

async function testField(field) {
  field._testing = true
  field._error = null
  field._matches = []
  try {
    const res = await api.post('/doctemplates/preview/', {
      text: tmpl.value.sample_text,
      pattern: field.regex_pattern,
      capture_group: field.capture_group,
      case_insensitive: field.case_insensitive,
    })
    if (res.data.error) {
      field._error = res.data.error
    } else {
      field._matches = res.data.matches || []
    }
  } catch {
    field._error = 'Error testing pattern'
  } finally {
    field._testing = false
    field._tested = true
  }
}

async function saveTemplate() {
  if (!tmpl.value.name.trim()) {
    $q.notify({ type: 'warning', message: 'Template name is required' })
    return
  }
  saving.value = true
  try {
    const payload = {
      name: tmpl.value.name,
      description: tmpl.value.description,
      keywords: tmpl.value.keywords,
      sample_text: tmpl.value.sample_text,
      fields: tmpl.value.fields.map((f, i) => ({
        ...(f.id ? { id: f.id } : {}),
        field_name: f.field_name,
        custom_label: f.custom_label,
        regex_pattern: f.regex_pattern,
        capture_group: f.capture_group || 1,
        case_insensitive: f.case_insensitive,
        order: i,
      })),
    }

    let res
    if (savedId.value) {
      res = await api.put(`/doctemplates/${savedId.value}/`, payload)
    } else {
      res = await api.post('/doctemplates/', payload)
      savedId.value = res.data.id
      router.replace({ name: 'template-builder', params: { id: savedId.value } })
    }

    // Sync saved field IDs back into local state
    const savedFields = res.data.fields || []
    tmpl.value.fields = tmpl.value.fields.map((f, i) => ({
      ...f,
      id: savedFields[i]?.id ?? f.id,
    }))

    $q.notify({ type: 'positive', message: 'Template saved' })
  } catch {
    $q.notify({ type: 'negative', message: 'Save failed' })
  } finally {
    saving.value = false
  }
}

async function onPdfUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return
  event.target.value = ''
  extracting.value = true
  try {
    const form = new FormData()
    form.append('file', file)
    const res = await api.post('/doctemplates/extract-text/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    tmpl.value.sample_text = res.data.text || ''
    if (!tmpl.value.sample_text) {
      $q.notify({ type: 'warning', message: 'No text could be extracted from this PDF' })
    } else {
      $q.notify({ type: 'positive', message: `Extracted text from ${file.name} (${res.data.page_count} page${res.data.page_count !== 1 ? 's' : ''})` })
    }
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to extract text from PDF' })
  } finally {
    extracting.value = false
  }
}

async function loadFromReport() {
  if (!loadReportId.value) return
  try {
    const res = await api.get(`/reports/${loadReportId.value}/`)
    tmpl.value.sample_text = res.data.raw_text || ''
    if (!tmpl.value.sample_text) {
      $q.notify({ type: 'warning', message: 'Report has no extracted text. Parse it first.' })
    } else {
      $q.notify({ type: 'positive', message: 'Text loaded' })
    }
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to load report text' })
  }
}

async function applyTemplate() {
  if (!applyReportId.value || !savedId.value) return
  applying.value = true
  applyResults.value = null
  try {
    const res = await api.post(`/doctemplates/${savedId.value}/apply/`, {
      report_id: applyReportId.value,
    })
    applyResults.value = res.data.extracted
  } catch {
    $q.notify({ type: 'negative', message: 'Apply failed' })
  } finally {
    applying.value = false
  }
}

async function loadTemplate() {
  try {
    const res = await api.get(`/doctemplates/${savedId.value}/`)
    const data = res.data
    tmpl.value = {
      name: data.name,
      description: data.description,
      keywords: data.keywords || [],
      sample_text: data.sample_text || '',
      fields: (data.fields || []).map(f => newField(f)),
    }
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to load template' })
  }
}

async function loadReports() {
  try {
    const res = await api.get('/reports/', { params: { page_size: 200 } })
    reportOptions.value = (res.data.results ?? res.data).map(r => ({
      id: r.id,
      label: r.original_filename || r.id,
    }))
  } catch { /* non-fatal */ }
}

onMounted(() => {
  loadReports()
  if (!isNew.value) loadTemplate()
})
</script>

<style scoped>
.full-height-card {
  height: 100%;
}

.field-block {
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.02);
}

.keyword-wrap {
  flex-wrap: wrap;
}

.apply-result-row {
  gap: 12px;
}

.apply-result-label {
  min-width: 130px;
  flex-shrink: 0;
}

code {
  background: rgba(255, 255, 255, 0.07);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 0.75rem;
}
</style>
