<template>
  <div class="compare-fullscreen-overlay">
    <div class="compare-header-bar">
      <div class="ch-left">
        <button class="btn-icon-return" @click="handleClose">
          <span class="material-symbols-outlined">arrow_back</span> 返回
        </button>
        <h2 class="compare-title">双屏对比：{{ itemKey }}</h2>
      </div>
      <div class="ch-right">
        <button v-if="!readonly" class="btn-success btn-pass" @click="handleVerify" :disabled="verifying">
          <span class="material-symbols-outlined">check_circle</span>
          {{ verifying ? '提交中...' : '通过' }}
        </button>
      </div>
    </div>

    <div v-if="verifyError" class="global-error" style="margin: 1rem 2rem 0;">{{ verifyError }}</div>

    <div class="dual-view-container">
      <!-- 左侧：原始 Excel 只读预览 -->
      <div class="sheet-wrapper">
        <div class="sheet-header">
          <span class="material-symbols-outlined sheet-icon" style="color: #64748b;">description</span>
          系统原版 (Base) - 原始 Excel 数据
        </div>

        <!-- Sheet 标签栏（多 Sheet 切换） -->
        <div v-if="false" class="sheet-tab-bar">
        </div>

        <!-- 加载占位 -->
        <div v-if="leftLoading" class="sheet-placeholder">
          <span class="material-symbols-outlined spin">sync</span>
          <span>正在加载原始 Excel…</span>
        </div>

        <!-- 错误提示 -->
        <div v-else-if="leftError" class="sheet-placeholder error">
          <span class="material-symbols-outlined">error</span>
          <span>{{ leftError }}</span>
        </div>

        <!-- 表格容器 -->
        <div class="sheet-body" :style="{ visibility: (leftLoading || leftError) ? 'hidden' : 'visible' }">
          <iframe 
            id="iframe-luckysheet-left" 
            :src="iframeUrl" 
            style="margin:0;padding:0;position:absolute;width:100%;height:100%;border:none;">
          </iframe>
        </div>
      </div>

      <div class="compare-divider-wrapper">
        <div class="compare-divider-icon">
          <span class="material-symbols-outlined">compare_arrows</span>
        </div>
      </div>

      <!-- 右侧：系统解析入库数据 -->
      <div class="sheet-wrapper">
        <div class="sheet-header modified">
          <span class="material-symbols-outlined sheet-icon" style="color: #059669;">table_view</span>
          最新修订版 (Modified) - 系统导入后数据
          <div v-if="report?.reportType === 'FundAnalysis'" class="view-toggle" style="margin-left: 16px;">
            <button @click="viewMode = 'luckysheet'" :class="{ active: viewMode === 'luckysheet' }">入库数据对比</button>
            <button @click="viewMode = 'html'" :class="{ active: viewMode === 'html' }">历史同期对比</button>
          </div>
          <span
            class="badge"
            :class="isCheckedOrVerified ? 'badge-success' : 'badge-warning'"
            style="margin-left: auto;"
          >{{ isCheckedOrVerified ? '已核对' : '待核对' }}</span>
        </div>
        <!-- 右侧加载占位 (luckysheet 模式) -->
        <div v-if="rightLoading && viewMode === 'luckysheet'" class="sheet-placeholder">
          <span class="material-symbols-outlined spin">sync</span>
          <span>正在加载系统数据…</span>
        </div>

        <!-- 右侧错误提示 (luckysheet 模式) -->
        <div v-else-if="rightError && viewMode === 'luckysheet'" class="sheet-placeholder error">
          <span class="material-symbols-outlined">error</span>
          <span>{{ rightError }}</span>
        </div>

        <div class="sheet-body" :style="{ visibility: ((rightLoading || rightError) && viewMode === 'luckysheet') ? 'hidden' : 'visible' }">
          <!-- 系统解析后数据: Luckysheet -->
          <div
            v-show="viewMode === 'luckysheet'"
            id="luckysheet-right"
            style="margin:0;padding:0;position:absolute;width:100%;height:100%;"
          ></div>
          <!-- 历史数据: HTML -->
          <div v-if="viewMode === 'html'" style="width:100%;height:100%;overflow:auto;">
            <div v-if="faLoading" class="sheet-placeholder">
              <span class="material-symbols-outlined spin">sync</span>
              <span>正在加载历史对比数据...</span>
            </div>
            <div v-else-if="faError" class="sheet-placeholder error">
              <span class="material-symbols-outlined">error</span>
              <span>{{ faError }}</span>
            </div>
            <LCFundAnalysisView v-else :sheets="faSheets" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import LCFundAnalysisView from './LCFundAnalysisView.vue'

