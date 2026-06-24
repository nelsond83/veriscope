<template>
  <q-page class="q-pa-lg">
    <!-- Back nav -->
    <div class="row items-center q-mb-md">
      <q-btn flat round icon="arrow_back" :to="{ name: 'identities', query: route.query.dd_filter ? { dd_status: route.query.dd_filter } : {} }" class="q-mr-sm" />
      <span class="text-caption text-grey-6">Identities</span>
    </div>

    <!-- Loading skeleton -->
    <template v-if="loading && !identity">
      <q-card class="vs-card q-mb-xl">
        <q-card-section>
          <div class="row items-start justify-between no-wrap q-mb-md">
            <div>
              <q-skeleton type="text" width="220px" height="28px" class="q-mb-xs" />
              <q-skeleton type="text" width="160px" />
            </div>
            <div class="row items-center" style="gap:8px">
              <q-skeleton type="QBadge" width="70px" />
              <q-skeleton type="circle" size="28px" />
              <q-skeleton type="circle" size="28px" />
            </div>
          </div>
          <div class="row q-col-gutter-md q-mb-sm">
            <div v-for="n in 4" :key="n" class="col-xs-6 col-sm-3">
              <q-skeleton type="text" width="60%" class="q-mb-xs" />
              <q-skeleton type="text" width="85%" />
            </div>
          </div>
          <div class="row q-col-gutter-md">
            <div class="col-xs-6 col-sm-3">
              <q-skeleton type="text" width="60%" class="q-mb-xs" />
              <q-skeleton type="text" width="75%" />
            </div>
            <div class="col-xs-6 col-sm-5">
              <q-skeleton type="text" width="60%" class="q-mb-xs" />
              <q-skeleton type="QBadge" width="90px" />
            </div>
          </div>
        </q-card-section>
      </q-card>

      <q-skeleton type="text" width="160px" height="24px" class="q-mb-md" />
      <div class="row q-col-gutter-md q-mb-xl">
        <div v-for="n in 3" :key="n" class="col-xs-12 col-md-4">
          <q-card class="vs-card column full-height">
            <q-card-section class="row items-center no-wrap q-pb-sm" style="gap:8px">
              <q-skeleton type="QBadge" width="90px" />
              <q-space />
              <q-skeleton type="QBadge" width="60px" />
            </q-card-section>
            <q-separator dark />
            <q-card-section>
              <div v-for="i in 4" :key="i" class="q-py-md">
                <q-skeleton type="text" width="40%" class="q-mb-xs" />
                <div class="row items-center" style="gap:5px">
                  <q-skeleton type="circle" size="15px" />
                  <q-skeleton type="text" width="55%" />
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>
    </template>

    <template v-else>
    <!-- Identity reference card -->
    <q-card class="vs-card q-mb-xl" v-if="identity">
      <q-card-section>
        <div class="row items-start justify-between no-wrap q-mb-md">
          <div>
            <div class="text-h5 text-weight-bold text-white">{{ identity.full_name }}</div>
            <div class="text-caption q-mt-xs" style="color:#AAAAAE">
              Reference identity record
            </div>
          </div>
          <div class="row items-center" style="gap:8px">
            <q-badge :color="ddColor(identity.dd_status)" :label="ddLabel(identity.dd_status)"
              style="padding:6px 14px; font-size:0.75rem" />
            <q-btn flat round icon="edit" size="sm" title="Edit" @click="openEdit" />
            <q-btn flat round icon="delete" size="sm" title="Delete identity" color="negative"
              @click="showDelete = true" />
          </div>
        </div>

        <!-- Core fields row -->
        <div class="row q-col-gutter-md q-mb-sm">
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
        <div class="row q-col-gutter-md q-mb-md">
          <div class="col-xs-6 col-sm-3">
            <div class="ref-label">In File Since</div>
            <div class="ref-value">{{ fmtFullDate(identity.created_at) || '—' }}</div>
          </div>
          <div class="col-xs-6 col-sm-5">
            <div class="ref-label">Expected FICO / Advantage Score Range</div>
            <div v-if="identity.expected_fico_range" class="row items-center" style="gap:8px; margin-top:2px">
              <q-badge :color="ficoBadgeColor(identity.expected_fico_range)" :label="identity.expected_fico_range"
                style="font-size:0.75rem; padding:4px 10px" />
              <span style="color:#AAAAAE; font-size:0.8rem">{{ ficoRatingLabel(identity.expected_fico_range) }}</span>
            </div>
            <div v-else class="ref-value" style="color:#AAAAAE">—</div>
          </div>
        </div>

        <!-- Name variations -->
        <template v-if="identity.name_variations?.length">
          <div class="ref-label q-mb-xs">Also Known As</div>
          <div class="q-mb-md">
            <div v-for="v in identity.name_variations" :key="v.id"
              style="font-size:0.85rem; color:#FFFFFF; line-height:1.7">
              {{ v.name }}
              <span v-if="v.note" style="color:#AAAAAE; font-size:0.75rem; margin-left:4px">({{ v.note }})</span>
            </div>
          </div>
        </template>

        <!-- Phone numbers -->
        <template v-if="identity.phones?.length">
          <div class="ref-label q-mb-xs">Phone Numbers</div>
          <div class="q-mb-md">
            <div v-for="(p, i) in identity.phones" :key="p.id || i"
              class="row items-center q-mb-xs" style="gap:6px">
              <q-icon name="phone" size="13px" style="color:#AAAAAE" />
              <span class="ref-value" style="font-size:0.85rem">{{ p.number }}</span>
              <span style="color:#AAAAAE; font-size:0.7rem; text-transform:capitalize">{{ p.phone_type }}</span>
            </div>
          </div>
        </template>

        <!-- Addresses: current prominent, prior as list -->
        <template v-if="identityCurrentAddr">
          <div class="ref-label q-mb-xs">Current Address</div>
          <div class="ref-current-addr q-mb-md">
            <div class="text-white" style="font-size:0.92rem; font-weight:500; line-height:1.5">
              {{ identityCurrentAddr.street }}
            </div>
            <div style="color:#C4C4C8; font-size:0.85rem">
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
          <div class="ref-acct-grid q-mb-md">
            <div class="rag-header">
              <div>Creditor</div>
              <div>Type</div>
              <div>Account #</div>
              <div>Status</div>
              <div class="rag-r">Balance</div>
              <div class="rag-r">Limit</div>
              <div class="rag-r">High Bal</div>
              <div class="rag-r">Mthly Pmt</div>
              <div class="rag-r">Opened</div>
            </div>
            <div v-for="(acct, i) in identity.ref_accounts" :key="acct.id || i" class="rag-row">
              <div class="rag-creditor">{{ acct.creditor_name }}</div>
              <div class="rag-type">{{ acct.account_type || '—' }}</div>
              <div class="rag-acctnum">{{ fmtAcctNum(acct.account_number) }}</div>
              <div>
                <q-badge v-if="acct.status" dense :color="acctStatusColor(acct.status)"
                  :label="acct.status" style="font-size:0.56rem" />
                <span v-else style="font-size:0.7rem;color:#AAAAAE">—</span>
              </div>
              <div class="rag-r rag-num">{{ acct.balance != null ? fmtCurrency(acct.balance) : '—' }}</div>
              <div class="rag-r rag-num">{{ acct.credit_limit != null ? fmtCurrency(acct.credit_limit) : '—' }}</div>
              <div class="rag-r rag-num">{{ acct.highest_balance != null ? fmtCurrency(acct.highest_balance) : '—' }}</div>
              <div class="rag-r rag-num">{{ acct.monthly_payment != null ? fmtCurrency(acct.monthly_payment) : '—' }}</div>
              <div class="rag-r rag-date">{{ acct.date_opened ? fmtDate(acct.date_opened) : '—' }}</div>
              <div v-if="acct.account_address" class="rag-address">{{ acct.account_address }}</div>
            </div>
          </div>
        </template>

        <!-- Notes -->
        <template v-if="identity.notes">
          <div class="ref-label q-mb-xs">Notes</div>
          <div style="color:#C4C4C8; font-size:0.85rem">{{ identity.notes }}</div>
        </template>
      </q-card-section>
    </q-card>

    <!-- DD Report Card — one card per bureau -->
    <div class="row items-center q-mb-md">
      <div class="text-subtitle1 text-weight-medium text-white">DD Report Card</div>
      <q-space />
      <q-btn unelevated icon="download" label="Export Corrections" class="q-mr-sm" @click="exportDD" />
      <q-btn unelevated icon="restart_alt" label="Clear DD" color="warning"
        :disable="!identity?.comparisons?.length && !identity?.reports?.length"
        @click="showClearDD = true" />
    </div>
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
            <q-icon name="description" size="28px" style="color:#606064" />
            <div class="q-mt-sm" style="color:#AAAAAE; font-size:0.8rem">
              No report uploaded
            </div>
          </q-card-section>

          <!-- Fields + credit info (shown when report exists) -->
          <template v-else>
            <q-list dense>
              <q-item v-for="field in FIELDS" :key="field.key" class="q-py-md">
                <q-item-section>
                  <div class="field-label q-mb-xs">{{ field.label }}</div>
                  <template v-if="cellResult(field.key, b)">
                    <div class="row items-center no-wrap" style="gap:5px">
                      <q-icon
                        :name="matchIcon(cellResult(field.key, b).match_status)"
                        :color="matchColor(cellResult(field.key, b).match_status)"
                        size="15px" style="flex-shrink:0" />
                      <div>
                        <span class="field-value"
                          :style="{ color: matchTextColor(cellResult(field.key, b).match_status) }">
                          {{ cellResult(field.key, b).report_value || '—' }}
                        </span>
                        <div v-if="cellResult(field.key, b).match_status === 'mismatch'"
                          style="font-size:0.65rem; color:#FF6B6B; font-weight:600; letter-spacing:0.3px; margin-top:2px">
                          MISMATCH — on file: {{ cellResult(field.key, b).identity_value || '—' }}
                        </div>
                        <div v-else-if="cellResult(field.key, b).match_status === 'missing'"
                          style="font-size:0.65rem; color:#FF6B6B; font-weight:600; letter-spacing:0.3px; margin-top:2px">
                          NOT IN REPORT
                        </div>
                        <div v-else-if="cellResult(field.key, b).match_status === 'partial'"
                          style="font-size:0.65rem; color:#FF9500; font-weight:600; letter-spacing:0.3px; margin-top:2px">
                          PARTIAL MATCH — on file: {{ cellResult(field.key, b).identity_value || '—' }}
                        </div>
                      </div>
                    </div>
                  </template>
                  <span v-else class="field-value" style="color:#AAAAAE">—</span>
                </q-item-section>
              </q-item>

              <!-- Credit Score row -->
              <q-item v-if="reportFor(b)?.subject?.credit_score" class="q-py-md">
                <q-item-section>
                  <div class="field-label q-mb-xs">{{ reportFor(b).subject.score_type || 'Credit Score' }}</div>
                  <template v-if="cellResult('credit_score', b)">
                    <div class="row items-center no-wrap" style="gap:5px">
                      <q-icon
                        :name="matchIcon(cellResult('credit_score', b).match_status)"
                        :color="matchColor(cellResult('credit_score', b).match_status)"
                        size="15px" style="flex-shrink:0" />
                      <div>
                        <span class="field-value"
                          :style="{ color: matchTextColor(cellResult('credit_score', b).match_status) }">
                          {{ cellResult('credit_score', b).report_value || '—' }}
                        </span>
                        <div v-if="cellResult('credit_score', b).match_status === 'mismatch'"
                          style="font-size:0.65rem; color:#FF6B6B; font-weight:600; letter-spacing:0.3px; margin-top:2px">
                          MISMATCH — on file: {{ cellResult('credit_score', b).identity_value || '—' }}
                        </div>
                      </div>
                    </div>
                  </template>
                  <span v-else class="field-value"
                    :style="{ color: ficoScoreColor(reportFor(b).subject.credit_score) }">
                    {{ reportFor(b).subject.credit_score }}
                  </span>
                </q-item-section>
              </q-item>

              <!-- In File Since row -->
              <q-item v-if="reportFor(b)?.subject?.in_file_since" class="q-py-md">
                <q-item-section>
                  <div class="field-label q-mb-xs">In File Since</div>
                  <div class="row items-center no-wrap" style="gap:5px">
                    <q-icon name="check_circle" color="positive" size="15px" style="flex-shrink:0" />
                    <span class="field-value" style="color:#34C759">
                      {{ fmtDate(reportFor(b).subject.in_file_since) }}
                    </span>
                  </div>
                </q-item-section>
              </q-item>
            </q-list>

            <!-- Addresses: reference addresses checked against bureau, then extra bureau addresses -->
            <template v-if="reportFor(b) && (identity.addresses?.length || reportFor(b)?.subject?.addresses?.length)">
              <q-separator dark />
              <div class="q-pa-md">
                <div class="field-label q-mb-sm">Addresses</div>

                <!-- All addresses: ref first, then bureau-only -->
                <div v-for="(addr, i) in allAddrs(b)" :key="addr._kind + '-' + (addr.id || i)"
                  class="bureau-addr-row" :class="i > 0 ? 'q-mt-sm' : ''">
                  <div v-if="addr._kind === 'ref'" class="row items-start no-wrap" style="gap:7px">
                    <q-icon
                      :name="refAddrInBureau(addr, b) ? 'check_circle' : 'cancel'"
                      :color="refAddrInBureau(addr, b) ? 'positive' : 'negative'"
                      size="14px" style="margin-top:2px; flex-shrink:0" />
                    <div>
                      <div class="row items-center no-wrap" style="gap:5px">
                        <span :style="{ fontSize:'0.79rem', lineHeight:'1.3', color: refAddrInBureau(addr, b) ? '#34C759' : '#FF6B6B' }">{{ addr.street }}</span>
                        <q-badge v-if="i === 0" dense label="Current" color="blue-grey-9"
                          style="font-size:0.52rem; padding:1px 5px" />
                      </div>
                      <div :style="{ fontSize:'0.72rem', marginTop:'1px', color: refAddrInBureau(addr, b) ? 'rgba(52,199,89,0.65)' : 'rgba(255,107,107,0.65)' }">
                        {{ [addr.city, addr.state, addr.zip_code].filter(Boolean).join(', ') }}
                      </div>
                      <div v-if="!refAddrInBureau(addr, b)"
                        style="font-size:0.65rem; color:#FF6B6B; margin-top:2px; font-weight:600; letter-spacing:0.3px">
                        NOT IN REPORT
                      </div>
                    </div>
                  </div>
                  <div v-else class="row items-start no-wrap" style="gap:7px">
                    <q-icon name="cancel" color="negative" size="14px" style="margin-top:2px; flex-shrink:0" />
                    <div>
                      <span style="font-size:0.79rem; color:#FF6B6B; line-height:1.3">{{ addr.street }}</span>
                      <div style="font-size:0.72rem; color:rgba(255,107,107,0.65); margin-top:1px">
                        {{ [addr.city, addr.state, addr.zip_code].filter(Boolean).join(', ') }}
                      </div>
                      <div style="font-size:0.65rem; color:#FF6B6B; margin-top:2px; font-weight:600; letter-spacing:0.3px">
                        NOT IN REFERENCE DATA
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </template>

            <!-- Accounts: reference accounts checked against bureau, then bureau unknowns -->
            <template v-if="reportFor(b) && (identity.ref_accounts?.length || reportFor(b)?.subject?.financial_accounts?.length)">
              <q-separator dark />
              <div class="q-pa-md">
                <div class="field-label q-mb-sm">Accounts</div>

                <!-- No accounts parsed but ref accounts exist -->
                <div v-if="!reportFor(b)?.subject?.financial_accounts?.length"
                  class="row items-center no-wrap" style="gap:6px; padding:4px 0">
                  <q-icon name="warning" size="15px" style="color:#FF6B6B; flex-shrink:0" />
                  <span style="font-size:0.72rem; color:#FF6B6B; font-weight:600; letter-spacing:0.3px">
                    No accounts found in report —
                    {{ identity.ref_accounts?.length }}
                    reference account{{ identity.ref_accounts?.length !== 1 ? 's' : '' }} expected
                  </span>
                </div>

                <template v-else>
                  <!-- All accounts: ref first, then bureau-only -->
                  <div v-for="(acct, i) in allAccts(b)" :key="acct._kind + '-' + (acct.id || i)"
                    class="bureau-acct-row" :class="i > 0 ? 'q-mt-xs' : ''"
                    style="cursor:pointer" @click="toggleAcct(acctKey(acct, b))">
                    <div v-if="acct._kind === 'ref'" class="row items-start no-wrap" style="gap:7px">
                      <q-icon
                        :name="refAcctInBureau(acct, b) ? 'check_circle' : 'cancel'"
                        :color="refAcctInBureau(acct, b) ? 'positive' : 'negative'"
                        size="14px" style="margin-top:2px; flex-shrink:0" />
                      <div style="flex:1">
                        <div class="row items-center" style="gap:5px; flex-wrap:wrap">
                          <span :style="{ fontSize:'0.79rem', lineHeight:'1.4', color: refAcctInBureau(acct, b) ? '#34C759' : '#FF6B6B' }">{{ acct.creditor_name }}</span>
                          <span v-if="acct.account_number" :style="{ fontFamily:'monospace', fontSize:'0.7rem', color: refAcctInBureau(acct, b) ? 'rgba(52,199,89,0.65)' : 'rgba(255,107,107,0.65)' }">{{ acct.account_number }}</span>
                        </div>
                        <div v-if="!refAcctInBureau(acct, b)"
                          style="font-size:0.65rem; color:#FF6B6B; margin-top:2px; font-weight:600; letter-spacing:0.3px">
                          NOT IN REPORT
                        </div>
                      </div>
                      <q-icon v-if="bureauAcctDetail(acct, b)"
                        :name="expandedAccts.has(acctKey(acct, b)) ? 'expand_less' : 'expand_more'"
                        size="14px" style="color:#606064; margin-top:2px; flex-shrink:0" />
                    </div>
                    <div v-else class="row items-start no-wrap" style="gap:7px">
                      <q-icon name="cancel" color="negative" size="14px" style="margin-top:2px; flex-shrink:0" />
                      <div style="flex:1">
                        <div class="row items-center" style="gap:5px; flex-wrap:wrap">
                          <span style="font-size:0.79rem; color:#FF6B6B; line-height:1.4">{{ acct.creditor_name }}</span>
                          <span v-if="acct.account_number" style="font-family:monospace; font-size:0.7rem; color:rgba(255,107,107,0.65)">{{ acct.account_number }}</span>
                        </div>
                        <div style="font-size:0.65rem; color:#FF6B6B; margin-top:2px; font-weight:600; letter-spacing:0.3px">
                          NOT IN REFERENCE DATA
                        </div>
                      </div>
                      <q-icon v-if="bureauAcctDetail(acct, b)"
                        :name="expandedAccts.has(acctKey(acct, b)) ? 'expand_less' : 'expand_more'"
                        size="14px" style="color:#606064; margin-top:2px; flex-shrink:0" />
                    </div>
                    <!-- Expanded detail panel -->
                    <div v-if="expandedAccts.has(acctKey(acct, b)) && bureauAcctDetail(acct, b)"
                      class="bureau-acct-detail">
                      <div class="row q-mt-xs" style="gap:6px 14px; flex-wrap:wrap">
                        <div v-if="bureauAcctDetail(acct, b).date_opened" class="detail-item">
                          <span class="detail-label">Opened</span>
                          <span class="detail-value">{{ bureauAcctDetail(acct, b).date_opened }}</span>
                        </div>
                        <div v-if="bureauAcctDetail(acct, b).balance != null" class="detail-item">
                          <span class="detail-label">Balance</span>
                          <span class="detail-value">{{ fmtCurrency(bureauAcctDetail(acct, b).balance) }}</span>
                        </div>
                        <div v-if="bureauAcctDetail(acct, b).highest_balance != null" class="detail-item">
                          <span class="detail-label">High Balance</span>
                          <span class="detail-value">{{ fmtCurrency(bureauAcctDetail(acct, b).highest_balance) }}</span>
                        </div>
                        <div v-if="bureauAcctDetail(acct, b).credit_limit != null" class="detail-item">
                          <span class="detail-label">Limit</span>
                          <span class="detail-value">{{ fmtCurrency(bureauAcctDetail(acct, b).credit_limit) }}</span>
                        </div>
                        <div v-if="bureauAcctDetail(acct, b).monthly_payment != null" class="detail-item">
                          <span class="detail-label">Monthly Pmt</span>
                          <span class="detail-value">{{ fmtCurrency(bureauAcctDetail(acct, b).monthly_payment) }}</span>
                        </div>
                        <div v-if="bureauAcctDetail(acct, b).account_address" class="detail-item detail-item--full">
                          <span class="detail-label">Account Address</span>
                          <span class="detail-value">{{ bureauAcctDetail(acct, b).account_address }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </template>
              </div>
            </template>

            <!-- Corrections: editable list of issues to send to this bureau -->
            <q-separator dark />
            <div class="q-pa-md">
              <div class="row items-center q-mb-sm">
                <div class="field-label">Corrections</div>
                <q-badge v-if="correctionsFor(b).length" :label="correctionsFor(b).length" color="grey-7" class="q-ml-sm" />
                <q-space />
                <q-btn flat dense round icon="add" size="sm" color="primary" title="Add correction"
                  @click="openCorrectionDialog(b)" />
              </div>

              <div v-if="!correctionsFor(b).length" style="font-size:0.75rem; color:#AAAAAE">
                No corrections for this bureau.
              </div>

              <div v-for="corr in correctionsFor(b)" :key="corr.id" class="bureau-correction-row">
                <div class="row items-start no-wrap" style="gap:7px">
                  <q-icon name="flag" size="14px" style="color:#FF9500; margin-top:2px; flex-shrink:0" />
                  <div style="flex:1; min-width:0">
                    <div class="row items-center" style="gap:6px; flex-wrap:wrap">
                      <span style="font-size:0.79rem; color:#EBEBED">{{ corr.note }}</span>
                    </div>
                  </div>
                  <div class="row items-center no-wrap" style="gap:2px">
                    <q-btn flat round dense icon="edit" size="xs" color="grey-6"
                      @click="openCorrectionDialog(b, corr)" />
                    <q-btn flat round dense icon="delete" size="xs" color="negative"
                      @click="confirmDeleteCorrection(corr)" />
                  </div>
                </div>
              </div>
            </div>
          </template>

        </q-card>
      </div>
    </div>

    <!-- Add/Edit Correction dialog -->
    <q-dialog v-model="showCorrectionDialog" persistent>
      <q-card class="vs-card" style="min-width:380px; max-width:440px">
        <q-card-section>
          <div class="text-h6 text-white">{{ correctionForm.id ? 'Edit' : 'Add' }} Correction</div>
          <div class="text-caption text-grey-6">{{ bureauLabel(correctionForm.bureau) }}</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-input v-model="correctionForm.note" label="Correction" type="textarea" autogrow
            dark filled :rules="[v => !!v?.trim() || 'Required']" />
        </q-card-section>
        <q-card-actions align="right" class="q-px-md q-pb-md">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn unelevated color="primary" label="Save" :loading="savingCorrection" @click="saveCorrection" />
        </q-card-actions>
      </q-card>
    </q-dialog>

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
            <q-badge v-if="idx === 0" label="Latest"
              style="background:#FFB81C; color:#111111; font-weight:700; font-size:0.65rem; letter-spacing:0.4px; padding:3px 8px" />
            <span class="text-caption text-grey-6">{{ batch.reports.length }} report{{ batch.reports.length !== 1 ? 's' : '' }}</span>
          </div>

          <q-card class="vs-card">
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
          <q-item v-for="r in unmatched" :key="r.id"
            clickable v-ripple :to="{ name: 'unmatched' }">
            <q-item-section avatar>
              <BureauBadge :bureau="r.bureau" :show-name="false" size="md" />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ r.original_filename }}</q-item-label>
              <q-item-label caption>{{ r.subject?.full_name || 'Not parsed' }}</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-btn unelevated color="secondary" label="Assign here" icon="link"
                :loading="assigning === r.id"
                @click.prevent.stop="assignReport(r.id)" />
            </q-item-section>
          </q-item>
        </q-list>
      </q-card>
    </template>
    </template>

    <!-- Archived DD Runs -->
    <template v-if="identity?.dd_runs?.length">
      <div class="row items-center q-mb-md q-mt-xl">
        <div class="text-subtitle1 text-weight-medium text-grey-5">Archived DD Runs</div>
        <q-badge :label="identity.dd_runs.length" color="grey-7" class="q-ml-sm" />
      </div>
      <div class="q-mb-xl">
        <q-card v-for="run in identity.dd_runs" :key="run.id" class="vs-card q-mb-md">
          <q-card-section>
            <div class="row items-center q-mb-sm" style="gap:10px">
              <q-icon name="history" size="16px" color="grey-6" />
              <span class="text-weight-medium text-grey-3" style="font-size:0.9rem">
                {{ fmtFullDate(run.created_at) }}
              </span>
              <q-badge :color="ddColor(run.dd_status)" :label="ddLabel(run.dd_status)"
                style="font-size:0.65rem; padding:3px 8px" />
              <q-space />
              <div class="row items-center" style="gap:6px">
                <q-badge v-for="r in run.reports" :key="r.id" dense color="dark"
                  style="font-size:0.6rem; cursor:pointer"
                  :label="r.bureau.slice(0,2).toUpperCase()"
                  @click="openArchivedPdf(r)" />
              </div>
            </div>
            <div v-if="run.results_snapshot?.length">
              <div v-for="result in run.results_snapshot.filter(r => r.match_status !== 'match')" :key="result.id"
                class="row items-center q-mb-xs" style="gap:6px">
                <q-icon
                  :name="result.match_status === 'mismatch' ? 'cancel' : result.match_status === 'partial' ? 'warning' : 'info'"
                  :color="result.match_status === 'mismatch' ? 'negative' : result.match_status === 'partial' ? 'warning' : 'grey'"
                  size="13px" />
                <span style="font-size:0.75rem; color:#AAAAAE; text-transform:capitalize">
                  {{ result.field_name.replace(/_/g, ' ') }}
                </span>
                <span v-if="result.report_value" style="font-size:0.75rem; color:#C4C4C8">
                  {{ result.report_value }}
                </span>
                <q-badge dense color="dark" style="font-size:0.55rem"
                  :label="bureauAbbr(result.report)" />
              </div>
              <div v-if="run.results_snapshot.every(r => r.match_status === 'match')"
                class="row items-center" style="gap:5px">
                <q-icon name="check_circle" color="positive" size="13px" />
                <span style="font-size:0.75rem; color:#34C759">All fields matched</span>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </template>

    <!-- Clear DD confirmation dialog -->
    <q-dialog v-model="showClearDD" persistent>
      <q-card class="vs-card" style="min-width:360px">
        <q-card-section>
          <div class="text-h6 text-white">Clear DD Results?</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <p style="color:#EBEBED">
            The current DD results and linked reports for
            <strong>{{ identity?.full_name }}</strong> will be archived and a new DD
            will require fresh PDFs to be uploaded.
          </p>
        </q-card-section>
        <q-card-actions align="right" class="q-pa-md" style="gap:8px">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn unelevated color="warning" label="Clear DD" icon="restart_alt"
            :loading="clearingDD" @click="clearDD" />
        </q-card-actions>
      </q-card>
    </q-dialog>

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

          <!-- Reference Accounts -->
          <div class="row items-center q-mb-xs q-mt-sm">
            <span class="text-caption text-grey-5 text-uppercase" style="letter-spacing:.5px">Reference Accounts</span>
            <q-space />
            <q-btn flat dense size="sm" icon="add" color="primary"
              @click="editForm.ref_accounts.push({ creditor_name:'', account_type:'', account_number:'', status:'open', balance:null, credit_limit:null, highest_balance:null, monthly_payment:null, date_opened:'', account_address:'' })" />
          </div>
          <div v-for="(acct, i) in editForm.ref_accounts" :key="i"
            class="q-mb-sm q-pa-sm" style="border:1px solid rgba(245,245,247,0.08); border-radius:8px">
            <div class="row items-center q-gutter-xs q-mb-xs">
              <q-input v-model="acct.creditor_name" label="Creditor" dark filled dense class="col" />
              <q-input v-model="acct.account_number" label="Account #" dark filled dense style="max-width:120px" />
              <q-btn flat round dense icon="close" size="xs" color="grey-6" @click="editForm.ref_accounts.splice(i,1)" />
            </div>
            <div class="row q-gutter-xs q-mb-xs">
              <q-select v-model="acct.account_type"
                :options="['credit card','auto loan','mortgage','student loan','personal loan','collection','medical','other']"
                dark filled dense label="Type" class="col" clearable />
              <q-select v-model="acct.status"
                :options="['open','closed','derogatory','collection','charged off']"
                dark filled dense label="Status" style="max-width:120px" />
            </div>
            <div class="row q-gutter-xs q-mb-xs">
              <q-input v-model.number="acct.balance" label="Balance ($)" dark filled dense type="number" class="col" />
              <q-input v-model.number="acct.credit_limit" label="Limit ($)" dark filled dense type="number" class="col" />
              <q-input v-model.number="acct.highest_balance" label="High Bal ($)" dark filled dense type="number" class="col" />
            </div>
            <div class="row q-gutter-xs">
              <q-input v-model.number="acct.monthly_payment" label="Monthly Pmt ($)" dark filled dense type="number" class="col" />
              <q-input v-model="acct.date_opened" label="Opened (YYYY-MM-DD)" dark filled dense class="col" />
              <q-input v-model="acct.account_address" label="Address" dark filled dense class="col-12 q-mt-xs" />
            </div>
          </div>

          <q-select v-model="editForm.expected_fico_range" label="Expected FICO Score Range (optional)"
            dark filled clearable :options="FICO_RANGES" emit-value map-options class="q-mt-sm"
            hint="When set, credit score on reports will be compared to this range" />
          <q-input v-model="editForm.notes" label="Notes" dark filled type="textarea" autogrow class="q-mt-sm" />
        </q-card-section>
        <q-card-actions align="right" class="q-px-md q-pb-md">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn unelevated color="primary" label="Save" :loading="saving" @click="saveEdit" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Delete confirmation dialog -->
    <q-dialog v-model="showDelete" persistent>
      <q-card class="vs-card" style="min-width:340px">
        <q-card-section>
          <div class="text-h6 text-white">Delete Identity?</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <p style="color:#EBEBED">
            This will permanently delete <strong>{{ identity?.full_name }}</strong> and all
            associated reports and comparisons. This cannot be undone.
          </p>
        </q-card-section>
        <q-card-actions align="right" class="q-pa-md" style="gap:8px">
          <q-btn flat label="Cancel" v-close-popup />
          <q-btn unelevated color="negative" label="Delete" icon="delete"
            :loading="deleting" @click="deleteIdentity" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { api } from 'boot/axios'
