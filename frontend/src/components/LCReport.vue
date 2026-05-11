<template>
  <div class="ia-dashboard-layout">
    <!-- SideNavBar -->
    <aside class="ia-sidebar">
      <div class="sidebar-header">
        <div class="sidebar-brand-container">
          <div class="sidebar-icon">
            <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">account_balance</span>
          </div>
          <div class="sidebar-brand-text">
            <h2 class="brand-title">Institutional Alpha</h2>
            <p class="brand-subtitle">Fund Management</p>
          </div>
        </div>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/lcreport" class="nav-link active"><span class="material-symbols-outlined">analytics</span> LCReport</router-link>
      </nav>

      <div class="sidebar-footer">
        <a class="nav-link" href="#"><span class="material-symbols-outlined">contact_support</span> Support</a>
        <a class="nav-link" href="#" @click.prevent="handleLogout"><span class="material-symbols-outlined">logout</span> Sign Out</a>
      </div>
    </aside>

    <!-- Main Content Canvas -->
    <main class="ia-main">
      <!-- TopNavBar -->
      <header class="ia-top-nav">
        <div class="nav-left">
          <span class="nav-brand">LC Report Dashboard</span>
        </div>
        <div class="nav-right">
          <div class="search-container">
            <span class="material-symbols-outlined search-icon">search</span>
            <input class="search-input" placeholder="Search reports..." type="text"/>
          </div>
          <button class="icon-btn relative">
            <span class="material-symbols-outlined">notifications</span>
            <span class="notification-dot"></span>
          </button>
          <img alt="User profile" class="user-avatar" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAPQN0l-TQg4rhuEA2VKujdTzbncXPN9KD7vxRZTahAsjRUxv_hzWVDmYt-hRT_TfpIiyscZ3xP9_76v_pnn6IgKq7Mz4w9A9WujS1nqAe_OAIFYzupB5L-Al6Tg6wKOOox5Q6IRRASqLzxDQwWa0mBG0as2LXMicB1nG7CcT4ziT1wvDBOsd7djfYc59CtMiEJ4VAJPw5nfdxCc1v3THDoWKwa4Xqso-a2yuNFaPrn9Mg7rnwcyAfTJY14QkTGxwmeAPltJyZdNHA"/>
        </div>
      </header>

      <!-- Main Content Area -->
      <section class="content-section">
        <div class="lcreport-container">
          <!-- Top Section (Filters) -->
          <div class="top-section">
            <div class="filter-group">
                <label>日期范围：</label>
              <div class="date-picker-wrapper">
                  <VueDatePicker
                    v-model="dateRange"
                    range
                    auto-apply
                    :time-config="{ enableTimePicker: false }"
                    :clearable="false"
                    :format="customFormat"
                    :preview-format="customFormat"
                    placeholder="选择日期范围"
                  />
              </div>
            </div>
            <div class="action-group">
              <button class="btn-success" @click="handleQuery" :disabled="loading">{{ loading ? '查询中...' : '查询' }}</button>
              <button class="btn-success" @click="showNewReportModal = true">新增报告</button>
            </div>
          </div>
          <div v-if="globalError" class="global-error">⚠️ {{ globalError }}</div>
          <div v-if="loading && reports.length === 0" class="loading-tip">加载中...</div>

          <!-- Bottom Section (Cards List) -->
          <div class="cards-section">
            <div
              class="report-card"
              :class="{ 'report-card--archived': report.is_readonly }"
              v-for="report in filteredReports" :key="report.id"
            >
              <div class="card-header">
                <div class="header-left">
                  <h3>{{ report.reportTime }}</h3>
                  <span v-if="report.is_readonly" class="archived-badge">🔒 已归档</span>
                  <span v-else class="status-label-badge" :class="'slb-' + report.status">
                    {{ report.status_label }}
                  </span>
                </div>
                <button
                  v-if="!report.is_readonly"
                  class="btn-delete-report"
                  @click="handleDeleteReport(report)"
                  title="删除报告"
                >
                  <span class="material-symbols-outlined">delete</span>
                </button>
              </div>
              <div v-if="report.is_readonly" class="archived-tip">
                该报告已于周五 18:00 后自动归档，仅可查看。
              </div>
              <div class="card-content">
                <h4>原始数据</h4>

                <div class="check-item">
                  <div class="item-left">
                    <span class="status-icon">
                      <template v-if="!report.items.Quartile_weekly.hasData">❌</template>
                      <template v-else-if="report.items.Quartile_weekly.data_status === 'PARSING'">⏳</template>
                      <template v-else-if="!report.items.Quartile_weekly.isChecked">⚠️</template>
                      <template v-else>✅</template>
                    </span>
                    <span class="item-name">Quartile_weekly</span>
                    <span v-if="report.items.Quartile_weekly.data_status_label" class="status-badge"
                      :class="'badge-' + report.items.Quartile_weekly.data_status">{{ report.items.Quartile_weekly.data_status_label }}</span>
                  </div>
                  <div class="item-actions">
                    <button
                      class="btn-sm btn-upload"
                      :disabled="report.is_readonly || report.items.Quartile_weekly.data_status === 'PARSING'"
                      @click="openUploadModal(report, 'Quartile_weekly')"
                    >上传</button>
                    <button
                      class="btn-sm btn-verify"
                      :disabled="report.is_readonly || !report.items.Quartile_weekly.hasData || report.items.Quartile_weekly.data_status === 'PARSING'"
                      @click="openVerifyModal(report, 'Quartile_weekly')"
                    >
                      核对
                    </button>
                  </div>
                </div>

                <div class="check-item">
                  <div class="item-left">
                    <span class="status-icon">
                      <template v-if="!report.items.SalesRptByProduct.hasData">❌</template>
                      <template v-else-if="report.items.SalesRptByProduct.data_status === 'PARSING'">⏳</template>
                      <template v-else-if="!report.items.SalesRptByProduct.isChecked">⚠️</template>
                      <template v-else>✅</template>
                    </span>
                    <span class="item-name">SalesRptByProduct</span>
                    <span v-if="report.items.SalesRptByProduct.data_status_label" class="status-badge"
                      :class="'badge-' + report.items.SalesRptByProduct.data_status">{{ report.items.SalesRptByProduct.data_status_label }}</span>
                  </div>
                  <div class="item-actions">
                    <button
                      class="btn-sm btn-upload"
                      :disabled="report.is_readonly || report.items.SalesRptByProduct.data_status === 'PARSING'"
                      @click="openUploadModal(report, 'SalesRptByProduct')"
                    >上传</button>
                    <button
                      class="btn-sm btn-verify"
                      :disabled="report.is_readonly || !report.items.SalesRptByProduct.hasData || report.items.SalesRptByProduct.data_status === 'PARSING'"
                      @click="openVerifyModal(report, 'SalesRptByProduct')"
                    >
                      核对
                    </button>
                  </div>
                </div>

                <div class="check-item">
                  <div class="item-left">
                    <span class="status-icon">
                      <template v-if="!report.items.FundAnalysis.hasData">❌</template>
                      <template v-else-if="report.items.FundAnalysis.data_status === 'PARSING'">⏳</template>
                      <template v-else-if="!report.items.FundAnalysis.isChecked">⚠️</template>
                      <template v-else>✅</template>
                    </span>
                    <span class="item-name">Fund Analysis</span>
                    <span v-if="report.items.FundAnalysis.data_status_label" class="status-badge"
                      :class="'badge-' + report.items.FundAnalysis.data_status">{{ report.items.FundAnalysis.data_status_label }}</span>
                  </div>
                  <div class="item-actions">
                    <button
                      class="btn-sm btn-upload"
                      :disabled="report.is_readonly || report.items.FundAnalysis.data_status === 'PARSING'"
                      @click="openUploadModal(report, 'FundAnalysis')"
                    >上传</button>
                    <button
                      class="btn-sm btn-verify"
                      :disabled="report.is_readonly || !report.items.FundAnalysis.hasData || report.items.FundAnalysis.data_status === 'PARSING'"
                      @click="openVerifyModal(report, 'FundAnalysis')"
                    >
                      核对
                    </button>
                  </div>
                </div>
              </div>

              <div class="card-footer">
                <template v-if="report.is_readonly">
                  <!-- 已归档：只显示查看按鈕 -->
                  <button
                    class="btn-view"
                    @click="handleViewReport(report)"
                  >
                    查看报告
                  </button>
                </template>
                <template v-else>
                  <button
                    class="btn-primary btn-generate"
                    :disabled="!isReportReady(report) || generating"
                    @click="handleGenerate(report)"
                  >
                    {{ generating ? '生成中...' : '生成报告' }}
                  </button>
                  <button
                    class="btn-view"
                    :disabled="!isReportReady(report)"
                    @click="handleViewReport(report)"
                  >
                    查看报告
                  </button>
                </template>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Modals -->
    <div v-if="showNewReportModal" class="modal-overlay">
      <div class="modal-content">
        <h3>新增报告</h3>
        <div class="form-group">
          <label>输入报告时间：</label>
          <input type="date" v-model="newReportTime" class="form-input" />
          <p v-if="createError" class="error-text">{{ createError }}</p>
        </div>
        <div class="modal-actions">
          <button class="btn-default" @click="showNewReportModal = false" :disabled="creating">取消</button>
          <button class="btn-primary" @click="createNewReport" :disabled="creating">
            {{ creating ? '创建中...' : '确认' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="showUploadModal" class="modal-overlay">
      <div class="modal-content">
        <h3>上传原始数据 ({{ currentUploadItem }})</h3>
        <div class="form-group">
          <input type="file" class="form-input" accept=".xlsx,.xls" @change="onFileChange" />
          <p class="help-text">支持重复上传覆盖，Quartile_weekly 上传后将自动解析导入</p>
          <p v-if="uploadError" class="error-text">{{ uploadError }}</p>
        </div>
        <div class="modal-actions">
          <button class="btn-default" @click="showUploadModal = false" :disabled="uploading">取消</button>
          <button class="btn-primary" @click="confirmUpload" :disabled="uploading">
            {{ uploading ? '上传中...' : '确认上传' }}
          </button>
        </div>
      </div>
    </div>

    <LCReportCompare
      v-if="showVerifyModal"
      :report="currentVerifyReport"
      :itemKey="currentVerifyItem"
      @close="closeVerifyModal"
      @verified="onVerified"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { VueDatePicker } from '@vuepic/vue-datepicker'
import '@vuepic/vue-datepicker/dist/main.css'
import LCReportCompare from './LCReportCompare.vue'

const router = useRouter()
const BASE = '/api/lc-report'

const handleLogout = () => {
  localStorage.removeItem('isAuthenticated')
  localStorage.removeItem('currentUser')
  router.push('/login')
}

// ─── 日期选择 ───────────────────────────────────────────────
const dateRange = ref(null)

const customFormat = (date) => {
  if (!date) return ''
  const fmt = (d) => {
    if (!d) return ''
    const o = new Date(d)
    return `${o.getFullYear()}-${String(o.getMonth()+1).padStart(2,'0')}-${String(o.getDate()).padStart(2,'0')}`
  }
  if (Array.isArray(date)) {
    const [s, e] = date
    if (s && e) return `${fmt(s)} ~ ${fmt(e)}`
    if (s) return `${fmt(s)} ~ `
    return ''
  }
  return fmt(date)
}

const toDateStr = (d) => {
  const o = new Date(d)
  return `${o.getFullYear()}-${String(o.getMonth()+1).padStart(2,'0')}-${String(o.getDate()).padStart(2,'0')}`
}

// ─── 报告列表 ────────────────────────────────────────────────
const reports = ref([])
const loading = ref(false)
const globalError = ref('')

/** 将后端返回格式转换为前端 card 格式 */
function adaptReport(r) {
  return {
    id:           r.report_id,
    reportTime:   r.report_date,
    status:       r.status,
    status_label: r.status_label || '',
    is_readonly:  r.is_readonly ?? false,
    items: {
      Quartile_weekly: {
        file_id:           r.items?.Quartile_weekly?.file_id        ?? null,
        fileName:          r.items?.Quartile_weekly?.original_name  ?? '',
        hasData:           r.items?.Quartile_weekly?.hasData         ?? false,
        isChecked:         r.items?.Quartile_weekly?.isChecked       ?? false,
        data_status:       r.items?.Quartile_weekly?.data_status     || 'NOT_IMPORTED',
        data_status_label: r.items?.Quartile_weekly?.data_status_label || '未导入',
      },
      SalesRptByProduct: {
        file_id:           r.items?.SalesRptByProduct?.file_id        ?? null,
        fileName:          r.items?.SalesRptByProduct?.original_name  ?? '',
        hasData:           r.items?.SalesRptByProduct?.hasData         ?? false,
        isChecked:         r.items?.SalesRptByProduct?.isChecked       ?? false,
        data_status:       r.items?.SalesRptByProduct?.data_status     || 'NOT_IMPORTED',
        data_status_label: r.items?.SalesRptByProduct?.data_status_label || '未导入',
      },
      FundAnalysis: {
        file_id:           r.items?.FundAnalysis?.file_id        ?? null,
        fileName:          r.items?.FundAnalysis?.original_name  ?? '',
        hasData:           r.items?.FundAnalysis?.hasData         ?? false,
        isChecked:         r.items?.FundAnalysis?.isChecked       ?? false,
        data_status:       r.items?.FundAnalysis?.data_status     || 'NOT_IMPORTED',
        data_status_label: r.items?.FundAnalysis?.data_status_label || '未导入',
      },
    },
  }
}

async function fetchReports() {
  loading.value = true
  globalError.value = ''
  try {
    let url = `${BASE}/reports`
    const params = []
    if (dateRange.value?.length === 2 && dateRange.value[0] && dateRange.value[1]) {
      params.push(`start_date=${toDateStr(dateRange.value[0])}`)
      params.push(`end_date=${toDateStr(dateRange.value[1])}`)
    }
    if (params.length) url += '?' + params.join('&')
    const res = await fetch(url)
    const json = await res.json()
    if (json.success) {
      reports.value = json.data.map(adaptReport)
    } else {
      globalError.value = json.detail || '查询失败'
    }
  } catch (e) {
    globalError.value = '网络错误：' + e.message
  } finally {
    loading.value = false
  }
}

const filteredReports = computed(() =>
  [...reports.value].sort((a, b) => new Date(b.reportTime) - new Date(a.reportTime))
)

const handleQuery = () => fetchReports()
onMounted(() => fetchReports())

// ─── 新增报告 ─────────────────────────────────────────────────
const showNewReportModal = ref(false)
const newReportTime = ref('')
const creating = ref(false)
const createError = ref('')

async function createNewReport() {
  if (!newReportTime.value) { alert('请选择报告时间'); return }
  creating.value = true
  createError.value = ''
  try {
    const res = await fetch(`${BASE}/reports`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ report_date: newReportTime.value }),
    })
    const json = await res.json()
    if (json.success) {
      showNewReportModal.value = false
      newReportTime.value = ''
      await fetchReports()
    } else {
      createError.value = json.detail || json.message || '创建失败'
    }
  } catch (e) {
    createError.value = '网络错误：' + e.message
  } finally {
    creating.value = false
  }
}

