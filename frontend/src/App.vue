<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isReportPage = computed(() => route.path === '/report')
const isLoginPage = computed(() => route.path === '/login')
const isDownloading = ref(false)

// ── 打印按钮 ──────────────────────────────────────────────────
const handlePrint = () => {
  window.print()
}

// ── 下载 PDF 按钮（html2canvas + jsPDF，独立于打印样式）──────
const handleDownloadPdf = async () => {
  if (isDownloading.value) return
  isDownloading.value = true

  try {
    // 动态导入，避免首屏加载
    const [{ default: html2canvas }, { jsPDF }] = await Promise.all([
      import('html2canvas'),
      import('jspdf')
    ])

    const isLCMeeting = route.query.name === 'LC meeting'
    const pdfOrientation = isLCMeeting ? 'landscape' : 'portrait'
    const pdf = new jsPDF({ orientation: pdfOrientation, unit: 'mm', format: 'a4', compress: true })

    // A4 纸张尺寸（横纵向自适应）
    const A4_W_MM = isLCMeeting ? 297 : 210
    const A4_H_MM = isLCMeeting ? 210 : 297
    const SCALE = 2  // 2× 足够清晰，3× 内存压力大易崩溃

    let elements = []
    if (isLCMeeting) {
      // 捕获 LC Meeting 的三个独立区块，作为单独的三页
      const part1 = document.querySelector('.lc-report-page .report-body')
      const part2 = document.querySelector('.lc-report-page .aum-report-page')
      const part3 = document.querySelector('.lc-report-page .quartile-report')
      elements = [part1, part2, part3].filter(Boolean)
    } else {
      const page1El = document.querySelector('.report-container > .report-wrapper:not(.page-break)') || document.querySelector('.lc-report-page')
      const page2El = document.querySelector('.report-wrapper.page-break')
      elements = [page1El, page2El].filter(Boolean)
    }

    if (elements.length === 0) {
      alert('找不到报告内容，请确保已打开报告页面（/report）')
      return
    }

    // 截图配置（独立于 @media print，不影响打印）
    const captureOpts = {
      scale: SCALE,
      useCORS: true,
      allowTaint: true,
      backgroundColor: '#ffffff',
      logging: false,
      ignoreElements: el =>
        el.classList?.contains('navbar') ||
        el.classList?.contains('bottom-actions') ||
        el.tagName === 'NAV'
    }

    for (let i = 0; i < elements.length; i++) {
      const el = elements[i]

      // ── 无感截图：深克隆元素，放到屏幕外渲染，原始 DOM 完全不动 ──
      const clone = el.cloneNode(true)
      
      // 修复：手动复制 canvas 内容（如 ECharts 饼图），因为 cloneNode 不会克隆 canvas 像素
      const originalCanvases = el.querySelectorAll('canvas')
      const clonedCanvases = clone.querySelectorAll('canvas')
      originalCanvases.forEach((canvas, idx) => {
        const ctx = clonedCanvases[idx].getContext('2d')
        ctx.drawImage(canvas, 0, 0)
      })

      clone.classList.add('pdf-capture-mode')
      if (isLCMeeting) {
        // 保证单独截取子组件时也能继承 lc-report-page 的样式
        clone.classList.add('lc-report-page')
      }
      
      // 定位在可见区域之外，但仍在 DOM 中，浏览器会正常布局和渲染
      Object.assign(clone.style, {
        position: 'fixed',
        top: '0',
        left: '-9999px',
        zIndex: '-1',
        // 强制 950px/1700px（与 pdf-capture-mode 内的 !important 一致）
        width: isLCMeeting ? '1700px' : '950px',
        maxWidth: isLCMeeting ? '1700px' : '950px',
        background: '#fff',
        margin: '0',
        padding: '24px 22px 2px'
      })
      document.body.appendChild(clone)

      // 等两帧，让浏览器完成布局计算（字体、图片已加载，无需重新请求）
      await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))

      const canvas = await html2canvas(clone, captureOpts)

      // 截图完成，立即移除克隆体
      document.body.removeChild(clone)

      const imgData = canvas.toDataURL('image/jpeg', 0.92)

      // 将 canvas 像素尺寸换算回 CSS 像素，再适配 A4
      const cssW = canvas.width / SCALE
      const cssH = canvas.height / SCALE

      let drawW = A4_W_MM
      let drawH = cssH * (A4_W_MM / cssW)

      // 智能缩放：保证当前区块刚好在一页中展示完整
      if (drawH > A4_H_MM) {
        const shrinkRatio = A4_H_MM / drawH
        drawH = A4_H_MM
        drawW = drawW * shrinkRatio
      }

      // 居中对齐
      const offsetX = (A4_W_MM - drawW) / 2
      const offsetY = 0

      if (i > 0) pdf.addPage()
      pdf.addImage(imgData, 'JPEG', offsetX, offsetY, drawW, drawH)
    }


    // 用 Blob + <a> 触发下载，比 pdf.save() 更稳定，避免浏览器静默拦截
    const blob = pdf.output('blob')
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = route.query.name === 'LC meeting' ? 'Value_Partners_LC_Meeting_Report.pdf' : 'Value_Partners_Classic_Fund_Report.pdf'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error('PDF 生成失败：', err)
    alert('PDF 生成失败：' + (err.message || err))
  } finally {
    isDownloading.value = false
  }
}
</script>

