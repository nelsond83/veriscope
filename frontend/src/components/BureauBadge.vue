<template>
  <div class="bureau-badge" :class="`bureau-badge--${bureau}`" :style="sizeStyle">
    <span class="bureau-badge__abbr">{{ abbr }}</span>
    <span v-if="showName" class="bureau-badge__name">{{ label }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  bureau: {
    type: String,
    default: 'unknown',
  },
  showName: {
    type: Boolean,
    default: true,
  },
  size: {
    type: String,
    default: 'md', // sm | md | lg
  },
})

const META = {
  equifax:    { abbr: 'EFX', label: 'Equifax' },
  experian:   { abbr: 'EXP', label: 'Experian' },
  transunion: { abbr: 'TU',  label: 'TransUnion' },
  unknown:    { abbr: '?',   label: 'Unknown' },
}

const abbr  = computed(() => META[props.bureau]?.abbr  ?? '?')
const label = computed(() => META[props.bureau]?.label ?? 'Unknown')

const sizeStyle = computed(() => ({
  sm: { '--badge-font': '10px', '--badge-abbr-size': '9px',  '--badge-pad': '2px 7px' },
  md: { '--badge-font': '12px', '--badge-abbr-size': '11px', '--badge-pad': '3px 10px' },
  lg: { '--badge-font': '14px', '--badge-abbr-size': '13px', '--badge-pad': '5px 14px' },
}[props.size] ?? {}))
</script>

<style scoped>
.bureau-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border-radius: 6px;
  padding: var(--badge-pad, 3px 10px);
  font-family: 'Segoe UI', Inter, sans-serif;
  font-size: var(--badge-font, 12px);
  font-weight: 600;
  letter-spacing: 0.3px;
  white-space: nowrap;
  border: 1px solid transparent;
}

.bureau-badge__abbr {
  font-size: var(--badge-abbr-size, 11px);
  font-weight: 800;
  font-family: 'Roboto Mono', monospace;
  letter-spacing: 1px;
}

/* Equifax — red */
.bureau-badge--equifax {
  background: rgba(255, 59, 48, 0.12);
  border-color: rgba(255, 59, 48, 0.3);
  color: #FF6B6B;
}
.bureau-badge--equifax .bureau-badge__abbr {
  color: #FF8585;
}

/* Experian — violet */
.bureau-badge--experian {
  background: rgba(175, 82, 222, 0.12);
  border-color: rgba(175, 82, 222, 0.3);
  color: #C57EE8;
}
.bureau-badge--experian .bureau-badge__abbr {
  color: #D49AF0;
}

/* TransUnion — Science Blue */
.bureau-badge--transunion {
  background: rgba(0, 102, 204, 0.15);
  border-color: rgba(0, 102, 204, 0.35);
  color: #5AABFF;
}
.bureau-badge--transunion .bureau-badge__abbr {
  color: #80BEFF;
}

/* Unknown */
.bureau-badge--unknown {
  background: rgba(245, 245, 247, 0.07);
  border-color: rgba(245, 245, 247, 0.15);
  color: rgba(245, 245, 247, 0.45);
}
</style>