async function handleDeleteReport(report) {
  if (report.is_readonly) return
  if (!confirm(`确定要删除 ${report.reportTime} 的报告吗？`)) return
  
  try {
    const res = await fetch(`${BASE}/reports/${report.id}`, { method: 'DELETE' })
    const json = await res.json()
    if (json.success) {
      alert('报告已删除')
      fetchReports()
    } else {
      alert('删除失败: ' + (json.message || json.detail))
    }
  } catch (e) {
    alert('请求失败：' + e.message)
  }
}

// ─── 上传文件 Modal ───────────────────────────────────────────
const showUploadModal = ref(false)
const currentUploadReport = ref(null)
const currentUploadItem = ref('')
const uploadFile = ref(null)
const uploading = ref(false)
const uploadError = ref('')
/** 存储正在轮询的 file_id -> timer 映射 */
const pollingTimers = ref({})

function openUploadModal(report, itemKey) {
  currentUploadReport.value = report
  currentUploadItem.value = itemKey
  uploadFile.value = null
  uploadError.value = ''
  showUploadModal.value = true
}

function onFileChange(e) {
  uploadFile.value = e.target.files[0] || null
}

async function confirmUpload() {
  if (!uploadFile.value) { alert('请选择文件'); return }
  const report = currentUploadReport.value
  const itemKey = currentUploadItem.value
  if (!report) return

  uploading.value = true
  uploadError.value = ''
  try {
    const form = new FormData()
    form.append('report_id', String(report.id))
    form.append('report_date', report.reportTime)
    form.append('report_type', itemKey)
    form.append('file', uploadFile.value)

    const res = await fetch(`${BASE}/files/upload`, { method: 'POST', body: form })
    const json = await res.json()
    if (json.success) {
      showUploadModal.value = false
      uploadFile.value = null
      
      // 乐观更新：立即将状态设为 PARSING 禁用按钮，避免等待接口
      const item = report.items[itemKey]
      if (item) {
        item.data_status = 'PARSING'
        item.data_status_label = '解析中'
        item.file_id = json.data?.file_id
      }

      if (json.data?.file_id) {
        startPolling(json.data.file_id, report, itemKey)
      }
    } else {
      uploadError.value = json.detail || '上传失败'
    }
  } catch (e) {
    uploadError.value = '网络错误：' + e.message
  } finally {
    uploading.value = false
  }
}