import BureauBadge from 'components/BureauBadge.vue'

const route = useRoute()
const router = useRouter()
const $q = useQuasar()

const identity = ref(null)
const reports = ref([])
const comparisons = ref([])
const unmatched = ref([])
const loading = ref(true)
const assigning = ref(null)
const showEdit = ref(false)
const showDelete = ref(false)
const showClearDD = ref(false)
const saving = ref(false)
const deleting = ref(false)
const clearingDD = ref(false)
const editForm = ref({})

const showCorrectionDialog = ref(false)
const savingCorrection = ref(false)
const correctionForm = ref({ id: null, bureau: '', note: '' })

const BUREAUS = ['equifax', 'experian', 'transunion']

const FICO_RANGES = [
  { label: '800–850 (Exceptional)', value: '800-850' },
  { label: '740–799 (Very Good)', value: '740-799' },
  { label: '670–739 (Good)', value: '670-739' },
  { label: '580–669 (Fair)', value: '580-669' },
  { label: '300–579 (Poor)', value: '300-579' },
]

const expandedAccts = ref(new Set())
const expandedRefAccts = ref(new Set())

function toggleRefAcct(key) {
  const s = new Set(expandedRefAccts.value)
  s.has(key) ? s.delete(key) : s.add(key)
  expandedRefAccts.value = s
}

