<script setup>
import { ref, onMounted, computed } from 'vue'
import ReportLcMeetingAUM from './ReportLcMeetingAUM.vue'
import ReportLcMeetingQuartile from './ReportLcMeetingQuartile.vue'
import LCNoteEditor from './LCNoteEditor.vue'

const loading = ref(true)
const error = ref(null)
const allRows = ref([])
const asOfDate = ref('')

// ── 分离数据行和汇总行 ──────────────────────────────────────────
const fundRows = computed(() =>
  allRows.value.filter(r => r.fund_code && r.fund_code.trim() !== '')
)

const totalFundsRow = computed(() =>
  allRows.value.find(r => r.fund_name && r.fund_name.includes("Total Funds"))
)

const totalVPRow = computed(() =>
  allRows.value.find(r => r.fund_name && r.fund_name.includes("Total VP"))
)

// ── 格式化 AUM ──────────────────────────────────────────────────
function fmtAum(val) {
  if (val == null) return '-'
  return Number(val).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

function fmtPct(val) {
  if (val == null) return '-'
  const n = parseFloat(val) * 100
  return n.toFixed(1) + '%'
}

// ── 报告日期格式 ────────────────────────────────────────────────
const displayDate = computed(() => {
  if (!asOfDate.value) return ''
  const d = new Date(asOfDate.value)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
})

// ── 数值颜色：负数红色，正数蓝色；空值灰底 ─────────────────────
function perfClass(val) {
  if (val == null || val === '') return ''
  const n = parseFloat(val)
  if (isNaN(n)) return ''
  return n <= 0 ? 'neg' : n > 0 ? 'pos' : ''
}

function excessClass(val) {
  if (val == null || val === '') return ''
  const n = parseFloat(val)
  if (isNaN(n)) return ''
  return n <= 0 ? 'neg' : n > 0 ? 'pos' : ''
}

// 空值返回灰底 class
function nullBgClass(val) {
  return (val == null || val === '') ? 'null-bg' : ''
}

// 去掉前缀 + 号（后端返回的小数包含+号）
function stripPlus(val) {
  if (val == null) return ''
  return String(val).replace('+', '')
}

// 解析 URL 参数，支持基于 date 的全局数据查询
const urlParams = new URLSearchParams(window.location.search)
const targetDate = urlParams.get('date')

// ── 分析师注释 ──────────────────────────────────────────────────
const noteReportId  = ref(null)
const noteStatus    = ref('')
const analystNote   = ref('')
const faFileId      = ref(null)
const showEditor    = ref(false)

const isArchived    = computed(() => noteStatus.value === 'ARCHIVED')
const hasNote       = computed(() => !!analystNote.value && analystNote.value !== '<p><br></p>')
// 将原始 \n 转为 <br>，确保 HTML 渲染时保留忌行
const renderedNote  = computed(() =>
  (analystNote.value || '').replace(/\n/g, '<br>')
)

async function fetchNote(date) {
  if (!date) return
  try {
    const res  = await fetch(`/api/lc-report/note?date=${date}`)
    const json = await res.json()
    if (json.success) {
      noteReportId.value = json.report_id
      noteStatus.value   = json.status
      analystNote.value  = json.analyst_note || ''
      faFileId.value     = json.fa_file_id
    }
  } catch { /* ignore */ }
}

function openEditor() {
  if (isArchived.value) return
  showEditor.value = true
}

function onNoteSaved(html) {
  analystNote.value = html
  showEditor.value  = false
}

// ── 加载数据 ────────────────────────────────────────────────────
async function fetchData() {
  loading.value = true
  error.value = null
  try {
    let url = '/api/lc-meeting/fund-performance'
    if (targetDate) {
      url += `?as_of_date=${targetDate}`
    }
    const res = await fetch(url)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    allRows.value = data
    if (data.length > 0) asOfDate.value = data[0].as_of_date
    else if (targetDate) asOfDate.value = targetDate
    // 同步加载注释
    const noteDate = targetDate || (data[0]?.as_of_date)
    if (noteDate) fetchNote(noteDate)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<template>
  <div class="lc-report-page">
    <!-- ── 加载 / 错误状态 ─────────────────────── -->
    <div v-if="loading" class="state-overlay">
      <div class="spinner"></div>
      <span>Loading report data…</span>
    </div>
    <div v-else-if="error" class="state-overlay error">
      <span>⚠ Failed to load: {{ error }}</span>
    </div>

    <!-- ── 报告主体 ─────────────────────────────── -->
    <div v-else class="report-body">

      <!-- ── 主表格 ─────────────────────────────── -->
      <div class="table-wrapper">
        <table class="perf-table">
          <!-- ===== COLGROUP ===== -->
          <colgroup>
            <col class="col-no">
            <col class="col-code">
            <col class="col-name">
            <col class="col-bm">
            <col class="col-aum-usd">
            <col class="col-aum-pct">
            <!-- YTD -->
            <col><col><col>
            <!-- 1Y -->
            <col><col><col>
            <!-- 3Y -->
            <col><col><col>
            <!-- 5Y -->
            <col><col><col>
            <!-- 10Y -->
            <col><col><col>
            <!-- 20Y -->
            <col><col><col>
            <!-- Since Inc -->
            <col><col><col>
            <col class="col-inc-date">
          </colgroup>

          <!-- ===== HEADER ===== -->
          <thead>
            <tr class="hdr-row-0">
              <th style="background-color: #fff;"></th>
              <th style="background-color: #fff; color: #1e3a8a; font-weight: normal;">As of: </th>
              <th style="background-color: #fff; color: #1e3a8a; font-weight: bold;">{{ displayDate }}</th>
              <th style="background-color: #fff;"></th>
              <th colspan="2" style="background-color: #fff;"></th>
              <th colspan="21" style="background-color: #1F4E78; color: #ffffff; font-weight: bold;">Performance as of {{ displayDate }} (All fund and benchmark are converted into USD return)</th>
              <th rowspan="4" class="th-inc-date" style="background-color: #A9D08E; color: #000000; font-weight: bold;">Inception<br>Date</th>
            </tr>
            <tr class="hdr-row-1">
              <th rowspan="3" class="th-no">No</th>
              <th rowspan="3" class="th-code">Fund<br>Code</th>
              <th rowspan="3" class="th-name">Fund Name</th>
              <th rowspan="3" class="th-bm">Benchmark</th>
              <th colspan="2" class="th-group">AUM as of {{ displayDate }}</th>
              <th colspan="3" class="th-group th-ytd">YTD</th>
              <th colspan="3" class="th-group th-1y">1Y</th>
              <th colspan="3" class="th-group th-ann">Annualized 3Y</th>
              <th colspan="3" class="th-group th-ann">Annualized 5Y</th>
              <th colspan="3" class="th-group th-ann">Annualized 10Y</th>
              <th colspan="3" class="th-group th-ann">Annualized 20Y</th>
              <th colspan="3" class="th-group th-since">Since Inception<br>(Annualized)*</th>
            </tr>
            <tr class="hdr-row-2">
              <th class="th-sub">USD</th>
              <th class="th-sub">% VP's</th>
              <th class="th-sub">Fund</th>
              <th class="th-sub">BM</th>
              <th class="th-sub">Excess</th>
              <th class="th-sub">Fund</th>
              <th class="th-sub">BM</th>
              <th class="th-sub">Excess</th>
              <th class="th-sub">Fund</th>
              <th class="th-sub">BM</th>
              <th class="th-sub">Excess</th>
              <th class="th-sub">Fund</th>
              <th class="th-sub">BM</th>
              <th class="th-sub">Excess</th>
              <th class="th-sub">Fund</th>
              <th class="th-sub">BM</th>
              <th class="th-sub">Excess</th>
              <th class="th-sub">Fund</th>
              <th class="th-sub">BM</th>
              <th class="th-sub">Excess</th>
              <th class="th-sub">Fund</th>
              <th class="th-sub">BM</th>
              <th class="th-sub">Excess</th>
            </tr>
          </thead>

          <!-- ===== BODY ===== -->
          <tbody>
            <tr
              v-for="(row, idx) in fundRows"
              :key="row.id"
              class="data-row"
            >
              <td class="td-center">{{ idx + 1 }}</td>
              <td class="td-code">{{ row.fund_code }}</td>
              <td class="td-name">{{ row.fund_name }}</td>
              <td class="td-bm">{{ row.benchmark || '' }}</td>
              <!-- AUM（第5、6列，居中） -->
              <td class="td-num">{{ fmtAum(row.aum_usd_mn) }}</td>
              <td class="td-num">{{ row.aum_vp_pct || '' }}</td>
              <!-- YTD -->
              <td class="td-num" :class="[perfClass(row.ytd_fund), nullBgClass(row.ytd_fund)]">{{ stripPlus(row.ytd_fund) }}</td>
              <td class="td-num" :class="[perfClass(row.ytd_bm), nullBgClass(row.ytd_bm)]">{{ stripPlus(row.ytd_bm) }}</td>
              <td class="td-num" :class="[excessClass(row.ytd_excess), nullBgClass(row.ytd_excess)]">{{ stripPlus(row.ytd_excess) }}</td>
              <!-- 1Y -->
              <td class="td-num" :class="[perfClass(row['1y_fund']), nullBgClass(row['1y_fund'])]">{{ stripPlus(row['1y_fund']) }}</td>
              <td class="td-num" :class="[perfClass(row['1y_bm']), nullBgClass(row['1y_bm'])]">{{ stripPlus(row['1y_bm']) }}</td>
              <td class="td-num" :class="[excessClass(row['1y_excess']), nullBgClass(row['1y_excess'])]">{{ stripPlus(row['1y_excess']) }}</td>
              <!-- 3Y -->
              <td class="td-num" :class="[perfClass(row.ann_3y_fund), nullBgClass(row.ann_3y_fund)]">{{ stripPlus(row.ann_3y_fund) }}</td>
              <td class="td-num" :class="[perfClass(row.ann_3y_bm), nullBgClass(row.ann_3y_bm)]">{{ stripPlus(row.ann_3y_bm) }}</td>
              <td class="td-num" :class="[excessClass(row.ann_3y_excess), nullBgClass(row.ann_3y_excess)]">{{ stripPlus(row.ann_3y_excess) }}</td>
              <!-- 5Y -->
              <td class="td-num" :class="[perfClass(row.ann_5y_fund), nullBgClass(row.ann_5y_fund)]">{{ stripPlus(row.ann_5y_fund) }}</td>
              <td class="td-num" :class="[perfClass(row.ann_5y_bm), nullBgClass(row.ann_5y_bm)]">{{ stripPlus(row.ann_5y_bm) }}</td>
              <td class="td-num" :class="[excessClass(row.ann_5y_excess), nullBgClass(row.ann_5y_excess)]">{{ stripPlus(row.ann_5y_excess) }}</td>
              <!-- 10Y -->
              <td class="td-num" :class="[perfClass(row.ann_10y_fund), nullBgClass(row.ann_10y_fund)]">{{ stripPlus(row.ann_10y_fund) }}</td>
              <td class="td-num" :class="[perfClass(row.ann_10y_bm), nullBgClass(row.ann_10y_bm)]">{{ stripPlus(row.ann_10y_bm) }}</td>
              <td class="td-num" :class="[excessClass(row.ann_10y_excess), nullBgClass(row.ann_10y_excess)]">{{ stripPlus(row.ann_10y_excess) }}</td>
              <!-- 20Y -->
              <td class="td-num" :class="[perfClass(row.ann_20y_fund), nullBgClass(row.ann_20y_fund)]">{{ stripPlus(row.ann_20y_fund) }}</td>
              <td class="td-num" :class="[perfClass(row.ann_20y_bm), nullBgClass(row.ann_20y_bm)]">{{ stripPlus(row.ann_20y_bm) }}</td>
              <td class="td-num" :class="[excessClass(row.ann_20y_excess), nullBgClass(row.ann_20y_excess)]">{{ stripPlus(row.ann_20y_excess) }}</td>
              <!-- Since Inception -->
              <td class="td-num" :class="[perfClass(row.since_inc_fund), nullBgClass(row.since_inc_fund)]">{{ stripPlus(row.since_inc_fund) }}</td>
              <td class="td-num" :class="[perfClass(row.since_inc_bm), nullBgClass(row.since_inc_bm)]">{{ stripPlus(row.since_inc_bm) }}</td>
              <td class="td-num" :class="[excessClass(row.since_inc_excess), nullBgClass(row.since_inc_excess)]">{{ stripPlus(row.since_inc_excess) }}</td>
              <td class="td-center td-inc-date">{{ row.inception_date ?? '' }}</td>
            </tr>
          </tbody>

          <!-- ===== FOOTER: Total rows (改为 tbody 防止打印时每页重复) ===== -->
          <tbody class="totals-body">
            <tr v-if="totalFundsRow" class="total-row">
              <td colspan="2" style="background-color: #fff;"></td>
              <td colspan="2" class="total-label">Total Funds' AUM (USD, million)</td>
              <td class="td-num total-val">{{ fmtAum(totalFundsRow.aum_usd_mn) }}</td>
              <td class="td-num total-val">{{ totalFundsRow.aum_vp_pct || '' }}</td>
              <td colspan="22"></td>
            </tr>
            <tr v-if="totalVPRow" class="total-row total-vp">
              <td colspan="2" style="background-color: #fff;"></td>
              <td colspan="2" class="total-label">Total VP's AUM (USD, million)</td>
              <td class="td-num total-val">{{ fmtAum(totalVPRow.aum_usd_mn) }}</td>
              <td colspan="22"></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ── 注脚 ─────────────────────────────────── -->
      <div class="footnotes">
        <!-- ── 可编辑分析师注释区域 ─────────────────────── -->
        <div
          class="analyst-note-block"
          :class="{ 'archived': isArchived, 'has-content': hasNote }"
          @click="openEditor"
        >
          <!-- 有内容：渲染富文本 -->
          <div v-if="hasNote" class="analyst-note-content" v-html="renderedNote"></div>
          <!-- 无内容：占位符 -->
          <div v-else class="analyst-note-placeholder">
            <span class="placeholder-icon">✏️</span>
            <span>待补充</span>
            <span v-if="!isArchived" class="placeholder-hint">点击编辑注释</span>
          </div>

        </div>

        <!-- 全屏注释编辑器 -->
        <LCNoteEditor
          v-if="showEditor && noteReportId"
          :report-id="noteReportId"
          :fa-file-id="faFileId"
          :initial-note="analystNote"
          @close="showEditor = false"
          @saved="onNoteSaved"
        />
      </div>
    </div>

    <!-- ── 第二份报告：Funds Performance & AUM Contribution ── -->
    <ReportLcMeetingAUM v-if="asOfDate" :asOfDate="targetDate || ''" class="lc-report-section" />

    <!-- ── 第三份报告：Quartile Ranking & AUM Contribution ── -->
    <ReportLcMeetingQuartile v-if="asOfDate" :asOfDate="targetDate || ''" class="lc-report-section" />
  </div>
</template>

<style scoped>
/* ── 页面布局 ──────────────────────────────────────────────────── */
.lc-report-page {
  min-height: 100vh;
  background: #f4f6f9;
  padding: 24px 16px;
  font-family: 'Calibri', 'Arial', sans-serif;
  font-size: 11px;
  color: #1a1a2e;
}

.report-body {
  background: #ffffff;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  overflow: hidden;
}

/* ── 头部 ──────────────────────────────────────────────────────── */
.report-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 10px 16px 8px;
  background: #fff;
  border-bottom: 2px solid #1e5799;
}

.company-brand {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1;
}
.brand-blue { color: #1e5799; }
.brand-red  { color: #c0392b; }

.header-meta {
  margin-top: 4px;
  font-size: 10px;
  color: #555;
}

.header-title {
  text-align: right;
  font-size: 11px;
  font-weight: 600;
  color: #1e3a5f;
  line-height: 1.4;
}
.subtitle {
  font-weight: 400;
  font-size: 9.5px;
  color: #666;
}

/* ── 表格容器 ─────────────────────────────────────────────────── */
.table-wrapper {
  overflow-x: auto;
  padding: 0;
}

/* ── 主表格 ───────────────────────────────────────────────────── */
.perf-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 10px;
  white-space: nowrap;
}

/* 列宽 */
.col-no       { width: 26px; }
.col-code     { width: 44px; }
.col-name     { width: 140px; white-space: normal; }
.col-bm       { width: 160px; white-space: normal; }
.col-aum-usd  { width: 52px; }
.col-aum-pct  { width: 44px; }
.col-inc-date { width: 66px; }

/* ── 表头样式（统一基础） ─────────────────────────────────────── */
thead th {
  background: #1F4E78;
  color: #ffffff;
  text-align: center;
  vertical-align: middle;
  padding: 4px 5px;
  font-weight: 700;
  font-size: 14px;
  line-height: 1.3;
  /* 外框黑色，内垂直隔断白色 */
  border-top: 1px solid #000;
  border-bottom: 1px solid #000;
  border-left: 1px solid #ffffff;
  border-right: 1px solid #ffffff;
}

/* 第一行（hdr-row-0）：无边框、透明背景（行内 style 可覆盖 background） */
.hdr-row-0 th {
  background: transparent;
  color: #1e3a5f;
  border: none !important;
  font-size: 12px;
  font-weight: 600;
  padding: 6px 5px 2px;
}

/* hdr-row-1/2 左右两端的 th 加黑色外框 */
.hdr-row-1 th:first-child,
.hdr-row-2 th:first-child {
  border-left: 1px solid #000;
}
.hdr-row-1 th:last-child,
.hdr-row-2 th:last-child {
  border-right: 1px solid #000;
}

/* 跨行 th（No/Code/Name/BM/IncDate）左右外框也用黑色 */
.th-no, .th-code, .th-name, .th-bm, .th-inc-date {
  background: #1F4E78;
  color: #ffffff;
}
.th-no   { border-left: 1px solid #000 !important; }
.th-inc-date { border-right: 1px solid #000 !important; }

/* 所有分组区块用同一底色 */
.th-group, .th-ytd, .th-1y, .th-ann, .th-since {
  background: #1F4E78;
}


/* ── 数据行 ───────────────────────────────────────────────────── */
tbody tr {
  transition: background 0.15s;
}
tbody tr:hover {
  background: #eaf2ff !important;
}
.data-row td {
  border: 1px solid #000;
  padding: 2px 5px;
  vertical-align: middle;
  color: #1e3a8a;
  font-size: 14px;
}


/* ── 单元格对齐 ───────────────────────────────────────────────── */
.td-center   { text-align: center; }
/* 第5列起均居中 */
.td-num      { text-align: center; font-variant-numeric: tabular-nums; }
.td-code     { text-align: left; font-weight: 700; color: #1e3a8a; }
.td-name     { white-space: normal; word-break: break-word; max-width: 130px; }
.td-bm       { white-space: normal; word-break: break-word; max-width: 100px; font-size: 12px; color: #1e3a8a; }
.td-inc-date { text-align: center; font-size: 12px; white-space: nowrap; font-weight: bold !important; color: #000000 !important; }

/* ── 数值着色：负数红，正数蓝（!important 覆盖 .data-row td 的默认色） ── */
.neg { color: #c0392b !important; }
.pos { color: #1e3a8a !important; }

/* ── 空值单元格粉色背景 ─────────────────────────────────────── */
.null-bg { background-color: #E0E0E0 !important; }

/* ── 合计行（tfoot 完全无边框） ─────────────────────────────── */
tfoot tr {
  border: none;
}
tfoot td {
  border: none !important;
  padding: 3px 5px;
  font-size: 14px;
}
.total-label {
  font-weight: 700;
  color: #000;
  text-align: left;
  padding-left: 0px !important;
  background: transparent;
}
.total-val {
  font-weight: 700;
  text-align: right;
  color: #1e3a8a;
  background: transparent;
}

/* ── 注脚（与 Total Funds 列对齐：跳过前2列的空白宽度） ──────── */
.footnotes {
  /* col-no(26px) + col-code(44px) = 70px 的左缩进，与 Total Funds 列对齐 */
  padding: 0px 16px 16px calc(26px + 44px + 8px);
  color: #1e3a5f;
  font-size: 12px;
  line-height: 1;
}
.note-title {
  font-weight: 600;
  color: #1e3a5f;
  margin-bottom: 3px;
}
.note-link {
  color: #000;
  text-decoration: none;
}
.note-italic {
  color: #1e3a5f;
  margin: 0px 0;
}
.note-italic span {
  display: block;
  margin-bottom: 5px;
}
.note-italic strong {
  color: #000;
}

/* ── 加载 / 错误状态 ─────────────────────────────────────────── */
.state-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  gap: 16px;
  color: #555;
  font-size: 14px;
}
.state-overlay.error { color: #c0392b; }

.spinner {
  width: 36px;
  height: 36px;
  border: 4px solid #d0d8e4;
  border-top-color: #1e5799;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── 分析师注释区域 ──────────────────────────────────────────── */
.analyst-note-block {
  position: relative;
  min-height: 48px;
  border: 2px dashed #b0b8c8;
  border-radius: 4px;
  background: #f5f7fa;
  margin: 4px 0 0;
  padding: 0px 0px 10px 0px;
  cursor: pointer;
  transition: border-color .2s, background .2s;
  font-family: 'Calibri', 'Arial', sans-serif;
  font-size: 12px;
  color: #1e3a5f;
}
.analyst-note-block:not(.archived):hover {
  border-color: #1e5799;
  background: #eef4fb;
}
.analyst-note-block.has-content {
  border-color: transparent;
  background: transparent;
}
.analyst-note-block.archived {
  cursor: default;
  opacity: .85;
}

/* 占位符 */
.analyst-note-placeholder {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #94a3b8;
}
.placeholder-icon { font-size: 14px; }
.placeholder-hint {
  font-size: 11px;
  color: #b0b8c8;
  font-style: italic;
}

/* 编辑角标 */
.edit-badge {
  position: absolute;
  top: 6px;
  right: 8px;
  font-size: 10px;
  background: #1e5799;
  color: #fff;
  padding: 1px 7px;
  border-radius: 8px;
  font-weight: 600;
  pointer-events: none;
  white-space: nowrap;
}

/* 富文本渲染区 */
.analyst-note-content {
  line-height: 1;
  color: #1e3a5f;
}
.analyst-note-content strong { color: #000; }
.analyst-note-content ul { padding-left: 18px; margin: 4px 0; }

@media print {
  .data-row {
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .total-row {
    break-inside: avoid;
    page-break-inside: avoid;
  }
}
</style>
