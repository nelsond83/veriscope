<template>
  <q-page class="q-pa-lg">
    <div class="row items-center q-mb-xs">
      <div class="text-h5 text-weight-bold text-white">Upload Reports</div>
      <q-space />
      <q-btn flat dense size="sm" icon="delete_sweep" label="Clear All Data" color="grey-6"
        @click="showClearConfirm = true" />
    </div>
    <div class="text-caption text-grey-6 q-mb-xl">
      Drop multiple PDFs or a ZIP. Reports are automatically parsed and matched to identities by SSN or name.
    </div>

    <!-- Clear all confirmation dialog -->
    <q-dialog v-model="showClearConfirm" persistent>
      <q-card class="vs-card" style="min-width:360px">
        <q-card-section>
          <div class="text-h6 text-white">Clear All Data?</div>
          <div class="text-body2 text-grey-5 q-mt-sm">
            This will permanently delete all identities, reports, and comparison results.
            Use this to reset the database for a fresh test run.
          </div>
        </q-card-section>
        <q-card-actions align="right" class="q-px-md q-pb-md">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn unelevated color="negative" label="Clear Everything" :loading="clearing" @click="clearAll" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <div class="row q-gutter-lg">
      <div class="col-xs-12 col-md-6">
        <q-card class="vs-card">
          <q-card-section>
            <div
              class="vs-dropzone"
              :class="{ 'vs-dropzone--active': dragging }"
              @dragover.prevent="dragging = true"
              @dragleave="dragging = false"
              @drop.prevent="onDrop"
              @click="$refs.fileInput.click()"
            >
              <q-icon name="cloud_upload" color="grey-6" size="48px" />
              <div class="q-mt-sm text-grey-4" style="font-size:15px">
                Drop PDFs or a ZIP here, or click to browse
              </div>
              <div class="text-caption text-grey-6 q-mt-xs">Multiple PDFs supported</div>
            </div>
            <input ref="fileInput" type="file" accept=".pdf,.zip" multiple class="hidden" @change="onFileSelect" />

            <!-- Queued files list -->
            <div v-if="queue.length" class="q-mt-md">
              <div class="text-caption text-grey-5 q-mb-xs">{{ queue.length }} file{{ queue.length !== 1 ? 's' : '' }} queued</div>
              <q-list dense>
                <q-item v-for="(item, i) in queue" :key="i" dense class="q-px-none">
                  <q-item-section avatar style="min-width:28px">
                    <q-icon v-if="item.status === 'done'" name="check_circle" color="positive" size="16px" />
                    <q-icon v-else-if="item.status === 'error'" name="error" color="negative" size="16px" />
                    <q-spinner v-else-if="item.status === 'uploading'" color="primary" size="16px" />
                    <q-icon v-else name="description" color="grey-6" size="16px" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label class="text-caption text-grey-4">{{ item.file.name }}</q-item-label>
                  </q-item-section>
                  <q-item-section side v-if="item.status === 'pending'">
                    <q-btn flat round dense icon="close" size="xs" color="grey-6" @click.stop="removeFromQueue(i)" />
                  </q-item-section>
                </q-item>
              </q-list>
            </div>

            <q-toggle v-model="autoParse" label="Auto-parse and match after upload" color="primary" dark class="q-mt-md" />
          </q-card-section>
          <q-card-actions class="q-pa-md q-pt-none">
            <q-btn unelevated color="primary" icon="upload" label="Upload All"
              :loading="uploading" :disable="pendingCount === 0" class="full-width" @click="uploadAll" />
          </q-card-actions>
        </q-card>
      </div>

      <!-- Results -->
      <div v-if="uploaded.length" class="col">
        <div class="row items-center q-mb-md">
          <div class="text-subtitle1 text-weight-medium text-white">
            Results ({{ uploaded.length }})
          </div>
          <q-space />
          <div class="text-caption text-grey-6">
            {{ uploaded.filter(r => r.identity).length }} matched
            · {{ uploaded.filter(r => !r.identity).length }} unmatched
          </div>
        </div>
        <q-card v-for="r in uploaded" :key="r.id" class="vs-card q-mb-sm">
          <q-card-section horizontal class="items-center">
            <q-card-section class="col">
              <div class="row items-center q-gutter-xs q-mb-xs">
                <BureauBadge :bureau="r.bureau" size="sm" />
              </div>
              <div class="text-white text-weight-medium text-caption">{{ r.original_filename }}</div>
              <div v-if="r.identity" class="text-caption text-positive q-mt-xs">
                <q-icon name="link" size="xs" /> Matched to identity
              </div>
              <div v-else class="text-caption text-grey-6 q-mt-xs">
                <q-icon name="link_off" size="xs" /> No match —
                <router-link :to="{ name: 'unmatched' }" class="text-primary" style="text-decoration:none">assign via Unmatched Reports</router-link>
              </div>
            </q-card-section>
            <q-card-section class="row items-center q-gutter-sm">
              <q-badge :color="statusColor(r.status)" :label="r.status_display" />
              <q-btn flat round dense icon="chevron_right" :to="{ name: 'report-detail', params: { id: r.id } }" />
            </q-card-section>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useQuasar } from 'quasar'
