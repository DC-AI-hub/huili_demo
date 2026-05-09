<script setup>
import { onMounted } from 'vue'
import ReportRisk from './ReportRisk.vue'

const isReportRiskReady = !!ReportRisk

onMounted(() => {
  if (!isReportRiskReady) {
    console.error('[ReportAssetConcentration] Failed to load ReportRisk component.')
    return
  }
  console.log('Asset Concentration Risk report mounted')
})
</script>

<template>
  <div class="generic-report-container">
    <ReportRisk v-if="isReportRiskReady" />
    <p v-else class="error-tip">ReportRisk 组件加载失败，请检查控制台报错信息。</p>
  </div>
</template>

<style scoped>
.generic-report-container {
  padding: 0px;
  background-color: #f7fafc;
  min-height: calc(100vh - 135px);
}
.error-tip {
  color: #c53030;
  font-size: 14px;
  margin: 12px 0;
}
</style>
