<template>
  <q-page class="q-pa-lg">
    <div class="text-h5 text-weight-bold text-white q-mb-xs">Dashboard</div>
    <div class="text-caption text-grey-6 q-mb-lg">Overview of your due diligence activity</div>

    <!-- Stat cards -->
    <div class="row q-gutter-md q-mb-xl">
      <div v-for="stat in stats" :key="stat.label" class="col-xs-12 col-sm-6 col-md-3">
        <q-card class="vs-card">
          <q-card-section>
            <div class="row items-center no-wrap">
              <div class="col">
                <div class="text-caption text-grey-5 text-uppercase q-mb-xs" style="letter-spacing:1px">
                  {{ stat.label }}
                </div>
                <div class="text-h4 text-weight-bold" :style="{ color: stat.color }">
                  {{ stat.value }}
                </div>
              </div>
              <q-icon :name="stat.icon" size="36px" :color="stat.iconColor" class="q-ml-md" />
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Recent reports -->
    <div class="row q-gutter-lg">
      <div class="col-xs-12 col-md-7">
        <div class="text-subtitle1 text-weight-medium text-white q-mb-md">Recent Reports</div>
        <q-card class="vs-card">
          <q-list separator>
            <q-item v-if="!recentReports.length">
              <q-item-section class="text-grey-6 text-center q-py-lg">
                No reports uploaded yet
              </q-item-section>
            </q-item>
            <q-item
              v-for="r in recentReports"
              :key="r.id"
              :to="{ name: 'report-detail', params: { id: r.id } }"
              clickable
              v-ripple
            >
              <q-item-section avatar>
                <q-icon name="description" :color="statusColor(r.status)" />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ r.original_filename }}</q-item-label>
                <q-item-label caption>{{ r.bureau_display }} · {{ formatDate(r.uploaded_at) }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-badge :color="statusColor(r.status)" :label="r.status_display" />
              </q-item-section>
            </q-item>
          </q-list>
        </q-card>
      </div>

      <div class="col">
        <div class="text-subtitle1 text-weight-medium text-white q-mb-md">Open Cases</div>
        <q-card class="vs-card">
          <q-list separator>
            <q-item v-if="!recentCases.length">
              <q-item-section class="text-grey-6 text-center q-py-lg">
                No cases open
              </q-item-section>
            </q-item>
            <q-item
              v-for="c in recentCases"
              :key="c.id"
              :to="{ name: 'case-detail', params: { id: c.id } }"
              clickable
              v-ripple
            >
              <q-item-section>
                <q-item-label>{{ c.name }}</q-item-label>
                <q-item-label caption>{{ c.report_count }} report{{ c.report_count !== 1 ? 's' : '' }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from 'boot/axios'

const recentReports = ref([])
const recentCases = ref([])

const stats = ref([
  { label: 'Total Cases', value: 0, icon: 'folder_open', color: '#22d3ee', iconColor: 'info' },
  { label: 'Reports Parsed', value: 0, icon: 'description', color: '#10b981', iconColor: 'positive' },
  { label: 'Mismatches', value: 0, icon: 'warning', color: '#f59e0b', iconColor: 'warning' },
  { label: 'Pending', value: 0, icon: 'schedule', color: '#94a3b8', iconColor: 'grey' },
])

const statusColor = (s) =>
  ({ parsed: 'positive', failed: 'negative', parsing: 'info', pending: 'grey' }[s] || 'grey')

const formatDate = (d) => d ? new Date(d).toLocaleDateString() : ''

onMounted(async () => {
  try {
    const [casesRes, reportsRes] = await Promise.all([
      api.get('/cases/'),
      api.get('/reports/'),
    ])
    recentCases.value = (casesRes.data.results || casesRes.data).slice(0, 5)
    recentReports.value = (reportsRes.data.results || reportsRes.data).slice(0, 8)

    stats.value[0].value = casesRes.data.count ?? recentCases.value.length
    stats.value[1].value = recentReports.value.filter(r => r.status === 'parsed').length
    stats.value[3].value = recentReports.value.filter(r => r.status === 'pending').length
  } catch (e) {
    console.error(e)
  }
})
</script>
