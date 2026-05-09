<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const props = defineProps({
  asOfDate: {
    type: String,
    default: null
  }
})

const allData   = ref(null)
const loading   = ref(true)
const error     = ref(null)

async function fetchData() {
  loading.value = true
  error.value   = null
  try {
    const url = props.asOfDate ? `/api/lc-meeting/aum-report?as_of_date=${props.asOfDate}` : '/api/lc-meeting/aum-report'
    const res = await fetch(url)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    allData.value = await res.json()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

watch(() => props.asOfDate, fetchData)
onMounted(fetchData)

// ── 日期显示 ──────────────────────────────────────────────────
const displayDate = computed(() => {
  const raw = allData.value?.as_of_date
  if (!raw) return ''
  const d = new Date(raw + 'T00:00:00')
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'numeric', year: 'numeric' })
})

// ── Performance Summary 辅助 ──────────────────────────────────
const PERIODS = ['YTD', '1Y', '3Y', '5Y']

function fmtP(p) {
  if (p === 'YTD') return 'YTD'
  return p.toLowerCase()
}

function getSummaryVal(type, period, field) {
  if (!allData.value?.summary) return null
  const item = allData.value.summary.find(
    s => s.summary_type === type && s.period === period
  )
  return item ? item[field] : null
}

// 图片中的特定高亮逻辑
function isPsHighlighted(type, period, field) {
  if (type !== 'Outperform Benchmark') return false
  if (field === 'pct_no_of_funds') {
    return ['1Y', '3Y', '5Y'].includes(period)
  }
  if (field === 'pct_of_aum') {
    return ['YTD', '1Y', '3Y'].includes(period)
  }
  return false
}

function highlightBg(type, period, field) {
  return {}
}

// ── 基金分组 ──────────────────────────────────────────────────
const largeCapFunds = computed(() =>
  (allData.value?.ratings || []).filter(r => r.aum_category === '> USD 100mil')
)
const midFunds = computed(() =>
  (allData.value?.ratings || []).filter(r => r.aum_category === 'USD 15mil - 100mil')
)
const totalLargeCap = computed(() =>
  largeCapFunds.value.reduce((s, r) => s + (r.aum_usd_mn || 0), 0)
)
const totalMidCap = computed(() =>
  midFunds.value.reduce((s, r) => s + (r.aum_usd_mn || 0), 0)
)

// ── Other Accounts ────────────────────────────────────────────
const otherAccounts = computed(() => allData.value?.other_accounts || [])
const totalOther = computed(() =>
  otherAccounts.value.reduce((s, r) => s + (r.aum_usd_mn || 0), 0)
)
const totalVpAUM = computed(() => totalLargeCap.value + totalMidCap.value + totalOther.value)

const largeCapTotalPct = computed(() => {
  const sum = largeCapFunds.value.reduce((s, r) => {
    const val = parseFloat(r.aum_vp_pct) || 0
    return s + val
  }, 0)
  return sum.toFixed(1) + '%'
})

const midCapTotalPct = computed(() => {
  const sum = midFunds.value.reduce((s, r) => {
    const val = parseFloat(r.aum_vp_pct) || 0
    return s + val
  }, 0)
  return sum.toFixed(1) + '%'
})

// ── 颜色工具 ──────────────────────────────────────────────────
const MS_COLORS = {
  1: { bg: '#009900', color: '#fff' },
  2: { bg: '#C6E0B4', color: '#000' },
  3: { bg: '#fff', color: '#000' },
  4: { bg: '#fff', color: '#000' },
}
function msStyle(rank) {
  if (!rank) return {}
  const c = MS_COLORS[rank]
  return c ? { backgroundColor: c.bg, color: c.color } : {}
}

