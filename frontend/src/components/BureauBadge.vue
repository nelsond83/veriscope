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
  equifax:    { abbr: 'EQ', label: 'Equifax' },
  experian:   { abbr: 'EX', label: 'Experian' },
  transunion: { abbr: 'TU', label: 'TransUnion' },
  unknown:    { abbr: '?',  label: 'Unknown' },
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

/* Equifax — red  |  text #FFCCCC on effective bg ~#4B2028 = 9.1:1 ✓ */
.bureau-badge--equifax {
  background: rgba(200, 16, 46, 0.20);
  border-color: rgba(200, 16, 46, 0.45);
  color: #FFCCCC;
}
.bureau-badge--equifax .bureau-badge__abbr {
  color: #FFB0B0;
}

/* Experian — violet  |  text #E5B8FF on effective bg ~#41244F = 7.9:1 ✓ */
.bureau-badge--experian {
  background: rgba(148, 0, 211, 0.20);
  border-color: rgba(148, 0, 211, 0.45);
  color: #E5B8FF;
}
.bureau-badge--experian .bureau-badge__abbr {
  color: #D090F8;
}

/* TransUnion — Blue  |  text #5AABFF on effective bg ~#1A2D4A = 5.3:1 ✓ */
.bureau-badge--transunion {
  background: rgba(0, 82, 204, 0.20);
  border-color: rgba(0, 82, 204, 0.45);
  color: #5AABFF;
}
.bureau-badge--transunion .bureau-badge__abbr {
  color: #80BEFF;
}

/* Unknown  |  #AAAAAE on dark bg = 6.3:1 ✓ */
.bureau-badge--unknown {
  background: rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.15);
  color: #AAAAAE;
}
</style>
