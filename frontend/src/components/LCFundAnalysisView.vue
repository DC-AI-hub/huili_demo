<template>
  <div class="fa-view">
    <!-- 无数据 -->
    <div v-if="!sheets.length" class="fa-empty">
      <span>暂无 FundAnalysis 解析数据</span>
    </div>

    <template v-else>
      <!-- Sheet 标签栏 -->
      <div class="fa-tabs">
        <button
          v-for="(sheet, idx) in sheets"
          :key="sheet.sheet_name"
          class="fa-tab"
          :class="{ active: activeSheet === idx }"
          @click="activeSheet = idx"
        >{{ sheet.sheet_name }}</button>
      </div>

      <!-- 当前 Sheet 内容 -->
      <div v-if="currentSheet" class="fa-sheet">
        <!-- Meta 信息条 -->
        <div class="fa-meta-bar">
          <div class="fa-meta-item">
            <span class="fa-meta-label">T0 (最新)</span>
            <span class="fa-meta-val">{{ currentSheet.meta_t0?.snapshot_date }}</span>
          </div>
          <div v-if="currentSheet.meta_t1" class="fa-meta-item">
            <span class="fa-meta-label">T1 (上一期)</span>
            <span class="fa-meta-val">{{ currentSheet.meta_t1?.snapshot_date }}</span>
          </div>
          <div class="fa-meta-item">
            <span class="fa-meta-label">Currency</span>
            <span class="fa-meta-val">{{ currentSheet.meta_t0?.currency }}</span>
          </div>
          <div class="fa-meta-item">
            <span class="fa-meta-label">Records</span>
            <span class="fa-meta-val">{{ currentSheet.rows.length }}</span>
          </div>
        </div>

        <!-- 数据表格 -->
        <div class="fa-table-wrap">
          <table class="fa-table">
            <colgroup>
              <col style="min-width:220px;max-width:260px" />
              <col style="width:110px" />
              <col style="width:54px" />
              <col style="width:90px" />
              <!-- period cols: 每个 period 6列 -->
              <template v-for="pt in currentSheet.period_types" :key="pt">
                <col style="width:90px" />
                <col style="width:50px" />
                <col style="width:34px" />
                <col style="width:80px" />
                <col style="width:50px" />
                <col style="width:70px" />
              </template>
            </colgroup>

            <!-- 表头第1行：period 分组 -->
            <thead>
              <tr class="fa-head-1">
                <th rowspan="2" class="ha-left sticky-col">Fund Name</th>
                <th rowspan="2" class="ha-center">ISIN</th>
                <th rowspan="2" class="ha-center">Rating</th>
                <th rowspan="2" class="ha-right">Fund Size</th>
                <th
                  v-for="pt in currentSheet.period_types"
                  :key="pt"
                  colspan="6"
                  class="ha-center period-group-header"
                >
                  {{ pt }}
                  <div class="period-dates">{{ periodDates(pt) }}</div>
                </th>
              </tr>
              <!-- 表头第2行：子列 -->
              <tr class="fa-head-2">
                <template v-for="pt in currentSheet.period_types" :key="pt">
                  <th class="ha-right">Return (Cumulative)</th>
                  <th class="ha-center">Peer group rank</th>
                  <th class="ha-center">Peer group quartile</th>
                  <th class="ha-center sub-wkly">Wkly Rtn</th>
                  <th class="ha-center sub-prev">Previous Wk Ranking</th>
                  <th class="ha-center sub-chg">Δ Rank</th>
                </template>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="row in currentSheet.rows"
                :key="row.entity_name"
                class="fa-row"
              >
                <!-- Fund name -->
                <td class="fa-cell name-cell sticky-col" :title="row.entity_name">
                  {{ row.entity_name }}
                </td>
                <!-- ISIN -->
                <td class="fa-cell isin-cell">{{ row.isin }}</td>
                <!-- Rating：原文字 -->
                <td class="fa-cell ha-center rating-cell">
                  {{ row.morningstar_rating || '' }}
                </td>
                <!-- Fund Size：原始值 -->
                <td class="fa-cell ha-right size-cell">{{ rawVal(row.fund_size) }}</td>

                <!-- Period columns -->
                <template v-for="pt in currentSheet.period_types" :key="pt">
                  <template v-if="row.periods && row.periods[pt]">
                    <!-- Return：原始值 -->
                    <td class="fa-cell ha-right val-cell">
                      {{ rawVal(getPeriodMetric(row.periods[pt], 't0', 'value')) }}
                    </td>
                    <!-- Rank：仅 t0 -->
                    <td
                      class="fa-cell ha-center rank-cell"
                      :class="quartileClass(getPeriodMetric(row.periods[pt], 't0', 'quartile'))"
                    >
                      {{ rawVal(getPeriodMetric(row.periods[pt], 't0', 'rank')) }}
                    </td>
                    <!-- Quartile -->
                    <td
                      class="fa-cell ha-center q-cell"
                      :class="quartileClass(getPeriodMetric(row.periods[pt], 't0', 'quartile'))"
                    >
                      {{ rawVal(getPeriodMetric(row.periods[pt], 't0', 'quartile')) }}
                    </td>
                    <!-- Wkly Rtn = t0_return - t1_return -->
                    <td class="fa-cell ha-center wkly-cell">
                      <span v-if="wklyRtn(row.periods[pt]) !== null" class="wkly-wrap">
                        <span
                          class="wkly-bar"
                          :class="wklyRtn(row.periods[pt]) >= 0 ? 'bar-pos' : 'bar-neg'"
                          :style="{ width: barWidth(wklyRtn(row.periods[pt])) }"
                        ></span>
                        <span class="wkly-num" :class="wklyRtn(row.periods[pt]) >= 0 ? 'pos' : 'neg'">
                          {{ rawVal(wklyRtn(row.periods[pt])) }}
                        </span>
                      </span>
                      <span v-else class="na">—</span>
                    </td>
                    <!-- Prev Rank = t1 rank -->
                    <td class="fa-cell ha-center prev-rank-cell">
                      {{ rawVal(getPeriodMetric(row.periods[pt], 't1', 'rank')) }}
                    </td>
                    <!-- Δ Rank -->
                    <td class="fa-cell ha-center chg-cell">
                      <span
                        v-if="row.periods[pt].rank_change"
                        class="chg-badge"
                        :class="row.periods[pt].rank_change.toLowerCase()"
                      >{{ row.periods[pt].rank_change }}</span>
                      <span v-else class="na">—</span>
                    </td>
                  </template>
                  <template v-else>
                    <td class="fa-cell" colspan="6"></td>
                  </template>
                </template>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  sheets: { type: Array, default: () => [] }
})

