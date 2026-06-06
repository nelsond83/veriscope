<template>
  <q-page class="q-pa-lg">
    <!-- Back nav -->
    <div class="row items-center q-mb-md">
      <q-btn flat round icon="arrow_back" :to="{ name: 'identities' }" class="q-mr-sm" />
      <span class="text-caption text-grey-6">Identities</span>
    </div>

    <!-- Identity reference card -->
    <q-card class="vs-card q-mb-xl" v-if="identity">
      <q-card-section>
        <div class="row items-start justify-between no-wrap q-mb-md">
          <div>
            <div class="text-h5 text-weight-bold text-white">{{ identity.full_name }}</div>
            <div class="text-caption q-mt-xs" style="color:rgba(245,245,247,0.45)">
              Reference identity record
            </div>
          </div>
          <div class="row items-center" style="gap:8px">
            <q-badge :color="ddColor(identity.dd_status)" :label="ddLabel(identity.dd_status)"
              style="padding:6px 14px; font-size:0.75rem" />
            <q-btn flat round icon="edit" size="sm" title="Edit" @click="openEdit" />
          </div>
        </div>

        <!-- Core fields row -->
        <div class="row q-col-gutter-md q-mb-md">
          <div class="col-xs-12 col-sm-3">
            <div class="ref-label">Full Name</div>
            <div class="ref-value">{{ identity.full_name }}</div>
          </div>
          <div class="col-xs-6 col-sm-2">
            <div class="ref-label">Gender</div>
            <div class="ref-value" style="text-transform:capitalize">{{ identity.gender || '—' }}</div>
          </div>
          <div class="col-xs-6 col-sm-3">
            <div class="ref-label">SSN</div>
            <div class="ref-value">{{ identity.ssn || '—' }}</div>
          </div>
          <div class="col-xs-6 col-sm-4">
            <div class="ref-label">Date of Birth</div>
            <div class="ref-value">{{ identity.date_of_birth || '—' }}</div>
          </div>
        </div>

        <!-- Name variations -->
        <template v-if="identity.name_variations?.length">
          <div class="ref-label q-mb-xs">Also Known As</div>
          <div class="row q-col-gutter-xs q-mb-md">
            <div v-for="v in identity.name_variations" :key="v.id" class="col-auto">
              <q-chip dense dark color="blue-grey-9" style="font-size:0.8rem">
                {{ v.name }}
                <span v-if="v.note" style="opacity:.55; font-size:0.7rem; margin-left:4px">({{ v.note }})</span>
              </q-chip>
            </div>
          </div>
        </template>

        <!-- Contact: phones then emails, stacked -->
        <template v-if="identity.phones?.length || identity.emails?.length">
          <div class="q-mb-md">
            <template v-if="identity.phones?.length">
              <div class="ref-label q-mb-xs">Phone Numbers</div>
              <div v-for="(p, i) in identity.phones" :key="p.id || i"
                class="row items-center q-mb-xs" style="gap:6px">
                <q-icon name="phone" size="13px" style="color:rgba(245,245,247,0.35)" />
                <span class="ref-value" style="font-size:0.85rem">{{ p.number }}</span>
                <span style="color:rgba(245,245,247,0.35); font-size:0.7rem; text-transform:capitalize">{{ p.phone_type }}</span>
              </div>
            </template>
            <template v-if="identity.emails?.length">
              <div class="ref-label q-mb-xs" :class="identity.phones?.length ? 'q-mt-sm' : ''">Email Addresses</div>
              <div v-for="(e, i) in identity.emails" :key="e.id || i"
                class="row items-center q-mb-xs" style="gap:6px">
                <q-icon name="email" size="13px" style="color:rgba(245,245,247,0.35)" />
                <span class="ref-value" style="font-size:0.85rem">{{ e.address }}</span>
                <span style="color:rgba(245,245,247,0.35); font-size:0.7rem; text-transform:capitalize">{{ e.email_type }}</span>
              </div>
            </template>
          </div>
        </template>

        <!-- Addresses: current prominent, prior as list -->
        <template v-if="identityCurrentAddr">
          <div class="ref-label q-mb-xs">Current Address</div>
          <div class="ref-current-addr q-mb-md">
            <div class="text-white" style="font-size:0.92rem; font-weight:500; line-height:1.5">
              {{ identityCurrentAddr.street }}
            </div>
            <div style="color:rgba(245,245,247,0.65); font-size:0.85rem">
              {{ [identityCurrentAddr.city, identityCurrentAddr.state, identityCurrentAddr.zip_code].filter(Boolean).join(', ') }}
            </div>
          </div>
        </template>

        <template v-if="identityPriorAddrs.length">
          <div class="ref-label q-mb-sm">Prior Addresses</div>
          <div class="ref-prior-list q-mb-md">
            <div v-for="(addr, i) in identityPriorAddrs" :key="addr.id || i" class="ref-prior-item">
              <span class="ref-prior-type">{{ addr.address_type === 'previous' ? 'Previous' : 'Other' }}</span>
              <span class="ref-prior-addr">
                {{ [addr.street, addr.city, addr.state, addr.zip_code].filter(Boolean).join(', ') }}
              </span>
            </div>
          </div>
        </template>

        <div v-if="!identityCurrentAddr && !identityPriorAddrs.length"
          class="ref-label q-mb-md" style="opacity:.5">
          No address on file
        </div>

        <!-- Reference Accounts -->
        <template v-if="identity.ref_accounts?.length">
          <div class="ref-label q-mb-sm q-mt-sm">Reference Accounts</div>
          <div class="ref-accounts-table q-mb-md">
            <div class="ref-accounts-header">
              <span>Creditor</span>
              <span>Type</span>
              <span>Account #</span>
              <span>Status</span>
            </div>
            <div v-for="(acct, i) in identity.ref_accounts" :key="acct.id || i" class="ref-accounts-row">
              <span class="ref-acct-name">{{ acct.creditor_name }}</span>
              <span class="ref-acct-cell">{{ acct.account_type || '—' }}</span>
              <span class="ref-acct-cell" style="font-family:monospace">{{ acct.account_number || '—' }}</span>
              <span class="ref-acct-cell">
                <q-badge dense :color="acctStatusColor(acct.status)" :label="acct.status || '—'"
                  style="font-size:0.62rem" />
              </span>
            </div>
          </div>
        </template>

        <!-- Notes -->
        <template v-if="identity.notes">
          <div class="ref-label q-mb-xs">Notes</div>
          <div style="color:rgba(245,245,247,0.65); font-size:0.85rem">{{ identity.notes }}</div>
        </template>
      </q-card-section>
    </q-card>

    <!-- DD Report Card — one card per bureau -->
    <div class="text-subtitle1 text-weight-medium text-white q-mb-md">DD Report Card</div>
    <div class="row q-col-gutter-md q-mb-xl">
      <div v-for="b in BUREAUS" :key="b" class="col-xs-12 col-md-4">
        <q-card class="vs-card column full-height">

          <!-- Card header -->
          <q-card-section class="row items-center no-wrap q-pb-sm" style="gap:8px">
            <BureauBadge :bureau="b" size="sm" />
            <q-space />
            <template v-if="reportFor(b)">
              <q-badge :color="statusColor(reportFor(b).status)"
                :label="reportFor(b).status_display" style="font-size:0.6rem" />
              <q-badge :color="bureauStatusColor(b)"
                :label="bureauStatusLabel(b)" style="font-size:0.6rem" />
            </template>
          </q-card-section>

          <q-separator dark />

          <!-- No report placeholder -->
          <q-card-section v-if="!reportFor(b)"
            class="col column items-center justify-center q-py-xl text-center">
            <q-icon name="description" size="28px" style="color:rgba(245,245,247,0.2)" />
            <div class="q-mt-sm" style="color:rgba(245,245,247,0.3); font-size:0.8rem">
              No report uploaded
            </div>
          </q-card-section>

          <!-- Fields -->
          <template v-else>
            <q-list dense class="col">
              <q-item v-for="field in FIELDS" :key="field.key" class="q-py-md">
                <q-item-section>
                  <div class="field-label q-mb-xs">{{ field.label }}</div>
                  <template v-if="cellResult(field.key, b)">
                    <div class="row items-center no-wrap" style="gap:5px">
                      <q-icon
                        :name="matchIcon(cellResult(field.key, b).match_status)"
                        :color="matchColor(cellResult(field.key, b).match_status)"
                        size="15px" />
                      <span class="field-value"
                        :style="{ color: matchTextColor(cellResult(field.key, b).match_status) }">
                        {{ cellResult(field.key, b).report_value || '—' }}
                      </span>
                    </div>
                  </template>
                  <span v-else class="field-value" style="color:rgba(245,245,247,0.3)">—</span>
                </q-item-section>
              </q-item>
            </q-list>

            <!-- Bureau addresses: check each against reference data -->
            <template v-if="reportFor(b)?.subject?.addresses?.length">
              <q-separator dark />
              <div class="q-pa-md">
                <div class="field-label q-mb-sm">Addresses</div>
                <div v-for="(addr, i) in reportFor(b).subject.addresses" :key="i"
                  class="bureau-addr-row" :class="i > 0 ? 'q-mt-sm' : ''">
                  <div class="row items-start no-wrap" style="gap:7px">
                    <q-icon
                      :name="addrInRef(addr) ? 'check_circle' : 'cancel'"
                      :color="addrInRef(addr) ? 'positive' : 'negative'"
                      size="14px" style="margin-top:2px; flex-shrink:0" />
                    <div>
                      <div class="row items-center no-wrap" style="gap:5px">
                        <span style="font-size:0.79rem; color:rgba(245,245,247,0.85); line-height:1.3">{{ addr.street }}</span>
                        <q-badge v-if="i === 0" dense label="Current" color="blue-grey-9"
                          style="font-size:0.52rem; padding:1px 5px" />
                      </div>
                      <div style="font-size:0.72rem; color:rgba(245,245,247,0.4); margin-top:1px">
                        {{ [addr.city, addr.state, addr.zip_code].filter(Boolean).join(', ') }}
                      </div>
                      <div v-if="!addrInRef(addr)"
                        style="font-size:0.65rem; color:#FF3B30; margin-top:2px; font-weight:600; letter-spacing:0.3px">
                        NOT IN REFERENCE DATA
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </template>

            <!-- Bureau accounts: check each against reference data -->
            <template v-if="reportFor(b)?.subject?.financial_accounts?.length">
              <q-separator dark />
              <div class="q-pa-md">
                <div class="field-label q-mb-sm">Accounts</div>
                <div v-for="(acct, i) in reportFor(b).subject.financial_accounts" :key="i"
                  class="bureau-acct-row" :class="i > 0 ? 'q-mt-xs' : ''">
                  <div class="row items-start no-wrap" style="gap:7px">
                    <q-icon
                      :name="acctInRef(acct) ? 'check_circle' : 'cancel'"
                      :color="acctInRef(acct) ? 'positive' : 'negative'"
                      size="14px" style="margin-top:2px; flex-shrink:0" />
                    <div>
                      <div class="row items-center" style="gap:5px; flex-wrap:wrap">
                        <span style="font-size:0.79rem; color:rgba(245,245,247,0.85); line-height:1.4">{{ acct.creditor_name }}</span>
                        <span v-if="acct.account_number" style="font-family:monospace; font-size:0.7rem; color:rgba(245,245,247,0.35)">{{ acct.account_number }}</span>
                      </div>
                      <div v-if="!acctInRef(acct)"
                        style="font-size:0.65rem; color:#FF3B30; margin-top:2px; font-weight:600; letter-spacing:0.3px">
                        NOT IN REFERENCE DATA
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </template>

        </q-card>
      </div>
    </div>

    <!-- DD Run Timeline -->
    <div class="row items-center q-mb-md">
      <div class="text-subtitle1 text-weight-medium text-white">DD History</div>
      <q-badge :label="reports.length + ' report' + (reports.length !== 1 ? 's' : '')"
        color="grey-8" class="q-ml-sm" />
      <q-space />
      <q-btn unelevated color="primary" icon="upload_file" label="New Run"
        :to="{ name: 'upload' }" />
    </div>

    <div v-if="!reports.length" class="text-grey-6 q-mb-xl q-pa-md">
      No reports linked yet. Upload PDFs and they'll auto-match here.
    </div>

    <div v-else class="timeline q-mb-xl">
      <div v-for="(batch, idx) in reportsByBatch" :key="batch.key" class="timeline-entry">
        <!-- Spine -->
        <div class="timeline-spine">
          <div class="timeline-dot" :class="idx === 0 ? 'timeline-dot--latest' : ''" />
          <div v-if="idx < reportsByBatch.length - 1" class="timeline-line" />
        </div>

        <!-- Content -->
        <div class="timeline-content q-mb-lg">
          <div class="row items-center q-mb-xs" style="gap:8px">
            <span class="text-weight-bold text-white" style="font-size:0.9rem">{{ batch.label }}</span>
            <q-badge v-if="idx === 0" label="Latest" color="primary" />
            <span class="text-caption text-grey-6">{{ batch.reports.length }} report{{ batch.reports.length !== 1 ? 's' : '' }}</span>
          </div>

          <q-card class="vs-card">
            <!-- Bureau summary row -->
            <div class="row q-pa-md" style="gap:12px; flex-wrap:wrap">
              <div v-for="b in BUREAUS" :key="b" class="row items-center" style="gap:6px">
                <BureauBadge :bureau="b" :show-name="true" size="sm" />
                <template v-if="batch.byBureau[b]">
                  <q-badge :color="statusColor(batch.byBureau[b].status)"
                    :label="batch.byBureau[b].status_display" style="font-size:0.65rem" />
                </template>
                <span v-else class="text-caption text-grey-7">—</span>
              </div>
            </div>

            <q-separator dark />

            <q-list separator dense>
              <q-item v-for="r in batch.reports" :key="r.id"
                :to="{ name: 'report-detail', params: { id: r.id }, query: { from: route.params.id } }" clickable v-ripple>
                <q-item-section avatar style="min-width:36px">
                  <BureauBadge :bureau="r.bureau" :show-name="false" size="sm" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-grey-3">{{ r.original_filename }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <div class="row items-center" style="gap:6px">
                    <q-chip v-if="r.match_confidence" dense size="xs" color="dark">
                      {{ confidenceLabel(r.match_confidence) }}
                    </q-chip>
                    <q-badge :color="statusColor(r.status)" :label="r.status_display" />
                  </div>
                </q-item-section>
              </q-item>
            </q-list>
          </q-card>
        </div>
      </div>
    </div>

    <!-- Unmatched reports (assign manually) -->
    <template v-if="unmatched.length">
      <div class="row items-center q-mb-md">
        <div class="text-subtitle1 text-weight-medium text-grey-5">Unmatched Reports</div>
        <q-badge :label="unmatched.length" color="grey-7" class="q-ml-sm" />
      </div>
      <q-card class="vs-card q-mb-xl">
        <q-list separator>
          <q-item v-for="r in unmatched" :key="r.id">
            <q-item-section avatar>
              <BureauBadge :bureau="r.bureau" :show-name="false" size="sm" />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ r.original_filename }}</q-item-label>
              <q-item-label caption>{{ r.subject?.full_name || 'Not parsed' }}</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-btn unelevated dense size="sm" color="secondary" label="Assign here"
                :loading="assigning === r.id" @click="assignReport(r.id)" />
            </q-item-section>
          </q-item>
        </q-list>
      </q-card>
    </template>

    <!-- Edit dialog -->
    <q-dialog v-model="showEdit" persistent>
      <q-card class="vs-card" style="min-width:480px; max-width:600px; max-height:90vh; overflow-y:auto">
        <q-card-section>
          <div class="text-h6 text-white">Edit Identity</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-input v-model="editForm.full_name" label="Full Name" dark filled class="q-mb-sm" />
          <div class="row q-gutter-sm q-mb-sm">
            <q-input v-model="editForm.ssn" label="SSN" dark filled class="col"
              mask="###-##-####" unmasked-value />
            <q-input v-model="editForm.date_of_birth" label="Date of Birth" dark filled class="col"
              mask="##/##/####" hint="MM/DD/YYYY" />
            <q-select v-model="editForm.gender" label="Gender" dark filled class="col"
              :options="[{label:'Male',value:'male'},{label:'Female',value:'female'},{label:'Other',value:'other'},{label:'Unknown',value:'unknown'}]"
              emit-value map-options clearable />
          </div>

          <!-- Name Variations -->
          <div class="row items-center q-mb-xs">
            <span class="text-caption text-grey-5 text-uppercase" style="letter-spacing:.5px">Name Variations / AKA</span>
            <q-space />
            <q-btn flat dense size="sm" icon="add" color="primary"
              @click="editForm.name_variations.push({ name:'', note:'' })" />
          </div>
          <div v-for="(v, i) in editForm.name_variations" :key="i"
            class="row q-gutter-xs q-mb-xs items-center">
            <q-input v-model="v.name" label="Name" dark filled dense class="col" />
            <q-input v-model="v.note" label="Note (optional)" dark filled dense style="max-width:140px" />
            <q-btn flat round dense icon="close" size="xs" color="grey-6"
              @click="editForm.name_variations.splice(i,1)" />
          </div>

          <!-- Phones -->
          <div class="row items-center q-mb-xs q-mt-sm">
            <span class="text-caption text-grey-5 text-uppercase" style="letter-spacing:.5px">Phone Numbers</span>
            <q-space />
            <q-btn flat dense size="sm" icon="add" color="primary"
              @click="editForm.phones.push({ number:'', phone_type:'mobile' })" />
          </div>
          <div v-for="(p, i) in editForm.phones" :key="i"
            class="row q-gutter-xs q-mb-xs items-center">
            <q-input v-model="p.number" label="Number" dark filled dense class="col" />
            <q-select v-model="p.phone_type"
              :options="[{label:'Mobile',value:'mobile'},{label:'Home',value:'home'},{label:'Work',value:'work'},{label:'Other',value:'other'}]"
              emit-value map-options dark filled dense style="max-width:100px" />
            <q-btn flat round dense icon="close" size="xs" color="grey-6"
              @click="editForm.phones.splice(i,1)" />
          </div>

          <!-- Emails -->
          <div class="row items-center q-mb-xs q-mt-sm">
            <span class="text-caption text-grey-5 text-uppercase" style="letter-spacing:.5px">Email Addresses</span>
            <q-space />
            <q-btn flat dense size="sm" icon="add" color="primary"
              @click="editForm.emails.push({ address:'', email_type:'personal' })" />
          </div>
          <div v-for="(e, i) in editForm.emails" :key="i"
            class="row q-gutter-xs q-mb-xs items-center">
            <q-input v-model="e.address" label="Email" dark filled dense class="col" />
            <q-select v-model="e.email_type"
              :options="[{label:'Personal',value:'personal'},{label:'Work',value:'work'},{label:'Other',value:'other'}]"
              emit-value map-options dark filled dense style="max-width:100px" />
            <q-btn flat round dense icon="close" size="xs" color="grey-6"
              @click="editForm.emails.splice(i,1)" />
          </div>

          <!-- Addresses -->
          <div class="row items-center q-mb-xs q-mt-sm">
            <span class="text-caption text-grey-5 text-uppercase" style="letter-spacing:.5px">Addresses</span>
            <q-space />
            <q-btn flat dense size="sm" icon="add" label="Add" color="primary"
              @click="editForm.addresses.push({ street:'', city:'', state:'', zip_code:'', address_type:'previous' })" />
          </div>
          <div v-for="(addr, i) in editForm.addresses" :key="i"
            class="q-mb-sm q-pa-sm" style="border:1px solid rgba(245,245,247,0.08); border-radius:8px">
            <div class="row items-center q-mb-xs" style="gap:6px">
              <q-select v-model="addr.address_type"
                :options="[{label:'Current',value:'current'},{label:'Previous',value:'previous'},{label:'Other',value:'other'}]"
                emit-value map-options dark filled dense style="min-width:110px" />
              <q-space />
              <q-btn flat round dense icon="close" size="xs" color="grey-6"
                @click="editForm.addresses.splice(i,1)"
                :disable="editForm.addresses.length === 1" />
            </div>
            <q-input v-model="addr.street" label="Street" dark filled dense class="q-mb-xs" />
            <div class="row q-gutter-xs">
              <q-input v-model="addr.city" label="City" dark filled dense class="col" />
              <q-input v-model="addr.state" label="State" dark filled dense style="max-width:70px" />
              <q-input v-model="addr.zip_code" label="ZIP" dark filled dense style="max-width:90px" />
            </div>
          </div>

          <q-input v-model="editForm.notes" label="Notes" dark filled type="textarea" autogrow class="q-mt-sm" />
        </q-card-section>
        <q-card-actions align="right" class="q-px-md q-pb-md">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn unelevated color="primary" label="Save" :loading="saving" @click="saveEdit" />
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

