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
        <a class="nav-link" href="#"><span class="material-symbols-outlined">home</span> Home</a>
        <router-link to="/" class="nav-link"><span class="material-symbols-outlined">dashboard</span> Dashboard</router-link>
        <router-link to="/generate" class="nav-link active"><span class="material-symbols-outlined">description</span> Reports</router-link>
        <a class="nav-link" href="#"><span class="material-symbols-outlined">settings</span> Settings</a>
      </nav>

      <div class="sidebar-footer">
        <a class="nav-link" href="#"><span class="material-symbols-outlined">contact_support</span> Support</a>
        <a class="nav-link" href="#"><span class="material-symbols-outlined">logout</span> Sign Out</a>
      </div>
    </aside>

    <!-- Main Content Canvas -->
    <main class="ia-main">
      <!-- TopNavBar -->
      <header class="ia-top-nav">
        <div class="nav-left">
          <span class="nav-brand">Portfolio</span>
          <nav class="nav-links-top">
            <a href="#">Compliance</a>
            <a href="#">Analytics</a>
          </nav>
        </div>
        <div class="nav-right">
          <div class="search-container">
            <span class="material-symbols-outlined search-icon">search</span>
            <input class="search-input" placeholder="Search portfolios..." type="text"/>
          </div>
          <button class="icon-btn relative">
            <span class="material-symbols-outlined">notifications</span>
            <span class="notification-dot"></span>
          </button>
          <button class="icon-btn"><span class="material-symbols-outlined">help_outline</span></button>
          <img alt="User profile" class="user-avatar" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAPQN0l-TQg4rhuEA2VKujdTzbncXPN9KD7vxRZTahAsjRUxv_hzWVDmYt-hRT_TfpIiyscZ3xP9_76v_pnn6IgKq7Mz4w9A9WujS1nqAe_OAIFYzupB5L-Al6Tg6wKOOox5Q6IRRASqLzxDQwWa0mBG0as2LXMicB1nG7CcT4ziT1wvDBOsd7djfYc59CtMiEJ4VAJPw5nfdxCc1v3THDoWKwa4Xqso-a2yuNFaPrn9Mg7rnwcyAfTJY14QkTGxwmeAPltJyZdNHA"/>
        </div>
      </header>

      <!-- Form Canvas Section -->
      <section class="form-canvas-section">
        <div class="form-canvas-wrapper">
          <!-- Header Section -->
          <div class="form-header-sec">
            <h2 class="form-main-title">Generate Fund Report</h2>
            <p class="form-main-desc">Configure institutional-grade reports with real-time data integration.</p>
          </div>

          <!-- Form Card -->
          <div class="styled-form-card group">
            <div style="position: absolute; inset: 0; border-radius: inherit; overflow: hidden; pointer-events: none;">
              <div class="glassy-accent"></div>
            </div>
            
            <form class="form-content" @submit.prevent>
              <!-- Field: Report Name -->
              <div class="input-group">
                <label for="reportName" class="ia-label">Report Template</label>
                <div class="relative flex-col">
                  <select id="reportName" v-model="form.reportName" class="ia-input ia-select">
                    <option v-for="opt in sortedReportOptions" :key="opt.id" :value="opt.name">
                      {{ opt.name }}
                    </option>
                  </select>
                  <span class="material-symbols-outlined dropdown-icon">expand_more</span>
                </div>
              </div>

              <!-- Field: Report Date -->
              <div class="input-group">
                <label class="ia-label">Reporting Period End Date</label>
                <div class="relative custom-datepicker-wrapper" :class="{ 'has-error': dateError }">
                  <span class="material-symbols-outlined input-icon" style="z-index: 10;">calendar_today</span>
                  <VueDatePicker 
                    v-model="form.reportDate"
                    model-type="yyyy-MM-dd"
                    format="yyyy-MM-dd"
                    :disabled-dates="disabledDates"
                    :enable-time-picker="false"
                    :time-picker="false"
                    :time-config="{ enableTimePicker: false }"
                    :auto-apply="true"
                    placeholder="mm/dd/yyyy"
                    input-class-name="ia-dp-input"
                  />
                </div>
                <p v-if="dateError" class="ia-error-msg">{{ dateError }}</p>
              </div>

              <!-- Field: Feishu Doc Link -->
              <div class="input-group">
                <label for="feishuLink" class="ia-label">Feishu Doc Destination URL</label>
                <div class="relative">
                  <span class="material-symbols-outlined input-icon">link</span>
                  <input 
                    type="url" 
                    id="feishuLink" 
                    v-model="form.feishuLink" 
                    placeholder="https://feishu.cn/docs/..." 
                    class="ia-input ia-pl-input" 
                  />
                </div>
                <p class="ia-hint-msg">Ensure the service account has 'Edit' permissions for this document.</p>
              </div>

              <div v-if="error" class="ia-error-msg" style="text-align: center; margin-top:-10px;">
                {{ error }}
              </div>

              <!-- Action Button -->
              <div class="pt-4">
                <button 
                  class="ia-submit-btn group-hover-btn" 
                  @click="generateReport" 
                  :disabled="loading || !!dateError"
                  :class="{ 'is-loading': loading }"
                >
                  <span class="material-symbols-outlined sync-icon">sync</span>
                  {{ loading ? 'Generating...' : 'Generate Report' }}
                </button>
              </div>
            </form>
          </div>

          <!-- Helper Text -->
          <div class="helper-text-container">
            <div class="helper-item">
              <span class="material-symbols-outlined">verified_user</span>
              <span>SEC Compliant</span>
            </div>
            <div class="helper-item">
              <span class="material-symbols-outlined">encrypted</span>
              <span>End-to-End Encryption</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Footer -->
      <footer class="ia-footer">
        <div class="footer-links">
          <a href="#">Privacy Policy</a>
          <a href="#">Terms of Service</a>
          <a href="#">SEC Disclosures</a>
        </div>
        <p class="footer-copy">© 2024 Digital Ledger Institutional. All rights reserved.</p>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { VueDatePicker } from '@vuepic/vue-datepicker';