const activeSheet = ref(0)
const currentSheet = computed(() => props.sheets[activeSheet.value] ?? null)

// ── 辅助：获取 period 的某个 metric 的某个字段 ──────────────────────────────
// periodObj = { t0: {metric: {value, rank, quartile}}, t1: {...}, ... }
function getSnapMetricObj(periodObj, snapshot) {
  const snap = periodObj?.[snapshot] || {}
  // 优先 return_cumulative, 然后 return_cum, 然后 return_ann, 然后取第一个
  return snap['return_cumulative'] ?? snap['return_cum'] ??
         snap['return_ann'] ?? snap['return_annualized'] ??
         Object.values(snap)[0] ?? null
}

function getPeriodMetric(periodObj, snapshot, field) {
  const obj = getSnapMetricObj(periodObj, snapshot)
  return obj?.[field] ?? null
}

// Wkly Rtn = t0 value - t1 value
function wklyRtn(periodObj) {
  const v0 = getPeriodMetric(periodObj, 't0', 'value')
  const v1 = getPeriodMetric(periodObj, 't1', 'value')
  if (v0 === null || v1 === null) return null
  const n0 = parseFloat(v0), n1 = parseFloat(v1)
  if (isNaN(n0) || isNaN(n1)) return null
  return parseFloat((n0 - n1).toFixed(4))
}

// 原始值展示（不做格式处理，null/undefined 显示 —）
function rawVal(v) {
  if (v === null || v === undefined || v === '') return '—'
  return v
}

// 相对宽度用于 bar（最大 60px 对应 5% 差值，超过 5% 就满格）
function barWidth(v) {
  if (v === null) return '0px'
  const pct = Math.min(Math.abs(parseFloat(v)) / 5, 1) * 60
  return pct.toFixed(1) + 'px'
}

function periodDates(pt) {
  const row = currentSheet.value?.rows?.find(r => r.periods?.[pt])
  if (!row) return ''
  const p = row.periods[pt]
  if (p.start_date && p.end_date) return `${p.start_date} ~ ${p.end_date}`
  if (p.end_date) return `~ ${p.end_date}`
  return ''
}

function quartileClass(q) {
  if (q === null || q === undefined) return ''
  const n = parseInt(q)
  if (n === 1) return 'q1'
  if (n === 2) return 'q2'
  if (n === 3) return 'q3'
  if (n === 4) return 'q4'
  return ''
}
</script>

<style scoped>
/* ── 容器 ───────────────────────────────────────────────────────────── */
.fa-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: #f8fafc;
  font-family: 'Inter', 'Segoe UI', sans-serif;
  font-size: 12px;
}
.fa-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #94a3b8;
  font-size: 14px;
}

/* ── Sheet 标签 ─────────────────────────────────────────────────────── */
.fa-tabs {
  display: flex;
  gap: 4px;
  padding: 8px 12px 0;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
  overflow-x: auto;
}
.fa-tab {
  padding: 6px 14px;
  border: 1px solid transparent;
  border-bottom: none;
  background: #f1f5f9;
  color: #64748b;
  border-radius: 6px 6px 0 0;
  cursor: pointer;
  font-size: 12px;
  white-space: nowrap;
  transition: all .15s;
}
.fa-tab.active {
  background: #fff;
  color: #0f172a;
  border-color: #e2e8f0;
  font-weight: 600;
}