const identity = ref(null)
const reports = ref([])
const comparisons = ref([])
const unmatched = ref([])
const assigning = ref(null)
const showEdit = ref(false)
const saving = ref(false)
const editForm = ref({})

const BUREAUS = ['equifax', 'experian', 'transunion']

const identityCurrentAddr = computed(() => {
  const addrs = identity.value?.addresses || []
  return addrs.find(a => a.address_type === 'current') || addrs[0] || null
})
const identityPriorAddrs = computed(() => {
  const addrs = identity.value?.addresses || []
  const current = identityCurrentAddr.value
  return current ? addrs.filter(a => a.id !== current.id) : addrs.slice(1)
})

// Check if a bureau-reported address matches any identity reference address
function addrInRef(addr) {
  const norm = s => (s || '').toLowerCase().trim().replace(/\s+/g, ' ')
  const reportStreet = norm(addr.street)
  return (identity.value?.addresses || []).some(a => norm(a.street) === reportStreet)
}

// Check if a bureau-reported account matches any identity reference account
function acctInRef(bureauAcct) {
  const last4 = s => (s || '').replace(/\D/g, '').slice(-4)
  const tokens = s => new Set((s || '').toLowerCase().replace(/[^a-z\s]/g, ' ').split(/\s+/).filter(t => t.length > 2))
  const bl4 = last4(bureauAcct.account_number)
  const bt = tokens(bureauAcct.creditor_name)
  return (identity.value?.ref_accounts || []).some(ref => {
    const rl4 = last4(ref.account_number)
    if (bl4 && rl4 && bl4 === rl4) return true
    const rt = tokens(ref.creditor_name)
    const overlap = [...bt].filter(t => rt.has(t)).length
    return overlap >= Math.min(2, Math.min(bt.size, rt.size))
  })
}

