<template>
  <div class="modal-overlay">
    <div class="modal-content modal-xl">
      <div class="modal-header">
        <h3>基金配置核对</h3>
        <button class="close-btn" @click="$emit('close')">&times;</button>
      </div>

      <!-- Toolbar -->
      <div class="toolbar">
        <div class="filters">
          <input v-model="filters.fund_code" placeholder="Fund Code" class="form-input filter-input" />
          <input v-model="filters.fund_name" placeholder="Fund Name" class="form-input filter-input" />
          <input v-model="filters.isin" placeholder="ISIN" class="form-input filter-input" />
          <select v-model="filters.is_fund" class="form-input filter-input">
            <option :value="null">所有 (isFund)</option>
            <option :value="1">是</option>
            <option :value="0">否</option>
          </select>
          <select v-model="filters.is_new" class="form-input filter-input">
            <option :value="null">所有 (isNew)</option>
            <option :value="1">是</option>
            <option :value="0">否</option>
          </select>
          <select v-model="filters.is_diff" class="form-input filter-input">
            <option :value="null">所有 (isDiff)</option>
            <option :value="1">有差异</option>
            <option :value="0">无差异</option>
          </select>
          <button class="btn-success" @click="handleSearch">查询</button>
          <button class="btn-primary" @click="handleReset">重置</button>
        </div>
        <button class="btn-primary" @click="handleAddNew">新增配置</button>
      </div>

      <!-- Data Table -->
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>序号</th>
              <th>Fund Code</th>
              <th>Fund Name</th>
              <th>ISIN</th>
              <th>isFund</th>
              <th>isNew</th>
              <th>isDiff</th>
              <th style="text-align: center;" title="配置Performace实际显示的Benchmark名称">Performance<br>Benchmark Name</th>
              <th>Inception Date</th>
              <th style="text-align: center;">Morningstar AUM<br>MS_VP Open End Fund Name</th>
              <th style="text-align: center;">Morningstar AUM<br>BM Name</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="12" class="text-center">加载中...</td>
            </tr>
            <tr v-else-if="items.length === 0">
              <td colspan="12" class="text-center">无数据</td>
            </tr>
            <tr v-for="(item, index) in items" :key="item.fund_code" :class="{ 'row-diff': item.is_diff > 0 }">
              <td>{{ (page - 1) * pageSize + index + 1 }}</td>
              <td>{{ item.fund_code }}</td>
              <td>{{ item.fund_name }}</td>
              <td>{{ item.isin }}</td>
              <td>
                <span class="badge" :class="item.is_fund === 1 ? 'badge-yes' : 'badge-no'">
                  {{ item.is_fund === 1 ? '是' : '否' }}
                </span>
              </td>
              <td>
                <span class="badge" :class="item.is_new === 1 ? 'badge-yes' : 'badge-no'">
                  {{ item.is_new === 1 ? '是' : '否' }}
                </span>
              </td>
              <td>
                <span class="badge" :class="item.is_diff > 0 ? 'badge-yes' : 'badge-no'">
                  {{ item.is_diff > 0 ? '有差异' : '无差异' }}
                </span>
              </td>
              <td>{{ item.benchmark_name }}</td>
              <td>{{ item.inception_date }}</td>
              <td>
                <span :class="{ 'text-danger fw-bold': item.is_diff === 1 || item.is_diff === 3 }">
                  {{ item.entity_name }}
                </span>
              </td>
              <td>
                <span :class="{ 'text-danger fw-bold': item.is_diff === 2 || item.is_diff === 3 }">
                  {{ item.bm_entity_name }}
                </span>
              </td>
              <td>
                <div style="display: flex; flex-direction: column; align-items: center; gap: 0.3rem;">
                  <button class="btn-sm btn-verify" @click="handleEdit(item)">编辑</button>
                  <button class="btn-sm btn-success" @click="handleCompare(item)">对比</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="pagination">
        <button class="btn-default btn-sm" :disabled="page <= 1" @click="changePage(page - 1)">上一页</button>
        <span>第 {{ page }} 页 / 共 {{ Math.ceil(total / pageSize) || 1 }} 页 (总数 {{ total }})</span>
        <button class="btn-default btn-sm" :disabled="page * pageSize >= total" @click="changePage(page + 1)">下一页</button>
      </div>
    </div>

    <!-- Edit/Add Modal -->
    <div v-if="showEditModal" class="modal-overlay sub-modal">
      <div class="modal-content edit-modal">
        <h3>{{ isEditing ? '编辑配置' : '新增配置' }}</h3>
        <div class="form-grid">
          <div class="form-group">
            <label>Fund Code (必填)<span v-if="isEditing" class="text-muted">（主键修改需谨慎）</span></label>
            <input v-model="editForm.fund_code" class="form-input" />
          </div>
          <div class="form-group">
            <label>Inception Date</label>
            <input type="date" v-model="editForm.inception_date" class="form-input" />
          </div>
          <div class="form-group full-width">
            <label>Fund Name</label>
            <input v-model="editForm.fund_name" class="form-input" />
          </div>
          <div class="form-group">
            <label>ISIN</label>
            <input v-model="editForm.isin" class="form-input" />
          </div>
          <div class="form-group">
            <label>isFund</label>
            <select v-model="editForm.is_fund" class="form-input">
              <option :value="1">是</option>
              <option :value="0">否</option>
            </select>
          </div>
          <div class="form-group full-width">
            <label>Performance - Benchmark Name</label>
            <input v-model="editForm.benchmark_name" class="form-input" />
          </div>
          <div class="form-group full-width">
            <label>Morningstar AUM - MS_VP Open End Fund Name</label>
            <input v-model="editForm.entity_name" class="form-input" />
          </div>
          <div class="form-group full-width">
            <label>Morningstar AUM - BM Name</label>
            <input v-model="editForm.bm_entity_name" class="form-input" />
          </div>
        </div>
        <div v-if="editError" class="error-text">{{ editError }}</div>
        <div class="modal-actions">
          <button class="btn-default" @click="showEditModal = false" :disabled="saving">取消</button>
          <button class="btn-success" @click="handleSave" :disabled="saving">{{ saving ? '保存中...' : '保存' }}</button>
        </div>
      </div>
    </div>
    <!-- Compare Modal -->
    <div v-if="showCompareModal" class="modal-overlay sub-modal">
      <div 
        class="modal-content compare-modal" 
        ref="compareModalRef"
        :style="{ transform: `translate(${modalPosition.x}px, ${modalPosition.y}px)`, transition: isDragging ? 'none' : 'transform 0.1s' }"
      >
        <div class="modal-header" @mousedown="startDrag" style="cursor: move; user-select: none;">
          <h3>报告对比</h3>
          <button class="close-btn" @click="closeCompareModal">&times;</button>
        </div>
        <div class="table-container" v-if="compareData">
          <table class="data-table compare-table">
            <thead>
              <tr>
                <th style="width: 45%;">
                  <div class="fw-bold text-dark">RF_fund performance_t-1</div>
                  <div class="header-info">Currency: US Dollar</div>
                  <div class="header-info">Grouped by: Custom</div>
                  <div class="header-info">Calculated on: {{ compareData.current_date }}</div>
                  <div class="header-info" style="margin-bottom: 1rem;">Exported on: {{ compareData.current_date }}</div>
                  <div class="fw-bold text-dark border-bottom-dark">Group/Investment</div>
                </th>
                <th class="text-center" style="width: 10%; border-bottom: 1px solid #000;"></th>
                <th style="width: 45%;">
                  <div class="fw-bold text-dark">RF_fund performance_t-1</div>
                  <div class="header-info">Currency: US Dollar</div>
                  <div class="header-info">Grouped by: Custom</div>
                  <div class="header-info">Calculated on: {{ compareData.previous_date }}</div>
                  <div class="header-info" style="margin-bottom: 1rem;">Exported on: {{ compareData.previous_date }}</div>
                  <div class="fw-bold text-dark border-bottom-dark">Group/Investment</div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in compareData.rows" :key="idx">
                <td :class="{'fw-bold': row.is_header}">{{ row.current }}</td>
                <td class="text-center" style="border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0;">
                  <span v-if="row.current || row.previous" class="text-danger fw-bold">
                    {{ row.is_match ? 'TRUE' : 'FALSE' }}
                  </span>
                </td>
                <td :class="{'fw-bold': row.is_header}">{{ row.previous }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else-if="compareLoading" class="text-center" style="padding: 3rem;">加载中...</div>
        <div v-if="compareError" class="error-text text-center" style="padding: 1rem;">{{ compareError }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  reportDate: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close'])

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

const filters = ref({
  fund_code: '',
  fund_name: '',
  isin: '',
  benchmark_name: '',
  is_fund: null,
  is_new: null,
  is_diff: null
})

const showEditModal = ref(false)
const isEditing = ref(false)
const saving = ref(false)
const editError = ref('')
const originalFundCode = ref('')

const editForm = ref({
  fund_code: '',
  fund_name: '',
  isin: '',
  is_fund: 0,
  is_new: 0,
  is_diff: 0,
  benchmark_name: '',
  inception_date: '',
  entity_name: '',
  bm_entity_name: ''
})

const loadData = async () => {
  loading.value = true
  try {
    let url = `/api/lc-report/fund-code-map?page=${page.value}&page_size=${pageSize.value}`
    if (filters.value.fund_code) url += `&fund_code=${encodeURIComponent(filters.value.fund_code)}`
    if (filters.value.fund_name) url += `&fund_name=${encodeURIComponent(filters.value.fund_name)}`
    if (filters.value.isin) url += `&isin=${encodeURIComponent(filters.value.isin)}`
    if (filters.value.benchmark_name) url += `&benchmark_name=${encodeURIComponent(filters.value.benchmark_name)}`
    if (filters.value.is_fund !== null) url += `&is_fund=${filters.value.is_fund}`
    if (filters.value.is_new !== null) url += `&is_new=${filters.value.is_new}`
    if (filters.value.is_diff !== null) url += `&is_diff=${filters.value.is_diff}`

    const res = await fetch(url)
    const json = await res.json()
    if (json.success) {
      items.value = json.data
      total.value = json.total
    }
  } catch (e) {
    alert('加载数据失败：' + e.message)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  page.value = 1
  loadData()
}

const handleReset = () => {
  filters.value = {
    fund_code: '',
    fund_name: '',
    isin: '',
    benchmark_name: '',
    is_fund: null,
    is_new: null,
    is_diff: null
  }
  handleSearch()
}

const changePage = (p) => {
  page.value = p
  loadData()
}

const handleAddNew = () => {
  isEditing.value = false
  editError.value = ''
  editForm.value = {
    fund_code: '',
    fund_name: '',
    isin: '',
    is_fund: 0,
    is_new: 0,
    is_diff: 0,
    benchmark_name: '',
    inception_date: '',
    entity_name: '',
    bm_entity_name: ''
  }
  showEditModal.value = true
}

const handleEdit = (item) => {
  isEditing.value = true
  originalFundCode.value = item.fund_code
  editError.value = ''
  editForm.value = { ...item }
  showEditModal.value = true
}

const showCompareModal = ref(false)
const compareLoading = ref(false)
const compareData = ref(null)
const compareError = ref('')

const compareModalRef = ref(null)
const isDragging = ref(false)
const dragOffset = ref({ x: 0, y: 0 })
const modalPosition = ref({ x: 0, y: 0 })

const startDrag = (e) => {
  if (e.target.closest('.close-btn')) return
  isDragging.value = true
  dragOffset.value = {
    x: e.clientX - modalPosition.value.x,
    y: e.clientY - modalPosition.value.y
  }
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

const onDrag = (e) => {
  if (!isDragging.value) return
  modalPosition.value = {
    x: e.clientX - dragOffset.value.x,
    y: e.clientY - dragOffset.value.y
  }
}

const stopDrag = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

const closeCompareModal = () => {
  showCompareModal.value = false
  modalPosition.value = { x: 0, y: 0 }
}

const handleCompare = async (item) => {
  showCompareModal.value = true
  compareLoading.value = true
  compareError.value = ''
  try {
    let url = '/api/lc-report/fund-code-map/compare-rf-perf'
    if (props.reportDate) {
      url += `?report_date=${encodeURIComponent(props.reportDate)}`
    }
    const res = await fetch(url)
    const json = await res.json()
    if (json.success) {
      compareData.value = json.data
    } else {
      compareError.value = json.detail || '获取对比数据失败'
    }
  } catch (e) {
    compareError.value = '网络错误：' + e.message
  } finally {
    compareLoading.value = false
  }
}

const handleSave = async () => {
  if (!editForm.value.fund_code) {
    editError.value = 'Fund Code 不能为空'
    return
  }
  
  saving.value = true
  editError.value = ''
  try {
    const isNew = !isEditing.value
    const url = isNew ? '/api/lc-report/fund-code-map' : `/api/lc-report/fund-code-map/${encodeURIComponent(originalFundCode.value)}`
    const method = isNew ? 'POST' : 'PUT'
    
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editForm.value)
    })
    
    const json = await res.json()
    if (json.success) {
      showEditModal.value = false
      loadData()
    } else {
      editError.value = json.detail || '保存失败'
    }
  } catch (e) {
    editError.value = '网络错误：' + e.message
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(15,23,42,0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
}

.sub-modal {
  z-index: 10010;
}

.modal-content {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  width: 500px;
  max-width: 95vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
}

.modal-xl {
  width: 96vw;
  max-width: 1600px;
  height: 85vh;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.modal-header h3 {
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #64748b;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.filters {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  align-items: center;
}

.filter-input {
  width: 140px;
  padding: 0.4rem;
}

.form-input {
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: inherit;
  font-size: 0.9rem;
  padding: 0.4rem 0.6rem;
}

.btn-primary, .btn-success, .btn-default, .btn-verify {
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.btn-primary { background-color: #0f1c2c; color: white; }
.btn-success { background-color: #059669; color: white; }
.btn-default { background-color: #f1f5f9; color: #334155; }
.btn-verify { background-color: #059669; color: white; }

.btn-sm { padding: 0.3rem 0.6rem; font-size: 0.8rem; white-space: nowrap; }

.table-container {
  flex: 1;
  overflow: auto;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 1000px;
}

.data-table th, .data-table td {
  padding: 0.6rem;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.85rem;
}

.data-table th {
  background: #f8fafc;
  font-weight: 600;
  position: sticky;
  top: 0;
  z-index: 10;
  white-space: nowrap;
}

.data-table tbody tr:hover {
  background-color: #f1f5f9;
}

.data-table tbody tr.row-diff {
  background-color: #fef08a;
}

.data-table tbody tr.row-diff:hover {
  background-color: #fde047;
}

.text-danger { color: #dc2626 !important; }
.fw-bold { font-weight: bold; }

.text-center { text-align: center; }

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  font-size: 0.9rem;
}

.badge {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: bold;
  white-space: nowrap;
}
.badge-yes { background: #d1fae5; color: #065f46; }
.badge-no { background: #f1f5f9; color: #64748b; }

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.edit-modal {
  width: 750px;
}

.full-width {
  grid-column: 1 / -1;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.form-group label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #334155;
}
.text-muted { color: #94a3b8; font-size: 0.75rem; font-weight: normal; }
.error-text { color: #be123c; margin-bottom: 1rem; font-size: 0.85rem; }
.modal-actions { display: flex; justify-content: flex-end; gap: 1rem; }

.compare-modal {
  width: 1000px;
  max-width: 95vw;
  height: 85vh;
}

.compare-table {
  border: 1px solid #cbd5e1;
}

.compare-table th {
  background: white;
  vertical-align: bottom;
  padding-bottom: 0.2rem;
  border-bottom: 1px solid #000;
}

.header-info {
  font-weight: normal;
  font-size: 0.8rem;
  color: #333;
}

.text-dark { color: #000; }
.border-bottom-dark { border-bottom: 1px solid #000; padding-bottom: 0.2rem; display: inline-block; width: 100%; }

.compare-table td {
  padding: 0.3rem 0.6rem;
  font-size: 0.85rem;
  border-bottom: none;
}
</style>