import '@vuepic/vue-datepicker/dist/main.css';

const router = useRouter();
const route = useRoute();

const reportOptions = ref([]);

const sortedReportOptions = computed(() => {
  return [...reportOptions.value].sort((a, b) => a.name.localeCompare(b.name, 'zh'));
});

const form = ref({
  reportName: '',
  reportDate: '',
  feishuLink: ''
});

const selectedConfig = computed(() => {
  return reportOptions.value.find(opt => opt.name === form.value.reportName);
});

const dateError = computed(() => {
  if (!form.value.reportDate || !selectedConfig.value) return '';
  
  // Use manual parsing to avoid timezone shifts (YYYY-MM-DD)
  const [year, month, day] = form.value.reportDate.split('-').map(Number);
  const date = new Date(year, month - 1, day);
  
  const freq = selectedConfig.value.frequency;

  if (freq === 'Weekly') {
    // getDay() returns 0 for Sunday, 5 for Friday
    if (date.getDay() !== 5) {
      return 'Report date must be a Friday for Weekly reports.';
    }
  } else if (freq === 'Monthly') {
    // Check if it's the last day of the month by checking if tomorrow is first day of next month
    const nextDay = new Date(year, month - 1, day + 1);
    if (nextDay.getMonth() !== month - 1) {
      // It's the last day
      return '';
    } else {
      return 'Report date must be the last day of the month for Monthly reports.';
    }
  }
  return '';
});

const disabledDates = (date) => {
  if (!selectedConfig.value) return false;
  const freq = selectedConfig.value.frequency;

  if (freq === 'Weekly') {
    // getDay() returns 0 for Sunday, 5 for Friday
    return date.getDay() !== 5;
  } else if (freq === 'Monthly') {
    // Check if it's NOT the last day of the month
    const m = date.getMonth();
    const tomorrow = new Date(date);
    tomorrow.setDate(date.getDate() + 1);
    return tomorrow.getMonth() === m;
  }
  return false;
};