function fmtAcctNum(num) {
  if (!num) return '—'
  const d = String(num).replace(/\D/g, '')
  if (d.length === 16) return `${d.slice(0,4)} ${d.slice(4,8)} ${d.slice(8,12)} ${d.slice(12)}`
  return num
}

function refAcctHasExtraDetail(acct) {
  return !!(acct.highest_balance != null || acct.monthly_payment != null || acct.account_address)
}

function acctKey(acct, b) {
  return `${b}-${acct._kind}-${acct.id || acct.creditor_name}-${acct.account_number || ''}`
}

function toggleAcct(key) {
  const s = new Set(expandedAccts.value)
  s.has(key) ? s.delete(key) : s.add(key)
  expandedAccts.value = s
}

function bureauAcctDetail(acct, b) {
  const bureauAccts = reportFor(b)?.subject?.financial_accounts || []
  if (acct._kind === 'bureau') return acct
  return bureauAccts.find(ba => acctPairMatches(acct, ba)) || null
}

function fmtCurrency(val) {
  if (val == null) return '—'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val)
}

function fmtDate(dateStr) {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr + 'T12:00:00Z')
    return d.toLocaleDateString('en-US', { month: 'short', year: 'numeric', timeZone: 'UTC' })
  } catch {
    return dateStr
  }
}

