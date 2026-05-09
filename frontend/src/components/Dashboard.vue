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
        <button class="action-btn-primary sidebar-btn" @click="goToGenerateGeneral">
          <span class="material-symbols-outlined text-sm">add_chart</span>
          Generate Report
        </button>
      </div>

      <nav class="sidebar-nav">
        <a class="nav-link" href="#"><span class="material-symbols-outlined">home</span> Home</a>
        <a class="nav-link active" href="#"><span class="material-symbols-outlined">dashboard</span> Dashboard</a>
        <a class="nav-link" style="cursor: pointer;" @click="goToGenerateGeneral"><span class="material-symbols-outlined">description</span> Reports</a>
        <a class="nav-link" style="cursor: pointer;" @click="goToLCReport"><span class="material-symbols-outlined">analytics</span> LCReport</a>
        <a class="nav-link" href="#"><span class="material-symbols-outlined">settings</span> Settings</a>
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
          <span class="nav-brand">Digital Ledger</span>
          <nav class="nav-links-top">
            <a href="#">Portfolio</a>
            <a href="#">Compliance</a>
            <a href="#">Analytics</a>
          </nav>
        </div>
        <div class="nav-right">
          <div class="search-container">
            <span class="material-symbols-outlined search-icon">search</span>
            <input class="search-input" placeholder="Search reports..." type="text"/>
          </div>
          <button class="icon-btn"><span class="material-symbols-outlined">notifications</span></button>
          <button class="icon-btn"><span class="material-symbols-outlined">help_outline</span></button>
          <img alt="User profile" class="user-avatar" src="https://lh3.googleusercontent.com/aida-public/AB6AXuD-Q-am9SazYsIi56Mg7kBUHZ6uL2b_frYKOg1OeBaFLoIsFrFCiAmvS_raDIwzNOuMTm5UMYhiWjETt7AHuzDJsZHxLXczGh8k_mwru1GpTz1BEo2RNRNHiFuEsfwcqa1KjGU8l7el4Jb3a1fPZKYeuT5wEhxf6x8KdVxV1vasBykMuYnu3Ii5lGL5uPuqL8T7H2pDPXZ9FXwLnJ_PgaUTG7ZDoqEeECqgz8CXrlfpny26gPr3ua_BNlJ_R4OZ3jZEtIzaGTn9IGo"/>
        </div>
      </header>

      <!-- Dashboard Body -->
      <div class="ia-content">
        <!-- Hero Title Section -->
        <section class="hero-section">
          <p class="hero-subtitle">Q4 Performance Framework</p>
          <h1 class="hero-title">Reporting & Delivery</h1>
          <p class="hero-desc">Manage institutional data pipelines and automate delivery across morningstar, risk compliance, and internal asset tracking modules.</p>
        </section>

        <!-- Delivery Reports Section -->
        <section class="deliveries-section">
          <div class="section-header-row">
            <h2 class="section-title">Pending Deliveries</h2>
            <span class="reports-active-badge">{{ sortedPendingReports.length }} Reports Active</span>
          </div>

          <div v-if="!isLoadingPending && sortedPendingReports.length > 0" class="cards-grid">
            <div 
              v-for="report in sortedPendingReports" 
              :key="report.config_id"
              class="report-card group hover-shadow"
              @click="rotateStack(report)"
            >
              <div v-for="(record, index) in report.records" :key="record.id" :style="getStackStyle(index, report.activeIndex || 0, report.records.length, recordBorderColor(record.status))" class="stack-item">
                <div class="card-top">
                  <span :class="['freq-badge', getFrequencyBadgeClass(report.frequency)]">{{ report.frequency }}</span>
                  <span :class="['status-badge', getStatusColorClass(record.status)]">
                    <span class="material-symbols-outlined icon-fill">{{ getStatusIcon(record.status) }}</span>
                    {{ getStatusText(record.status) }}
                  </span>
                </div>
                
                <h3 class="card-title">{{ getDisplayName(report.name) }}</h3>
                
                <div class="card-details">
                  <div class="detail-row">
                    <span class="detail-label">Report Date</span>
                    <span class="detail-value">{{ record.report_date }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="detail-label">Delivery Date</span>
                    <span class="detail-value">{{ record.deadline }}</span>
                  </div>
                  
                  <div v-if="record.status === '待提交'" class="detail-row">
                    <span class="detail-label">Time Left</span>
                    <span class="detail-value text-error font-bold">{{ record.daysRemaining }} Days</span>
                  </div>
                  <div v-else class="detail-row">
                    <span class="detail-label">Submit Date</span>
                    <span class="detail-value">{{ record.submitted_at || '-' }}</span>
                  </div>
                </div>
                
                <div class="card-actions">
                  <button 
                    v-if="record.status === '待提交'" 
                    class="btn-fill-primary w-full"
                    @click.stop="goToSubmit(report)"
                  >
                    <span class="material-symbols-outlined text-sm">upload_file</span>
                    Submit Report
                  </button>
                  <template v-else-if="record.status === '已提交'">
                    <button class="btn-light flex-1" @click.stop="viewReportFromCard(report, record)">View Report</button>
                    <button class="btn-outline flex-1" @click.stop="goToSubmit(report)">Resubmit</button>
                  </template>
                  <template v-else>
                    <button class="btn-outline-primary w-full" @click.stop="viewReportFromCard(report, record)">
                      <span class="material-symbols-outlined text-sm">edit_square</span> Draft Report
                    </button>
                  </template>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="loading-text">
            Loading delivery reports...
          </div>
        </section>

        <!-- Historical Delivered Reports Section -->
        <section class="history-section">
          <div class="section-header-row">
            <h2 class="section-title">Historical Delivered Reports</h2>
            <div class="history-actions">
              <div class="search-filter-box">
                <span class="material-symbols-outlined">filter_list</span>
                <input type="text" v-model="searchQuery" placeholder="Filter..." />
              </div>
              <button class="btn-outline icon-text-btn">
                <span class="material-symbols-outlined">download</span> Export
              </button>
            </div>
          </div>
          
          <div class="table-card">
            <table class="ia-table">
              <thead>
                <tr>
                  <th>Report Name</th>
                  <th>Frequency</th>
                  <th>Report Date</th>
                  <th>Delivery Date</th>
                  <th>Submit Date</th>
                  <th>Status</th>
                  <th class="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="isLoadingHistory">
                  <td colspan="7" class="text-center py-4 text-slate-400">Loading history reports...</td>
                </tr>
                <tr v-else-if="paginatedHistory.length === 0">
                  <td colspan="7" class="text-center py-4 text-slate-400">No historical reports found.</td>
                </tr>
                <tr v-for="(item, index) in paginatedHistory" :key="item.id" :class="index % 2 !== 0 ? 'bg-stripe' : ''">
                  <td class="font-bold text-slate-900">{{ item.name }}</td>
                  <td><span :class="['freq-badge-sm', getHistoryListFrequencyClass(item.frequency)]">{{ item.frequency }}</span></td>
                  <td>{{ item.reportDate }}</td>
                  <td>{{ item.deliveryDate }}</td>
                  <td>{{ item.submittedAt || '-' }}</td>
                  <td>
                    <span class="status-inline-badge">
                      <div class="dot bg-tertiary"></div> Delivered
                    </span>
                  </td>
                  <td class="text-right">
                    <a class="action-link" @click="viewReport(item)">Download</a>
                  </td>
                </tr>
              </tbody>
            </table>
            
            <div class="table-footer">
              <span>Showing {{ Math.min(((currentPage - 1) * itemsPerPage + 1), filteredHistory.length) }} to {{ Math.min(currentPage * itemsPerPage, filteredHistory.length) }} of {{ filteredHistory.length }} reports</span>
              <div class="pagination-group">
                <button :disabled="currentPage === 1" @click="currentPage--">Previous</button>
                <button v-for="page in displayedPages" :key="page" 
                  :class="['page-btn', currentPage === page ? 'active' : '']"
                  @click="currentPage = page">{{ page }}</button>
                <button :disabled="currentPage === totalPages || totalPages === 0" @click="currentPage++">Next</button>
              </div>
            </div>
          </div>
        </section>

      </div>
      
      <!-- Footer -->
      <footer class="ia-footer">
        <p class="footer-copy">© 2024 Digital Ledger Institutional. All rights reserved.</p>
        <div class="footer-links">
          <a href="#">Privacy Policy</a>
          <a href="#">Terms of Service</a>
          <a href="#">SEC Disclosures</a>
        </div>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const goToGenerateGeneral = () => {
  router.push('/generate')
}

const goToLCReport = () => {
  router.push('/lcreport')
}

const handleLogout = () => {
  localStorage.removeItem('isAuthenticated')
  localStorage.removeItem('currentUser')
  router.push('/login')
}

const getDisplayName = (name) => {
  const betaReports = [
    'Risk Reporting',
    'Asset Concentration Risk',
    'AUM',
    'Morningstart Report',
    'Morningstar Report'
  ]
  return betaReports.includes(name) ? `${name} Beta` : name
}

const pendingReports = ref([])
const historicalReports = ref([])
const isLoadingPending = ref(true)
const isLoadingHistory = ref(true)
const pendingSortBy = ref('deadline')

const fetchPendingReports = async () => {
  try {
    isLoadingPending.value = true
    const response = await fetch('/api/dashboard/pending')
    if (response.ok) {
      pendingReports.value = await response.json()
    } else {
      console.error('Failed to fetch pending reports')
    }
  } catch (error) {
    console.error('Error fetching pending reports:', error)
  } finally {
    isLoadingPending.value = false
  }
}

const fetchHistoryReports = async () => {
  try {
    isLoadingHistory.value = true
    const response = await fetch('/api/dashboard/history')
    if (response.ok) {
      historicalReports.value = await response.json()
    } else {
      console.error('Failed to fetch history reports')
    }
  } catch (error) {
    console.error('Error fetching history reports:', error)
  } finally {
    isLoadingHistory.value = false
  }
}

onMounted(() => {
  fetchPendingReports()
  fetchHistoryReports()
})

const searchQuery = ref('')
const currentPage = ref(1)
const itemsPerPage = 6

const filteredHistory = computed(() => {
  return historicalReports.value
    .filter(item => item.name.toLowerCase().includes(searchQuery.value.toLowerCase()))
    .sort((a, b) => new Date(b.submittedAt) - new Date(a.submittedAt))
})

const totalPages = computed(() => Math.ceil(filteredHistory.value.length / itemsPerPage))

const displayedPages = computed(() => {
  const maxPages = 3;
  let start = Math.max(1, currentPage.value - Math.floor(maxPages / 2));
  let end = start + maxPages - 1;

  if (end > totalPages.value) {
    end = totalPages.value;
    start = Math.max(1, end - maxPages + 1);
  }

  const pages = [];
  for (let i = start; i <= end; i++) {
    pages.push(i);
  }
  return pages;
});

const paginatedHistory = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  return filteredHistory.value.slice(start, start + itemsPerPage)
})