/** 每 3 秒轮询一次文件状态，直到状态脱离 PARSING (局部更新，避免全列表刷新) */
function startPolling(fileId, report, itemKey) {
  if (pollingTimers.value[fileId]) return
  const timer = setInterval(async () => {
    try {
      const res = await fetch(`${BASE}/files/${fileId}/status`)
      const json = await res.json()
      if (json.success) {
        const s = json.data.data_status
        
        // 局部更新绑定的 report item，不调用全量 fetchReports 避免页面抖动
        const item = report.items[itemKey]
        if (item) {
          item.data_status = s
          item.data_status_label = json.data.data_status_label
          item.hasData = json.data.hasData
          item.isChecked = json.data.isChecked
        }

        if (s !== 'PARSING') {
          clearInterval(timer)
          delete pollingTimers.value[fileId]
          if (json.data.parse_error) {
            alert(`解析失败：\n${json.data.parse_error}`)
          }
        }
      }
    } catch (_) { /* 静默 */ }
  }, 3000)
  pollingTimers.value[fileId] = timer
}

// ─── 核对 Modal ───────────────────────────────────────────────
const showVerifyModal = ref(false)
const currentVerifyReport = ref(null)
const currentVerifyItem = ref('')

function openVerifyModal(report, itemKey) {
  currentVerifyReport.value = report
  currentVerifyItem.value = itemKey
  showVerifyModal.value = true
}