const FIELDS = [
  { key: 'full_name', label: 'Full Name' },
  { key: 'ssn', label: 'SSN' },
  { key: 'date_of_birth', label: 'Date of Birth' },
]

// Bureau-level overall DD status (worst match across all fields for that report)
function bureauStatus(b) {
  const r = reportFor(b)
  if (!r) return null
  const results = comparisons.value.filter(c => c.report === r.id)
  if (!results.length) return 'missing'
  if (results.some(c => c.match_status === 'mismatch')) return 'mismatch'
  if (results.some(c => c.match_status === 'partial')) return 'partial'
  if (results.every(c => c.match_status === 'match')) return 'match'
  return 'missing'
}
const bureauStatusColor = (b) => matchColor(bureauStatus(b))
const bureauStatusLabel = (b) => ({ match: 'Clear', mismatch: 'Flagged', partial: 'Review', missing: 'Pending' }[bureauStatus(b)] || '—')

// Group reports by monitoring batch (date)
const reportsByBatch = computed(() => {
  const map = new Map()
  for (const r of reports.value) {
    const key = r.batch_run_date || r.uploaded_at?.slice(0, 10) || 'unknown'
    if (!map.has(key)) {
      const d = key !== 'unknown' ? new Date(key + 'T00:00:00') : null
      const label = d ? d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : 'Unknown Date'
      map.set(key, { key, label, reports: [], byBureau: {} })
    }
    const entry = map.get(key)
    entry.reports.push(r)
    entry.byBureau[r.bureau] = r
  }
  return [...map.values()].sort((a, b) => b.key.localeCompare(a.key))
})