<template>
  <div id="app">
    <nav class="navbar" v-if="!isLoginPage">
      <div class="brand">📊 Value Partners Demo</div>
      <div class="nav-links">
        <!-- 在报告页面展示打印和下载按钮 -->
        <template v-if="isReportPage">
          <button @click="handlePrint" class="action-btn">
            🖨️ 打印
          </button>
          <button
            @click="handleDownloadPdf"
            class="action-btn download-btn"
            :disabled="isDownloading"
          >
            <span v-if="isDownloading">⏳ 生成中...</span>
            <span v-else>⬇️ 下载报告</span>
          </button>
        </template>
        <router-link to="/lcreport" class="nav-item">Home</router-link>
      </div>
    </nav>
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <component :is="Component" :key="route.fullPath" />
      </router-view>
    </main>
  </div>
  <component :is="'style'">
    @media print {
      @page {
        size: {{ route.query.name === 'LC meeting' ? 'landscape' : 'portrait' }};
        margin: 8mm 5mm;
      }
    }
  </component>
</template>

<style>
:root {
  --primary: #3498db;
  --secondary: #2c3e50;
  --bg-color: #f8f9fa;
  --text-main: #34495e;
}

body {
  margin: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background-color: var(--bg-color);
  color: var(--text-main);
  -webkit-font-smoothing: antialiased;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  background: white;
  padding: 1rem 2rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
}

.brand {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--secondary);
}

.nav-links {
  display: flex;
  gap: 1.5rem;
}

.nav-item {
  text-decoration: none;
  color: #7f8c8d;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  transition: all 0.2s;
}

.nav-item:hover {
  color: var(--primary);
  background: #f1f8ff;
}

.nav-item.router-link-active {
  color: white;
  background: var(--primary);
}

.main-content {
  flex: 1;
  padding: 2rem;
}


.action-btn {
  background: white;
  color: var(--secondary);
  border: 1px solid #ccc;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 5px;
}
.action-btn:hover {
  background: #f1f8ff;
  border-color: var(--primary);
  color: var(--primary);
}
.download-btn {
  background: var(--primary);
  color: white;
  border: none;
}
.download-btn:hover {
  background: #2980b9;
  color: white;
}
.download-btn:disabled {
  background: #95a5a6;
  cursor: not-allowed;
  opacity: 0.85;
}

/* ── PDF 截图专用样式（加在元素上，独立于 @media print） ──
   核心思路：与打印CSS应用相同的压缩规则，使截图高度 ≤ 950×(297/210)=1344px，
   然后按宽度铺满A4（drawW=210mm）时高度刚好 ≤ 297mm，内容不截断。 */