function fmtFullDate(dateStr) {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  } catch {
    return dateStr
  }
}

function ficoScoreColor(score) {
  if (!score) return '#EBEBED'
  if (score >= 800) return '#34C759'
  if (score >= 740) return '#30D158'
  if (score >= 670) return '#EBEBED'
  if (score >= 580) return '#FF9500'
  return '#FF6B6B'
}

function ficoRangeStatus(b) {
  const score = reportFor(b)?.subject?.credit_score
  const range = identity.value?.expected_fico_range
  if (!score || !range) return null
  const [low, high] = range.split('-').map(Number)
  if (isNaN(low) || isNaN(high)) return null
  return (score >= low && score <= high) ? 'match' : 'mismatch'
}

function ficoBadgeColor(range) {
  const low = parseInt((range || '').split('-')[0])
  if (low >= 800) return 'positive'
  if (low >= 740) return 'teal'
  if (low >= 670) return 'grey-7'
  if (low >= 580) return 'orange'
  return 'negative'
}

function ficoRatingLabel(range) {
  const labels = {
    '800-850': 'Exceptional', '740-799': 'Very Good', '670-739': 'Good',
    '580-669': 'Fair', '300-579': 'Poor',
  }
  return labels[range] || ''
}

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
const normStreet = s => (s || '').toLowerCase().trim().replace(/\s+/g, ' ')

