<template>
  <q-page class="q-pa-lg">
    <div class="row items-center q-mb-xs">
      <div class="text-h5 text-weight-bold text-white">Document Templates</div>
      <q-space />
      <q-btn unelevated color="primary" icon="add" label="New Template"
        :to="{ name: 'template-builder', params: { id: 'new' } }" />
    </div>
    <div class="text-caption text-grey-6 q-mb-xl">
      Define regex patterns to extract fields from unknown document types. Upload a sample, tag the fields, and reuse the template on future uploads.
    </div>

    <div v-if="loading" class="text-center q-pa-xl">
      <q-spinner size="40px" color="primary" />
    </div>

    <div v-else-if="!templates.length" class="text-center q-pa-xl">
      <q-icon name="description" size="64px" color="grey-8" />
      <div class="text-grey-6 q-mt-md">No templates yet.</div>
      <div class="text-grey-7 text-caption q-mt-xs">Create one to start defining extraction patterns for a new document type.</div>
      <q-btn unelevated color="primary" icon="add" label="Create First Template" class="q-mt-lg"
        :to="{ name: 'template-builder', params: { id: 'new' } }" />
    </div>

    <div v-else class="row q-gutter-md">
      <q-card v-for="t in templates" :key="t.id" class="vs-card template-card">
        <q-card-section>
          <div class="text-subtitle1 text-white text-weight-medium">{{ t.name }}</div>
          <div v-if="t.description" class="text-caption text-grey-5 q-mt-xs ellipsis-2-lines">{{ t.description }}</div>
          <div v-if="t.keywords?.length" class="row items-center q-mt-sm q-gutter-xs">
            <q-chip v-for="kw in t.keywords" :key="kw" dense size="xs" color="dark" text-color="grey-4">{{ kw }}</q-chip>
          </div>
        </q-card-section>
        <q-separator dark />
        <q-card-section class="q-py-xs">
          <div class="text-caption text-grey-6">
            {{ t.fields?.length || 0 }} field pattern{{ t.fields?.length !== 1 ? 's' : '' }}
          </div>
        </q-card-section>
        <q-card-actions align="right" class="q-pt-none">
          <q-btn flat size="sm" icon="edit" label="Edit"
            :to="{ name: 'template-builder', params: { id: t.id } }" />
          <q-btn flat size="sm" icon="delete" color="negative" @click="confirmDelete(t)" />
        </q-card-actions>
      </q-card>
    </div>

    <q-dialog v-model="deleteDialog.show" persistent>
      <q-card class="vs-card" style="min-width:320px">
        <q-card-section>
          <div class="text-h6 text-white">Delete Template?</div>
          <div class="text-body2 text-grey-5 q-mt-sm">
            "{{ deleteDialog.template?.name }}" and all its field patterns will be permanently removed.
          </div>
        </q-card-section>
        <q-card-actions align="right" class="q-px-md q-pb-md">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn unelevated color="negative" label="Delete"
            :loading="deleteDialog.loading" @click="deleteTemplate" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const loading = ref(false)
const templates = ref([])
const deleteDialog = ref({ show: false, template: null, loading: false })

async function load() {
  loading.value = true
  try {
    const res = await api.get('/doctemplates/')
    templates.value = res.data.results ?? res.data
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to load templates' })
  } finally {
    loading.value = false
  }
}

function confirmDelete(t) {
  deleteDialog.value = { show: true, template: t, loading: false }
}

async function deleteTemplate() {
  deleteDialog.value.loading = true
  try {
    await api.delete(`/doctemplates/${deleteDialog.value.template.id}/`)
    templates.value = templates.value.filter(t => t.id !== deleteDialog.value.template.id)
    deleteDialog.value.show = false
    $q.notify({ type: 'positive', message: 'Template deleted' })
  } catch {
    $q.notify({ type: 'negative', message: 'Delete failed' })
  } finally {
    deleteDialog.value.loading = false
  }
}

onMounted(load)
</script>

<style scoped>
.template-card {
  width: 280px;
  transition: transform 0.12s ease;
}
.template-card:hover {
  transform: translateY(-2px);
}
</style>