const BMK_STYLES = {
  'A':      { backgroundColor: '#009644', color: '#fff' },
  'B':      { backgroundColor: '#F4B084', color: '#000' },
  'No BMK': { backgroundColor: '#ffffff', color: '#000' },
  'N/A':    { backgroundColor: '#ffffff', color: '#000' },
}
function bmkStyle(val) {
  return BMK_STYLES[val] || {}
}
function bmkLabel(val) {
  return val || ''
}

function fmtAum(v) {
  if (v == null) return ''
  return Number(v).toLocaleString()
}
</script>

<template>
  <div class="aum-report-page">
    <div v-if="loading" class="state-msg">Loading…</div>
    <div v-else-if="error"  class="state-msg err">{{ error }}</div>

    <div v-else class="report-body">

      <!-- ══ HEADER ══════════════════════════════════════════════ -->
      <div class="report-header">
        <span class="hd-title">Funds Performance &amp; AUM Contribution</span>
        <span class="hd-sep">As of</span>
        <span class="hd-date">{{ displayDate }}</span>
      </div>

      <!-- ══ PERFORMANCE SUMMARY ════════════════════════════════ -->
      <div class="perf-summary">
        <div class="ps-title">Performance Summary</div>
        <table class="ps-table">
          <tbody>
            <!-- Section 1 -->
            <tr>
              <td colspan="4" class="ps-section-label">Funds Ranked in 1st and 2nd Quartile</td>
            </tr>
            <tr>
              <td v-for="p in PERIODS" :key="p + 'no'" class="ps-data-cell">
                {{ fmtP(p) }}: {{ getSummaryVal('Ranked in 1st and 2nd Quartile', p, 'pct_no_of_funds') || 'N/A' }}
                <span class="ps-sub">(No. of Funds)</span>
              </td>
            </tr>
            <tr>
              <td v-for="p in PERIODS" :key="p + 'aum'" class="ps-data-cell">
                {{ fmtP(p) }}: {{ getSummaryVal('Ranked in 1st and 2nd Quartile', p, 'pct_of_aum') || 'N/A' }}
                <span class="ps-sub">(of AUM)</span>
              </td>
            </tr>
            <!-- Section 2 -->
            <tr>
              <td colspan="4" class="ps-section-label ps-outperform-label">Funds Outperform Benchmark</td>
            </tr>
            <tr>
              <td v-for="p in PERIODS" :key="p + 'outno'" class="ps-data-cell" :style="highlightBg('Outperform Benchmark', p, 'pct_no_of_funds')">
                {{ fmtP(p) }}: {{ getSummaryVal('Outperform Benchmark', p, 'pct_no_of_funds') || 'N/A' }}
                <span class="ps-sub">(No. of Funds)</span>
              </td>
            </tr>
            <tr>
              <td v-for="p in PERIODS" :key="p + 'outaum'" class="ps-data-cell" :style="highlightBg('Outperform Benchmark', p, 'pct_of_aum')">
                {{ fmtP(p) }}: {{ getSummaryVal('Outperform Benchmark', p, 'pct_of_aum') || 'N/A' }}
                <span class="ps-sub">(of AUM)</span>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="ps-note">*Note: AUM is the total AUM for the VP's funds with benchmarks</div>
      </div>

      <!-- ══ MAIN TABLE (Funds & Other Accounts) ══════════════ -->
      <table class="fund-table-full">
        <colgroup>
          <col style="width: 30px">
          <col style="width: 260px">
          <col style="width: 150px">
          <col style="width: 150px">
          <col v-for="i in 7" :key="'ms'+i">
          <col style="width: 25px">
          <col v-for="i in 7" :key="'bm'+i">
        </colgroup>

        <template v-for="(group, gi) in [
          { label: 'Funds with AUM > USD 100mil',            funds: largeCapFunds, total: totalLargeCap, totalPct: largeCapTotalPct },
          { label: 'Funds with AUM USD 15 mil - USD 100mil', funds: midFunds,      total: totalMidCap,  totalPct: midCapTotalPct  }
        ]" :key="gi">
          <thead>
            <!-- Section Heading -->
            <tr class="section-header-row"><td colspan="19" class="cat-label">{{ group.label }}</td></tr>
            <tr class="thead-row-1">
              <th rowspan="2">No</th>
              <th rowspan="2" class="th-name">Name</th>
              <th rowspan="2" class="th-aum">AUM*<br>(USDm)</th>
              <th rowspan="2" class="th-pct">% / VP's AUM</th>
              <th colspan="7" class="th-group-ms">Morningstar Ranking: HKSFC Fund Peer Group</th>
              <th rowspan="2" class="th-spacer"></th>
              <th colspan="7" class="th-group-bmk">Performance vs. Benchmark*<br>(Above / Below)</th>
            </tr>
            <tr class="thead-row-2">
              <th v-for="p in ['YTD','1Y','3Y','5Y','10Y','20Y','Since<br>Inception']" :key="p" class="th-sub" :class="{ 'td-l': p.includes('Since') }" v-html="p"></th>
              <th v-for="p in ['YTD','1Y','3Y','5Y','10Y','20Y','SI']" :key="p" class="th-sub">{{ p }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in group.funds" :key="row.id" class="data-row">
              <td class="td-c blue-text">{{ idx + 1 }}</td>
              <td class="td-name-cell blue-text">{{ row.fund_name }}</td>
              <td class="td-c blue-text">{{ fmtAum(row.aum_usd_mn) }}</td>
              <td class="td-c blue-text">{{ row.aum_vp_pct }}</td>
              <!-- MS Ranking -->
              <td class="td-ms" :style="msStyle(row.ms_rank_ytd)">{{ row.ms_rank_ytd ?? '' }}</td>
              <td class="td-ms" :style="msStyle(row.ms_rank_1y)">{{ row.ms_rank_1y ?? '' }}</td>
              <td class="td-ms" :style="msStyle(row.ms_rank_3y)">{{ row.ms_rank_3y ?? '' }}</td>
              <td class="td-ms" :style="msStyle(row.ms_rank_5y)">{{ row.ms_rank_5y ?? '' }}</td>
              <td class="td-ms" :style="msStyle(row.ms_rank_10y)">{{ row.ms_rank_10y ?? '' }}</td>
              <td class="td-ms" :style="msStyle(row.ms_rank_20y)">{{ row.ms_rank_20y ?? '' }}</td>
              <td class="td-ms" :style="msStyle(row.ms_rank_si)">{{ row.ms_rank_si ?? '' }}</td>
              <td class="td-spacer"></td>
              <!-- Performance vs BMK -->
              <template v-if="row.vs_bmk_ytd === 'No BMK'">
                <td colspan="7" class="td-bmk-merged">No BMK</td>
              </template>
              <template v-else>
                <td class="td-bmk" :style="bmkStyle(row.vs_bmk_ytd)">{{ bmkLabel(row.vs_bmk_ytd) }}</td>
                <td class="td-bmk" :style="bmkStyle(row.vs_bmk_1y)">{{ bmkLabel(row.vs_bmk_1y) }}</td>
                <td class="td-bmk" :style="bmkStyle(row.vs_bmk_3y)">{{ bmkLabel(row.vs_bmk_3y) }}</td>
                <td class="td-bmk" :style="bmkStyle(row.vs_bmk_5y)">{{ bmkLabel(row.vs_bmk_5y) }}</td>
                <td class="td-bmk" :style="bmkStyle(row.vs_bmk_10y)">{{ bmkLabel(row.vs_bmk_10y) }}</td>
                <td class="td-bmk" :style="bmkStyle(row.vs_bmk_20y)">{{ bmkLabel(row.vs_bmk_20y) }}</td>
                <td class="td-bmk" :style="bmkStyle(row.vs_bmk_si)">{{ bmkLabel(row.vs_bmk_si) }}</td>
              </template>
            </tr>
            <!-- Total row -->
            <tr class="total-row">
              <td></td>
              <td class="total-label bl">Total</td>
              <td class="total-val td-r">{{ fmtAum(group.total) }}</td>
              <td class="total-val td-c">{{ group.totalPct }}</td>
              <td colspan="15"></td>
            </tr>
          </tbody>
        </template>

        <!-- ══ OTHER ACCOUNTS Section ══ -->
        <thead class="thead-other">
          <tr>
            <th colspan="2" class="td-l">Other Accounts</th>
            <th class="td-l">AUM (USDm)</th>
            <th colspan="16"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(acc, idx) in otherAccounts" :key="acc.account_name" 
              class="row-other">
            <td class="td-c blue-text">{{ idx + 1 }}</td>
            <td class="td-name-cell blue-text">{{ acc.account_name }}</td>
            <td class="td-c blue-text">{{ fmtAum(acc.aum_usd_mn) }}</td>
            <td colspan="16" class="o-remark">{{ acc.remarks || '' }}</td>
          </tr>
          <tr class="other-total-summary">
            <td></td>
            <td class="total-label-other" style="border-bottom: 1px solid #000 !important; border-top: 1px solid #000 !important;">Total</td>
            <td class="total-val-other td-r" style="border-bottom: 1px solid #000 !important; border-top: 1px solid #000 !important;">{{ fmtAum(totalOther) }}</td>
            <td style="border-bottom: 1px solid #000 !important; border-top: 1px solid #000 !important;"></td>
            <td colspan="15"></td>
          </tr>
          <tr class="other-total-summary">
            <td></td>
            <td class="total-label-other">VP's Total AUM (After Net off)</td>
            <td class="total-val-other td-r" style="border-bottom: 1px solid #000 !important;"><strong>{{ fmtAum(totalVpAUM) }}</strong></td>
            <td colspan="16"></td>
          </tr>
        </tbody>
      </table>

      <!-- ══ FOOTNOTES ══════════════════════════════════════════ -->
      <div class="aum-footnotes">
        <p>1 For Value Partners Health care Fund, here it is using the EAA OE Sector Equity Healthcare peer group(Investment area=China).</p>
        <p>2 All fund and benchmark are converted into common currency return in measuring peer group ranking</p>
      </div>

    </div><!-- /report-body -->
  </div><!-- /aum-report-page -->
</template>

<style scoped>
/* ── 全局容器 ─────────────────────────────────────────────────── */
.aum-report-page {
  font-family: 'Calibri', 'Arial', sans-serif;
  font-size: 14px;
  color: #000;
  background: #fff;
  padding: 0px;
  margin-top: 30px;
}

.state-msg { padding: 20px; text-align: center; color: #666; }
.state-msg.err { color: #c0392b; }

/* ── 报告标题行 ── */
.report-header {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #1F4E78;
  color: #fff;
  padding: 5px 10px;
  font-weight: 700;
  font-size: 14px;
  margin-bottom: 6px;
}
.hd-title { flex: 1; }
.hd-sep   { font-weight: 400; font-size: 14px; }
.hd-date  { font-weight: 700; font-size: 14px; }

/* ── Performance Summary 表格布局 ── */
.perf-summary {
  margin-bottom: 2px;
}
.ps-title {
  font-weight: 700;
  font-size: 14px;
  color: #1F4E78;
  margin-bottom: 2px;
  text-align: left;
}
.ps-table {
  border-collapse: collapse;
  width: 50%;
  table-layout: fixed;
  margin-left: 20px; /* 标题缩进 */
}
.ps-section-label {
  font-weight: 700;
  font-size: 14px;
  color: #1F4E78;
  text-align: left;
  padding: 4px 0 2px 20px; /* 再次缩进 */
}
.ps-outperform-label {
  color: #1F4E78; /* 统一颜色，图片中颜色较深 */
}
.ps-data-cell {
  text-align: right; /* 数据列右对齐 */
  padding: 1px 15px 1px 0;
  white-space: nowrap;
  font-size: 14px;
  font-family: inherit;
  color: #1F4E78;
}
.ps-sub {
  font-size: 14px;
  color: #1F4E78;
}
.ps-note {
  font-size: 12px;
  color: #1F4E78;
  margin-top: 4px;
  font-style: italic;
  padding-left: 0;
}

/* ── 分组标签 ── */
.cat-label {
  font-weight: 700;
  font-size: 14px;
  color: #1F4E78;
  margin-top: 2px;
}

/* ── 统一表格 (100%) ── */
.fund-table-full {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  table-layout: fixed;
}
.fund-table-full th,
.fund-table-full td {
  border: 1px solid #000;
  padding: 2px 4px;
  vertical-align: middle;
}

.th-spacer { border-top: none !important; border-bottom: none !important; background: #fff !important; }
.td-spacer { border-top: none !important; border-bottom: none !important; border-left: 1px solid #000; border-right: 1px solid #000; background: #fff; }

.td-bmk-merged {
  text-align: center;
  font-weight: 700;
  font-size: 14px;
  background-color: #ffffff;
}

/* ── 表头 ── */
.thead-row-1 th,
.thead-row-2 th {
  background: #1F4E78;
  color: #fff;
  text-align: center;
  font-weight: 700;
  font-size: 14px;
}
.th-group-ms,
.th-group-bmk {
  text-align: center;
  font-size: 14px;
}
.th-group-bmk small { font-size: 12px; font-weight: 400; }
.th-sub { width: 28px; }

/* ── 数据单元格 ── */
.data-row td { background: #fff; }
.td-c  { text-align: center; }
.td-l  { text-align: left !important; }
.td-r  { text-align: right; }
.blue-text { color: #1e3a8a !important; }
.td-name-cell {
  white-space: nowrap;
  font-size: 14px;
  text-align: left;
  padding-left: 8px;
}

/* ── Morningstar 数字格 ── */
.td-ms {
  text-align: center;
  font-weight: 700;
  font-size: 14px;
  width: 28px;
}

/* ── vs Benchmark 字母格 ── */
.td-bmk {
  text-align: center;
  font-weight: 700;
  font-size: 14px;
  width: 28px;
}

/* ── Total 行 ── */
.total-row td {
  background: #fff;
  border: none;
  padding: 2px 4px;
}
.total-label {
  font-weight: 700;
  text-align: left;
  font-size: 14px;
  border-bottom: 2px solid #000 !important;
}
.total-val {
  font-weight: 700;
  border-bottom: 2px solid #000 !important;
}

/* ── Table Row Spacing ── */
.group-spacer-row td {
  height: 20px;
  border: none !important;
  background: #fff;
}
.section-header-row td {
  border: none !important;
  padding: 0px 0 2px 0;
  background: #fff;
}
/* ══ OTHER ACCOUNTS Özel Stillendirme ══ */
.thead-other th {
  background: #fff !important;
  color: #000 !important;
  font-weight: bold !important;
  border: none !important;
  text-align: left !important;
  padding: 0px 0 2px 0 !important;
}
.thead-other .td-r { text-align: right !important; padding-right: 8px !important; }

.row-other td {
  border: none !important;
  background: #fff !important;
  padding: 4px 8px !important;
}

.other-total-summary td {
  border: none !important;
  background: #fff !important;
  padding: 4px 8px !important;
}

.total-label-other {
  font-weight: bold;
  border-bottom: 1px solid #000 !important;
  text-align: left;
}

.total-val-other {
  font-weight: bold;
  border-bottom: 1px solid #000 !important;
  text-align: right;
}

.o-remark {
  color: #000;
  font-size: 14px;
  text-align: left;
}

/* ── 注脚 ── */
.aum-footnotes {
  margin-top: 15px;
  font-size: 14px;
  color: #000;
  line-height: 1.6;
}
.aum-footnotes p { margin: 1px 0; }
</style>