.pdf-capture-mode {
  box-shadow: none !important;
  margin: 0 !important;
  width: 950px !important;
  max-width: 950px !important;
  min-width: 950px !important;
  box-sizing: border-box !important;
  /* 与打印保持一致的内边距（原来是 40px，压缩到 24px top、22px sides、2px bottom） */
  padding: 24px 22px 2px !important;
  font-size: 11.5px !important;
  line-height: 1.35 !important;
}

.pdf-capture-mode.lc-report-page {
  width: 1700px !important;
  max-width: 1700px !important;
  min-width: 1700px !important;
}

.pdf-capture-mode .perf-table th,
.pdf-capture-mode .perf-table td {
  padding: 1.5px 2px !important;
}
.pdf-capture-mode .total-label,
.pdf-capture-mode .total-val {
  padding: 1.5px 2px !important;
}

.pdf-capture-mode .table-wrapper {
  overflow: visible !important;
}

/* 以下与 @media print 中的压缩规则一一对应（使用 child 选择器，作用范围相同） */
.pdf-capture-mode .section      { margin-top: 10px !important; }
.pdf-capture-mode h2            { margin-bottom: 3px !important; padding-bottom: 1.5px !important; }
.pdf-capture-mode .header-green-box h1 { margin-bottom: 4px !important; }
.pdf-capture-mode .header-green-box    { padding: 9px 18px !important; }

.pdf-capture-mode .disclaimer-list    { margin-bottom: 8px !important; padding: 5px 15px 5px 20px !important; }
.pdf-capture-mode .disclaimer-list ul { margin: 2.5px 0 !important; }
.pdf-capture-mode .disclaimer-list li { margin-bottom: 1.5px !important; }

.pdf-capture-mode .monthly-performance          { margin-top: 12px !important; }
.pdf-capture-mode .data-table th,
.pdf-capture-mode .data-table td                { padding: 2px 2px !important; }
.pdf-capture-mode .perf-svg                     { max-height: 162px !important; margin: 0 auto; }
.pdf-capture-mode .report-footer               { padding-top: 4px !important; margin-top: 12px !important; }
.pdf-capture-mode .disclaimers-footer          { margin-bottom: 8px !important; }
.pdf-capture-mode .stat-line                   { white-space: nowrap !important; }

/* 第二页专属压缩（page-break 的 wrapper 内部） */
.pdf-capture-mode.page-break .section          { margin-top: 10px !important; }
.pdf-capture-mode.page-break h2                { margin-bottom: 3px !important; padding-bottom: 0 !important; }
.pdf-capture-mode.page-break .data-table th,
.pdf-capture-mode.page-break .data-table td    { padding: 1.8px 2px !important; }
.pdf-capture-mode .footnotes-block {
  margin-top: 6px !important;
  padding-top: 6px !important;
  font-size: 7.2px !important;
  line-height: 1.25 !important;
}
.pdf-capture-mode .footnotes-block p { margin-bottom: 2px !important; }
.pdf-capture-mode .qr-section       { margin-top: 5px !important; }