const sortedPendingReports = computed(() => {
  const reports = [...pendingReports.value]
  if (pendingSortBy.value === 'name') {
    return reports.sort((a, b) => a.name.localeCompare(b.name, 'zh'))
  } else {
    // Default sort by Time Remaining
    return reports.sort((a, b) => {
      // 1. Status priority: Pending (0) < Submitted (1)
      const statusA = a.status === 'Pending' ? 0 : 1
      const statusB = b.status === 'Pending' ? 0 : 1
      if (statusA !== statusB) return statusA - statusB
      
      // 2. Tie-breakers based on status
      if (statusA === 0) {
        // Both Pending: daysRemaining ascending (shortest first)
        return a.topDaysRemaining - b.topDaysRemaining
      } else {
        // Both Submitted: submitted_at ascending (earliest first)
        const dateA = (a.records && a.records[0] && a.records[0].submitted_at) || ''
        const dateB = (b.records && b.records[0] && b.records[0].submitted_at) || ''
        return dateA.localeCompare(dateB)
      }
    })
  }
})

const recordBorderColor = (status) => {
  if (status === '待提交') return '#ba1a1a'; // error red
  if (status === '已提交') return '#00210c'; // submitted green dark
  return '#1e293b'; 
}

const getFrequencyBadgeClass = (freq) => {
  if (freq?.toLowerCase().includes('month')) return 'bg-tertiary-fixed text-on-tertiary-fixed-variant'
  if (freq?.toLowerCase().includes('week')) return 'bg-primary-fixed text-on-primary-fixed-variant'
  if (freq?.toLowerCase().includes('quarter')) return 'bg-tertiary-fixed text-on-tertiary-fixed-variant'
  if (freq?.toLowerCase().includes('annual')) return 'bg-secondary-container text-on-secondary-container'
  return 'bg-surface-container-high text-on-surface-variant'
}