/* ── Meta 信息条 ────────────────────────────────────────────────────── */
.fa-meta-bar {
  display: flex;
  gap: 24px;
  padding: 8px 16px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}
.fa-meta-item { display: flex; align-items: center; gap: 6px; }
.fa-meta-label {
  font-size: 11px; font-weight: 600; color: #64748b;
  text-transform: uppercase; letter-spacing: .04em;
}
.fa-meta-val { font-size: 12px; color: #0f172a; font-weight: 500; }

/* ── 表格容器 ────────────────────────────────────────────────────────── */
.fa-sheet { display: flex; flex-direction: column; flex: 1; overflow: hidden; }
.fa-table-wrap { flex: 1; overflow: auto; }

/* ── 表格 ────────────────────────────────────────────────────────────── */
.fa-table {
  border-collapse: separate;
  border-spacing: 0;
  width: max-content;
  min-width: 100%;
}
.fa-table th, .fa-table td {
  padding: 4px 6px;
  border-right: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
  white-space: nowrap;
}
.fa-table th:last-child, .fa-table td:last-child { border-right: none; }

/* ── 表头 ────────────────────────────────────────────────────────────── */
.fa-head-1 th {
  background: #0f172a;
  color: #fff;
  font-weight: 600;
  font-size: 11px;
  position: sticky;
  top: 0;
  z-index: 3;
  padding: 6px 8px;
}
.fa-head-2 th {
  background: #1e293b;
  color: #cbd5e1;
  font-weight: 500;
  font-size: 10px;
  position: sticky;
  top: 29px;
  z-index: 3;
  padding: 4px 6px;
}
.period-group-header {
  background: #064e3b !important;
  border-left: 2px solid #34d399 !important;
}
.period-dates { font-size: 9px; font-weight: 400; color: #86efac; margin-top: 2px; }
.sub-wkly  { background: #0f3460 !important; color: #93c5fd !important; }
.sub-prev  { background: #1e293b !important; color: #94a3b8 !important; }
.sub-chg   { background: #1e293b !important; color: #94a3b8 !important; }

/* ── 对齐工具 ────────────────────────────────────────────────────────── */
.ha-left   { text-align: left; }
.ha-center { text-align: center; }
.ha-right  { text-align: right; }

/* ── 冻结首列 ────────────────────────────────────────────────────────── */
.sticky-col {
  position: sticky;
  left: 0;
  z-index: 2;
  background: #ffffff;   /* 必须是不透明色，不能用 inherit */
  border-right: 2px solid #cbd5e1 !important;
}
.fa-head-1 .sticky-col { z-index: 4 !important; background: #0f172a; }
.fa-row:nth-child(even) .sticky-col { background: #f8fafc; }
.fa-row:hover .sticky-col { background: #eff6ff !important; }

/* ── 数据行 ──────────────────────────────────────────────────────────── */
.fa-row:nth-child(even) td { background: #f8fafc; }
.fa-row:hover td           { background: #eff6ff !important; }
.fa-cell { font-size: 11.5px; color: #1e293b; vertical-align: middle; }

/* ── 专项列 ──────────────────────────────────────────────────────────── */
.name-cell {
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
}
.isin-cell    { font-size: 10.5px; color: #64748b; letter-spacing: .04em; }
.rating-cell  { font-weight: 600; color: #1e293b; letter-spacing: .04em; }
.size-cell    { color: #475569; }
.val-cell     { font-weight: 500; }
.prev-rank-cell { color: #94a3b8; }
.na           { color: #cbd5e1; }

/* ── Quartile 着色 ───────────────────────────────────────────────────── */
.rank-cell.q1, .q-cell.q1 { background: #dcfce7 !important; color: #166534; font-weight: 700; }
.rank-cell.q2, .q-cell.q2 { background: #d1fae5 !important; color: #065f46; }
.rank-cell.q3, .q-cell.q3 { background: #fef9c3 !important; color: #854d0e; }
.rank-cell.q4, .q-cell.q4 { background: #fee2e2 !important; color: #991b1b; }

/* ── Wkly Rtn 迷你条 ────────────────────────────────────────────────── */
.wkly-cell { padding: 0 6px; }
.wkly-wrap { display: flex; align-items: center; gap: 4px; justify-content: center; }
.wkly-bar  { display: inline-block; height: 10px; border-radius: 2px; flex-shrink: 0; min-width: 2px; }
.bar-pos   { background: #22c55e; }
.bar-neg   { background: #ef4444; }
.wkly-num  { font-size: 11px; font-weight: 500; }
.wkly-num.pos { color: #16a34a; }
.wkly-num.neg { color: #dc2626; }

/* ── 排名变化徽章 ────────────────────────────────────────────────────── */
.chg-badge {
  display: inline-block;
  padding: 1px 7px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 600;
}
.chg-badge.better { background: #dcfce7; color: #166534; }
.chg-badge.same   { background: #f1f5f9; color: #475569; }
.chg-badge.worse  { background: #fee2e2; color: #991b1b; }
</style>