function closeVerifyModal() {
  showVerifyModal.value = false
}

async function onVerified() {
  closeVerifyModal()
  await fetchReports()
}

// ─── 报告就绪判断 ─────────────────────────────────────────────
const isReportReady = (report) => Boolean(
  report?.items?.Quartile_weekly?.isChecked &&
  report?.items?.SalesRptByProduct?.isChecked &&
  report?.items?.FundAnalysis?.isChecked
)

// ─── 生成 / 查看报告 ──────────────────────────────────────────
const generating = ref(false)

const handleGenerate = async (report) => {
  if (!isReportReady(report)) {
    alert('检查项未全部通过！请检查原始数据是否都已经检查通过。')
    return
  }
  if (generating.value) return
  generating.value = true
  try {
    const res = await fetch(`${BASE}/reports/${report.id}/generate`, { method: 'POST' })
    const json = await res.json()
    if (json.success) {
      await fetchReports()
      router.push(`/report?name=LC%20meeting&date=${encodeURIComponent(report.reportTime)}`)
    } else {
      alert('生成报告失败：' + (json.detail || json.message || '未知错误'))
    }
  } catch (e) {
    alert('请求失败：' + e.message)
  } finally {
    generating.value = false
  }
}

const handleViewReport = (report) => {
  if (!isReportReady(report)) {
    alert('请先完成所有核对通过后再查看报告。')
    return
  }
  router.push(`/report?name=LC%20meeting&date=${encodeURIComponent(report.reportTime)}`)
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&family=Inter:wght@400;500;600&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  vertical-align: middle;
}

