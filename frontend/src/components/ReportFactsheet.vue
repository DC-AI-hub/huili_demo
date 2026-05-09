<script setup>
import { ref, onMounted, computed } from 'vue'
import ReportFactsheetPage2 from './ReportFactsheetPage2.vue'

// ── 头部基金信息（从 value_partners_classic_fund_info 表动态获取）──
const fundInfo = ref(null)   // 最新一条记录
const loading  = ref(true)
const error    = ref('')

// 解析 URL 参数，支持基于 date 的全局数据查询
const urlParams = new URLSearchParams(window.location.search)
const targetDate = urlParams.get('date')

onMounted(async () => {
  try {
    let url = '/api/classic/info'
    if (targetDate) {
      url += `?as_of_date=${targetDate}`
    }
    const res = await fetch(url)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const list = await res.json()
    if (list && list.length > 0) {
      if (targetDate) {
        const found = list.find(item => item.as_of_date === targetDate)
        fundInfo.value = found ? found : list[0]
      } else {
        fundInfo.value = list[0]  // 接口已按 as_of_date 倒序，取最新
      }
    } else if (targetDate) {
      fundInfo.value = { as_of_date: targetDate }
    }
  } catch (e) {
    error.value = `数据加载失败：${e.message}`
  } finally {
    loading.value = false
  }
})

/**
 * 从 as_of_date（如 "2026-01-31"）格式化为 "January 2026"
 * 用于报告右侧大字日期显示
 */
const reportMonth = computed(() => {
  if (!fundInfo.value?.as_of_date) return ''
  const dateStr = fundInfo.value.as_of_date
  let d;
  if (dateStr.includes('-')) {
    d = new Date(dateStr + 'T00:00:00')
  } else {
    d = new Date(dateStr)
  }
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
})

/**
 * 格式化为 "As at DD-MM-YYYY" 用于 Morningstar rating 下方小字
 */
const asAtDate = computed(() => {
  if (!fundInfo.value?.as_of_date) return ''
  const dateStr = fundInfo.value.as_of_date
  if (dateStr.includes('-')) {
    const [y, m, d] = dateStr.split('-')
    return `As at ${d}-${m}-${y}`
  } else {
    // 31 Jan 2026 -> 31-01-2026
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return `As at ${dateStr}`
    const day = String(d.getDate()).padStart(2, '0')
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const year = d.getFullYear()
    return `As at ${day}-${month}-${year}`
  }
})

/**
 * 从 nav_a_unit（如 "USD 527.78"）中提取纯数字部分展示
 * 原始值为 "USD 527.78"，保留前缀 "USD"
 */
/**
 * 头部显示去除硬编码规则，直接使用 v-for 遍历 navs 数组
 */
const fundSize = computed(() => fundInfo.value?.fund_size  ?? '-')

// ── 股息分派数据（从 dividend_distribution 表动态获取）──────────────
const dividends = ref([])       // 接口返回的所有派息记录
const divLoading = ref(true)

onMounted(async () => {
  try {
    let url = '/api/dividend'
    if (targetDate) {
      url += `?as_of_date=${targetDate}`
    }
    const res = await fetch(url)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    dividends.value = await res.json()
  } catch (e) {
    console.error('股息数据加载失败：', e)
  } finally {
    divLoading.value = false
  }
})

/**
 * 股息分派数据
 */

// ── 按 fund_class 前缀拆分为 Class C（CM*）和 Class D（DM*）──
// ── 按 fund_class 前缀拆分为 Class C（CM*）和 Class D（DM*）── 
// 使用 backend 的 fund_class_raw 来区分
const classCDividends = computed(() =>
  dividends.value.filter(r => r.fund_class_raw?.startsWith('CM'))
)
const classDDividends = computed(() =>
  dividends.value.filter(r => r.fund_class_raw?.startsWith('DM'))
)
// ── NAV 动态数据（从 value_partners_classic_fund_navs 表）──────────────
const navs = ref([])          // 接口返回的最新一期 NAV 列表

