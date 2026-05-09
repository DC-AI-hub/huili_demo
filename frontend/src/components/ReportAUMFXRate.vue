<script setup>
import { ref } from 'vue'

const fxData = ref([
  { currency: 'Australian Dollar', current: '1.42745', previous: '1.49959' },
  { currency: 'Hong Kong Dollar', current: '7.80970', previous: '7.78350' },
  { currency: 'New Taiwan Dollar', current: '31.47000', previous: '31.42050' },
  { currency: 'US Dollar', current: '1.00000', previous: '1.00000' },
  { currency: 'Pound Sterling', current: '0.72873', previous: '0.74347' },
  { currency: 'Won', current: '1,439.40000', previous: '1,440.55000' },
  { currency: 'Yen', current: '154.26000', previous: '156.74500' },
  { currency: 'Yuan Renminbi', current: '6.94850', previous: '6.98815' },
  { currency: 'Malaysian Ringgit', current: '3.94200', previous: '4.05800' },
  { currency: 'Offshore Chinese Yuan', current: '6.95130', previous: '6.97995', highlight: true },
])

const marketPriceData = ref([
  { name: 'Australian Dollar (Market Price, USD)', value: '1.42745000' },
  { name: 'Canadian Dollar (Market Price, USD)', value: '1.35415000' },
  { name: 'Euro (Market Price, USD)', value: '0.84058000' },
  { name: 'Hong Kong Dollar (Market Price, USD)', value: '7.80970000' },
  { name: 'New Taiwan Dollar (Market Price, USD)', value: '31.47000000' },
  { name: 'New Zealand Dollar (Market Price, USD)', value: '1.65330000' },
  { name: 'Singapore Dollar (Market Price, USD)', value: '1.26900000' },
  { name: 'US Dollar (Market Price, USD)', value: '1.00000000' },
  { name: 'Pound Sterling (Market Price, USD)', value: '0.72873000' },
  { name: 'Won (Market Price, USD)', value: '1,439.400000' },
  { name: 'Yen (Market Price, USD)', value: '154.260000' },
  { name: 'Yuan Renminbi (Market Price, USD)', value: '6.94850000' },
  { name: 'Malaysian Ringgit (Market Price, USD)', value: '3.94200000' },
  { name: 'Offshore Chinese Yuan', value: '6.95130000', highlight: true },
])
</script>

<template>
  <div class="fx-rate-container">
    <table class="fx-table">
      <thead>
        <tr>
          <td class="label-cell">Date</td>
          <td class="date-val text-bold">2026/1/31</td>
          <td class="date-val text-bold">2025/12/31</td>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in fxData" :key="row.currency">
          <td class="label-cell">{{ row.currency }}</td>
          <td class="val-cell text-bold" :class="{ 'highlight-green': row.highlight }">{{ row.current }}</td>
          <td class="val-cell text-bold" :class="{ 'highlight-green': row.highlight }">{{ row.previous }}</td>
        </tr>
      </tbody>
    </table>

    <div class="spacer"></div>

    <table class="market-price-table">
      <thead>
        <tr>
          <th style="background: white"></th>
          <th class="date-val text-right">2026/1/31</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in marketPriceData" :key="item.name">
          <td class="label-cell">{{ item.name }}</td>
          <td class="val-cell highlight-yellow text-right" :class="{ 'highlight-green-market': item.highlight }">
            {{ item.value }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.fx-rate-container {
  padding: 20px;
  background-color: white;
}

table {
  border-collapse: collapse;
  font-family: 'Times New Roman', Times, serif;
  font-size: 14px;
}

.fx-table td, .fx-table th {
  border: 1px solid #d1d1d1;
  padding: 4px 10px;
}

.market-price-table td, .market-price-table th {
  border: 1px solid #d1d1d1;
  padding: 4px 10px;
}

.label-cell {
  text-align: left;
  width: 250px;
  font-weight: bold;
}

.date-header {
  color: #888;
  font-weight: normal;
  text-align: center;
}

.date-val {
  color: red;
  text-align: center !important;
  font-weight: normal !important;
}

.text-bold {
  font-weight: bold !important;
}

.val-cell {
  color: red;
  text-align: center !important;
  width: 120px;
}

.text-right {
  text-align: right !important;
}

.highlight-green {
  background-color: #c6e0b4 !important;
}

.highlight-green-market {
  background-color: #c6e0b4 !important;
}

.highlight-yellow {
  background-color: #ffff00;
}

.spacer {
  height: 40px;
}

/* Remove default table borders like the image */
.fx-table, .market-price-table {
  border: none;
}
.fx-table td, .fx-table th, .market-price-table td, .market-price-table th {
  border: 0.5px solid #e2e8f0;
}
</style>