:deep(*) {
  box-sizing: border-box;
}

.ia-dashboard-layout {
  position: fixed;
  inset: 0;
  z-index: 9999; 
  display: flex;
  background-color: #f7f9fb;
  font-family: 'Inter', sans-serif;
  color: #191c1e;
  overflow: auto;
  text-align: left;
}

h1, h2, h3, h4, .font-headline {
  font-family: 'Manrope', sans-serif;
}

/* Sidebar */
.ia-sidebar {
  width: 16rem; 
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  overflow-y: auto;
  background-color: #f7f9fb;
  border-right: 1px solid rgba(226, 232, 240, 0.5); 
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
  font-family: 'Manrope', sans-serif;
  font-size: 0.875rem; 
  z-index: 50;
}
.sidebar-header { margin-bottom: 2rem; }
.sidebar-brand-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}
.sidebar-icon {
  width: 2.5rem; height: 2.5rem;
  border-radius: 0.5rem;
  background-color: #0f1c2c;
  display: flex; align-items: center; justify-content: center;
  color: white;
}
.brand-title {
  font-weight: 800; font-size: 1.125rem; color: #0f172a; margin: 0;
}
.brand-subtitle {
  font-size: 0.625rem; font-family: 'Inter', sans-serif; color: #778598;
  text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; margin: 0;
}