const getHistoryListFrequencyClass = (freq) => {
  if (freq?.toLowerCase().includes('month')) return 'bg-primary-fixed text-on-primary-fixed-variant font-bold'
  if (freq?.toLowerCase().includes('week')) return 'bg-secondary-container text-on-secondary-container'
  if (freq?.toLowerCase().includes('quarter')) return 'bg-surface-container-high text-on-surface-variant'
  return 'bg-surface-container-high text-on-surface-variant'
}


const getStatusIcon = (status) => {
  if (status === '待提交') return 'error'
  if (status === '已提交') return 'check_circle'
  return 'schedule'
}

const getStatusColorClass = (status) => {
  if (status === '待提交') return 'text-error'
  if (status === '已提交') return 'text-on-tertiary-container'
  return 'text-on-primary-container'
}

const getStatusText = (status) => {
  if (status === '待提交') return 'To Submit'
  if (status === '已提交') return 'Submitted'
  return status || 'Pending'
}

const rotateStack = (report) => {
  if (report.records && report.records.length > 1) {
    if (typeof report.activeIndex === 'undefined') {
      report.activeIndex = 0
    }
    report.activeIndex = (report.activeIndex + 1) % report.records.length
  }
}

const getStackStyle = (index, activeIndex, total, color) => {
  const relIndex = (index - activeIndex + total) % total
  if (relIndex > 2) return { display: 'none' }
  const isTop = relIndex === 0
  return {
    position: isTop ? 'relative' : 'absolute',
    top: isTop ? 'auto' : `-${relIndex * 6}px`,
    left: isTop ? 'auto' : `${relIndex * 4}px`,
    right: isTop ? 'auto' : `-${relIndex * 4}px`,
    bottom: isTop ? 'auto' : `-${relIndex * 6}px`,
    transform: isTop ? 'none' : `scale(${1 - relIndex * 0.02})`,
    zIndex: total - relIndex,
    opacity: isTop ? 1 : (1 - relIndex * 0.15),
    borderTopColor: isTop ? 'transparent' : color,
    borderTopWidth: isTop ? '0' : '3px',
    borderTopStyle: 'solid',
    pointerEvents: isTop ? 'auto' : 'none',
    boxShadow: isTop ? 'none' : '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
    transition: 'all 0.3s ease-in-out',
    backgroundColor: '#fff',
    width: '100%',
    height: '100%'
  }
}