// Map bureau → report
const reportByBureau = computed(() => {
  const map = {}
  for (const r of reports.value) map[r.bureau] = r
  return map
})

// Map "field|reportId" → ComparisonResult
const compMap = computed(() => {
  const map = {}
  for (const c of comparisons.value) map[`${c.field_name}|${c.report}`] = c
  return map
})

function reportFor(bureau) { return reportByBureau.value[bureau] }
function cellResult(field, bureau) {
  const r = reportFor(bureau)
  return r ? compMap.value[`${field}|${r.id}`] : null
}

function identityValue(field) {
  if (!identity.value) return '—'
  return identity.value[field] || '—'
}

const acctStatusColor = (s) => {
  const l = (s || '').toLowerCase()
  if (l === 'open') return 'positive'
  if (l === 'derogatory' || l === 'collection' || l === 'charged_off') return 'negative'
  if (l === 'closed') return 'grey-7'
  return 'grey-7'
}
const ddColor = (s) => ({ clear: 'positive', flagged: 'negative', review: 'warning', pending: 'grey' }[s] || 'grey')
const ddLabel = (s) => ({ clear: 'Clear', flagged: 'Flagged', review: 'Review', pending: 'Pending' }[s] || s)
const statusColor = (s) => ({ parsed: 'positive', failed: 'negative', parsing: 'info', pending: 'grey' }[s] || 'grey')
const confidenceLabel = (c) => ({ ssn: 'SSN', ssn_last4_name: 'SSN+Name', name_dob: 'Name+DOB', manual: 'Manual' }[c] || c)

