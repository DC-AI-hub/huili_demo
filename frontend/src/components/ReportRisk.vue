<template>
  <div class="report-risk-container">
    <div class="report-header">
      <div class="header-left">
        <div class="title">Chloe_fund_Tracking Error</div>
        <div class="meta-info">
          <div>Currency: US Dollar</div>
          <div>Grouped by: Custom</div>
          <div>Calculated on: 3/4/2026 3:05:33 PM</div>
          <div>Exported on: 3/4/2026 3:05:34 PM</div>
        </div>
      </div>
    </div>

    <div class="table-wrapper">
      <table class="risk-table">
        <thead>
          <!-- Row 1: Titles -->
          <tr>
            <th class="sticky-col col-isin row1"></th>
            <th class="sticky-col col-group row1"></th>
            <th class="sticky-col col-bench row1"></th>
            <th class="sticky-col col-rating row1"></th>
            <th v-for="(h, i) in headers" :key="i" class="data-header row1">
              {{ h.title }}
            </th>
          </tr>
          <!-- Row 2: Start Dates -->
          <tr>
            <th class="sticky-col col-isin row2"></th>
            <th class="sticky-col col-group row2"></th>
            <th class="sticky-col col-bench row2"></th>
            <th class="sticky-col col-rating row2"></th>
            <th v-for="(h, i) in headers" :key="'s'+i" class="data-header date-cell row2">
              {{ h.startDate }}
            </th>
          </tr>
          <!-- Row 3: End Dates -->
          <tr>
            <th class="sticky-col col-isin row3"></th>
            <th class="sticky-col col-group row3"></th>
            <th class="sticky-col col-bench row3"></th>
            <th class="sticky-col col-rating row3"></th>
            <th v-for="(h, i) in headers" :key="'e'+i" class="data-header date-cell row3">
              {{ h.endDate }}
            </th>
          </tr>
          <!-- Row 4: Column Labels -->
          <tr>
            <th class="sticky-col col-isin row4">ISIN</th>
            <th class="sticky-col col-group row4">Group/Investment</th>
            <th class="sticky-col col-bench row4">Calculation Benchmark</th>
            <th class="sticky-col col-rating row4">Morningstar Rating Overall</th>
            <th v-for="(h, i) in headers" :key="'n'+i" class="data-header row4">
              {{ h.colName }}
            </th>
          </tr>
        </thead>
        <tbody>
          <template v-for="group in riskData" :key="group.code">
            <!-- Group Header Row -->
            <tr class="group-row">
              <td class="sticky-col col-isin"></td>
              <td class="sticky-col col-group group-code">{{ group.code }}</td>
              <td class="sticky-col col-bench"></td>
              <td class="sticky-col col-rating"></td>
              <td :colspan="headers.length"></td>
            </tr>
            <!-- Item Rows -->
            <tr v-for="(item, idx) in group.items" :key="group.code + idx" class="data-row">
              <td class="sticky-col col-isin">{{ item.isin }}</td>
              <td class="sticky-col col-group align-left">{{ item.name }}</td>
              <td class="sticky-col col-bench align-left">{{ item.benchmark }}</td>
              <td class="sticky-col col-rating">{{ item.rating }}</td>
              <td v-for="(val, vIdx) in getDisplayValues(item.values, group.code, idx)" :key="vIdx" class="val-cell">
                {{ val }}
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const headers = ref([
  { title: '1y', colName: 'Return (Cumulative)', startDate: '2/1/2025', endDate: '1/31/2026' },
  { title: '1y (SD)', colName: 'Std Dev (Annualized)', startDate: '2/1/2025', endDate: '1/31/2026' },
  { title: '1y (TE)', colName: 'Tracking Error (Annualized)', startDate: '2/1/2025', endDate: '1/31/2026' },
  { title: '1y (Beta)', colName: 'Beta', startDate: '2/1/2025', endDate: '1/31/2026' },
  { title: '3y', colName: 'Return (Cumulative)', startDate: '2/1/2023', endDate: '1/31/2026' },
  { title: '3y', colName: 'Return (Annualized)', startDate: '2/1/2023', endDate: '1/31/2026' },
  { title: '3y (SD)', colName: 'Std Dev (Annualized)', startDate: '2/1/2023', endDate: '1/31/2026' },
  { title: '3y (TE)', colName: 'Tracking Error (Annualized)', startDate: '2/1/2023', endDate: '1/31/2026' },
  { title: '3y (Beta)', colName: 'Beta', startDate: '2/1/2023', endDate: '1/31/2026' }
])