function addrInRef(addr) {
  return (identity.value?.addresses || []).some(a => normStreet(a.street) === normStreet(addr.street))
}

function refAddrInBureau(refAddr, b) {
  const bureauAddrs = reportFor(b)?.subject?.addresses || []
  return bureauAddrs.some(a => normStreet(a.street) === normStreet(refAddr.street))
}

function unknownBureauAddrs(b) {
  const refStreets = new Set((identity.value?.addresses || []).map(a => normStreet(a.street)))
  return (reportFor(b)?.subject?.addresses || []).filter(a => !refStreets.has(normStreet(a.street)))
}

const acctLast4 = s => (s || '').replace(/\D/g, '').slice(-4)
const acctTokens = s => new Set((s || '').toLowerCase().replace(/[^a-z\s]/g, ' ').split(/\s+/).filter(t => t.length > 2))
function acctPairMatches(a, b) {
  const al4 = acctLast4(a.account_number), bl4 = acctLast4(b.account_number)
  if (al4 && bl4 && al4 === bl4) return true
  const at = acctTokens(a.creditor_name), bt = acctTokens(b.creditor_name)
  const overlap = [...at].filter(t => bt.has(t)).length
  return overlap >= Math.min(2, Math.min(at.size, bt.size))
}

// Check if a bureau-reported account matches any identity reference account
function acctInRef(bureauAcct) {
  return (identity.value?.ref_accounts || []).some(ref => acctPairMatches(ref, bureauAcct))
}