watch(() => form.value.reportName, (newName) => {
  if (newName) {
    const nameLower = newName.toLowerCase();
    if (nameLower.includes('lc meeting') || nameLower.includes('lc_meeting')) {
      form.value.feishuLink = 'https://zcngcv5c3qrq.feishu.cn/sheets/C5UzsBNnzhgfVwto4hlcAylXnte';
    } else if (nameLower.includes('factsheet') || nameLower.includes('fact sheet')) {
      form.value.feishuLink = 'https://zcngcv5c3qrq.feishu.cn/sheets/ZZA6sh2ddhyJAot4Rozc5unxnvh';
    } else {
      form.value.feishuLink = 'https://zcngcv5c3qrq.feishu.cn/sheets/TbWosRwq9h0lPrtjlblcr9sVnJf';
    }
  }

  // If the currently selected date becomes invalid for the new report, clear it or signal error
  if (form.value.reportName && form.value.reportDate && dateError.value) {
    // We keep the date but the user will see the error message and button will be disabled
  }
}, { immediate: true });

onMounted(async () => {
  try {
    const res = await fetch('/api/report_configs');
    if (res.ok) {
      reportOptions.value = await res.json();
    }
  } catch (err) {
    console.error('Failed to fetch report configs', err);
  }

  if (route.query.report) {
    const selected = route.query.report;
    const exists = reportOptions.value.find(r => r.name === selected);
    if (!exists) {
       reportOptions.value.push({ id: Date.now(), name: selected });
    }
    form.value.reportName = selected;
  } else if (reportOptions.value.length > 0) {
    form.value.reportName = reportOptions.value[0].name;
  }

  if (route.query.date) {
    form.value.reportDate = route.query.date;
  }
});

const loading = ref(false);
const error = ref('');

async function generateReport() {
  if (!form.value.reportDate) {
    error.value = 'Please select a report date.';
    return;
  }
  if (!form.value.feishuLink) {
    error.value = 'Please input the Feishu doc link.';
    return;
  }

  error.value = '';
  loading.value = true;

  try {
    const response = await fetch('/api/generate_report', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        report_name: form.value.reportName,
        report_date: form.value.reportDate,
        feishu_link: form.value.feishuLink
      })
    });

    if (!response.ok) {
      const errData = await response.json();
      if (errData.detail === 'under_development') {
        alert('该报告功能正在开发中，敬请期待！');
        return;
      }
      throw new Error(errData.detail || 'Failed to generate report');
    }

    const data = await response.json();
    
    // On success, redirect to the report page with the date and name
    router.push(`/report?name=${encodeURIComponent(form.value.reportName)}&date=${encodeURIComponent(data.date)}`);
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
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