const matchColor = (s) => ({ match: 'positive', mismatch: 'negative', partial: 'warning', missing: 'grey' }[s] || 'grey')
const matchTextColor = (s) => ({ match: '#34C759', mismatch: '#FF3B30', partial: '#FF9500', missing: 'rgba(245,245,247,0.45)' }[s] || 'rgba(245,245,247,0.45)')
const matchIcon = (s) => ({ match: 'check_circle', mismatch: 'cancel', partial: 'change_circle', missing: 'help' }[s] || 'help')

async function load() {
  const id = route.params.id
  const [idRes, unmatchedRes] = await Promise.all([
    api.get(`/identities/${id}/`),
    api.get('/reports/', { params: { unmatched: '1' } }),
  ])
  identity.value = idRes.data
  reports.value = idRes.data.reports || []
  comparisons.value = idRes.data.comparisons || []
  unmatched.value = unmatchedRes.data.results || unmatchedRes.data
}

async function assignReport(reportId) {
  assigning.value = reportId
  try {
    await api.post(`/identities/${route.params.id}/assign-report/`, { report_id: reportId })
    $q.notify({ type: 'positive', message: 'Report assigned and compared.' })
    await load()
  } catch {
    $q.notify({ type: 'negative', message: 'Assignment failed.' })
  } finally {
    assigning.value = null
  }
}