// Check if a reference account appears in the bureau report for bureau b
function refAcctInBureau(refAcct, b) {
  const bureauAccts = reportFor(b)?.subject?.financial_accounts || []
  return bureauAccts.some(bureau => acctPairMatches(refAcct, bureau))
}

// Bureau accounts not matched by any reference account
function unknownBureauAccts(b) {
  return (reportFor(b)?.subject?.financial_accounts || []).filter(acct => !acctInRef(acct))
}

function allAddrs(b) {
  const ref = (identity.value?.addresses || []).map(a => ({ ...a, _kind: 'ref' }))
  const unk = unknownBureauAddrs(b).map(a => ({ ...a, _kind: 'bureau' }))
  return [...ref, ...unk]
}

function allAccts(b) {
  const ref = (identity.value?.ref_accounts || []).map(a => ({ ...a, _kind: 'ref' }))
  const unk = unknownBureauAccts(b).map(a => ({ ...a, _kind: 'bureau' }))
  return [...ref, ...unk]
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
const matchTextColor = (s) => ({ match: '#34C759', mismatch: '#FF6B6B', partial: '#FF9500', missing: '#AAAAAE' }[s] || '#AAAAAE')
const matchIcon = (s) => ({ match: 'check_circle', mismatch: 'cancel', partial: 'change_circle', missing: 'help' }[s] || 'help')

async function load() {
  loading.value = true
  try {
    const id = route.params.id
    const [idRes, unmatchedRes] = await Promise.all([
      api.get(`/identities/${id}/`),
      api.get('/reports/', { params: { unmatched: '1' } }),
    ])
    identity.value = idRes.data
    reports.value = idRes.data.reports || []
    comparisons.value = idRes.data.comparisons || []
    unmatched.value = unmatchedRes.data.results || unmatchedRes.data
  } finally {
    loading.value = false
  }
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
    ref_accounts: (identity.value.ref_accounts || []).map(a => ({ ...a })),
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

async function deleteIdentity() {
  deleting.value = true
  try {
    await api.delete(`/identities/${route.params.id}/`)
    showDelete.value = false
    $q.notify({ type: 'positive', message: 'Identity deleted.' })
    router.push({ name: 'identities' })
  } catch {
    $q.notify({ type: 'negative', message: 'Delete failed.' })
  } finally {
    deleting.value = false
  }
}

async function clearDD() {
  clearingDD.value = true
  try {
    await api.post(`/identities/${route.params.id}/clear-dd/`)
    showClearDD.value = false
    $q.notify({ type: 'positive', message: 'DD archived and cleared.' })
    await load()
  } catch (e) {
    $q.notify({ type: 'negative', message: e?.response?.data?.detail || 'Failed to clear DD.' })
  } finally {
    clearingDD.value = false
  }
}

async function exportDD() {
  try {
    const res = await api.get(`/identities/${route.params.id}/export-dd/`, { responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `corrections_${identity.value?.full_name?.replace(/\s+/g, '_') || 'export'}.zip`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    $q.notify({ type: 'negative', message: 'Export failed.' })
  }
}

function bureauAbbr(reportId) {
  const r = reports.value.find(r => r.id === reportId)
  return r ? { equifax: 'EQ', experian: 'EX', transunion: 'TU' }[r.bureau] || r.bureau.slice(0, 2).toUpperCase() : '??'
}

function correctionsFor(bureau) {
  return (identity.value?.corrections || []).filter(c => c.bureau === bureau)
}

function bureauLabel(bureau) {
  return { equifax: 'Equifax', experian: 'Experian', transunion: 'TransUnion' }[bureau] || bureau
}

function openCorrectionDialog(bureau, correction = null) {
  correctionForm.value = correction
    ? { ...correction }
    : { id: null, bureau, note: '' }
  showCorrectionDialog.value = true
}

async function saveCorrection() {
  if (!correctionForm.value.note?.trim()) return
  savingCorrection.value = true
  try {
    const payload = {
      identity: route.params.id,
      bureau: correctionForm.value.bureau,
      note: correctionForm.value.note,
    }
    if (correctionForm.value.id) {
      await api.patch(`/corrections/${correctionForm.value.id}/`, payload)
    } else {
      await api.post('/corrections/', payload)
    }
    showCorrectionDialog.value = false
    $q.notify({ type: 'positive', message: 'Correction saved.' })
    await load()
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to save correction.' })
  } finally {
    savingCorrection.value = false
  }
}

function confirmDeleteCorrection(correction) {
  $q.dialog({
    title: 'Delete Correction?',
    message: 'Remove this correction? This cannot be undone.',
    ok: { label: 'Delete', color: 'negative', unelevated: true },
    cancel: { label: 'Cancel', flat: true },
    dark: true,
  }).onOk(() => deleteCorrection(correction))
}

async function deleteCorrection(correction) {
  try {
    await api.delete(`/corrections/${correction.id}/`)
    $q.notify({ type: 'positive', message: 'Correction deleted.' })
    await load()
  } catch {
    $q.notify({ type: 'negative', message: 'Failed to delete correction.' })
  }
}

function openArchivedPdf(archivedReport) {
  if (archivedReport.file_url) window.open(archivedReport.file_url, '_blank')
}

onMounted(load)
</script>

<style scoped>
.ref-label {
  color: #FFB81C;
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
  border-left: 3px solid rgba(255, 255, 255, 0.2);
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
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}

.ref-prior-item:last-child {
  border-bottom: none;
}

.ref-prior-type {
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  color: #AAAAAE;
  min-width: 54px;
  flex-shrink: 0;
}

.ref-prior-addr {
  font-size: 0.82rem;
  color: #C4C4C8;
  line-height: 1.4;
}

.ref-acct-grid {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  overflow-x: auto;
}

.rag-header,
.rag-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1.6fr 0.6fr 1fr 1fr 1fr 1fr 1fr;
  align-items: center;
  gap: 14px;
  padding: 6px 14px;
  min-width: 1000px;
}

.rag-header {
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  color: #AAAAAE;
}

.rag-row {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.rag-row:last-child {
  border-bottom: none;
}

.rag-creditor {
  font-size: 0.82rem;
  color: #FFFFFF;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.rag-type {
  font-size: 0.75rem;
  color: #AAAAAE;
  text-transform: capitalize;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.rag-acctnum {
  font-family: monospace;
  font-size: 0.72rem;
  color: #AAAAAE;
  letter-spacing: 0.3px;
  white-space: nowrap;
}

.rag-num {
  font-size: 0.76rem;
  color: #C4C4C8;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.rag-r {
  text-align: right;
}

.rag-date {
  font-size: 0.76rem;
  color: #C4C4C8;
  white-space: nowrap;
}

.rag-address {
  grid-column: 1 / -1;
  font-size: 0.65rem;
  color: #888890;
  padding: 1px 0 3px;
}

.bureau-addr-row {
  padding: 4px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.bureau-addr-row:last-child {
  border-bottom: none;
}

.bureau-acct-row {
  padding: 4px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.bureau-acct-row:last-child {
  border-bottom: none;
}

.bureau-correction-row {
  padding: 6px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.bureau-correction-row:last-child {
  border-bottom: none;
}

.bureau-acct-detail {
  padding: 6px 0 4px 21px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  flex-wrap: wrap;
  gap: 10px 20px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.detail-item--full {
  flex: 0 0 100%;
}

.detail-label {
  font-size: 0.58rem;
  color: #AAAAAE;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 700;
}

.detail-value {
  font-size: 0.78rem;
  color: #EBEBED;
}

.field-label {
  color: #FFB81C;
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
  border: 2px solid rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
}
.timeline-dot--latest {
  background: #C8102E;
  border-color: #C8102E;
  box-shadow: 0 0 8px rgba(200, 16, 46, 0.5);
}
.timeline-line {
  flex: 1;
  width: 2px;
  background: rgba(255, 255, 255, 0.08);
  margin-top: 4px;
}
.timeline-content {
  flex: 1;
  min-width: 0;
}

.ref-accounts-table {
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 8px;
  overflow: hidden;
}

.ref-accounts-header {
  display: grid;
  grid-template-columns: 2fr 1.2fr 1fr 0.8fr;
  gap: 8px;
  padding: 7px 12px;
  background: rgba(255, 255, 255, 0.05);
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  color: #AAAAAE;
}

.ref-accounts-row {
  display: grid;
  grid-template-columns: 2fr 1.2fr 1fr 0.8fr;
  gap: 8px;
  padding: 8px 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
  align-items: center;
}

.ref-acct-name {
  font-size: 0.8rem;
  color: #D8D8DA;
  font-weight: 500;
}

.ref-acct-cell {
  font-size: 0.78rem;
  color: #B8B8BD;
}
</style>
