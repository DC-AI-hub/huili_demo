<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import axios from 'axios'
import Echarts3DPie from './Echarts3DPie.vue'

const props = defineProps({
  asOfDate: {
    type: String,
    default: null
  }
})

const chartData = ref([])
const loading = ref(true)
const error = ref(null)

const fetchQuartileData = async () => {
  try {
    loading.value = true
    const params = {}
    if (props.asOfDate) params.as_of_date = props.asOfDate
    
    const res = await axios.get('/api/lc-meeting/quartile-report', { params })
    chartData.value = res.data.data
  } catch (err) {
    console.error('Failed to fetch quartile data:', err)
    error.value = 'Failed to load chart data'
  } finally {
    loading.value = false
  }
}

watch(() => props.asOfDate, fetchQuartileData)
onMounted(fetchQuartileData)

const getEchartsData = (item) => {
  return [
    { name: '1st Quartile', value: Math.round(item.q1_pct * 100), itemStyle: { color: '#00843D' } },
    { name: '2nd Quartile', value: Math.round(item.q2_pct * 100), itemStyle: { color: '#9BCA3C' } },
    { name: '3rd Quartile', value: Math.round(item.q3_pct * 100), itemStyle: { color: '#00A1E4' } },
    { name: '4th Quartile', value: Math.round(item.q4_pct * 100), itemStyle: { color: '#9D228E' } }
  ]
}

const getPeriodLabel = (p) => {
  return `${p} Performance:`
}

const filteredChartData = computed(() => {
  const allowedPeriods = ['YTD', '1Y', '3Y', '5Y', '10Y', '20Y']
  // Sort according to the allowedPeriods order
  return chartData.value
    .filter(item => allowedPeriods.includes(item.period))
    .sort((a, b) => allowedPeriods.indexOf(a.period) - allowedPeriods.indexOf(b.period))
})
</script>

<template>
  <div class="quartile-report">
    <div v-if="loading" class="state-msg">Loading premium charts...</div>
    <div v-else-if="error" class="state-msg err">{{ error }}</div>
    <div v-else class="charts-container">
      <div class="charts-grid">
        <div v-for="item in filteredChartData" :key="item.period" class="chart-item">
          
          <div class="chart-header-tag">
            <div class="tag-p">{{ getPeriodLabel(item.period) }}</div>
            <div class="tag-s">Quartile Ranking & AUM Contribution</div>
          </div>

          <div class="visual-wrapper">
             <Echarts3DPie :data="getEchartsData(item)" />
          </div>

          <div class="chart-summary">
            {{ item.top_half_summary_pct }} of our funds' {{ item.period }} performance is in 1st and 2nd quartile ranking.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.quartile-report {
  margin-top: 30px;
  background: #fff;
  padding-bottom: 60px;
}

.state-msg { padding: 80px; text-align: center; color: #666; font-size: 15px; }
.state-msg.err { color: #d63031; }

.charts-container {
  max-width: 1450px;
  margin: 0 auto;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 40px 20px;
  padding: 0 20px;
}

.chart-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 10px;
  border-radius: 8px;
}

.chart-header-tag {
  background: #1F4E78;
  color: #fff;
  text-align: center;
  padding: 6px 20px;
  border-radius: 4px;
  margin-bottom: 10px;
  min-width: 240px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.tag-p { font-weight: 700; font-size: 14px; line-height: 1.2; }
.tag-s { font-size: 11px; line-height: 1.2; opacity: 0.9; }

.visual-wrapper {
  width: 100%;
  max-width: 450px;
  height: 250px;
}

.chart-summary {
  margin-top: 10px;
  font-size: 14px;
  font-weight: 500;
  color: #1F4E78;
  text-align: center;
  max-width: 500px;
  line-height: 1.5;
  padding: 0 10px;
}

@media (max-width: 900px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media print {
  .charts-grid {
    display: block !important;
    text-align: center;
  }
  .chart-item {
    display: inline-block !important;
    width: 48% !important;
    vertical-align: top;
    page-break-inside: avoid !important;
    break-inside: avoid !important;
    margin-bottom: 30px !important;
  }
}
</style>