function openEdit() {
  if (!identity.value) return
  let dob = identity.value.date_of_birth || ''
  if (dob && dob.includes('-')) {
    const [y, m, d] = dob.split('-')
    dob = `${m}/${d}/${y}`
  }
  const addresses = (identity.value.addresses || []).map(a => ({ ...a }))
  editForm.value = {
    ...identity.value,
    date_of_birth: dob,
    addresses: addresses.length ? addresses : [{ street: '', city: '', state: '', zip_code: '', address_type: 'current' }],
    name_variations: (identity.value.name_variations || []).map(v => ({ ...v })),
    phones: (identity.value.phones || []).map(p => ({ ...p })),
    emails: (identity.value.emails || []).map(e => ({ ...e })),
  }
  showEdit.value = true
}

async function saveEdit() {
  saving.value = true
  try {
    const payload = { ...editForm.value }
    if (payload.date_of_birth && payload.date_of_birth.length === 10) {
      const [m, d, y] = payload.date_of_birth.split('/')
      payload.date_of_birth = `${y}-${m}-${d}`
    } else {
      delete payload.date_of_birth
    }
    await api.patch(`/identities/${route.params.id}/`, payload)
    showEdit.value = false
    $q.notify({ type: 'positive', message: 'Saved.' })
    await load()
  } catch {
    $q.notify({ type: 'negative', message: 'Save failed.' })
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.ref-label {
  color: rgba(245, 245, 247, 0.45);
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.7px;
  text-transform: uppercase;
  margin-bottom: 4px;
}
.ref-value {
  color: #FFFFFF;
  font-size: 0.9rem;
  font-weight: 500;
}
.ref-current-addr {
  border-left: 3px solid rgba(245, 245, 247, 0.2);
  padding: 6px 0 6px 12px;
}

.ref-prior-list {
  display: flex;
  flex-direction: column;
}

.ref-prior-item {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 6px 0;
  border-bottom: 1px solid rgba(245, 245, 247, 0.06);
}

.ref-prior-item:last-child {
  border-bottom: none;
}

.ref-prior-type {
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  color: rgba(245, 245, 247, 0.35);
  min-width: 54px;
  flex-shrink: 0;
}

.ref-prior-addr {
  font-size: 0.82rem;
  color: rgba(245, 245, 247, 0.6);
  line-height: 1.4;
}

.bureau-addr-row {
  padding: 4px 0;
  border-bottom: 1px solid rgba(245, 245, 247, 0.05);
}

.bureau-addr-row:last-child {
  border-bottom: none;
}

.bureau-acct-row {
  padding: 4px 0;
  border-bottom: 1px solid rgba(245, 245, 247, 0.05);
}

.bureau-acct-row:last-child {
  border-bottom: none;
}

.field-label {
  color: rgba(245, 245, 247, 0.45);
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.7px;
  text-transform: uppercase;
}
.field-value {
  font-size: 0.82rem;
  font-weight: 500;
  line-height: 1.3;
}

.timeline {
  position: relative;
}
.timeline-entry {
  display: flex;
  gap: 16px;
}
.timeline-spine {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  width: 20px;
  padding-top: 4px;
}
.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #3A3A3C;
  border: 2px solid rgba(245, 245, 247, 0.2);
  flex-shrink: 0;
}
.timeline-dot--latest {
  background: #0066CC;
  border-color: #0066CC;
  box-shadow: 0 0 8px rgba(0, 102, 204, 0.5);
}
.timeline-line {
  flex: 1;
  width: 2px;
  background: rgba(245, 245, 247, 0.08);
  margin-top: 4px;
}
.timeline-content {
  flex: 1;
  min-width: 0;
}

.ref-accounts-table {
  border: 1px solid rgba(245, 245, 247, 0.08);
  border-radius: 8px;
  overflow: hidden;
}

.ref-accounts-header {
  display: grid;
  grid-template-columns: 2fr 1.2fr 1fr 0.8fr;
  gap: 8px;
  padding: 7px 12px;
  background: rgba(245, 245, 247, 0.05);
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  color: rgba(245, 245, 247, 0.35);
}

.ref-accounts-row {
  display: grid;
  grid-template-columns: 2fr 1.2fr 1fr 0.8fr;
  gap: 8px;
  padding: 8px 12px;
  border-top: 1px solid rgba(245, 245, 247, 0.06);
  align-items: center;
}

.ref-acct-name {
  font-size: 0.8rem;
  color: rgba(245, 245, 247, 0.85);
  font-weight: 500;
}

.ref-acct-cell {
  font-size: 0.78rem;
  color: rgba(245, 245, 247, 0.55);
}
</style>
