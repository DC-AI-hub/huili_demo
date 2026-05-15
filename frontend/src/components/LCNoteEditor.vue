<!--
  LCNoteEditor.vue — 全屏分析师注释编辑器
  左侧：FundAnalysis 核对数据（只读）
  右侧：富文本输入框（contenteditable，支持加粗/颜色）
-->
<template>
  <teleport to="body">
    <div class="ne-overlay" @click.self="handleBackdrop">
      <div class="ne-container">
        <!-- ── 顶部标题栏 ─────────────────────────────────── -->
        <div class="ne-header">
          <div class="ne-header-left">
            <span class="ne-icon">✏️</span>
            <span class="ne-title">分析师注释编辑</span>
            <span class="ne-sub">参考左侧数据，在右侧撰写富文本注释</span>
          </div>
          <div class="ne-header-right">
            <button class="ne-btn ne-btn-cancel" @click="$emit('close')">取消</button>
            <button class="ne-btn ne-btn-confirm" :disabled="saving" @click="handleConfirm">
              {{ saving ? '保存中…' : '✓ 确认' }}
            </button>
          </div>
        </div>
        <div v-if="saveError" class="ne-error-bar">{{ saveError }}</div>

        <!-- ── 主体：左右分栏 ─────────────────────────────── -->
        <div class="ne-body">
          <!-- 左侧：FA 数据 -->
          <div class="ne-left">
            <div class="ne-panel-title">
              <span class="material-symbols-outlined">table_view</span>
              Fund Analysis 数据参考
            </div>
            <div class="ne-fa-wrap">
              <div v-if="faLoading" class="ne-placeholder">
                <span class="spin-icon">⟳</span> 加载数据中…
              </div>
              <div v-else-if="faError" class="ne-placeholder error">{{ faError }}</div>
              <LCFundAnalysisView v-else :sheets="faSheets" style="height:100%" />
            </div>
          </div>

          <!-- 分隔线 -->
          <div class="ne-divider"></div>

          <!-- 右侧：富文本编辑器 -->
          <div class="ne-right">
            <div class="ne-panel-title">
              <span class="material-symbols-outlined">edit_note</span>
              注释内容（富文本）
            </div>

            <!-- 工具栏 -->
            <div class="ne-toolbar">
              <button class="tb-btn" title="加粗 (Ctrl+B)" @click="cmd('bold')"><b>B</b></button>
              <button class="tb-btn" title="斜体 (Ctrl+I)" @click="cmd('italic')"><i>I</i></button>
              <button class="tb-btn" title="下划线 (Ctrl+U)" @click="cmd('underline')"><u>U</u></button>
              <span class="tb-sep"></span>
              <button class="tb-btn" title="字体颜色：黑色" @click="cmdColor('#000000')">
                <span style="font-weight:700;color:#000">A</span>
              </button>
              <button class="tb-btn" title="字体颜色：深蓝" @click="cmdColor('#1e3a8a')">
                <span style="font-weight:700;color:#1e3a8a">A</span>
              </button>
              <button class="tb-btn" title="字体颜色：红色" @click="cmdColor('#c0392b')">
                <span style="font-weight:700;color:#c0392b">A</span>
              </button>
              <button class="tb-btn" title="字体颜色：绿色" @click="cmdColor('#166534')">
                <span style="font-weight:700;color:#166534">A</span>
              </button>
              <span class="tb-sep"></span>
              <button class="tb-btn" title="无序列表" @click="cmd('insertUnorderedList')">• List</button>
              <button class="tb-btn" title="清除格式" @click="cmd('removeFormat')">✕ 清格式</button>
            </div>

            <!-- 编辑区域 -->
            <div
              ref="editorRef"
              class="ne-editor"
              contenteditable="true"
              @input="onEditorInput"
              @keydown.ctrl.b.prevent="cmd('bold')"
              @keydown.ctrl.i.prevent="cmd('italic')"
              @keydown.ctrl.u.prevent="cmd('underline')"
            ></div>
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import LCFundAnalysisView from './LCFundAnalysisView.vue'

const props = defineProps({
  reportId:     { type: Number, required: true },
  faFileId:     { type: Number, default: null },
  initialNote:  { type: String, default: '' },
})
const emit = defineEmits(['close', 'saved'])

const BASE = '/api/lc-report'

// ── 富文本编辑器 ──────────────────────────────────────────────────────────
const editorRef = ref(null)
const saving    = ref(false)
const saveError = ref('')

function cmd(command) {
  document.execCommand(command, false, null)
  editorRef.value?.focus()
}
function cmdColor(color) {
  document.execCommand('foreColor', false, color)
  editorRef.value?.focus()
}
function onEditorInput() { /* reactive via innerHTML on confirm */ }