h1, h2, h3, .font-headline {
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
  transition: all 0.2s; font-weight: 500;
}
.nav-link:hover { background-color: rgba(242, 244, 246, 0.5); transform: translateX(2px); color: #0f172a;}
.nav-link.active {
  background-color: #f2f4f6; color: black; font-weight: 700;
}

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
.nav-links-top { display: none; gap: 1.5rem; font-family: 'Manrope', sans-serif; font-size: 0.875rem; font-weight: 500;}
@media (min-width: 768px) { .nav-links-top { display: flex; } }
.nav-links-top a { color: #64748b; text-decoration: none; transition: color 0.2s; }
.nav-links-top a:hover { color: black; }
.nav-links-top a.nav-active { color: black; font-weight: 700; }

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

/* Form Canvas */
.form-canvas-section {
  flex-grow: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem;
}
.form-canvas-wrapper { width: 100%; max-width: 36rem; }
.form-header-sec { text-align: center; margin-bottom: 2.5rem; }
.form-main-title { font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 1.875rem; color: #191c1e; margin: 0 0 0.5rem 0; letter-spacing: -0.025em; }
.form-main-desc { font-family: 'Inter', sans-serif; color: #778598; margin: 0; }

.styled-form-card {
  background-color: #ffffff;
  border-radius: 0.75rem;
  padding: 2rem;
  box-shadow: 0 32px 64px -12px rgba(0,0,0,0.04);
  position: relative;
}
.glassy-accent {
  position: absolute; top: -4rem; right: -4rem; width: 8rem; height: 8rem;
  background-color: rgba(122, 218, 149, 0.1); 
  filter: blur(24px); border-radius: 9999px;
  transition: all 0.7s;
}
.styled-form-card:hover .glassy-accent { background-color: rgba(122, 218, 149, 0.2); }
.form-content { position: relative; z-index: 10; display: flex; flex-direction: column; gap: 2rem; }

.input-group { display: flex; flex-direction: column; gap: 0.5rem; }
.ia-label { font-family: 'Manrope', sans-serif; font-weight: 700; font-size: 0.875rem; color: #44474c; text-transform: uppercase; letter-spacing: 0.05em; margin:0;}

.relative { position: relative; }
.ia-input {
  width: 100%; background-color: #f2f4f6; border: none; border-radius: 0.5rem;
  padding: 0.875rem 1rem; color: #191c1e; font-family: 'Inter', sans-serif;
  transition: box-shadow 0.2s; outline: none; box-sizing: border-box;
}
.ia-input:focus { box-shadow: 0 0 0 2px rgba(52, 149, 87, 0.2); }
.ia-pl-input { padding-left: 3.5rem; }
.ia-select { appearance: none; cursor: pointer; }
.dropdown-icon { position: absolute; right: 1rem; top: 50%; transform: translateY(-50%); pointer-events: none; color: #778598; }
.input-icon { position: absolute; left: 1.25rem; top: 50%; transform: translateY(-50%); color: #778598; pointer-events: none; }

.ia-hint-msg { font-size: 0.625rem; color: #778598; font-style: italic; padding: 0 0.25rem; margin: 0; }
.ia-error-msg { font-size: 0.75rem; color: #ba1a1a; margin: 0; }
.has-error :deep(.dp__input) { border: 1px solid rgba(186,26,26,0.5); box-shadow: 0 0 0 1px rgba(186,26,26,0.2);}

/* Custom Datepicker Overrides */
:deep(.dp__input) {
  background-color: #f2f4f6;
  border: none;
  border-radius: 0.5rem;
  padding: 0.875rem 1rem 0.875rem 3.5rem;
  color: #191c1e;
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  transition: box-shadow 0.2s;
  box-sizing: border-box;
  width: 100%;
}
:deep(.dp__input:focus) { box-shadow: 0 0 0 2px rgba(52, 149, 87, 0.2); outline: none;}
:deep(.dp__input_icon) { display: none; } /* hiding default icon since we use material symbols */

.pt-4 { padding-top: 1rem; }
.ia-submit-btn {
  width: 100%;
  background: linear-gradient(to bottom right, #349557, #00210c);
  color: #ffffff;
  font-family: 'Manrope', sans-serif;
  font-weight: 700;
  padding: 1rem;
  border-radius: 0.5rem;
  border: none;
  box-shadow: 0 10px 15px -3px rgba(52, 149, 87, 0.2);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  font-size: 1rem;
}
.ia-submit-btn:hover:not(:disabled) { transform: scale(1.01); }
.ia-submit-btn:active:not(:disabled) { transform: scale(0.98); }
.ia-submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.sync-icon { transition: transform 0.5s; }
.group-hover-btn:hover:not(:disabled) .sync-icon { transform: rotate(180deg); }
.spin-anim { animation: spin 1s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }

.helper-text-container { display: flex; align-items: center; justify-content: center; gap: 1.5rem; opacity: 0.6; margin-top: 2rem; }
.helper-item { display: flex; align-items: center; gap: 0.375rem; }
.helper-item span:last-child { font-family: 'Inter', sans-serif; font-size: 0.6875rem; text-transform: uppercase; letter-spacing: 0.1em; }
.helper-item .material-symbols-outlined { font-size: 0.875rem; }

/* Footer */
.ia-footer { margin-top: auto; padding: 2rem 3rem; border-top: 1px solid rgba(226,232,240,0.5); display: flex; justify-content: space-between; align-items: center; background-color: #f7f9fb;}
.footer-links { display: flex; gap: 1.5rem; font-family: 'Inter', sans-serif; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }
.footer-links a { color: #94a3b8; text-decoration: none; transition: color 0.2s; }
.footer-links a:hover { color: #059669; }
.footer-copy { font-family: 'Inter', sans-serif; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; margin: 0; }

/* Custom Scrollbar */
.ia-sidebar::-webkit-scrollbar { width: 4px; }
.ia-sidebar::-webkit-scrollbar-track { background: transparent; }
.ia-sidebar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.ia-sidebar::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>
