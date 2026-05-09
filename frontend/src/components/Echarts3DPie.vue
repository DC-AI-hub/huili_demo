<script setup>
import { ref, onMounted, watch, nextTick, onBeforeUnmount } from 'vue';
import * as echarts from 'echarts';
import 'echarts-gl';

const props = defineProps({
  data: {
    type: Array,
    required: true
  }
});

const chartRef = ref(null);
let myChart = null;
let currentSeries = [];
let hoverTimer = null;
let hoverIndexCache = -1;

const highlightSlice = (hoverIndex) => {
  if (!myChart) return;

  const updatedSeries = currentSeries.map((s, index) => {
    if (s.type === 'surface') {
      const isOthers = hoverIndex !== -1 && hoverIndex !== index;
      
      return {
        ...s,
        itemStyle: {
          ...s.itemStyle,
          opacity: isOthers ? 0.3 : 1
        }
      };
    }
    return s;
  });

  myChart.setOption({ series: updatedSeries });
};

const getParametricEquation = (startRatio, endRatio, isSelected, isHovered, k, h) => {
  let midRatio = (startRatio + endRatio) / 2;
  let startRadian = startRatio * Math.PI * 2;
  let endRadian = endRatio * Math.PI * 2;
  let midRadian = midRatio * Math.PI * 2;

  if (startRatio === 0 && endRatio === 1) {
    isSelected = false;
  }

  let offsetX = isSelected ? Math.cos(midRadian) * 0.1 : 0;
  let offsetY = isSelected ? Math.sin(midRadian) * 0.1 : 0;
  let hoverRate = isHovered ? 1.05 : 1;

  return {
    u: { min: -Math.PI, max: Math.PI * 3, step: Math.PI / 32 },
    v: { min: 0, max: Math.PI * 2, step: Math.PI / 20 },
    x: function (u, v) {
      if (u < startRadian) {
        return offsetX + Math.cos(startRadian) * (1 + Math.cos(v) * k) * hoverRate;
      }
      if (u > endRadian) {
        return offsetX + Math.cos(endRadian) * (1 + Math.cos(v) * k) * hoverRate;
      }
      return offsetX + Math.cos(u) * (1 + Math.cos(v) * k) * hoverRate;
    },
    y: function (u, v) {
      if (u < startRadian) {
        return offsetY + Math.sin(startRadian) * (1 + Math.cos(v) * k) * hoverRate;
      }
      if (u > endRadian) {
        return offsetY + Math.sin(endRadian) * (1 + Math.cos(v) * k) * hoverRate;
      }
      return offsetY + Math.sin(u) * (1 + Math.cos(v) * k) * hoverRate;
    },
    z: function (u, v) {
      if (u < -Math.PI * 0.5) return Math.sin(u);
      if (u > Math.PI * 2.5) return Math.sin(u);
      return Math.sin(v) > 0 ? 1 * h : -1;
    }
  };
};

const getPie3D = (pieData, internalDiameterRatio) => {
  let series = [];
  let sumValue = 0;
  let startValue = 0;
  let endValue = 0;
  let k = typeof internalDiameterRatio !== 'undefined' ? (1 - internalDiameterRatio) / (1 + internalDiameterRatio) : 1 / 3;

  for (let i = 0; i < pieData.length; i++) {
    sumValue += pieData[i].value;
  }

  if (sumValue === 0) return [];

  for (let i = 0; i < pieData.length; i++) {
    let seriesItem = {
      name: pieData[i].name || `series${i}`,
      type: 'surface',
      parametric: true,
      wireframe: { show: false },
      pieData: { ...pieData[i] },
      itemStyle: {
        color: pieData[i].itemStyle?.color || '#333'
      },
      tooltip: { show: false } // disable tooltip for surface, rely on 2d pie
    };
    series.push(seriesItem);
  }

    for (let i = 0; i < series.length; i++) {
        endValue = startValue + series[i].pieData.value;
        let cwStartRatio = startValue / sumValue;
        let cwEndRatio = endValue / sumValue;

        // Convert clockwise ratio (from 12 o'clock) to counter-clockwise ratio (from 3 o'clock)
        let ccwStartRatio = (0.25 - cwEndRatio + 1) % 1;
        let ccwEndRatio = (0.25 - cwStartRatio + 1) % 1;

        if (ccwEndRatio < ccwStartRatio) {
            ccwEndRatio += 1;
        }

        series[i].pieData.startRatio = cwStartRatio;
        series[i].pieData.endRatio = cwEndRatio;
        series[i].pieData.ccwStartRatio = ccwStartRatio;
        series[i].pieData.ccwEndRatio = ccwEndRatio;
        series[i].pieData.k = k;

        series[i].parametricEquation = getParametricEquation(
            ccwStartRatio,
            ccwEndRatio,
            false,
            false,
            k,
            series[i].pieData.value === 0 ? 0 : 1 // use h=1
        );
        startValue = endValue;
    }

  // Revert to a single unified 2D pie series to restore ECharts native label anti-overlap engine (fixes missing labels).
  // We minimize the floating/inside gap by using a balanced radius.
  series.push({
    name: 'pie2d',
    type: 'pie',
    label: {
      show: true,
      formatter: '{b}\n{c}%',
      fontSize: 13,
      fontWeight: 'bold',
      color: '#333',
      distanceToLabelLine: 5
    },
    labelLine: {
      length: 20,
      length2: 20
    },
    startAngle: 90,
    radius: ['0%', '52%'], // A carefully calibrated radius balancing X and Y bounds
    center: ['50%', '50%'],
    itemStyle: {
      color: 'transparent'
    },
    emphasis: {
      itemStyle: {
        color: 'transparent'
      }
    },
    data: pieData.map(d => ({
      name: d.name,
      value: d.value,
      itemStyle: { color: 'transparent' },
      labelLine: {
        lineStyle: {
          color: d.itemStyle?.color || '#333',
          width: 1.5
        }
      }
    }))
  });

  return series;
};