const getDisplayValues = (values, groupCode, rowIdx) => {
  if (!Array.isArray(values)) {
    console.error(`[ReportRisk] values is not an array. group=${groupCode}, row=${rowIdx}`)
    return Array(headers.value.length).fill('')
  }

  if (values.length !== headers.value.length) {
    console.warn(
      `[ReportRisk] values length mismatch. group=${groupCode}, row=${rowIdx}, values=${values.length}, headers=${headers.value.length}`
    )
  }

  if (values.length >= headers.value.length) {
    return values.slice(0, headers.value.length)
  }

  return [...values, ...Array(headers.value.length - values.length).fill('')]
}

const riskData = ref([
  {
    "code": "VPAF",
    "items": [
      {
        "isin": "HK0000264868",
        "name": "Value Partners Classic A USD",
        "benchmark": "HSI HKD TR + MSCI G. Dragon (20171001)",
        "rating": "QQQ",
        "values": [
          "33.48",
          "13.8",
          "6.32",
          "0.88",
          "51.12",
          "14.75",
          "17.33",
          "5.11",
          "0.99"
        ]
      },
      {
        "isin": "",
        "name": "HSI HKD TR + MSCI G. Dragon (20171001)",
        "benchmark": "HSI HKD TR + MSCI G. Dragon (20171001)",
        "rating": "",
        "values": [
          "38.87",
          "14.13",
          "0.0",
          "1.0",
          "75.38",
          "20.59",
          "16.71",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "CG",
    "items": [
      {
        "isin": "KYG9317M1033",
        "name": "Value Partners China Greenchip Ltd",
        "benchmark": "MSCI Golden Dragon NR USD",
        "rating": "QQQ",
        "values": [
          "32.66",
          "13.46",
          "5.69",
          "0.87",
          "50.11",
          "14.5",
          "16.22",
          "4.62",
          "0.93"
        ]
      },
      {
        "isin": "",
        "name": "MSCI Golden Dragon NR USD",
        "benchmark": "MSCI Golden Dragon NR USD",
        "rating": "",
        "values": [
          "38.87",
          "14.13",
          "0.0",
          "1.0",
          "75.38",
          "20.59",
          "16.71",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "VPHY",
    "items": [
      {
        "isin": "HK0000288735",
        "name": "Value Partners Hi-Div Stks A1 USD",
        "benchmark": "MSCI AP x J + MSCI AxJ 20160430 (NR)",
        "rating": "QQQ",
        "values": [
          "46.12",
          "8.35",
          "5.93",
          "0.64",
          "61.61",
          "17.35",
          "12.82",
          "5.38",
          "0.87"
        ]
      },
      {
        "isin": "",
        "name": "MSCI AP x J + MSCI AxJ 20160430 (NR)",
        "benchmark": "MSCI AP x J + MSCI AxJ 20160430 (NR)",
        "rating": "",
        "values": [
          "48.84",
          "11.27",
          "0.0",
          "1.0",
          "78.28",
          "21.26",
          "13.61",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "VPGB",
    "items": [
      {
        "isin": "KYG9319N1097",
        "name": "Value Partners Grt CHN HY In P Acc USD",
        "benchmark": "JPM ACI Non Investment Grade TR USD",
        "rating": "QQQQ",
        "values": [
          "10.84",
          "4.35",
          "2.21",
          "0.99",
          "25.21",
          "7.78",
          "7.14",
          "3.15",
          "1.07"
        ]
      },
      {
        "isin": "",
        "name": "JPM ACI Non Investment Grade TR USD",
        "benchmark": "JPM ACI Non Investment Grade TR USD",
        "rating": "",
        "values": [
          "11.25",
          "3.83",
          "0.0",
          "1.0",
          "30.58",
          "9.3",
          "6.02",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "VAIF",
    "items": [
      {
        "isin": "HK0000352382",
        "name": "Value Partners Asian Inc A USD Inc",
        "benchmark": "50%MSCI AC Asia ex Jap + 50% JPM Asia Credit Index",
        "rating": "QQQQ",
        "values": [
          "42.37",
          "9.28",
          "4.78",
          "1.4",
          "67.64",
          "18.79",
          "9.07",
          "4.72",
          "0.99"
        ]
      },
      {
        "isin": "",
        "name": "50%MSCI AC Asia ex Jap + 50% JPM Asia Credit Index",
        "benchmark": "50%MSCI AC Asia ex Jap + 50% JPM Asia Credit Index",
        "rating": "",
        "values": [
          "26.84",
          "5.91",
          "0.0",
          "1.0",
          "48.82",
          "14.17",
          "7.86",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "VAIO",
    "items": [
      {
        "isin": "HK0000475969",
        "name": "Value Partners Asn Innovt OppsAUSDUnhAcc",
        "benchmark": "VAIO Custom Benchmark",
        "rating": "QQQQQ",
        "values": [
          "62.94",
          "14.03",
          "11.35",
          "0.56",
          "98.56",
          "25.69",
          "15.38",
          "11.35",
          "0.7"
        ]
      },
      {
        "isin": "",
        "name": "VAIO Custom Benchmark",
        "benchmark": "VAIO Custom Benchmark",
        "rating": "",
        "values": [
          "81.76",
          "23.16",
          "0.0",
          "1.0",
          "109.99",
          "28.06",
          "16.35",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "VPCA",
    "items": [
      {
        "isin": "KYG9317Q1047",
        "name": "Value Partners China Convergence",
        "benchmark": "MSCI China NR USD",
        "rating": "QQQQ",
        "values": [
          "19.55",
          "13.56",
          "5.05",
          "0.8",
          "25.43",
          "7.84",
          "20.25",
          "6.45",
          "0.84"
        ]
      },
      {
        "isin": "",
        "name": "MSCI China NR USD",
        "benchmark": "MSCI China NR USD",
        "rating": "",
        "values": [
          "14.74",
          "16.34",
          "0.0",
          "1.0",
          "36.99",
          "11.06",
          "23.43",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "VPMF",
    "items": [
      {
        "isin": "KYG9317Q1120",
        "name": "Val Ptnrs Chns Mnlnd Foc A",
        "benchmark": "MSCI China NR USD",
        "rating": "QQQQ",
        "values": [
          "19.12",
          "16.42",
          "5.14",
          "0.96",
          "21.51",
          "6.71",
          "22.92",
          "8.41",
          "0.92"
        ]
      },
      {
        "isin": "",
        "name": "MSCI China USD NR - CMF",
        "benchmark": "MSCI China NR USD",
        "rating": "",
        "values": [
          "14.74",
          "16.34",
          "0.0",
          "1.0",
          "36.99",
          "11.06",
          "23.43",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "VPTF",
    "items": [
      {
        "isin": "KYG9318Y1061",
        "name": "Value Partners Taiwan A",
        "benchmark": "Taiwan Weighted Index TR Daily",
        "rating": "QQQ",
        "values": [
          "103.22",
          "23.8",
          "12.85",
          "0.85",
          "198.34",
          "43.96",
          "20.46",
          "10.26",
          "0.94"
        ]
      },
      {
        "isin": "",
        "name": "Taiwan Weighted Index TR Daily",
        "benchmark": "Taiwan Weighted Index TR Daily",
        "rating": "",
        "values": [
          "66.28",
          "23.92",
          "0.0",
          "1.0",
          "144.21",
          "34.67",
          "18.86",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "VCAS",
    "items": [
      {
        "isin": "HK0000220001",
        "name": "Value Partners China A-Share Sel A CHN",
        "benchmark": "CSI 300 Index TR CNY",
        "rating": "QQ",
        "values": [
          "30.09",
          "16.76",
          "8.1",
          "1.17",
          "4.13",
          "1.36",
          "21.39",
          "6.95",
          "1.06"
        ]
      },
      {
        "isin": "",
        "name": "CSI 300 Index TR CNY",
        "benchmark": "CSI 300 Index TR CNY",
        "rating": "",
        "values": [
          "32.24",
          "12.65",
          "0.0",
          "1.0",
          "27.56",
          "8.45",
          "19.13",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "VPMA",
    "items": [
      {
        "isin": "HK0000269149",
        "name": "Value Partners Multi-Asset A USD",
        "benchmark": "50% MSCI Golden Dragon + 50% JACI China TR",
        "rating": "QQ",
        "values": [
          "31.95",
          "11.54",
          "7.24",
          "1.28",
          "35.22",
          "10.58",
          "15.18",
          "8.44",
          "1.49"
        ]
      },
      {
        "isin": "",
        "name": "50% MSCI Golden Dragon + 50% JACI China TR",
        "benchmark": "50% MSCI Golden Dragon + 50% JACI China TR",
        "rating": "",
        "values": [
          "22.07",
          "7.17",
          "0.0",
          "1.0",
          "45.93",
          "13.43",
          "8.98",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "VATB",
    "items": [
      {
        "isin": "HK0000402450",
        "name": "Value Partners Asian TR Bd A USD Acc",
        "benchmark": "JPM ACI APAC",
        "rating": "QQQ",
        "values": [
          "7.76",
          "2.77",
          "1.97",
          "1.34",
          "18.1",
          "5.7",
          "4.53",
          "2.45",
          "1.13"
        ]
      },
      {
        "isin": "",
        "name": "JPM ACI APAC",
        "benchmark": "JPM ACI APAC",
        "rating": "",
        "values": [
          "7.13",
          "1.5",
          "0.0",
          "1.0",
          "21.77",
          "6.79",
          "3.39",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "VHCF",
    "items": [
      {
        "isin": "IE00BSM8VZ90",
        "name": "Value Partners Health Care A USD Acc",
        "benchmark": "MSCI China All Shares HC 10/40 NR USD",
        "rating": "Q",
        "values": [
          "26.51",
          "25.32",
          "4.25",
          "1.14",
          "5.84",
          "1.91",
          "25.4",
          "5.95",
          "0.93"
        ]
      },
      {
        "isin": "",
        "name": "MSCI China All Shares HC 10/40 NR USD",
        "benchmark": "MSCI China All Shares HC 10/40 NR USD",
        "rating": "",
        "values": [
          "23.49",
          "22.08",
          "0.0",
          "1.0",
          "-10.91",
          "-3.78",
          "26.53",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "VACB",
    "items": [
      {
        "isin": "HK0000770799",
        "name": "Value Partners All CHN Bd A USD Acc Unh",
        "benchmark": "JPM ACI China TR USD",
        "rating": "QQQQQ",
        "values": [
          "6.9",
          "2.67",
          "2.2",
          "1.22",
          "20.7",
          "6.47",
          "3.73",
          "2.23",
          "1.01"
        ]
      },
      {
        "isin": "",
        "name": "JPM ACI Chn TR USD",
        "benchmark": "JPM ACI China TR USD",
        "rating": "",
        "values": [
          "6.13",
          "1.27",
          "0.0",
          "1.0",
          "18.03",
          "5.68",
          "2.94",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "VPEJ",
    "items": [
      {
        "isin": "IE00BD3HK754",
        "name": "Value Partners Asia ex-Japan Eq V USDAcc",
        "benchmark": "MSCI AC Asia Ex Japan NR USD",
        "rating": "QQQ",
        "values": [
          "57.57",
          "9.17",
          "5.63",
          "0.71",
          "74.32",
          "20.35",
          "14.13",
          "4.89",
          "0.98"
        ]
      },
      {
        "isin": "",
        "name": "MSCI AC Asia Ex Japan NR USD",
        "benchmark": "MSCI AC Asia Ex Japan NR USD",
        "rating": "",
        "values": [
          "48.84",
          "11.27",
          "0.0",
          "1.0",
          "78.28",
          "21.26",
          "13.61",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "VUGB",
    "items": [
      {
        "isin": "IE00BKRQZ838",
        "name": "Value Partners Grtr CHN HY Bd AUSDAccUnH",
        "benchmark": "JPM ACI China TR USD",
        "rating": "",
        "values": [
          "",
          "",
          "",
          "",
          "",
          "",
          "",
          "",
          ""
        ]
      }
    ]
  },
  {
    "code": "VUAD",
    "items": [
      {
        "isin": "IE00BN6JWM76",
        "name": "Val Ptnrs Asn Dyn Bd V USD UnH Acc",
        "benchmark": "JPM Asia Credit TR USD",
        "rating": "Q",
        "values": [
          "7.02",
          "2.06",
          "0.7",
          "1.26",
          "9.5",
          "3.07",
          "2.98",
          "3.0",
          "0.5"
        ]
      }
    ]
  },
  {
    "code": "VUHD",
    "items": [
      {
        "isin": "IE00BMGYK213",
        "name": "Value Partners CHN AShrsHiDiv V USD Acc",
        "benchmark": "CSI 300 Index TR CNY",
        "rating": "QQQQ",
        "values": [
          "26.95",
          "9.51",
          "7.84",
          "0.59",
          "32.92",
          "9.95",
          "14.67",
          "11.3",
          "0.62"
        ]
      }
    ]
  },
  {
    "code": "VPJR",
    "items": [
      {
        "isin": "HK0000997111",
        "name": "Value Partners Japan REIT A JPY UnH MDis",
        "benchmark": "TSE REIT TR JPY",
        "rating": "",
        "values": [
          "15.25",
          "8.9",
          "0.58",
          "0.99",
          "",
          "",
          "",
          "",
          ""
        ]
      },
      {
        "isin": "",
        "name": "TSE REIT TR JPY",
        "benchmark": "TSE REIT TR JPY",
        "rating": "",
        "values": [
          "19.04",
          "9.0",
          "0.0",
          "1.0",
          "8.78",
          "2.85",
          "13.35",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "MVTF",
    "items": [
      {
        "isin": "",
        "name": "Milltrust VP Taiwan Fund (7-Oct-24)",
        "benchmark": "MSCI Taiwan NR USD",
        "rating": "",
        "values": [
          "108.95",
          "25.38",
          "9.58",
          "0.9",
          "",
          "",
          "",
          "",
          ""
        ]
      },
      {
        "isin": "",
        "name": "MSCI Taiwan NR USD",
        "benchmark": "MSCI Taiwan NR USD",
        "rating": "",
        "values": [
          "76.44",
          "26.25",
          "0.0",
          "1.0",
          "174.18",
          "39.96",
          "21.31",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "VPGF",
    "items": [
      {
        "isin": "HK0000718657",
        "name": "Value Gold ETF(Unlisted Cl)AHKDUnhdgdAcc",
        "benchmark": "Goldlnam_hkd_hsbc",
        "rating": "",
        "values": [
          "80.03",
          "18.15",
          "0.16",
          "1.0",
          "182.4",
          "41.35",
          "15.57",
          "0.09",
          "1.0"
        ]
      },
      {
        "isin": "",
        "name": "Goldlnam_hkd_hsbc",
        "benchmark": "Goldlnam_hkd_hsbc",
        "rating": "",
        "values": [
          "80.83",
          "18.15",
          "0.0",
          "1.0",
          "185.95",
          "41.94",
          "15.58",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "VPLLC",
    "items": [
      {
        "isin": "",
        "name": "Value Partners Asia Fund LLC(21-Aug-06)",
        "benchmark": "Hang Seng HSI GR HKD",
        "rating": "",
        "values": [
          "33.75",
          "14.39",
          "7.91",
          "0.91",
          "49.03",
          "14.22",
          "18.02",
          "9.03",
          "0.8"
        ]
      },
      {
        "isin": "",
        "name": "Hang Seng HSI GR HKD",
        "benchmark": "Hang Seng HSI GR HKD",
        "rating": "",
        "values": [
          "19.27",
          "13.33",
          "0.0",
          "1.0",
          "52.09",
          "15.0",
          "20.08",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "VSP1",
    "items": [
      {
        "isin": "KYG9390M1298",
        "name": "Value Partners CHN AShr Innovt SPZJPYUnH",
        "benchmark": "70%MSCI China A Intl NR + 30%MSCI China NR",
        "rating": "QQ",
        "values": [
          "21.58",
          "19.65",
          "10.3",
          "1.41",
          "18.92",
          "5.95",
          "24.96",
          "12.09",
          "1.1"
        ]
      },
      {
        "isin": "",
        "name": "70%MSCI China A Intl NR + 30%MSCI China NR",
        "benchmark": "70%MSCI China A Intl NR + 30%MSCI China NR",
        "rating": "",
        "values": [
          "27.61",
          "12.39",
          "0.0",
          "1.0",
          "27.71",
          "8.5",
          "19.93",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "VSP2",
    "items": [
      {
        "isin": "KYG9390M1520",
        "name": "Value Partners Ch Engy Shifting ZJPYAcc",
        "benchmark": "MSCI China All Shares NR USD",
        "rating": "QQQ",
        "values": [
          "44.12",
          "18.6",
          "15.6",
          "0.78",
          "35.32",
          "10.61",
          "19.41",
          "13.72",
          "0.71"
        ]
      },
      {
        "isin": "",
        "name": "MSCI China All Shares NR USD",
        "benchmark": "MSCI China All Shares NR USD",
        "rating": "",
        "values": [
          "21.02",
          "13.58",
          "0.0",
          "1.0",
          "31.13",
          "9.45",
          "21.11",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "VGCP",
    "items": [
      {
        "isin": "",
        "name": "VP Grt Chn PS Inc Fund XAcc USD_Grs (16-Feb-16)",
        "benchmark": "ICE LIBOR USD 3M",
        "rating": "",
        "values": [
          "",
          "",
          "",
          "",
          "",
          "",
          "",
          "",
          ""
        ]
      },
      {
        "isin": "KYG9320G1846",
        "name": "VP Greater China Preference Inc A $ Acc",
        "benchmark": "ICE LIBOR USD 3M",
        "rating": "",
        "values": [
          "",
          "",
          "",
          "",
          "",
          "",
          "",
          "",
          ""
        ]
      }
    ]
  },
  {
    "code": "VPMM",
    "items": [
      {
        "isin": "HK0000945037",
        "name": "Value Partners USD Mny Mkt A USD UnH Acc",
        "benchmark": "SOFR Averages 90 Day Yld USD",
        "rating": "",
        "values": [
          "4.08",
          "0.09",
          "0.05",
          "0.82",
          "",
          "",
          "",
          "",
          ""
        ]
      },
      {
        "isin": "",
        "name": "SOFR Averages 90 Day Yld USD",
        "benchmark": "SOFR Averages 90 Day Yld USD",
        "rating": "",
        "values": [
          "4.39",
          "0.08",
          "0.0",
          "1.0",
          "15.79",
          "5.01",
          "0.16",
          "0.0",
          "1.0"
        ]
      }
    ]
  },
  {
    "code": "RM_DAIWA",
    "items": [
      {
        "isin": "",
        "name": "Daiwa Advisory Mandate_reference only (5-Mar-21)",
        "benchmark": "MSCI China NR USD",
        "rating": "",
        "values": [
          "",
          "",
          "",
          "",
          "",
          "",
          "",
          "",
          ""
        ]
      },
      {
        "isin": "",
        "name": "Daiwa Advisory Mandate (with cash)_Factset",
        "benchmark": "MSCI China NR USD",
        "rating": "",
        "values": [
          "",
          "",
          "",
          "",
          "",
          "",
          "",
          "",
          ""
        ]
      }
    ]
  },
  {
    "code": "PAIF",
    "items": [
      {
        "isin": "",
        "name": "Premium Asia Income Fund (Net)",
        "benchmark": "JPM ACI China TR USD",
        "rating": "",
        "values": [
          "",
          "",
          "",
          "",
          "",
          "",
          "",
          "",
          ""
        ]
      }
    ]
  }
])
</script>

<style scoped>
.report-risk-container {
  padding: 0 20px;
  background-color: white;
  color: black;
  font-family: Arial, sans-serif;
  font-size: 14px;
  height: calc(100vh - 135px); /* Fill the screen minus navbar */
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.report-header {
  flex-shrink: 0;
  margin-bottom: 20px;
}

.title {
  font-weight: bold;
  font-size: 16px;
  margin-bottom: 10px;
}

.meta-info {
  font-size: 13px;
  color: #333;
  line-height: 1.4;
}

.table-wrapper {
  overflow: auto;
  flex: 1;
  border: 0.5px solid #d1d1d1;
}

.risk-table {
  width: max-content;
  border-collapse: collapse;
  table-layout: fixed;
}

.risk-table th, .risk-table td {
  border: 0.5px solid #d1d1d1;
  padding: 6px 8px;
  text-align: center;
  font-weight: normal;
  box-sizing: border-box;
  height: 32px; /* Fixed height for rows to ease sticky calculations */
}

/* Header Specifics */
.risk-table thead th {
  background-color: #f9f9f9;
  z-index: 20;
  position: sticky;
}

/* Precise Row Offsets */
.row1 { top: 0; z-index: 30; height: 18px !important; padding: 0 !important; font-size: 14px; font-weight: bold !important; }
.row2 { top: 18px; z-index: 29; height: 18px !important; padding: 0 !important; font-size: 14px; font-weight: bold !important; }
.row3 { top: 36px; z-index: 28; height: 18px !important; padding: 0 !important; font-size: 14px; font-weight: bold !important; }
.row4 { top: 54px; z-index: 27; height: 32px; padding: 0 !important; font-size: 13px !important; font-weight: normal !important; text-align: left !important; }

/* Special Handling for Sticky Columns in Header */
.risk-table thead th.sticky-col {
  z-index: 40; /* High enough to cover data columns */
  background-color: #f9f9f9 !important;
}

/* Hide internal borders for frozen column headers to make them look like one block */
.sticky-col.row1 { border-bottom: none !important; }
.sticky-col.row2 { border-top: none !important; border-bottom: none !important; }
.sticky-col.row3 { border-top: none !important; border-bottom: none !important; }
.sticky-col.row4 { border-top: none !important; }

.measure-type {
  font-size: 11px;
  color: #666;
  margin-top: 4px;
}

.date-cell {
  font-size: 12px;
}

/* Sticky Columns */
.sticky-col {
  position: sticky;
  background-color: white !important;
  z-index: 10;
}

.col-isin { left: 0; width: 250px; min-width: 250px; max-width: 250px; }
.col-group { left: 250px; width: 350px; min-width: 350px; max-width: 350px; }
.col-bench { left: 600px; width: 350px; min-width: 350px; max-width: 350px; }
.col-rating { left: 950px; width: 150px; min-width: 150px; max-width: 150px; }

.col-isin,
.col-group,
.col-bench,
.col-rating {
  /* Use a dedicated separator layer to avoid border loss during sticky repaint. */
  position: sticky;
}

.col-isin::after,
.col-group::after,
.col-bench::after,
.col-rating::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 1px;
  background-color: #d1d1d1;
  pointer-events: none;
  z-index: 40;
}

/* Ensure proper intersection z-index for frozen columns */
thead th.sticky-col {
  z-index: 50 !important;
}

/* Group Row Styles */
.group-row td {
  background-color: #f0f0f0 !important;
  font-weight: bold !important;
  height: 30px;
}

.group-code {
  text-align: left !important;
  padding-left: 12px !important;
}

/* Data Row Styles */
.data-row td {
  background-color: white;
}

.align-left {
  text-align: left !important;
}

.val-cell {
  text-align: right !important;
  width: 115px;
}

.data-row:hover td {
  background-color: #f5f5f5 !important;
}
</style>
