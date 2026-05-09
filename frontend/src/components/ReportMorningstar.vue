<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  console.log("Morningstar report mounted");
})
</script>

<template>
  <div class="generic-report-container">
    <div class="report-wrapper">
      <h1>Morningstar Report</h1>
      <p>This is a placeholder for the Morningstar Report presentation page.</p>
    </div>
  </div>
</template>

<style scoped>
.generic-report-container {
  padding: 40px;
  background-color: #f7fafc;
  min-height: calc(100vh - 100px);
}
.report-wrapper {
  max-width: 950px;
  margin: 0 auto;
  background: white;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  font-family: Arial, sans-serif;
}
h1 {
  color: #2c5282;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 10px;
}
p {
  color: #4a5568;
  font-size: 16px;
  margin-top: 20px;
}
</style>