onMounted(async () => {
  await nextTick()
  if (editorRef.value && props.initialNote) {
    editorRef.value.innerHTML = props.initialNote
  }
  fetchFaData()
})

async function handleConfirm() {
  saving.value = true
  saveError.value = ''
  const html = editorRef.value?.innerHTML || ''
  try {
    const res = await fetch(`${BASE}/reports/${props.reportId}/note`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ analyst_note: html }),
    })
    const json = await res.json()
    if (!res.ok || !json.success) throw new Error(json.detail || '保存失败')
    emit('saved', html)
  } catch (e) {
    saveError.value = e.message
  } finally {
    saving.value = false
  }
}

function handleBackdrop() {
  // 点击遮罩不关闭（避免误操作）
}

// ── FA 数据加载 ───────────────────────────────────────────────────────────
const faSheets  = ref([])
const faLoading = ref(true)
const faError   = ref('')

async function fetchFaData() {
  if (!props.faFileId) {
    faError.value = '未找到 FundAnalysis 文件'
    faLoading.value = false
    return
  }
  try {
    const res  = await fetch(`${BASE}/reports/${props.reportId}/fa-compare`)
    if (!res.ok) {
      faError.value = `加载 FA 数据失败（HTTP ${res.status}）`
      return
    }
    const json = await res.json()
    faSheets.value = json.sheets || []
    if (!faSheets.value.length) faError.value = '暂无 FundAnalysis 解析数据'
  } catch (e) {
    faError.value = '加载 FA 数据失败：' + e.message
  } finally {
    faLoading.value = false
  }
}
</script>

<style scoped>
/* ── 全屏遮罩 ────────────────────────────────────────────────────── */
.ne-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.55);
  z-index: 9000;
  display: flex;
  align-items: stretch;
  justify-content: center;
}
.ne-container {
  background: #fff;
  width: 100%;
  max-width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ── 顶部 ────────────────────────────────────────────────────────── */
.ne-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #0f172a;
  color: #fff;
  flex-shrink: 0;
  gap: 12px;
}
.ne-header-left { display: flex; align-items: center; gap: 10px; }
.ne-icon  { font-size: 18px; }
.ne-title { font-size: 15px; font-weight: 700; }
.ne-sub   { font-size: 12px; color: #94a3b8; }
.ne-header-right { display: flex; gap: 10px; }

.ne-btn {
  padding: 7px 20px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity .15s;
}
.ne-btn:disabled { opacity: .5; cursor: not-allowed; }
.ne-btn-cancel  { background: #334155; color: #cbd5e1; }
.ne-btn-confirm { background: #059669; color: #fff; }
.ne-btn-confirm:not(:disabled):hover { background: #047857; }

.ne-error-bar {
  background: #fee2e2;
  color: #991b1b;
  padding: 6px 20px;
  font-size: 12px;
  flex-shrink: 0;
}

/* ── 主体 ────────────────────────────────────────────────────────── */
.ne-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}
.ne-left {
  flex: 0 0 55%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: 2px solid #e2e8f0;
}
.ne-divider { display: none; }
.ne-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── 面板标题 ─────────────────────────────────────────────────────── */
.ne-panel-title {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  flex-shrink: 0;
}

/* ── FA 数据区 ────────────────────────────────────────────────────── */
.ne-fa-wrap {
  flex: 1;
  overflow: hidden;
  position: relative;
}
.ne-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #94a3b8;
  font-size: 13px;
  gap: 8px;
}
.ne-placeholder.error { color: #ef4444; }
.spin-icon { animation: spin .8s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── 工具栏 ──────────────────────────────────────────────────────── */
.ne-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: #f1f5f9;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
  flex-wrap: wrap;
}
.tb-btn {
  padding: 3px 10px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  background: #fff;
  font-size: 12px;
  cursor: pointer;
  transition: background .1s;
  white-space: nowrap;
}
.tb-btn:hover { background: #e0f2fe; }
.tb-sep { width: 1px; height: 20px; background: #cbd5e1; margin: 0 4px; }

/* ── 富文本编辑区 ────────────────────────────────────────────────── */
.ne-editor {
  flex: 1;
  padding: 16px 20px;
  font-family: 'Calibri', 'Arial', sans-serif;
  font-size: 13px;
  line-height: 1.7;
  color: #1e3a5f;
  overflow-y: auto;
  outline: none;
  white-space: pre-wrap;
  word-break: break-word;
  text-align: left;
}
.ne-editor:empty::before {
  content: '在此输入注释内容…（支持 Ctrl+B 加粗、Ctrl+I 斜体）';
  color: #cbd5e1;
  pointer-events: none;
}
.ne-editor:focus { background: #fffbf0; }
</style>