const initChart = () => {
  if (!chartRef.value) return;

  if (!myChart) {
    myChart = echarts.init(chartRef.value);

    // Bind event listeners for 3D slicing hover effects
    myChart.on('mouseover', (params) => {
      if (hoverTimer) clearTimeout(hoverTimer);

      let index = -1;
      if (params.seriesName === 'pie2d') {
        index = params.dataIndex;
      } else if (params.seriesType === 'surface') {
        // since we push 3D surfaces first, seriesIndex matches the data index
        index = params.seriesIndex; 
      }

      if (index !== -1 && hoverIndexCache !== index) {
        hoverIndexCache = index;
        highlightSlice(index);
      }
    });

    myChart.on('mouseout', () => {
      if (hoverTimer) clearTimeout(hoverTimer);
      hoverTimer = setTimeout(() => {
        if (hoverIndexCache !== -1) {
          hoverIndexCache = -1;
          highlightSlice(-1);
        }
      }, 50);
    });

    myChart.on('globalout', () => {
      if (hoverTimer) clearTimeout(hoverTimer);
      if (hoverIndexCache !== -1) {
        hoverIndexCache = -1;
        highlightSlice(-1);
      }
    });
  }

  currentSeries = getPie3D(props.data, 0.0); // 0 corresponds to a full pie, not a donut

  const options = {
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderWidth: 1,
      borderColor: '#ccc',
      textStyle: { color: '#333' },
      formatter: params => {
        if (params.seriesName === 'pie2d') {
          // get color from original data
          const colorMarker = `<span style="display:inline-block;margin-right:4px;border-radius:10px;width:10px;height:10px;background-color:${props.data[params.dataIndex].itemStyle.color};"></span>`;
          return `${params.name}: ${colorMarker} <b>${params.value}%</b>`;
        }
      }
    },
    xAxis3D: { min: -2, max: 2 },
    yAxis3D: { min: -2, max: 2 },
    zAxis3D: { min: -2, max: 2 },
    grid3D: {
      show: false,
      boxHeight: 22, // increased height to compensate for steeper view
      top: '0%',
      viewControl: {
        alpha: 60, // steeper angle to minimize projection distortion
        beta: 0,
        distance: 155, // perfectly balance the zoom scale
        rotateSensitivity: 0,
        zoomSensitivity: 0,
        panSensitivity: 0
      }
    },
    series: currentSeries
  };

  myChart.setOption(options);
};

const handleResize = () => {
  if (myChart) myChart.resize();
};

onMounted(() => {
  nextTick(() => {
    initChart();
    window.addEventListener('resize', handleResize);
  });
});

watch(() => props.data, () => {
  nextTick(() => {
    initChart();
  });
}, { deep: true });

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  if (myChart) {
    myChart.dispose();
    myChart = null;
  }
});
</script>

<template>
  <div ref="chartRef" style="width: 100%; height: 250px;"></div>
</template>