/* ── 打印样式（与 pdf-capture-mode 完全独立，互不影响） ─── */
@media print {
  /* @page is dynamically injected in template */

  body {
    background-color: white !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    line-height: 1.35 !important;
  }

  /* ── 核心修复：消除 flex 布局，否则 Chrome 会无视内部所有的分页指令 ── */
  html, body, #app, .main-content, .lc-report-page, .report-wrapper, .report-body, .print-page-break {
    display: block !important;
    height: auto !important;
    min-height: auto !important;
    max-height: none !important;
    overflow: visible !important;
    position: static !important;
    float: none !important;
  }

  .navbar, .bottom-actions { display: none !important; }
  .main-content { padding: 0 !important; margin: 0 !important; }

  /* ── wrapper 通用 ── */
  .report-wrapper {
    width: 950px !important;
    max-width: 950px !important;
    margin: 0 auto !important;
    padding: 24px 22px 2px !important;
    box-sizing: border-box !important;
    box-shadow: none !important;
  }
  /* 全局强制缩放：最稳定的 Chrome 打印排版方式，避免局部 zoom 导致分页失效 */
  body {
    zoom: 0.60 !important;
  }

  .lc-report-page {
    width: 100% !important;
    max-width: none !important;
    margin: 0 !important;
    padding: 0 !important;
    box-sizing: border-box !important;
    box-shadow: none !important;
  }
  
  .table-wrapper {
    overflow: visible !important;
  }

  /* LC Meeting 专属表格压缩 */
  .perf-table th,
  .perf-table td {
    padding: 1.5px 2px !important;
  }
  .total-label,
  .total-val {
    padding: 1.5px 2px !important;
  }

  /* 简单纯粹的组件分页控制 */
  .lc-report-section {
    page-break-before: always !important;
    break-before: page !important;
    overflow: visible !important;
    margin-top: 0 !important;
  }

  /* 防止图表跨页断裂 */
  .chart-item {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
  }

  /* 第一页结束后强制换页（Factsheet） */
  .report-wrapper:not(.page-break) {
    page-break-after: always !important;
    break-after: page !important;
  }

  /* 第二页从新页开始，本页结束后不再产生空白页 */
  .report-wrapper.page-break {
    page-break-before: always !important;
    break-before: page !important;
    page-break-after: avoid !important;
    break-after: avoid !important;
  }

  /* ── 第一页压缩规则（防止底部跨页溢出） ── */
  .section { margin-top: 10px !important; }
  h2 { margin-bottom: 3px !important; padding-bottom: 1.5px !important; }
  .header-green-box h1 { margin-bottom: 4px !important; }
  .header-green-box { padding: 9px 18px !important; }
  .disclaimer-list { margin-bottom: 8px !important; padding: 5px 15px 5px 20px !important; }
  .disclaimer-list ul { margin: 2.5px 0 !important; }
  .disclaimer-list li { margin-bottom: 1.5px !important; }
  .monthly-performance { margin-top: 12px !important; }
  .data-table th, .data-table td { padding: 2px 2px !important; }
  .perf-svg { max-height: 162px !important; margin: 0 auto; }
  .report-footer { padding-top: 4px !important; margin-top: 12px !important; }
  .disclaimers-footer { margin-bottom: 10px !important; }

  /* ── break-inside: avoid 防止关键区域被跨页切割 ── */
  /* 注意：对高度超过一页的元素（如整页 wrapper）不加 avoid，否则会强制整体另起一页，反而产生空页 */
  .main-columns           { break-inside: avoid !important; page-break-inside: avoid !important; }
  .monthly-performance    { break-inside: avoid !important; page-break-inside: avoid !important; }
  .disclaimers-footer     { break-inside: avoid !important; page-break-inside: avoid !important; }
  .report-footer          { break-inside: avoid !important; page-break-inside: avoid !important; }
  .performance-update     { break-inside: avoid !important; page-break-inside: avoid !important; }
  svg.perf-svg            { break-inside: avoid !important; page-break-inside: avoid !important; }

  /* ── 第二页专属压缩 ── */
  .report-wrapper.page-break .section { margin-top: 10px !important; }
  .report-wrapper.page-break h2 { margin-bottom: 3px !important; padding-bottom: 0 !important; }
  .report-wrapper.page-break .data-table th,
  .report-wrapper.page-break .data-table td { padding: 1.8px 2px !important; }
  .footnotes-block {
    margin-top: 6px !important;
    padding-top: 6px !important;
    font-size: 7.2px !important;
    line-height: 1.25 !important;
    break-inside: avoid !important;
    page-break-inside: avoid !important;
  }
  .footnotes-block p { margin-bottom: 2px !important; }
  .qr-section { margin-top: 5px !important; }

  .stat-line { white-space: nowrap !important; }
}
</style>