import { api } from 'boot/axios'
import BureauBadge from 'components/BureauBadge.vue'

const $q = useQuasar()
const dragging = ref(false)
const uploading = ref(false)
const clearing = ref(false)
const showClearConfirm = ref(false)
const autoParse = ref(true)
const uploaded = ref([])

// Each item: { file, status: 'pending' | 'uploading' | 'done' | 'error' }
const queue = ref([])
const pendingCount = computed(() => queue.value.filter(i => i.status === 'pending').length)

const statusColor = (s) =>
  ({ parsed: 'positive', failed: 'negative', parsing: 'info', pending: 'grey' }[s] || 'grey')

function addFiles(fileList) {
  for (const f of fileList) {
    if (f.name.match(/\.(pdf|zip)$/i)) {
      queue.value.push({ file: f, status: 'pending' })
    }
  }
}

function onDrop(e) {
  dragging.value = false
  addFiles(e.dataTransfer.files)
}

function onFileSelect(e) {
  addFiles(e.target.files)
  e.target.value = ''
}

function removeFromQueue(i) {
  queue.value.splice(i, 1)
}

async function clearAll() {
  clearing.value = true
  try {
    await api.post('/identities/reset-all/')
    uploaded.value = []
    queue.value = []
    showClearConfirm.value = false
    $q.notify({ type: 'positive', message: 'All data cleared.' })
  } catch {
    $q.notify({ type: 'negative', message: 'Clear failed.' })
  } finally {
    clearing.value = false
  }
}

async function uploadAll() {
  uploading.value = true
  const pending = queue.value.filter(i => i.status === 'pending')

  for (const item of pending) {
    item.status = 'uploading'
    const form = new FormData()
    form.append('file', item.file)
    form.append('auto_parse', autoParse.value)
    try {
      const res = await api.post('/reports/upload/', form)
      const results = Array.isArray(res.data) ? res.data : [res.data]
      uploaded.value.push(...results)
      item.status = 'done'
    } catch {
      item.status = 'error'
    }
  }

  uploading.value = false
  const matched = uploaded.value.filter(r => r.identity).length
  const total = pending.filter(i => i.status === 'done').length
  const errors = pending.filter(i => i.status === 'error').length
  $q.notify({
    type: errors ? 'warning' : 'positive',
    message: `${total} uploaded, ${matched} matched to identities${errors ? `, ${errors} failed` : ''}.`,
  })
}
</script>

<style scoped>
.vs-dropzone {
  border: 2px dashed rgba(245, 245, 247, 0.15);
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}
.vs-dropzone:hover,
.vs-dropzone--active {
  border-color: #C8102E;
  background: rgba(200, 16, 46, 0.06);
}
.hidden { display: none; }
</style>