const props = defineProps({
  report:   { type: Object,  required: true },
  itemKey:  { type: String,  required: true },
  readonly: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'verified'])

const BASE = '/api/lc-report'
const verifying  = ref(false)
const verifyError = ref('')
const isVerified  = ref(false)   // 本次会话内通过核对

// 已核对：本次通过 or 文件本身已是 CHECKED 状态
const isCheckedOrVerified = computed(() =>
  isVerified.value || (props.report?.items?.[props.itemKey]?.isChecked ?? false)
)



// ── 左侧状态 ───────────────────────────────────────────
const leftLoading = ref(true)
const leftError = ref('')
const iframeUrl = ref('')

const luckysheetFrameHtml = `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Luckysheet Frame</title>
  <!-- Luckysheet 依赖 -->
  <link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/luckysheet@latest/dist/plugins/css/pluginsCss.css' />
  <link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/luckysheet@latest/dist/plugins/plugins.css' />
  <link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/luckysheet@latest/dist/css/luckysheet.css' />
  <link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/luckysheet@latest/dist/assets/iconfont/iconfont.css' />
  <script src="https://cdn.jsdelivr.net/npm/luckysheet@latest/dist/plugins/js/plugin.js"></scr` + `ipt>
  <script src="https://cdn.jsdelivr.net/npm/luckysheet@latest/dist/luckysheet.umd.js"></scr` + `ipt>
  <style>
    body, html { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: transparent; }
    #luckysheet-container { width: 100%; height: 100%; position: absolute; }
  </style>
</head>
<body>
  <div id="luckysheet-container"></div>
  <script>
    // 通知父窗口已准备就绪
    window.parent.postMessage({ type: 'luckysheet-frame-ready' }, '*');

    // 监听来自 Vue 父组件的消息
    window.addEventListener('message', (event) => {
      const data = event.data;
      if (data && data.type === 'init-luckysheet') {
        const payload = data.payload;
        if (window.luckysheet) {
          window.luckysheet.create({
            container: 'luckysheet-container',
            lang: 'zh',
            showinfobar: false,
            showtoolbar: false,
            showstatisticBar: false,
            sheetFormulaBar: false,
            enableAddRow: false,
            enableAddBackTop: false,
            data: payload.sheets,
            title: payload.title || '原始 Excel',
            userInfo: payload.userInfo || ''
          });
        }
      }
    });
  </scr` + `ipt>
</body>
</html>`

// ── FundAnalysis 历史对比 ─────────────────────────────
const viewMode = ref('luckysheet')
const faSheets = ref([])
const faLoading = ref(false)
const faError = ref('')

async function fetchFaData() {
  if (props.report?.reportType !== 'FundAnalysis') return
  faLoading.value = true
  faError.value = ''
  try {
    const res = await fetch(`${BASE}/reports/${props.report.id}/fa-compare`)
    if (!res.ok) {
      faError.value = `加载对比数据失败 (${res.status})`
      return
    }
    const json = await res.json()
    if (!json.success) {
      faError.value = json.message || '获取数据失败'
      return
    }
    faSheets.value = json.sheets || []
  } catch (err) {
    faError.value = '网络错误: ' + err.message
  } finally {
    faLoading.value = false
  }
}

// ── 生命周期 ───────────────────────────────────────────
onMounted(async () => {
  const blob = new Blob([luckysheetFrameHtml], { type: 'text/html' })
  iframeUrl.value = URL.createObjectURL(blob)

  // 由于采用了 iframe 物理隔离，左右两边完全不需要再加串行锁了，直接并发飞起！
  initLeftPanel()
  initRightPanel()
  fetchFaData()
})

