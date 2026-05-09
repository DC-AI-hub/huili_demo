<script setup>
import { ref } from 'vue'
import ReportAUMFXRate from './ReportAUMFXRate.vue'
import ReportAUMPerformance from './ReportAUMPerformance.vue'

const activeTab = ref('fxrate') // 'fxrate' or 'performance'

const tabs = [
  { id: 'fxrate', label: 'FXrate Current month' },
  { id: 'performance', label: 'official performance' }
]
</script>

<template>
  <div class="aum-report-container">
    <div class="tab-header">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        class="tab-btn"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="tab-content">
      <ReportAUMFXRate v-if="activeTab === 'fxrate'" />
      <ReportAUMPerformance v-if="activeTab === 'performance'" />
    </div>
  </div>
</template>

<style scoped>
.aum-report-container {
  padding: 20px;
  background-color: #f8fafc;
  min-height: 100vh;
}

.tab-header {
  display: flex;
  margin-bottom: 20px;
  border-bottom: 2px solid #e2e8f0;
  background-color: white;
  padding: 10px 20px 0;
  border-radius: 8px 8px 0 0;
}

.tab-btn {
  padding: 12px 24px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  color: #64748b;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
  margin-right: 10px;
}

.tab-btn:hover {
  color: #1e293b;
}

.tab-btn.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
}

.tab-content {
  background-color: white;
  border-radius: 0 0 8px 8px;
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  min-height: 500px;
  overflow: auto;
}
</style>
