<template>
  <q-page class="q-pa-lg">
    <div class="text-h5 text-weight-bold text-white q-mb-xs">Dashboard</div>
    <div class="text-caption text-grey-6 q-mb-lg">Overview of your due diligence activity</div>

    <!-- Stat cards -->
    <div class="row q-gutter-md q-mb-xl">
      <template v-if="loading">
        <div v-for="n in 3" :key="n" class="col-xs-12 col-sm-6 col-md-3">
          <q-card class="vs-card stat-card">
            <q-card-section>
              <div class="row items-center no-wrap">
                <div class="col">
                  <q-skeleton type="text" width="70px" class="q-mb-sm" />
                  <q-skeleton type="text" width="50px" height="32px" />
                </div>
                <q-skeleton type="circle" size="36px" class="q-ml-md" />
              </div>
            </q-card-section>
          </q-card>
        </div>
      </template>
      <template v-else>
        <div v-for="stat in stats" :key="stat.label" class="col-xs-12 col-sm-6 col-md-3">
          <q-card class="vs-card stat-card" :class="{ 'stat-card--clickable': stat.to }"
            @click="stat.to ? router.push(stat.to) : null">
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
                <q-icon :name="stat.icon" size="36px" :style="{ color: stat.color }" class="q-ml-md" />
              </div>
            </q-card-section>
          </q-card>
        </div>
      </template>
    </div>

    <div class="row q-gutter-lg">
      <!-- Recent reports -->
      <div class="col-xs-12 col-md-7">
        <div class="text-subtitle1 text-weight-medium text-white q-mb-md">Recent Reports</div>
        <q-card class="vs-card">
          <q-list v-if="loading" separator>
            <q-item v-for="n in 5" :key="n">
              <q-item-section avatar>
                <q-skeleton type="circle" size="28px" />
              </q-item-section>
              <q-item-section>
                <q-skeleton type="text" width="55%" class="q-mb-xs" />
                <q-skeleton type="text" width="35%" />
              </q-item-section>
              <q-item-section side>
                <q-skeleton type="QBadge" width="60px" />
              </q-item-section>
            </q-item>
          </q-list>
          <q-list v-else separator>
            <q-item v-if="!recentReports.length">
              <q-item-section class="text-grey-6 text-center q-py-lg">No reports uploaded yet</q-item-section>
            </q-item>
            <q-item v-for="r in recentReports" :key="r.id"
              :to="{ name: 'report-detail', params: { id: r.id } }" clickable v-ripple>
              <q-item-section avatar>
                <BureauBadge :bureau="r.bureau" :show-name="false" size="sm" />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ r.original_filename }}</q-item-label>
                <q-item-label caption>{{ formatDate(r.uploaded_at) }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-badge :color="statusColor(r.status)" :label="r.status_display" />
              </q-item-section>
            </q-item>
          </q-list>
        </q-card>
      </div>

      <!-- Flagged identities -->
      <div class="col">
        <div class="text-subtitle1 text-weight-medium text-white q-mb-md">Flagged Identities</div>
        <q-card class="vs-card">
          <q-list v-if="loading" separator>
            <q-item v-for="n in 3" :key="n">
              <q-item-section>
                <q-skeleton type="text" width="65%" />
              </q-item-section>
              <q-item-section side>
                <q-skeleton type="QBadge" width="55px" />
              </q-item-section>
            </q-item>
          </q-list>
          <q-list v-else separator>
            <q-item v-if="!flaggedIdentities.length">
              <q-item-section class="text-grey-6 text-center q-py-lg">No flags</q-item-section>
            </q-item>
            <q-item v-for="i in flaggedIdentities" :key="i.id"
              :to="{ name: 'identity-detail', params: { id: i.id } }" clickable v-ripple>
              <q-item-section>
                <q-item-label>{{ i.full_name }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-badge color="negative" label="Flagged" />
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
import { useRouter } from 'vue-router'
import { api } from 'boot/axios'
import BureauBadge from 'components/BureauBadge.vue'

const router = useRouter()
const loading = ref(true)
const recentReports = ref([])
const flaggedIdentities = ref([])

const stats = ref([
  { label: 'Identities', value: 0, icon: 'people',  color: '#FFB81C', to: { name: 'identities' } },
  { label: 'Flagged',    value: 0, icon: 'flag',     color: '#C8102E', to: { name: 'identities', query: { dd_status: 'flagged' } } },
  { label: 'Unmatched',  value: 0, icon: 'link_off', color: '#94a3b8', to: { name: 'unmatched' } },
])

const statusColor = (s) => ({ parsed: 'positive', failed: 'negative', parsing: 'info', pending: 'grey' }[s] || 'grey')
const formatDate = (d) => d ? new Date(d).toLocaleDateString() : ''

onMounted(async () => {
  loading.value = true
  try {
    const [identitiesRes, reportsRes, unmatchedRes] = await Promise.all([
      api.get('/identities/'),
      api.get('/reports/'),
      api.get('/reports/', { params: { unmatched: '1' } }),
    ])
    const allIdentities = identitiesRes.data.results || identitiesRes.data
    const allReports = reportsRes.data.results || reportsRes.data
    const unmatchedReports = unmatchedRes.data.results || unmatchedRes.data

    recentReports.value = allReports.slice(0, 8)
    flaggedIdentities.value = allIdentities.filter(i => i.dd_status === 'flagged').slice(0, 5)

    stats.value[0].value = identitiesRes.data.count ?? allIdentities.length
    stats.value[1].value = allIdentities.filter(i => i.dd_status === 'flagged').length
    stats.value[2].value = unmatchedReports.length
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.stat-card--clickable {
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.stat-card--clickable:hover {
  border-color: rgba(200, 16, 46, 0.4) !important;
  box-shadow: 0 2px 16px rgba(200, 16, 46, 0.15), 0 1px 0 rgba(255, 255, 255, 0.05) inset !important;
}
</style>