onMounted(async () => {
  try {
    let url = '/api/navs'
    if (targetDate) {
      url += `?as_of_date=${targetDate}`
    }
    const res = await fetch(url)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    navs.value = await res.json()
  } catch (e) {
    console.error('NAV 数据加载失败：', e)
  }
})

/**
 * Map: fund class 名称 → nav 字符串
 * 用于模板中按 class 名称小写匹配
 */
const navMap = computed(() => {
  const m = new Map()
  for (const item of navs.value) {
    m.set(item['class'].toLowerCase().trim(), item.nav)
  }
  return m
})

/** 按 class 名称查 NAV，找不到返回 '-' */
function getNav(cls) {
  return navMap.value.get(cls.toLowerCase().trim()) ?? '-'
}

// ── NAVs & codes 表各行的固定定义（前三列硬编码，NAV 列动态）────────
const NAV_ROWS = [
  { cls: 'Class A USD',             isin: 'HK0000264868', bloomberg: 'VLPARAI HK'  },
  { cls: 'Class B USD',             isin: 'HK0000264876', bloomberg: 'VLPARBI HK'  },
  { cls: 'Class C USD',             isin: 'HK0000264884', bloomberg: 'VLPARCI HK'  },
  { cls: 'Class C HKD³',           isin: 'HK0000264884', bloomberg: 'VLPARCI HK'  },
  { cls: 'Class C RMB',             isin: 'HK0000264926', bloomberg: 'VLCHCRM HK'  },
  { cls: 'Class C AUD Hedged',      isin: 'HK0000264892', bloomberg: 'VLCHAUD HK'  },
  { cls: 'Class C CAD Hedged',      isin: 'HK0000264900', bloomberg: 'VLCHCAD HK'  },
  { cls: 'Class C HKD Hedged',      isin: 'HK0000264934', bloomberg: 'VLCHCHH HK'  },
  { cls: 'Class C NZD Hedged',      isin: 'HK0000264918', bloomberg: 'VLCHNZD HK'  },
  { cls: 'Class C RMB Hedged',      isin: 'HK0000264942', bloomberg: 'VLCHCRH HK'  },
  { cls: 'Class C USD MDis',        isin: 'HK0000360880', bloomberg: 'VLCCMDU HK'  },
  { cls: 'Class C HKD MDis',        isin: 'HK0000360898', bloomberg: 'VLCCMDH HK'  },
  { cls: 'Class C RMB MDis',        isin: 'HK0000362241', bloomberg: 'VLCCMDR HK'  },
  { cls: 'Class C RMB Hedged MDis', isin: 'HK0000362258', bloomberg: 'VLCCMRH HK'  },
]

// ── Performance since launch 图表数据（classic_a_historical 表）─────────────
const chartData    = ref([])
const chartLoading = ref(true)

onMounted(async () => {
  try {
    const res = await fetch('/api/classic/historical')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    chartData.value = await res.json()
  } catch(e) {
    console.error('历史数据加载失败：', e)
  } finally {
    chartLoading.value = false
  }
})

// SVG 布局常量
const SVG_W  = 480
const SVG_H  = 200
const PAD_L  = 46  // y轴标签宽度
const PAD_R  = 62  // 右侧标注宽度
const PAD_T  = 14  // 顶部留白
const PAD_B  = 22  // x轴标签高度
const CW     = SVG_W - PAD_L - PAD_R
const CH     = SVG_H - PAD_T - PAD_B

// 处理原始数据：存储的是倍数（如 36.272 = 3627.2%），乘 100 得百分比展示值
const cPts = computed(() =>
  chartData.value
    .map(d => ({
      year: +d.date.slice(0, 4),
      fv:   d.classic_a_cumulative          != null ? parseFloat(d.classic_a_cumulative)          * 100 : null,
      iv:   d.hang_seng_index_cumulative    != null ? parseFloat(d.hang_seng_index_cumulative)    * 100 : null,
      f_fmt: d.classic_a_cumulative_fmt,
      i_fmt: d.hang_seng_index_cumulative_fmt
    }))
    .filter(d => d.fv !== null)
)

