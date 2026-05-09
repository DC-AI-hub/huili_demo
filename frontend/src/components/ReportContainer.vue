<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import ReportLCMeeting from './ReportLCMeeting.vue'
import ReportMorningstar from './ReportMorningstar.vue'
import ReportRisk from './ReportRisk.vue'
import ReportFactsheet from './ReportFactsheet.vue'
import ReportAssetConcentration from './ReportAssetConcentration.vue'
import ReportAUM from './ReportAUM.vue'

const route = useRoute()

const reportMap = {
  'LC meeting': ReportLCMeeting,
  'Morningstart Report': ReportMorningstar,
  'Risk Reporting': ReportRisk,
  'Factsheet': ReportFactsheet,
  'Asset Concentration Risk': ReportAssetConcentration,
  'AUM': ReportAUM
}

// Fallback to factsheet or a default not-found placeholder if name is totally missing
const currentComponent = computed(() => {
  const name = route.query.name
  if (name && reportMap[name]) {
    return reportMap[name]
  }
  return ReportFactsheet // Default fallback logic
})
</script>

<template>
  <!-- Load the respective Vue component dynamically based on the report name -->
  <component :is="currentComponent" />
</template>