onBeforeUnmount(() => {
  if (iframeUrl.value) {
    URL.revokeObjectURL(iframeUrl.value)
  }
  if (window.luckysheet) {
    try { window.luckysheet.destroy() } catch (_) {}
  }
})

// ── 工具方法 ───────────────────────────────────────────
function handleClose() { emit('close') }

async function handleVerify() {
  const fileId = props.report?.items[props.itemKey]?.file_id
  if (!fileId) { alert('未找到文件 ID，请先上传文件'); return }
  verifying.value = true
  verifyError.value = ''
  try {
    const res = await fetch(`${BASE}/files/${fileId}/check`, { method: 'POST' })
    const json = await res.json()
    if (json.success) {
      isVerified.value = true
      emit('verified')
    } else verifyError.value = json.detail || '核对失败'
  } catch (e) {
    verifyError.value = '网络错误：' + e.message
  } finally {
    verifying.value = false
  }
}

// ── 左侧面板：LuckyExcel 渲染 ─────────────────────────────
async function initLeftPanel() {
  const fileId = props.report?.items[props.itemKey]?.file_id
  const fileName = props.report?.items[props.itemKey]?.fileName || ''

  if (!fileId) {
    leftError.value = '找不到对应文件 ID'
    leftLoading.value = false
    return
  }

  // 允许 xlsx 和 xls（xls 在后台下载接口会自动被替换为同名的带格式 xlsx 下载）
  const ext = fileName ? fileName.toLowerCase().split('.').pop() : 'xlsx'
  if (ext !== 'xlsx' && ext !== 'xls') {
    leftError.value = `当前仅支持 Excel 格式的在线预览，您上传的文件为 [${fileName}]`
    leftLoading.value = false
    return
  }

  if (!window.LuckyExcel) {
    leftError.value = 'LuckyExcel 库未加载，请刷新页面重试'
    leftLoading.value = false
    return
  }

  try {
    const res = await fetch(`${BASE}/files/${fileId}/download`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const blob = await res.blob()
    // 由于后端 api_download_file 的容错机制，如果存在 xlsx 它会返回 xlsx。
    // 如果由于未知原因返回了原始 xls，我们需要提醒，因为 LuckyExcel 只吃 xlsx
    const cd = res.headers.get('content-disposition') || ''
    const isActuallyXlsx = cd.includes('.xlsx') || (blob.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    const file = new File([blob], fileName + (isActuallyXlsx ? 'x' : ''), { type: blob.type })
    
    return new Promise((resolve) => {
      // 使用 LuckyExcel 转换
      window.LuckyExcel.transformExcelToLucky(file, function(exportJson, luckysheetfile){
        if(exportJson.sheets == null || exportJson.sheets.length === 0){
          leftError.value = '未能从文件中解析出表格数据，请确保上传了正确的 xlsx 格式。'
          leftLoading.value = false
          resolve()
          return
        }
        
        // 渲染隔离：将解析好的数据通过 postMessage 打给 iframe 内的隔离版 luckysheet
        const sendToIframe = () => {
          leftLoading.value = false

          const iframe = document.getElementById('iframe-luckysheet-left')
          if (!iframe || !iframe.contentWindow) {
             setTimeout(sendToIframe, 100)
             return
          }

          // 发送消息的动作
          const doSend = () => {
             iframe.contentWindow.postMessage({
              type: 'init-luckysheet',
              payload: {
                sheets: exportJson.sheets,
                title: exportJson.info.name,
                userInfo: exportJson.info.name.creator
              }
            }, '*')
            resolve()
          }

          // 稳妥起见：因为 iframe 的网络加载有个极小的时间差，直接抛 message 可能会在它监听前丢失
          // 我们监听它发出的 ready 信号（如果已经错过了也没关系，我们兜底直接发送）
          let hasSent = false
          const onMessage = (e) => {
            if (e.data && e.data.type === 'luckysheet-frame-ready' && !hasSent) {
              hasSent = true
              window.removeEventListener('message', onMessage)
              doSend()
            }
          }
          window.addEventListener('message', onMessage)
          
          // 兜底：如果 iframe 加载极快或者已经被浏览器缓存，直接发送
          setTimeout(() => {
            if (!hasSent) {
              hasSent = true
              window.removeEventListener('message', onMessage)
              doSend()
            }
          }, 300)
        }
        sendToIframe()

      }, function(err){
        leftError.value = 'LuckyExcel 解析失败：' + err
        leftLoading.value = false
        resolve()
      })
    })

  } catch (e) {
    leftError.value = '加载原始 Excel 失败：' + e.message
    console.error('[LCReportCompare] left panel error:', e)
    leftLoading.value = false
  }
}

// ── 右侧面板 ───────────────────────────────────────────
const rightLoading = ref(true)
const rightError = ref('')

async function initRightPanel() {
  const fileId = props.report?.items[props.itemKey]?.file_id
  if (!fileId) {
    rightLoading.value = false
    rightError.value = '未找到文件 ID'
    return
  }

  rightLoading.value = true
  rightError.value = ''

  try {
    const res = await fetch(`${BASE}/files/${fileId}/parsed-data`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const json = await res.json()

    // ── Quartile_weekly / FundAnalysis: 多 Sheet 格式 ────────────────────
    if (json.success && json.sheets?.length) {
      const luckySheets = json.sheets.map((sheet, sheetIdx) => {
        const celldata = []
        const columns = sheet.columns || []
        const rows = sheet.rows || []
        const meta = sheet.meta || {}
        const colGroups = sheet.column_groups || []

        // ── meta 信息行（前4行）──────────────────────────────────────────
        const metaLines = [
          `Currency: ${meta.currency || ''}`,
          `Grouped by: ${meta.grouped_by || ''}`,
          `Calculated on: ${meta.calculated_on || ''}`,
          `Exported on: ${meta.exported_on || ''}`,
        ]
        metaLines.forEach((txt, ri) => {
          celldata.push({ r: ri, c: 0, v: { m: txt, v: txt, fc: '#64748b', it: 1 } })
        })

        // ── 3 行表头从第 8 行开始（4 meta + 3 空行）──────────────────────
        const H0 = metaLines.length + 3   // period label 行
        const H1 = H0 + 1                  // date range 行
        const H2 = H0 + 2                  // sub-col label 行
        const DATA_START = H0 + 3          // 数据从第 H0+3 行开始

        // ── 合并配置 ─────────────────────────────────────────────────────
        const merge = {}

        // ── 表头颜色方案 ─────────────────────────────────────────────────
        const BG_MAIN   = '#064e3b'   // 主色（深绿）
        const BG_DATE   = '#065f46'   // 次色（稍浅绿）
        const BG_SUB    = '#047857'   // 第3行（再浅绿）
        const BG_GROUP  = '#166534'   // static/size 列颜色
        const FC_WHITE  = '#ffffff'
        const FC_LIGHT  = '#d1fae5'

        colGroups.forEach(grp => {
          if (grp.type === 'static' || grp.type === 'size') {
            const ci = grp.col_index
            // 合并 3 行 1 列
            merge[`${H0}_${ci}`] = { r: H0, c: ci, rs: 3, cs: 1 }
            celldata.push({
              r: H0, c: ci,
              v: { m: grp.label, v: grp.label, bg: BG_GROUP, fc: FC_WHITE, bl: 1, vt: 0, ht: 0 }
            })
          } else if (grp.type === 'period') {
            const cs = grp.col_start
            const cc = grp.col_count

            // 行1：period label，合并跨 cc 列
            merge[`${H0}_${cs}`] = { r: H0, c: cs, rs: 1, cs: cc }
            celldata.push({
              r: H0, c: cs,
              v: { m: grp.period_label, v: grp.period_label, bg: BG_MAIN, fc: FC_WHITE, bl: 1, ht: 0 }
            })

            // 行2：date range，合并跨 cc 列
            merge[`${H1}_${cs}`] = { r: H1, c: cs, rs: 1, cs: cc }
            celldata.push({
              r: H1, c: cs,
              v: { m: grp.date_range, v: grp.date_range, bg: BG_DATE, fc: FC_LIGHT, ht: 0 }
            })

            // 行3：各子列标签
            grp.sub_cols.forEach(sc => {
              celldata.push({
                r: H2, c: sc.col_index,
                v: { m: sc.label, v: sc.label, bg: BG_SUB, fc: FC_WHITE, bl: 1 }
              })
            })
          }
        })

        // ── 列宽配置 ─────────────────────────────────────────────────────
        const columnlen = {}
        columns.forEach((col, idx) => {
          columnlen[idx] = col === 'Group/Investment' ? 220
            : col.includes('Benchmark') || col.includes('Category') ? 190
            : col.includes('rank') || col.includes('quartile') ? 100
            : 130
        })

        // ── 数据行 ───────────────────────────────────────────────────────
        rows.forEach((row, ri) => {
          const isGroupHeader = row._is_group_header === true
          columns.forEach((col, ci) => {
            let val = row[col]
            if (val === null || val === undefined) val = ''
            const cellV = { m: String(val), v: val }
            if (isGroupHeader) {
              cellV.bg = '#dbeafe'
              cellV.fc = '#1e3a8a'
              cellV.bl = 1
            }
            celldata.push({ r: DATA_START + ri, c: ci, v: cellV })
          })
        })

        return {
          name: sheet.sheet_name,
          color: '',
          index: sheetIdx,
          status: sheetIdx === 0 ? 1 : 0,
          order: sheetIdx,
          celldata,
          config: { columnlen, merge },
        }
      })

      window.luckysheet.create({
        container: 'luckysheet-right',
        lang: 'zh',
        showinfobar: false,
        showsheetbar: luckySheets.length > 1,
        data: luckySheets,
      })
      rightLoading.value = false
      return
    }


    // ── SalesRptByProduct / FundAnalysis: 单 Sheet 扁平格式 ─────────────
    let celldata = [{ r: 0, c: 0, v: { m: '无解析数据', v: '无解析数据' } }]
    let config = { merge: {} }
    let sheetName = '导入数据'

    if (json.success && json.columns?.length) {
      celldata = []
      const columns = json.columns
      const rows = json.rows || []

      columns.forEach((col, idx) => {
        celldata.push({ r: 0, c: idx, v: { m: col, v: col, bg: '#064e3b', fc: '#ffffff', bl: 1 } })
      })
      rows.forEach((row, ri) => {
        columns.forEach((col, ci) => {
          let val = row[col]
          if (val === null || val === undefined) val = ''
          celldata.push({ r: ri + 1, c: ci, v: { m: String(val), v: val } })
        })
      })

      const columnlen = {}
      columns.forEach((_, idx) => { columnlen[idx] = 120 })
      if (columnlen[1] !== undefined) columnlen[1] = 200
      config = { columnlen, merge: {} }
      sheetName = json.report_type || '导入数据'
    }

    window.luckysheet.create({
      container: 'luckysheet-right',
      lang: 'zh',
      showinfobar: false,
      showsheetbar: false,
      data: [{
        name: sheetName,
        color: '',
        index: 0,
        status: 1,
        order: 0,
        celldata,
        config,
      }]
    })
    rightLoading.value = false
  } catch (e) {
    console.error('[LCReportCompare] right panel error:', e)
    rightError.value = '加载系统数据出错: ' + e.message
    rightLoading.value = false
  }
}

</script>

<style scoped>
/* ── 全屏对比样式 ─────────────────────────────────────── */
.compare-fullscreen-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: #f5f5f7;
  z-index: 10000;
  display: flex;
  flex-direction: column;
}

.compare-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  flex-shrink: 0;
}

.ch-left { display: flex; align-items: center; gap: 1rem; }
.ch-right { display: flex; align-items: center; }

.btn-icon-return {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.5rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  color: #334155;
  font-weight: 500;
  transition: all 0.2s;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
.btn-icon-return:hover { background: #f8fafc; color: #0f172a; }

.compare-title { margin: 0; font-size: 1.25rem; color: #0f172a; font-weight: 600; }

.btn-pass {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  padding: 0.6rem 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(5, 150, 105, 0.2);
  background-color: #059669;
  color: white;
  border: none;
  cursor: pointer;
}
.btn-pass:hover:not(:disabled) { background-color: #047857; }
.btn-pass:disabled { opacity: 0.6; cursor: not-allowed; }

.dual-view-container {
  flex: 1;
  display: flex;
  gap: 1.5rem;
  padding: 1.5rem 2rem;
  min-height: 0;
}

.sheet-wrapper {
  flex: 1;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #d2d2d7;
  display: flex;
  flex-direction: column;
  background: white;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
  min-width: 0;
}

.sheet-header {
  height: 48px;
  background: #fafafc;
  border-bottom: 1px solid #d2d2d7;
  display: flex;
  align-items: center;
  padding: 0 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
  gap: 0.5rem;
  flex-shrink: 0;
}
.sheet-header.modified { color: #0f172a; }
.sheet-icon { font-size: 1.25rem; }

/* Sheet 标签栏 */
.sheet-tab-bar {
  display: flex;
  gap: 0;
  background: #f1f5f9;
  border-bottom: 1px solid #d2d2d7;
  overflow-x: auto;
  flex-shrink: 0;
}
.sheet-tab {
  padding: 0.45rem 1rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: #64748b;
  background: transparent;
  border: none;
  border-right: 1px solid #d2d2d7;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
}
.sheet-tab:hover { background: #e2e8f0; color: #1e293b; }
.sheet-tab.active {
  background: white;
  color: #0071e3;
  font-weight: 600;
  border-bottom: 2px solid #0071e3;
  margin-bottom: -1px;
}

.sheet-body {
  flex: 1;
  position: relative;
  overflow: hidden;
}

/* 加载 / 错误占位 */
.sheet-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 0.75rem;
  color: #94a3b8;
  font-size: 0.9rem;
}
.sheet-placeholder .material-symbols-outlined { font-size: 2.5rem; }
.sheet-placeholder.error { color: #be123c; }
.sheet-placeholder.error .material-symbols-outlined { color: #be123c; }

/* 旋转动画 */
@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; display: inline-block; }

/* Excel 表格 */
.excel-table-wrapper {
  position: absolute;
  inset: 0;
  overflow: auto;
  padding: 0;
}

.excel-table {
  border-collapse: collapse;
  width: max-content;
  min-width: 100%;
  font-size: 0.8rem;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Inter', sans-serif;
}

.excel-table thead th {
  position: sticky;
  top: 0;
  background: #f1f5f9;
  color: #475569;
  font-weight: 600;
  font-size: 0.75rem;
  padding: 6px 10px;
  border: 1px solid #d2d2d7;
  text-align: center;
  white-space: nowrap;
  z-index: 3;
  min-width: 80px;
}

.excel-table thead th.row-num-col {
  min-width: 40px;
  width: 40px;
  left: 0;
  z-index: 4;
  background: #e2e8f0;
}

.excel-table tbody td {
  padding: 4px 10px;
  border: 1px solid #e2e8f0;
  color: #1e293b;
  white-space: nowrap;
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 0.8rem;
}

.excel-table tbody td.row-num-col {
  position: sticky;
  left: 0;
  background: #f8fafc;
  color: #94a3b8;
  font-size: 0.7rem;
  text-align: center;
  border-color: #d2d2d7;
  min-width: 40px;
  z-index: 2;
}

.excel-table tbody tr:hover td:not(.row-num-col) {
  background-color: #f0f9ff;
}

/* 分隔器 */
.compare-divider-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  flex-shrink: 0;
}
.compare-divider-icon {
  width: 2.5rem;
  height: 2.5rem;
  background: white;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  border: 1px solid #e2e8f0;
  color: #0071e3;
}

.global-error {
  background: #fff1f2;
  color: #be123c;
  border: 1px solid #fecdd3;
  border-radius: 6px;
  padding: 0.6rem 1rem;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.badge {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  margin-left: 0.4rem;
  vertical-align: middle;
  letter-spacing: 0.02em;
}
.badge-warning { background: #fef3c7; color: #b45309; }
.badge-success { background: #d1fae5; color: #065f46; }
</style>

<style scoped>
.view-toggle {
  display: flex;
  background: #f1f5f9;
  border-radius: 6px;
  padding: 2px;
}
.view-toggle button {
  background: transparent;
  border: none;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}
.view-toggle button.active {
  background: #fff;
  color: #059669;
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.fa-loading { padding: 20px; color: #64748b; text-align: center; }
.fa-error { padding: 20px; color: #ef4444; text-align: center; }
</style>