.sidebar-nav { flex: 1; display: flex; flex-direction: column; gap: 0.5rem; }
.nav-link {
  display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 1rem;
  color: #64748b; text-decoration: none; border-radius: 0.5rem;
  transition: all 0.2s; font-weight: 500; cursor: pointer;
}
.nav-link:hover { background-color: rgba(242, 244, 246, 0.5); transform: translateX(2px); color: #0f172a;}
.nav-link.active { background-color: #f2f4f6; color: black; font-weight: 700; }

.sidebar-footer {
  margin-top: auto; padding-top: 1.5rem; border-top: 1px solid rgba(226,232,240,0.5);
  display: flex; flex-direction: column; gap: 0.5rem;
}

/* Main */
.ia-main {
  margin-left: 16rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #f7f9fb;
}
.ia-top-nav {
  position: sticky; top: 0; z-index: 40;
  display: flex; justify-content: space-between; align-items: center;
  padding: 0 2rem; height: 4rem; background-color: #f7f9fb;
}
.nav-left { display: flex; align-items: center; gap: 2rem; }
.nav-brand { font-size: 1.25rem; font-weight: 700; color: #0f172a; letter-spacing: -0.025em; }

.search-container { position: relative; display: flex; align-items: center; }
.search-icon { position: absolute; left: 0.75rem; color: #778598; font-size: 1.125rem; }
.search-input {
  padding: 0.375rem 1rem 0.375rem 2.5rem;
  background-color: #f2f4f6; border: none; border-radius: 0.5rem;
  font-size: 0.875rem; width: 16rem; font-family: 'Inter', sans-serif;
  transition: all 0.2s; outline: none;
}
.search-input:focus { box-shadow: 0 0 0 1px #bac8dc; }

.nav-right { display: flex; align-items: center; gap: 1rem; }
.icon-btn {
  background: none; border: none; color: #475569; cursor: pointer;
  padding: 0.5rem; transition: background-color 0.2s; border-radius: 9999px;
  display: flex; align-items: center;
}
.icon-btn:hover { background-color: #f2f4f6; }
.notification-dot { position: absolute; top: 0.5rem; right: 0.5rem; width: 0.5rem; height: 0.5rem; background-color: #ba1a1a; border-radius: 9999px; }
.user-avatar { width: 2rem; height: 2rem; border-radius: 9999px; object-fit: cover; border: 1px solid rgba(196,198,204,0.2); margin-left: 0.5rem; background-color: #e6e8ea;}

/* Content Section */
.content-section {
  padding: 2rem;
  flex: 1;
}

.lcreport-container {
  width: 100%;
  max-width: 1200px;
}

.top-section {
  display: flex;
  justify-content: flex-start;
  gap: 1.5rem;
  align-items: center;
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
  margin-bottom: 2rem;
  border: 1px solid #eaeaea;
}

.filter-group {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.date-picker-wrapper {
  width: 280px;
}

.action-group {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.form-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  font-family: inherit;
}

.btn-primary {
  background-color: #0f1c2c;
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.btn-primary:hover { background-color: #1a2e4a; }

.btn-success {
  background-color: #059669;
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.btn-success:hover { background-color: #047857; }

.btn-warning {
  background-color: #f59e0b;
  color: white;
  border: none;
}

.btn-warning:hover { background-color: #d97706; }

.btn-default {
  background-color: #f1f5f9;
  color: #334155;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  cursor: pointer;
}

.btn-sm {
  padding: 0.3rem 0.6rem;
  font-size: 0.8rem;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  background: #f1f5f9;
  cursor: pointer;
  font-weight: 500;
  color: #334155;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap; /* 防止按钮文字换行导致错位 */
}
.btn-sm:hover { background: #f8fafc; }

.btn-upload {
  background-color: #059669;
  color: white;
  border: none;
}

.btn-upload:hover:not(:disabled) {
  background-color: #047857;
}

.btn-upload:disabled {
  background-color: #94a3b8;
  color: white;
  opacity: 1;
}

.btn-verify {
  background-color: #059669;
  color: white;
  border: none;
}

.btn-verify:hover:not(:disabled) {
  background-color: #047857;
}

.btn-verify:disabled {
  background-color: #94a3b8;
  color: white;
  opacity: 1;
}

.cards-section {
  display: grid;
  /* 自动放 3 列：空间够就 3 列，不够就自动降级到 2/1 列 */
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 1.25rem;
}

.report-card {
  background: white;
  width: 100%;
  display: flex;
  flex-direction: column;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.02);
  overflow: hidden;
  border: 1px solid #eaeaea;
}

.card-header {
  /* 毛玻璃感 */
  background: rgba(5, 150, 105, 0.18);
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(5, 150, 105, 0.35);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-delete-report {
  background: transparent;
  border: none;
  color: #ef4444;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-delete-report:hover {
  background: rgba(239, 68, 68, 0.1);
  transform: scale(1.05);
}

.card-header h3 {
  margin: 0;
  color: #0f172a;
  font-size: 1.1rem;
}

.card-content {
  padding: 1.5rem;
  flex: 1;
}

.card-content h4 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #334155;
  font-size: 1rem;
}

.check-item {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  padding: 0.8rem 0;
  border-bottom: 1px dashed #e2e8f0;
}

.check-item:last-child { border-bottom: none; }

.item-name {
  font-weight: 500;
  color: #475569;
  font-size: 0.95rem;
}

.item-left {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex: 1;
}

.item-actions {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  justify-content: flex-end;
  flex-shrink: 0; /* 保证按钮区域不被挤压导致换行 */
}

.status-icon {
  font-size: 1.2rem;
  width: 24px;
  text-align: center;
}

.card-footer {
  padding: 1.5rem;
  border-top: 1px solid #eaeaea;
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  background-color: #fdfdfd;
}

.card-footer button {
  flex: 1;
}

.btn-generate {
  width: auto;
  font-size: 1rem;
  padding: 0.75rem;
}

.btn-view {
  font-size: 1rem;
  padding: 0.75rem;
  background-color: #059669;
  color: white;
  border: none;
}

.btn-view:hover:not(:disabled) {
  background-color: #047857;
}

.btn-view:disabled {
  background-color: #94a3b8;
  color: white;
  opacity: 1;
  cursor: not-allowed;
}

.btn-sm:disabled,
.btn-primary:disabled,
.btn-default:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-upload:disabled,
.btn-verify:disabled {
  cursor: not-allowed;
}

@media (max-width: 980px) {
  .cards-section {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .cards-section {
    grid-template-columns: 1fr;
  }
}

/* Modals */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(15,23,42,0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  width: 400px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
}

.modal-lg { width: 600px; }

.modal-content h3 { margin-top: 0; margin-bottom: 1.5rem; color: #0f172a; }

.form-group { margin-bottom: 1.5rem; display: flex; flex-direction: column; gap: 0.5rem; }

.help-text { font-size: 0.8rem; color: #64748b; margin: 0; }

.modal-actions { display: flex; justify-content: flex-end; gap: 1rem; }

.data-preview {
  background: #f8fafc; padding: 1rem; border-radius: 6px; margin-bottom: 1.5rem; border: 1px solid #e2e8f0;
}

.mock-table { width: 100%; border-collapse: collapse; margin-top: 1rem; background: white;}
.mock-table th, .mock-table td { border: 1px solid #e2e8f0; padding: 8px; text-align: left; font-size: 0.9rem;}
.mock-table th { background-color: #f1f5f9; font-weight: 600;}

:deep(.dp__action_row),
:deep(.dp__button_bottom) {
  display: none !important;
}

/* ── 状态标签徽章 ────────────────────────────────────── */
.status-badge {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  margin-left: 0.4rem;
  vertical-align: middle;
  letter-spacing: 0.02em;
}

.badge-NOT_IMPORTED {
  background: #f1f5f9;
  color: #64748b;
}

.badge-PARSING {
  background: #fef3c7;
  color: #b45309;
  animation: pulse-badge 1.4s ease-in-out infinite;
}

.badge-UNCHECKED {
  background: #fef3c7;
  color: #92400e;
}

.badge-CHECKED {
  background: #d1fae5;
  color: #065f46;
}

@keyframes pulse-badge {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.55; }
}

/* ── 错误 / 加载提示 ─────────────────────────────────── */
.global-error {
  background: #fff1f2;
  color: #be123c;
  border: 1px solid #fecdd3;
  border-radius: 6px;
  padding: 0.6rem 1rem;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.loading-tip {
  color: #64748b;
  font-size: 0.875rem;
  text-align: center;
  padding: 2rem 0;
}

.error-text {
  color: #be123c;
  font-size: 0.8rem;
  margin: 0.4rem 0 0;
}

.verify-info {
  font-size: 0.9rem;
  color: #334155;
  margin-top: 0.5rem;
}

.verify-info strong {
  color: #0f172a;
}

/* ── 归档状态样式 ─────────────────────────────────────── */
.report-card--archived {
  opacity: 0.85;
  border-left: 3px solid #94a3b8;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

.archived-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: #e2e8f0;
  color: #475569;
  letter-spacing: 0.03em;
}

.archived-tip {
  background: #f1f5f9;
  border: 1px dashed #cbd5e1;
  border-radius: 6px;
  padding: 0.45rem 0.85rem;
  font-size: 0.78rem;
  color: #64748b;
  margin: 0 1rem 0.5rem;
}

/* 卡片头部报告状态标签 */
.status-label-badge {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  margin-left: 0.5rem;
}

.slb-PENDING  { background: #fef9c3; color: #854d0e; }
.slb-DONE     { background: #d1fae5; color: #065f46; }
.slb-ARCHIVED { background: #e2e8f0; color: #475569; }


</style>