// Y轴最大值（对齐到 800 整数倍）
const cYMax = computed(() => {
  if (!cPts.value.length) return 5600
  const max = Math.max(...cPts.value.map(d => d.fv ?? 0))
  return Math.max(800, Math.ceil(max / 800) * 800)
})

// Y轴刻度
const cYTicks = computed(() => {
  const m = cYMax.value
  const step = m <= 3200 ? 400 : 800
  const t = []
  for (let v = 0; v <= m; v += step) t.push(v)
  return t
})

// SVG 坐标转换
function cSvgY(v)   { return PAD_T + CH - (v / cYMax.value) * CH }
function cSvgX(i)   {
  const n = cPts.value.length
  return n > 1 ? PAD_L + (i / (n - 1)) * CW : PAD_L
}

// 基金折线点位串
const fundLine = computed(() =>
  cPts.value.map((d, i) => `${cSvgX(i)},${cSvgY(d.fv)}`).join(' ')
)

// 指数折线点位串（跳过 null）
const idxLine = computed(() => {
  const pts = []
  cPts.value.forEach((d, i) => {
    if (d.iv !== null) pts.push(`${cSvgX(i)},${cSvgY(d.iv)}`)
  })
  return pts.join(' ')
})

// 最后一点的标注坐标和数值
const lastFundV  = computed(() => { const d = cPts.value; return d.length ? d[d.length-1].fv  : null })
const lastIdxV   = computed(() => { const d = cPts.value; return d.length ? d[d.length-1].iv  : null })
const lastFundFmt= computed(() => { const d = cPts.value; return d.length ? d[d.length-1].f_fmt  : null })
const lastIdxFmt = computed(() => { const d = cPts.value; return d.length ? d[d.length-1].i_fmt  : null })
const lastFundY  = computed(() => lastFundV.value  !== null ? cSvgY(lastFundV.value)  : 0)
const lastIdxY   = computed(() => lastIdxV.value   !== null ? cSvgY(lastIdxV.value)   : 0)
const lastX      = computed(() => PAD_L + CW)

// X轴年份标签
const cXYears = computed(() => {
  const d = cPts.value
  if (!d.length) return []
  const first = d[0].year, last = d[d.length-1].year
  const step = Math.max(2, Math.round((last - first) / 12))
  const yrs = []
  for (let y = first; y <= last; y += step) yrs.push(y)
  if (yrs[yrs.length-1] !== last) yrs.push(last)
  return yrs
})

function yearX(yr) {
  const d = cPts.value
  if (!d.length) return 0
  let idx = d.findIndex(p => p.year >= yr)
  if (idx === -1) idx = d.length - 1
  return cSvgX(idx)
}

// ── 月度业绩表数据（monthly_performance 表）─────────────────
const monthlyRows    = ref([])   // [{ year, jan, feb, ... annual }]
const monthlyLoading = ref(true)

onMounted(async () => {
  try {
    const res = await fetch('/api/classic/monthly')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const fullData = await res.json()
    // 只展示最近 10 年的数据
    monthlyRows.value = fullData.slice(-10)
  } catch(e) {
    console.error('月度数据加载失败：', e)
  } finally {
    monthlyLoading.value = false
  }
})

// ── Performance update 表数据 ───────────────────────────────
const perfUpdateRows = ref([])
const perfUpdateLoading = ref(true)

const PERF_PERIODS = [
  "Year-to-date",
  "One month",
  "One year",
  "Three years",
  "Five years",
  "Total return since launch",
  "Annualized return since launch^"
]

onMounted(async () => {
  try {
    let url = '/api/period-performance'
    if (targetDate) {
      url += `?as_of_date=${targetDate}`
    }
    const res = await fetch(url)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    perfUpdateRows.value = await res.json()
  } catch(e) {
    console.error('Performance update 数据加载失败：', e)
  } finally {
    perfUpdateLoading.value = false
  }
})

function getPerfRow(period) {
  return perfUpdateRows.value.find(r => r.period === period) || {}
}


</script>

