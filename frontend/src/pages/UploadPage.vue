<template>
  <q-page class="q-pa-lg">
    <div class="text-h5 text-weight-bold text-white q-mb-xs">Upload Report</div>
    <div class="text-caption text-grey-6 q-mb-xl">Upload a single PDF or a ZIP of PDFs for batch processing</div>

    <div class="row q-gutter-lg">
      <div class="col-xs-12 col-md-6">
        <q-card class="vs-card">
          <q-card-section>
            <div class="text-subtitle1 text-weight-medium text-white q-mb-md">File</div>

            <!-- Drop zone -->
            <div
              class="vs-dropzone"
              :class="{ 'vs-dropzone--active': dragging }"
              @dragover.prevent="dragging = true"
              @dragleave="dragging = false"
              @drop.prevent="onDrop"
              @click="$refs.fileInput.click()"
            >
              <q-icon
                :name="file ? 'check_circle' : 'cloud_upload'"
                :color="file ? 'positive' : 'grey-6'"
                size="48px"
              />
              <div class="q-mt-sm text-grey-4" style="font-size:15px">
                {{ file ? file.name : 'Drop PDF or ZIP here, or click to browse' }}
              </div>
              <div class="text-caption text-grey-6 q-mt-xs">
                Supported: .pdf, .zip (multiple PDFs)
              </div>
            </div>
            <input ref="fileInput" type="file" accept=".pdf,.zip" class="hidden" @change="onFileSelect" />

            <div class="q-mt-md">
              <q-select
                v-model="selectedCase"
                :options="caseOptions"
                option-label="name"
                option-value="id"
                label="Assign to Case (optional)"
                dark
                filled
                clearable
                emit-value
                map-options
                class="q-mb-sm"
              />
              <q-toggle v-model="autoParse" label="Auto-parse after upload" color="primary" dark />
            </div>
          </q-card-section>

          <q-card-actions class="q-pa-md q-pt-none">
            <q-btn
              unelevated
              color="primary"
              icon="upload"
              label="Upload"
              :loading="uploading"
              :disable="!file"
              class="full-width"
              @click="upload"
            />
          </q-card-actions>
        </q-card>
      </div>

      <!-- Results -->
      <div v-if="uploaded.length" class="col">
        <div class="text-subtitle1 text-weight-medium text-white q-mb-md">Uploaded</div>
        <q-card
          v-for="r in uploaded"
          :key="r.id"
          class="vs-card q-mb-sm"
        >
          <q-card-section horizontal class="items-center">
            <q-card-section class="col">
              <div class="text-white text-weight-medium">{{ r.original_filename }}</div>
              <div class="text-caption text-grey-6">{{ r.bureau_display }}</div>
            </q-card-section>
            <q-card-section class="row items-center">
              <q-badge :color="statusColor(r.status)" :label="r.status_display" class="q-mr-sm" />
              <q-btn flat round dense icon="chevron_right" :to="{ name: 'report-detail', params: { id: r.id } }" />
            </q-card-section>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { api } from 'boot/axios'

const $q = useQuasar()
const file = ref(null)
const dragging = ref(false)
const uploading = ref(false)
const selectedCase = ref(null)
const autoParse = ref(true)
const uploaded = ref([])
const caseOptions = ref([])

const statusColor = (s) =>
  ({ parsed: 'positive', failed: 'negative', parsing: 'info', pending: 'grey' }[s] || 'grey')

function onDrop(e) {
  dragging.value = false
  const f = e.dataTransfer.files[0]
  if (f) file.value = f
}

function onFileSelect(e) {
  file.value = e.target.files[0] || null
}

async function upload() {
  if (!file.value) return
  uploading.value = true
  const form = new FormData()
  form.append('file', file.value)
  form.append('auto_parse', autoParse.value)
  if (selectedCase.value) form.append('case', selectedCase.value)

  try {
    const res = await api.post('/reports/upload/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    uploaded.value = Array.isArray(res.data) ? res.data : [res.data]
    file.value = null
    $q.notify({ type: 'positive', message: `${uploaded.value.length} report(s) uploaded.` })
  } catch (e) {
    $q.notify({ type: 'negative', message: e.response?.data?.detail || 'Upload failed.' })
  } finally {
    uploading.value = false
  }
}

onMounted(async () => {
  try {
    const res = await api.get('/cases/')
    caseOptions.value = res.data.results || res.data
  } catch { /* */ }
})
</script>

<style scoped>
.vs-dropzone {
  border: 2px dashed #334155;
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}
.vs-dropzone:hover,
.vs-dropzone--active {
  border-color: #22d3ee;
  background: rgba(34, 211, 238, 0.05);
}
.hidden { display: none; }
</style>