const goToSubmit = (report) => {
  const activeIndex = report.activeIndex || 0
  const currentRecord = report.records[activeIndex]
  const reportDate = currentRecord ? currentRecord.report_date : ''
  router.push(`/generate?report=${encodeURIComponent(report.name)}&date=${encodeURIComponent(reportDate)}`)
}

const viewReportFromCard = (report, record) => {
  router.push(`/report?name=${encodeURIComponent(report.name)}&date=${record.report_date}`)
}

const viewReport = (item) => {
  router.push(`/report?name=${encodeURIComponent(item.name)}&date=${item.reportDate}`)
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

:deep(*) {
  box-sizing: border-box;
}

.ia-dashboard-layout {
  position: fixed;
  inset: 0;
  z-index: 9999; /* Cover App.vue navbar completely */
  display: flex;
  background-color: #f7f9fb;
  font-family: 'Inter', sans-serif;
  color: #191c1e;
  overflow: hidden;
}

h1, h2, h3, .font-headline {
  font-family: 'Manrope', sans-serif;
}

/* Sidebar */
.ia-sidebar {
  width: 16rem; /* 256px */
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  overflow-y: auto;
  background-color: #f7f9fb;
  border-right: 1px solid rgba(226, 232, 240, 0.5); /* slate-200 / 50% kinda */
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
  font-family: 'Manrope', sans-serif;
  font-size: 0.875rem; /* 14px */
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
.action-btn-primary {
  width: 100%; padding: 0.75rem 1rem;
  background-color: #349557; color: white;
  border-radius: 0.5rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center; gap: 0.5rem;
  border: none; cursor: pointer; transition: transform 0.2s;
  font-family: 'Inter', sans-serif; font-size: 0.875rem;
}
.action-btn-primary:active { transform: scale(0.97); }

.sidebar-nav { flex: 1; display: flex; flex-direction: column; gap: 0.25rem; }
.nav-link {
  display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 1rem;
  color: #64748b; text-decoration: none; border-radius: 0.5rem;
  transition: all 0.2s; font-weight: 500;
}
.nav-link:hover { background-color: rgba(242, 244, 246, 0.5); transform: translateX(2px); color: #0f172a;}
.nav-link.active {
  background-color: #f2f4f6; color: black; font-weight: 700;
}

.sidebar-footer {
  margin-top: auto; padding-top: 1.5rem; border-top: 1px solid rgba(226,232,240,0.5);
  display: flex; flex-direction: column; gap: 0.25rem;
}

/* Main */
.ia-main {
  margin-left: 16rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #f7f9fb;
  overflow-y: auto;
}
.ia-top-nav {
  position: sticky; top: 0; z-index: 50;
  display: flex; justify-content: space-between; align-items: center;
  padding: 0 2rem; height: 4rem; background-color: #f7f9fb;
}
.nav-left { display: flex; align-items: center; gap: 2rem; }
.nav-brand { font-size: 1.25rem; font-weight: 700; color: #0f172a; letter-spacing: -0.025em; }
.nav-links-top { display: none; gap: 1.5rem; font-family: 'Manrope', sans-serif; font-size: 0.875rem; font-weight: 500;}
@media (min-width: 768px) { .nav-links-top { display: flex; } }
.nav-links-top a { color: #64748b; text-decoration: none; transition: color 0.2s; }
.nav-links-top a:hover { color: black; }

.nav-right { display: flex; align-items: center; gap: 1rem; }
.search-container { position: relative; display: flex; align-items: center; }
.search-icon { position: absolute; left: 0.75rem; color: #778598; font-size: 1.125rem; }
.search-input {
  padding: 0.375rem 1rem 0.375rem 2.5rem;
  background-color: #f2f4f6; border: none; border-radius: 9999px;
  font-size: 0.875rem; width: 16rem; font-family: 'Inter', sans-serif;
  transition: all 0.2s; outline: none;
}
.search-input:focus { box-shadow: 0 0 0 2px #bac8dc; }

.icon-btn {
  background: none; border: none; color: #778598; cursor: pointer;
  padding: 0.5rem; transition: color 0.2s; display: flex; align-items: center;
}
.icon-btn:hover { color: black; }
.icon-btn:active { transform: scale(0.95); }
.user-avatar { width: 2rem; height: 2rem; border-radius: 9999px; object-fit: cover; margin-left: 0.5rem; }

/* Content */
.ia-content { padding: 2.5rem; display: flex; flex-direction: column; gap: 3rem; text-align: left; }

.hero-subtitle { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #349557; margin: 0 0 0.5rem 0; }
.hero-title { font-size: 2.75rem; font-weight: 800; line-height: 1.2; color: #191c1e; margin: 0 0 0.5rem 0; }
.hero-desc { color: #44474c; max-width: 42rem; font-size: 0.875rem; margin: 0; line-height: 1.5; text-align: left;}

.section-header-row { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 2rem; }
.section-title { font-size: 1.25rem; font-weight: 700; color: #191c1e; margin: 0; text-align: left;}
.reports-active-badge { font-size: 0.75rem; font-weight: 600; color: #778598; padding: 0.25rem 0.75rem; background-color: #e6e8ea; border-radius: 9999px; }

/* Grid & Cards */
.cards-grid { display: grid; grid-template-columns: repeat(1, 1fr); gap: 1.5rem; text-align: left; }
@media(min-width: 768px){ .cards-grid { grid-template-columns: repeat(2, 1fr); } }
@media(min-width: 1024px){ .cards-grid { grid-template-columns: repeat(3, 1fr); } }

.report-card {
  position: relative;
  border-radius: 0.75rem;
  background-color: transparent;
  cursor: pointer;
  min-height: 240px;
}
.stack-item {
  background-color: #ffffff;
  border-radius: 0.75rem;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 40px -10px rgba(25, 28, 30, 0.05);
  box-sizing: border-box;
}

.report-card:hover .stack-item { background-color: #ffffff; }

.card-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; }
.freq-badge { padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.625rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; line-height: 1;}
.freq-badge-sm { padding: 0.125rem 0.5rem; border-radius: 9999px; font-size: 0.625rem; font-weight: 500; display: inline-block;}

.bg-tertiary-fixed { background-color: #96f7af; }
.text-on-tertiary-fixed-variant { color: #005228; }
.bg-primary-fixed { background-color: #d6e4f9; }
.text-on-primary-fixed-variant { color: #3a4859; }
.bg-surface-container-high { background-color: #e6e8ea; }
.text-on-surface-variant { color: #44474c; }
.bg-secondary-container { background-color: #d5e3fc; }
.text-on-secondary-container { color: #57657a; }

.status-badge { display: flex; align-items: center; gap: 0.25rem; font-size: 0.75rem; font-weight: 700; }
.text-error { color: #ba1a1a; }
.text-on-tertiary-container { color: #349557; }
.text-on-primary-container { color: #778598; }

.icon-fill { font-variation-settings: 'FILL' 1; font-size: 0.875rem;}
.card-title { font-size: 1.125rem; font-weight: 700; margin: 0 0 1rem 0; color: #0f172a; }

.card-details { display: flex; flex-direction: column; gap: 0.75rem; margin-bottom: 1.5rem; flex: 1; justify-content: flex-end;}
.detail-row { display: flex; justify-content: space-between; font-size: 0.75rem; }
.detail-label { color: #778598; }
.detail-value { font-weight: 500; color: #0f172a; }
.font-bold { font-weight: 700; }

.card-actions { display: flex; gap: 0.5rem; width: 100%; margin-top: auto;}
.btn-fill-primary {
  width: 100%; padding: 0.625rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: 700;
  background-color: #000; color: #fff; border: none; cursor: pointer; transition: opacity 0.2s;
  display: flex; justify-content: center; align-items: center; gap: 0.5rem; font-family: 'Inter', sans-serif;
  text-decoration: none;
}
.btn-fill-primary:hover { opacity: 0.9; }

.btn-light {
  flex: 1; padding: 0.625rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: 700;
  background-color: #f2f4f6; color: #191c1e; border: none; cursor: pointer; transition: background 0.2s;
  font-family: 'Inter', sans-serif;
  display: flex; justify-content: center; align-items: center; gap: 0.5rem;
}
.btn-light:hover { background-color: #e6e8ea; }
.btn-outline {
  flex: 1; padding: 0.625rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: 700;
  background-color: #fff; color: #191c1e; border: 1px solid rgba(196, 198, 204, 0.5); cursor: pointer; transition: border-color 0.2s;
  font-family: 'Inter', sans-serif;
  display: flex; justify-content: center; align-items: center; gap: 0.5rem;
}
.btn-outline:hover { border-color: #74777d; }
.btn-outline-primary {
  width: 100%; padding: 0.625rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: 700;
  background-color: #fff; color: #000; border: 1px solid rgba(0,0,0,0.2); cursor: pointer; transition: all 0.2s;
  display: flex; justify-content: center; align-items: center; gap: 0.5rem; font-family: 'Inter', sans-serif;
}
.btn-outline-primary:hover { background-color: #0f1c2c; color: #fff; }

.loading-text { text-align: center; color: #94a3b8; padding: 2.5rem 0; font-family: 'Inter'; font-size: 0.875rem; font-weight: 500;}

/* History Section */
.history-actions { display: flex; gap: 0.75rem; }
.search-filter-box { position: relative; }
.search-filter-box span { position: absolute; left: 0.5rem; top: 0.5rem; font-size: 0.875rem; color: #94a3b8; }
.search-filter-box input {
  padding: 0.5rem 1rem 0.5rem 2rem; font-size: 0.75rem; border: 1px solid #e2e8f0; border-radius: 0.5rem; outline: none; transition: border-color 0.2s;
  width: 12rem;
}
.search-filter-box input:focus { border-color: #bac8dc; box-shadow: 0 0 0 1px #bac8dc; }
.icon-text-btn { display: flex; align-items: center; gap: 0.5rem; font-size: 0.75rem; padding: 0.5rem 1rem; border-radius: 0.5rem;}
.icon-text-btn span { font-size: 0.875rem; }

.table-card { background: white; border-radius: 0.75rem; box-shadow: 0 24px 40px -10px rgba(25, 28, 30, 0.05); overflow: hidden; width: 100%;}
.ia-table { width: 100%; border-collapse: collapse; text-align: left; }
.ia-table th { padding: 1rem 1.5rem; font-size: 0.6875rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; color: #778598; background-color: #f2f4f6; }
.ia-table td { padding: 1rem 1.5rem; font-size: 0.875rem; color: #44474c; border-bottom: 1px solid #f2f4f6;}
.text-right { text-align: right; }
.bg-stripe { background-color: rgba(242, 244, 246, 0.3); text-align: left; }
.ia-table tr:hover { background-color: rgba(242, 244, 246, 0.7); }
.status-inline-badge { display: flex; align-items: center; gap: 0.375rem; font-weight: 600; color: #349557; }
.dot { width: 0.5rem; height: 0.5rem; border-radius: 9999px; }
.bg-tertiary { background-color: #349557; }
.action-link { color: #3a4859; font-weight: 700; text-decoration: none; cursor: pointer; }
.action-link:hover { text-decoration: underline; }
.text-center { text-align: center; }

.table-footer { display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.5rem; font-size: 0.75rem; color: #778598; font-weight: 500; border-top: 1px solid #e6e8ea;}
.pagination-group { display: flex; gap: 0.5rem; }
.pagination-group button { padding: 0.25rem 0.75rem; border: 1px solid rgba(196,198,204,0.5); border-radius: 0.25rem; background: white; cursor: pointer; transition: background 0.2s;}
.pagination-group button:disabled { opacity: 0.5; cursor: not-allowed; }
.pagination-group button:hover:not(:disabled) { background-color: #f2f4f6; }
.page-btn.active { background-color: #000 !important; color: white !important; border-color: #000; }

.ia-footer { margin-top: auto; padding: 2rem 3rem; border-top: 1px solid rgba(226,232,240,0.5); display: flex; justify-content: space-between; align-items: center; background-color: #f7f9fb;}
.footer-copy { font-family: 'Inter', sans-serif; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; margin: 0; }
.footer-links { display: flex; gap: 2rem; font-family: 'Inter', sans-serif; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }
.footer-links a { color: #94a3b8; text-decoration: none; transition: color 0.2s; }
.footer-links a:hover { color: #059669; }

/* Custom Scrollbar for Sidebar */
.ia-sidebar::-webkit-scrollbar { width: 4px; }
.ia-sidebar::-webkit-scrollbar-track { background: transparent; }
.ia-sidebar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.ia-sidebar::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>