<template>
  <div class="report-container">
    <div class="report-wrapper">
      <!-- Header Section -->
      <div class="top-header-row">
        <div class="header-green-box">
          <h1>Value Partners Classic Fund</h1>
          <!-- 加载中 -->
          <div v-if="loading" class="header-stats" style="opacity:0.6;">数据加载中...</div>
          <!-- 加载失败 -->
          <div v-else-if="error" class="header-stats" style="color:#ffcccc;">{{ error }}</div>
          <!-- 正常展示 -->
          <div v-else class="header-stats">
            <div class="stat-line">
              <span class="label">NAV per unit</span>: &nbsp;
              <span v-if="getNav('Class A USD') !== '-'">Class A USD - USD {{ getNav('Class A USD') }}</span>
              <span v-if="getNav('Class B USD') !== '-'"><span class="sep">|</span>Class B USD - USD {{ getNav('Class B USD') }}</span>
              <span v-if="getNav('Class C USD') !== '-'"><span class="sep">|</span>Class C USD - USD {{ getNav('Class C USD') }}</span>
            </div>
            <div class="stat-line" style="margin-top: 2px;">
              <span class="label">Fund size</span>: &nbsp;{{ fundSize }}
            </div>
          </div>
        </div>
        <div class="header-logo-container">
          <svg class="vp-logo-svg" viewBox="0 0 36 48" width="28" height="38">
            <polygon points="0,0 22,0 10,32" fill="#a4b42b"/>
            <polygon points="14,0 36,0 0,48" fill="#0d6b4d"/>
          </svg>
          <div class="vp-logo-text">
            <div class="vp-logo-title">Value<br>Partners</div>
            <div class="vp-logo-since">Since 1993</div>
          </div>
        </div>
      </div>

      <!-- Badges and Date -->
      <div class="badges-section">
        <div class="badges">
          <div class="rating-badge">
            <span class="stars">★★★</span>
            <span class="rating-text">Morningstar Rating™<br><small>{{ asAtDate }}</small></span>
          </div>
          <div class="cies-badge">CIES Eligible <sup>△</sup></div>
        </div>
        <div class="report-date">
          {{ reportMonth }}
        </div>
      </div>

      <!-- Disclaimers / Description list -->
      <div class="disclaimer-list">
        <ul>
          <li>Value Partners Classic Fund (The "Fund") primarily invests in markets of the Asia-Pacific region, with a Greater China focus.</li>
          <li>The Fund invests in China-related companies and emerging markets which involve certain risks not typically associated with investment in more developed markets, such as greater political, tax, economic, foreign exchange, liquidity and regulatory risks.</li>
          <li>The Fund is also subject to concentration risk due to its concentration in Asia-Pacific region, particularly China-related companies. The value of the Fund can be extremely volatile and could go down substantially within a short period of time. It is possible that the entire value of your investment could be lost.</li>
          <li>The Fund may also invest in derivatives which can involve material risks, e.g. counterparty default risk, insolvency or liquidity risk, and may expose the Fund to significant losses.</li>
          <li>In respect of the distribution units for the Fund, the Manager currently intends to make monthly dividend distribution. However, the distribution rate is not guaranteed. Distribution yield is not indicative of the return of the Fund. Distribution may be paid from capital of the Fund. Investors should note that where the payment of distributions are paid out of capital, this represents and amounts to a return or withdrawal of part of the amount you originally invested or capital gains attributable to that and may result in an immediate decrease in the value of units.</li>
          <li>You should not make investment decision on the basis of this material alone. Please read the explanatory memorandum for details and risk factors.</li>
        </ul>
      </div>

      <!-- Main Content 2 Columns -->
      <div class="main-columns">
        <!-- Left Column -->
        <div class="col-left">
          <div class="section">
            <h2>Investment objective</h2>
            <p class="objective-text">The Fund aims to achieve consistent superior returns through an investment discipline that places emphasis on the fundamental value of potential investments, which the Manager believes are being traded at deep discounts to their intrinsic values. The Fund will concentrate on investing in the markets of the Asia Pacific region (particularly in Greater China region) but without fixed geographical, sectoral or industry weightings.</p>
          </div>

          <div class="section">
            <h2>Performance since launch</h2>

            <!-- 无数据 / 加载中 -->
            <div v-if="chartLoading" class="chart-state">加载中...</div>
            <div v-else-if="!cPts.length" class="chart-state">暂无历史数据</div>

            <!-- 动态 SVG 图表 -->
            <svg v-else
              :viewBox="`0 0 ${SVG_W} ${SVG_H}`"
              style="width:100%;overflow:visible;display:block;"
              class="perf-svg">

              <!-- % 标识 -->
              <text :x="PAD_L - 2" :y="PAD_T - 4" font-size="7.5" text-anchor="end" fill="#777">%</text>

              <!-- 水平网格线 + Y轴标签 -->
              <g v-for="tick in cYTicks" :key="tick">
                <line :x1="PAD_L" :x2="PAD_L + CW"
                      :y1="cSvgY(tick)" :y2="cSvgY(tick)"
                      stroke="#e5e5e5" stroke-width="0.5"/>
                <text :x="PAD_L - 3" :y="cSvgY(tick) + 3"
                      font-size="7.5" text-anchor="end" fill="#777">
                  {{ tick.toLocaleString() }}
                </text>
              </g>

              <!-- X轴年份标签 -->
              <text v-for="yr in cXYears" :key="yr"
                :x="yearX(yr)" :y="PAD_T + CH + 14"
                font-size="7.5" text-anchor="middle" fill="#777">{{ yr }}</text>

              <!-- 指数线（灰色） -->
              <polyline v-if="idxLine"
                fill="none" stroke="#999" stroke-width="0.9"
                :points="idxLine"/>

              <!-- 基金线（深绿） -->
              <polyline v-if="fundLine"
                fill="none" stroke="#1a5e35" stroke-width="1.6"
                stroke-linejoin="round" stroke-linecap="round"
                :points="fundLine"/>

              <!-- 最后一个点的右侧标注 -->
              <text v-if="lastFundFmt !== null"
                :x="lastX + 4" :y="lastFundY + 3"
                font-size="8" fill="#1a5e35" font-weight="bold">{{ lastFundFmt }}</text>
              <text v-if="lastIdxFmt !== null"
                :x="lastX + 4" :y="lastIdxY + 3"
                font-size="8" fill="#777">{{ lastIdxFmt }}</text>

              <!-- 图例（图表内左上角） -->
              <g :transform="`translate(${PAD_L + 6}, ${PAD_T + 5})`">
                <line x1="0" y1="4" x2="18" y2="4" stroke="#1a5e35" stroke-width="1.6"/>
                <text x="22" y="8" font-size="8" fill="#333">The Fund (Class A USD)</text>
                <line x1="0" y1="16" x2="18" y2="16" stroke="#999" stroke-width="0.9"/>
                <text x="22" y="20" font-size="8" fill="#333">Index¹</text>
              </g>
            </svg>
          </div>

          <!-- Performance update 在左列 -->
          <div class="section performance-update" style="margin-top: 25px;">
            <h2>Performance update</h2>
            <table class="data-table full-width bordered-rows">
              <thead>
                <tr>
                  <th></th>
                  <th class="center-align">Class A<br>USD</th>
                  <th class="center-align">Class B<br>USD</th>
                  <th class="center-align">Class C<br>USD</th>
                  <th class="center-align border-left-col">Index ¹</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="perfUpdateLoading">
                  <td colspan="5" style="text-align:center;color:#aaa;padding:8px;">加载中...</td>
                </tr>
                <tr v-else-if="perfUpdateRows.length === 0">
                  <td colspan="5" style="text-align:center;color:#aaa;padding:8px;">暂无数据</td>
                </tr>
                <tr v-else v-for="period in PERF_PERIODS" :key="period">
                  <td>{{ period }}</td>
                  <td class="center-align">{{ getPerfRow(period).a_unit }}</td>
                  <td class="center-align">{{ getPerfRow(period).b_unit }}</td>
                  <td class="center-align">{{ getPerfRow(period).c_unit }}</td>
                  <td class="center-align border-left-col">{{ getPerfRow(period).a_unit_hang_seng_index }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Right Column：NAV + Class C MDis + Class D MDis 上下堆叠 -->
        <div class="col-right">
          <div class="section">
            <h2>NAVs & codes</h2>
            <table class="data-table">
              <thead>
                <tr>
                  <th>Classes²</th>
                  <th>NAV</th>
                  <th>ISIN</th>
                  <th>Bloomberg</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in NAV_ROWS" :key="row.cls">
                  <td>{{ row.cls }}</td>
                  <td>{{ getNav(row.cls) }}</td>
                  <td>{{ row.isin }}</td>
                  <td>{{ row.bloomberg }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Class C MDis 股息表 -->
          <div class="section" style="margin-top: 25px;">
            <h2>Dividend information – Class C MDis ⁴</h2>
            <table class="data-table">
              <thead>
                <tr>
                  <th>Classes²</th>
                  <th>Dividend<br>per unit</th>
                  <th>Annualized<br>yield</th>
                  <th>Ex-dividend<br>date</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="divLoading">
                  <td colspan="4" style="text-align:center;color:#aaa;padding:8px;">加载中...</td>
                </tr>
                <tr v-else-if="classCDividends.length === 0">
                  <td colspan="4" style="text-align:center;color:#aaa;padding:8px;">暂无数据</td>
                </tr>
                <tr v-else v-for="row in classCDividends" :key="row.id">
                  <td>{{ row.fund_class }}</td>
                  <td>{{ row.dividend_per_unit }}</td>
                  <td>{{ row.annualized_yield }}</td>
                  <td>{{ row.ex_date }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Class D MDis 股息表 -->
          <div class="section" style="margin-top: 18px;">
            <h2>Dividend information – Class D MDis ⁴</h2>
            <table class="data-table">
              <thead>
                <tr>
                  <th>Classes²</th>
                  <th>Dividend<br>per unit</th>
                  <th>Annualized<br>yield</th>
                  <th>Ex-dividend<br>date</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="divLoading">
                  <td colspan="4" style="text-align:center;color:#aaa;padding:8px;">加载中...</td>
                </tr>
                <tr v-else-if="classDDividends.length === 0">
                  <td colspan="4" style="text-align:center;color:#aaa;padding:8px;">暂无数据</td>
                </tr>
                <tr v-else v-for="row in classDDividends" :key="row.id">
                  <td>{{ row.fund_class }}</td>
                  <td>{{ row.dividend_per_unit }}</td>
                  <td>{{ row.annualized_yield }}</td>
                  <td>{{ row.ex_date }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div> <!-- /Main Columns -->

      <!-- Monthly performance -->
      <div class="section monthly-performance" style="margin-top:25px;">
        <h2>The Fund – Class A USD: Monthly performance</h2>
        <table class="data-table full-width dense striped bordered-table">
          <thead>
            <tr>
              <th>Year</th>
              <th>Jan</th><th>Feb</th><th>Mar</th><th>Apr</th><th>May</th><th>Jun</th>
              <th>Jul</th><th>Aug</th><th>Sep</th><th>Oct</th><th>Nov</th><th>Dec</th>
              <th class="bg-gray">Annual</th>
            </tr>
          </thead>
          <tbody>
            <!-- 加载中 -->
            <tr v-if="monthlyLoading">
              <td colspan="14" style="text-align:center;color:#aaa;padding:8px;">加载中...</td>
            </tr>
            <!-- 无数据 -->
            <tr v-else-if="monthlyRows.length === 0">
              <td colspan="14" style="text-align:center;color:#aaa;padding:8px;">暂无数据</td>
            </tr>
            <!-- 动态行：最后一年标注 (YTD) -->
            <tr v-else v-for="row in monthlyRows" :key="row.year">
              <td>{{ row.year === monthlyRows[monthlyRows.length-1].year && row.annual != null ? row.year + ' (YTD)' : row.year }}</td>
              <td>{{ row.jan }}</td>
              <td>{{ row.feb }}</td>
              <td>{{ row.mar }}</td>
              <td>{{ row.apr }}</td>
              <td>{{ row.may }}</td>
              <td>{{ row.jun }}</td>
              <td>{{ row.jul }}</td>
              <td>{{ row.aug }}</td>
              <td>{{ row.sep }}</td>
              <td>{{ row.oct }}</td>
              <td>{{ row.nov }}</td>
              <td>{{ row.dec }}</td>
              <td class="bg-gray">{{ row.annual }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div class="disclaimers-footer">
        <small>
          △ The Fund is one of the eligible collective investment schemes for the purpose of the New Capital Investment Entrant Scheme (New CIES) in Hong Kong with effect from 1 March 2024.<br>
          ^ Annualized return is calculated from inception based on published NAV.
        </small>
      </div>

      <!-- Footer Information -->
      <footer class="report-footer">
        <div class="footer-contact">
          43rd Floor, The Center, 99 Queen's Road Central, Hong Kong | www.valuepartners-group.com<br>
          Hotline: Hong Kong (852) 2143 0688 | Singapore (65) 6718 0380 | Email: fis@vp.com.hk
        </div>
        <div class="footer-social">
          Follow us on 
          <span class="social-icon">f</span>
          <span class="social-icon">▶</span>
          <span class="social-icon">in</span>
          <div style="display: flex; align-items: flex-end; margin-left: -3px;">
            <span class="social-icon wechat">💬</span>
            <strong style="color: #0d6b4d; font-size: 8px; margin-left: 3px; line-height: 1; margin-bottom: 1px;">惠理集团</strong>
          </div>
        </div>
      </footer>
    </div>

    <!-- Page 2 -->
    <ReportFactsheetPage2 :report-month="reportMonth" :as-at-date="asAtDate" />
    
  </div>
</template>

<style scoped>
.report-wrapper {
  max-width: 950px;
  margin: 30px auto;
  background: white;
  padding: 40px;
  font-family: Arial, Helvetica, sans-serif;
  color: #333;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  font-size: 11.5px;
  line-height: 1.4;
}

/* 图表加载/空状态 */
.chart-state {
  text-align: center;
  color: #aaa;
  padding: 48px 0;
  font-size: 11px;
}

/* SVG 图表 */
.perf-svg {
  overflow: visible;
  margin-top: 6px;
}

.top-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.header-green-box {
  background-color: #0b6748;
  color: white;
  padding: 16px 20px 18px;
  flex: 1;
  margin-right: 35px;
}

.header-green-box h1 {
  margin: 0 0 10px 0;
  font-size: 26px;
  font-weight: bold;
  letter-spacing: 0.2px;
}

.header-stats {
  font-size: 11px;
  font-weight: 700;
}

.stat-line {
  line-height: 1.4;
}

.stat-line .label {
  display: inline-block;
  width: 75px;
}

.stat-line .sep {
  opacity: 0.7;
  margin: 0 6px;
  font-weight: normal;
}

.header-logo-container {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.vp-logo-svg {
  margin-right: 12px;
}

.vp-logo-text {
  display: flex;
  flex-direction: column;
}

.vp-logo-title {
  color: #1a2a3a;
  font-size: 19px;
  font-weight: 800;
  line-height: 1;
  font-family: Arial, sans-serif;
  letter-spacing: -0.5px;
}

.vp-logo-since {
  color: #333;
  font-size: 8.5px;
  margin-top: 4px;
  font-family: Arial, sans-serif;
  font-style: italic;
  font-weight: bold;
}

.badges-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding: 10px 0;
}

.badges {
  display: flex;
  align-items: center;
  gap: 15px;
}

.rating-badge {
  color: #c00;
  text-align: center;
  line-height: 1.2;
}

.rating-badge .stars {
  font-size: 16px;
  letter-spacing: 2px;
  display: block;
}

.rating-badge .rating-text {
  font-size: 9px;
  color: #666;
}

.cies-badge {
  border: 1px solid #0d6b4d;
  color: #0d6b4d;
  font-weight: bold;
  padding: 3px 8px;
  font-size: 11px;
}

.report-date {
  font-size: 22px;
  font-weight: normal;
  color: #555;
}

.disclaimer-list {
  border: 1px solid #0d6b4d;
  padding: 8px 15px 8px 25px;
  margin-bottom: 25px;
}

.disclaimer-list ul {
  margin: 0;
  padding: 0;
  font-size: 9.5px;
  color: #444;
}

.disclaimer-list li {
  margin-bottom: 4px;
  text-align: justify;
}

.main-columns {
  display: flex;
  gap: 30px;
  margin-bottom: 25px;
}

.col-left { flex: 1.1; }
.col-right { flex: 0.9; }

h2 {
  color: #0d6b4d;
  font-size: 15px;
  font-weight: 700;
  border-bottom: 2px solid #a3d900;
  padding-bottom: 3px;
  margin-bottom: 10px;
  margin-top: 0;
}

.objective-text {
  font-size: 11.5px;
  text-align: justify;
  margin-bottom: 25px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 10.5px;
}

.data-table th {
  border-bottom: 1px solid #333;
  text-align: left;
  padding: 5px 2px;
  font-weight: normal;
  color: #555;
  vertical-align: bottom;
}

.data-table td {
  border-bottom: 1px solid #ccc;
  padding: 5px 2px;
}

.bordered-rows td {
  border-bottom: 1px solid #ddd;
}
.bordered-rows th, .bordered-table th {
  border-bottom: 2px solid #333;
  border-top: 2px solid #333;
}
.bordered-table {
  border-bottom: 2px solid #333;
}

.border-left-col {
  border-left: 1px solid #aaa;
}

.center-align {
  text-align: center !important;
}

.bg-gray {
  background-color: #eee;
  font-weight: bold;
}

.full-width {
  width: 100%;
}

.dense td, .dense th {
  padding: 4px 5px;
  text-align: center;
}

.dense td:first-child, .dense th:first-child {
  text-align: left;
}

.striped tbody tr:nth-child(even) {
  background-color: #f7f7f7;
}

.chart-placeholder {
  position: relative;
  height: 220px;
  margin-top: 30px;
  border-left: 1px solid #666;
  border-bottom: 1px solid #666;
  margin-left: 35px;
  margin-bottom: 25px;
}

.chart-y-axis {
  position: absolute;
  left: -40px;
  top: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  text-align: right;
  font-size: 10px;
  width: 35px;
  color: #555;
}

.chart-y-axis span::after {
  content: '';
  position: absolute;
  right: -5px;
  width: 5px;
  height: 1px;
  background-color: #666;
}

.chart-area {
  position: relative;
  width: 100%;
  height: 100%;
}

.chart-line-main { stroke: #0d6b4d; stroke-width: 1.5; }
.chart-line-index { stroke: #888; stroke-width: 1; stroke-dasharray: 4, 2; }

.chart-legend {
  position: absolute;
  top: 15px;
  left: 20px;
  font-size: 10.5px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
}

.line {
  display: inline-block;
  width: 25px;
  height: 2px;
  margin-right: 8px;
}

.line.green { background-color: #0d6b4d; }
.line.grey { background-color: #888; }

.val {
  font-weight: bold;
  margin-left: 15px;
}
.green-val {
  color: #0d6b4d;
}

.chart-x-axis {
  position: absolute;
  bottom: -22px;
  left: 0;
  width: 100%;
  font-size: 9.5px;
  display: flex;
  justify-content: space-between;
  color: #555;
}

.disclaimers-footer {
  color: #666;
  margin-top: 8px;
  margin-bottom: 30px;
  line-height: 1.3;
  font-size: 9px;
  font-style: italic;
}

.report-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 15px;
  font-size: 10px;
  color: #555;
}

.footer-social {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #0d6b4d;
}

.social-icon {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  width: 22px;
  height: 22px;
  background-color: #0d6b4d;
  color: white;
  border-radius: 4px;
  font-size: 13px;
  font-family: inherit;
}
.social-icon.wechat {
  background-color: #07c160;
}

.bottom-actions {
  text-align: center;
  margin: 30px 0 50px 0;
}

.return-btn {
  padding: 10px 24px;
  background-color: #34495e;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.return-btn:hover {
  background-color: #2c3e50;
}
</style>
