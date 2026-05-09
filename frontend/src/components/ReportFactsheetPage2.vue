<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  reportMonth: {
    type: String,
    default: ''
  },
  asAtDate: {
    type: String,
    default: ''
  }
})

const urlParams = new URLSearchParams(window.location.search)
const targetDate = urlParams.get('date')

const topHoldings = ref([])
const topHoldingsLoading = ref(true)

const geoExposures = ref([])
const geoLoading = ref(true)

const sectorExposures = ref([])
const sectorLoading = ref(true)

const portfolioChar = ref(null)
const charLoading = ref(true)

const feeStructures = ref([])
const feeLoading = ref(true)

const feeClassA = computed(() => feeStructures.value.find(f => f.fund_class === 'Class A') || {})
const feeClassB = computed(() => feeStructures.value.find(f => f.fund_class === 'Class B') || {})
const feeClassC = computed(() => feeStructures.value.find(f => f.fund_class === 'Class C') || {})

onMounted(async () => {
  try {
    const urlHoldings = targetDate ? `/api/top-holdings?as_of_date=${targetDate}` : '/api/top-holdings'
    const urlGeo = targetDate ? `/api/geographical-exposure?as_of_date=${targetDate}` : '/api/geographical-exposure'
    const urlSector = targetDate ? `/api/sector-exposure?as_of_date=${targetDate}` : '/api/sector-exposure'
    const urlChar = targetDate ? `/api/portfolio-characteristics?as_of_date=${targetDate}` : '/api/portfolio-characteristics'
    const urlFee = targetDate ? `/api/fee-structure?as_of_date=${targetDate}` : '/api/fee-structure'

    const [resHoldings, resGeo, resSector, resChar, resFee] = await Promise.all([
      fetch(urlHoldings),
      fetch(urlGeo),
      fetch(urlSector),
      fetch(urlChar),
      fetch(urlFee)
    ])

    if (resHoldings.ok) topHoldings.value = await resHoldings.json()
    if (resGeo.ok) geoExposures.value = await resGeo.json()
    if (resSector.ok) sectorExposures.value = await resSector.json()
    if (resFee.ok) feeStructures.value = await resFee.json()
    if (resChar.ok) {
      const charData = await resChar.json()
      if (charData && Object.keys(charData).length > 0) {
        portfolioChar.value = charData
      }
    }

  } catch (err) {
    console.error('Failed to fetch Page 2 data:', err)
  } finally {
    topHoldingsLoading.value = false
    geoLoading.value = false
    sectorLoading.value = false
    charLoading.value = false
    feeLoading.value = false
  }
})

const totalHoldingWeight = computed(() => {
  if (!topHoldings.value || topHoldings.value.length === 0) return 0;
  const sum = topHoldings.value.reduce((acc, curr) => acc + curr.weight, 0);
  return Math.round(sum);
})
</script>

<template>
  <div class="report-wrapper page-break">
    <!-- Top Thin Green Header -->
    <div class="page2-header">
      <div class="title">Value Partners Classic Fund</div>
      <div class="date-wrap">
        <div class="date-bg"></div>
        <div class="date">{{ reportMonth }}</div>
      </div>
    </div>

    <div class="main-columns" style="margin-top: 15px;">
      <!-- Left Column -->
      <div class="col-left">
        <!-- Top holdings -->
        <div class="section">
          <h2>Top holdings</h2>
          <table class="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Industry ⁵</th>
                <th class="right-align">% ⁶</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="topHoldingsLoading">
                <td colspan="3" class="center-align">Loading...</td>
              </tr>
              <tr v-else-if="!topHoldings.length">
                <td colspan="3" class="center-align">No data available</td>
              </tr>
              <tr v-else v-for="h in topHoldings" :key="h.id">
                <td v-html="h.company_name.replace('Co Ltd', '<br>Co Ltd').replace('Holding Ltd', '<br>Holding Ltd').replace('Corp', '<br>Corp')"></td>
                <td v-html="h.industry.replace('Semiconductors & semiconductor', 'Semiconductors &<br>semiconductor').replace('Technology, hardware', 'Technology,<br>hardware')"></td>
                <td class="right-align">{{ h.weight.toFixed(1) }}</td>
              </tr>
            </tbody>
          </table>
          <div class="footnote-under-table">These securities constitute {{ totalHoldingWeight }}% of the Fund.</div>
        </div>

        <!-- Portfolio characteristics -->
        <div class="section">
          <h2>Portfolio characteristics</h2>
          <div v-if="charLoading" style="padding: 10px; color: #666; font-size: 10.5px;">Loading...</div>
          <div v-else-if="!portfolioChar" style="padding: 10px; color: #666; font-size: 10.5px;">No data available</div>
          <div v-else>
            <table class="data-table bordered-rows">
              <tbody>
                <tr><td colspan="2">As at {{ (portfolioChar.as_of_date || '').replace('As at ', '') || asAtDate.replace('As at ', '') || '28 Jan 2025' }}</td></tr>
                <tr><td>Price/earnings ratio</td><td class="right-align">{{ portfolioChar.price_earnings_ratio }} times</td></tr>
                <tr><td>Price/book ratio</td><td class="right-align">{{ portfolioChar.price_book_ratio }} times</td></tr>
                <tr><td>Portfolio yield</td><td class="right-align">{{ portfolioChar.portfolio_yield }}%</td></tr>
              </tbody>
            </table>
            <table class="data-table" style="margin-top: 5px;">
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
                <tr style="border-top: 2px solid #333; border-bottom: 2px solid #333;">
                  <td>Annualized volatility (3 years) ⁷</td>
                  <td class="center-align">{{ portfolioChar.volatility_class_a }}%</td>
                  <td class="center-align">{{ portfolioChar.volatility_class_b }}%</td>
                  <td class="center-align">{{ portfolioChar.volatility_class_c }}%</td>
                  <td class="center-align border-left-col">{{ portfolioChar.volatility_index }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Geographical exposure -->
        <div class="section">
          <h2>Geographical exposure by listing ⁶</h2>
          <div class="bar-chart-container">
            <div v-if="geoLoading" style="padding: 10px; color: #666;">Loading...</div>
            <div v-else-if="!geoExposures.length" style="padding: 10px; color: #666;">No data available</div>
            <div v-else class="bar-row" v-for="g in geoExposures" :key="g.id">
              <div class="bar-label">{{ g.geography }}</div>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: g.weight + '%' }"></div>
                <span class="bar-val">{{ g.weight }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Sector exposure -->
        <div class="section" style="margin-top: 15px;">
          <h2>Sector exposure ⁵, ⁶</h2>
          <div class="bar-chart-container">
            <div v-if="sectorLoading" style="padding: 10px; color: #666;">Loading...</div>
            <div v-else-if="!sectorExposures.length" style="padding: 10px; color: #666;">No data available</div>
            <div v-else class="bar-row" v-for="s in sectorExposures" :key="s.id">
              <div class="bar-label">{{ s.sector }}</div>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: s.weight + '%' }"></div>
                <span class="bar-val">{{ s.weight }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column -->
      <div class="col-right">
        <!-- Fund facts -->
        <div class="section">
          <h2>Fund facts</h2>
          <table class="fact-table">
            <tbody>
              <tr><td class="fact-label">Manager:</td><td>Value Partners Hong Kong Limited</td></tr>
              <tr><td class="fact-label">Base currency:</td><td>USD</td></tr>
              <tr><td class="fact-label">Trustee and Custodian:</td><td>HSBC Institutional Trust Services (Asia) Limited</td></tr>
              <tr>
                <td class="fact-label" style="vertical-align: top;">Launch date:</td>
                <td>
                  1 Apr 1993<br><em>- Class A USD</em><br>
                  15 May 1996<br><em>- Class B USD</em><br>
                  15 Oct 2009<br><em>- Class C USD</em><br>
                  17 Mar 2014<br><em>- Class C AUD/CAD/NZD Hedged</em><br>
                  28 Oct 2015<br><em>- Class C RMB Hedged</em><br>
                  30 Nov 2015<br><em>- Class C HKD Hedged</em><br>
                  1 Dec 2015<br><em>- Class C RMB</em><br>
                  16 Oct 2017<br><em>- Class C USD/HKD/RMB/RMB Hedged MDis</em>
                </td>
              </tr>
              <tr>
                <td class="fact-label" style="vertical-align: top;">Dealing frequency:</td>
                <td>Daily redemption (Class A & B)<br>Daily dealing (Class C)</td>
              </tr>
            </tbody>
          </table>
          <p class="italic-desc" style="margin-top:10px;">Class A, B and C are invested in the same fund, Class A and B were no longer issued from 12 Apr 2002 and 15 Oct 2009 respectively. Only Class C is currently available.</p>
        </div>

        <!-- Fee structure -->
        <div class="section">
          <h2>Fee structure & Subscription information</h2>
          <div v-if="feeLoading" style="padding: 10px; color: #666; font-size: 10.5px;">Loading...</div>
          <div v-else-if="!feeStructures.length" style="padding: 10px; color: #666; font-size: 10.5px;">No data available</div>
          <table v-else class="data-table">
            <thead>
              <tr>
                <th></th>
                <th class="center-align">Class A</th>
                <th class="center-align">Class B</th>
                <th class="center-align">Class C</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Minimum subscription</td>
                <td class="center-align" v-html="feeClassA.min_subscription || '-'"></td>
                <td class="center-align" v-html="feeClassB.min_subscription || '-'"></td>
                <td class="center-align" v-html="feeClassC.min_subscription || '-'"></td>
              </tr>
              <tr>
                <td>Minimum subsequent<br>subscription</td>
                <td class="center-align" v-html="feeClassA.min_subsequent_subscription || '-'"></td>
                <td class="center-align" v-html="feeClassB.min_subsequent_subscription || '-'"></td>
                <td class="center-align" v-html="feeClassC.min_subsequent_subscription || '-'"></td>
              </tr>
              <tr>
                <td>Subscription fee</td>
                <td class="center-align" v-html="feeClassA.subscription_fee || '-'"></td>
                <td class="center-align" v-html="feeClassB.subscription_fee || '-'"></td>
                <td class="center-align" v-html="feeClassC.subscription_fee || '-'"></td>
              </tr>
              <tr>
                <td>Management fee</td>
                <td class="center-align" v-html="feeClassA.management_fee || '-'"></td>
                <td class="center-align" v-html="feeClassB.management_fee || '-'"></td>
                <td class="center-align" v-html="feeClassC.management_fee || '-'"></td>
              </tr>
              <tr>
                <td>Performance fee ⁸</td>
                <td colspan="3" class="center-align" v-html="feeClassA.performance_fee || '-'"></td>
              </tr>
              <tr>
                <td>Redemption fee</td>
                <td colspan="3" class="center-align" v-html="feeClassA.redemption_fee || '-'"></td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Senior investment staff -->
        <div class="section">
          <h2>Senior investment staff</h2>
          <div class="staff-list">
            <strong>Chief Investment Officer:</strong> Louis So<br>
            <strong>Deputy Chief Investment Officer, Equities:</strong> Yu Chen Jun<br>
            <strong>Senior Investment Directors:</strong> Norman Ho, CFA; Renee Hung<br>
            <strong>Chief Investment Officer, Multi Assets:</strong> Kelly Chung, CFA<br>
            <strong>Investment Directors:</strong> Lillian Cao; Luo Jing, CFA; Michelle Yu, CFA<br>
            <strong>Fund Managers:</strong> Wei Ming Ang, CFA; Van Liu
          </div>
        </div>

        <!-- Awards -->
        <div class="section awards-section">
          <h2>Key fund and corporate awards</h2>
          <div class="awards-container">
            <div class="award-icon-large">🏆</div>
            <div class="awards-list">
              <div class="award-item">
                <div class="award-text">
                  <strong>Golden Bull Overseas China Equity Fund (1-Year) ⁹</strong><br>
                  <em>~ China Securities Journal, The Overseas Fund Golden Bull Fund Awards 2020 & 2021</em>
                </div>
              </div>
              <div class="award-item">
                <div class="award-text">
                  <strong>Asia ex-Japan Equity House: Best-in-Class ¹⁰<br>Greater China Equity House: Outstanding Achiever ¹⁰</strong><br>
                  <em>~ Benchmark Fund of the Year Awards 2018, Hong Kong</em>
                </div>
              </div>
              <div class="award-item">
                <div class="award-text">
                  <strong>Offshore China Equity (10-year) ¹¹</strong><br>
                  <em>~ Insight & Mandate, Professional Investment Awards 2018</em>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- QR Codes -->
        <div class="qr-section">
          <div class="qr-scan-text">Scan QR code¹²:</div>
          <div class="qr-item">
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=60x60&data=docs" alt="QR Documents">
            <div>Fund<br>documents</div>
          </div>
          <div class="qr-item">
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=60x60&data=notices" alt="QR Notices">
            <div>Fund<br>notices</div>
          </div>
        </div>
      </div>
    </div> <!-- /Main Columns -->

    <!-- Footnotes -->
    <div class="footnotes-block">
      <p>Source: Value Partners, HSBC Institutional Trust Services (Asia) Limited, FactSet and Bloomberg, data as at the last valuation date of the month as stated above, unless stated otherwise. Performance is calculated on NAV to NAV in base currency with dividend reinvested and net of fees. All indices are for reference only. Our portfolio disclosure policy can be obtained from the Investment Manager upon request to email fis@vp.com.hk.</p>
      <p>* © Morningstar 2025. All Rights Reserved. The information contained herein: (1) is proprietary to Morningstar and/or its content providers; (2) may not be copied or distributed; and (3) is not warranted to be accurate, complete or timely. Neither Morningstar nor its content providers are responsible for any damages or losses arising from any use of this information.</p>
      <p><strong>1.</strong> Index refers to Hang Seng Index (Price Return) since fund inception till 31 Dec 2004, thereafter it is the Hang Seng Index (Total Return) up to 30 Sep 2017. Hang Seng Index (Total Return) includes dividend reinvestment whereas Hang Seng Index (Price Return) does not take into account reinvestment of dividends. With effect from 1 Oct 2017, it is the MSCI Golden Dragon Index (Total Net Return), which takes into account of dividend reinvestment after deduction of withholding tax. <strong>2.</strong> Each hedged share class will hedge the Fund's base currency back to its currency of denomination on a best efforts basis. However, the volatility of the hedged classes measured in the Fund's base currency may be higher than that of the equivalent class denominated in the Fund's base currency. The hedged classes may be suitable for investors who wish to reduce the impact of changes in exchange rates between their local currency and the Fund's base currency. <strong>3.</strong> Investors should note that the base currency of Class "C" is in USD. The HKD is for reference only and should not be used for subscription or redemption purpose. Conversion to the base currency of Class "C" will normally take place at the prevailing rate (as determined by the Fund's Trustee or Custodian) on the corresponding fund dealing day. Investor should be aware of possible risks resulting from fluctuations of exchange rates against USD. <strong>4.</strong> As dividends may be paid out from capital, this may result in an immediate decrease in the NAV per share/unit and may reduce the capital available for the Fund for future investment and capital growth. Distributions are not guaranteed and may fluctuate. Past distributions are not necessarily indicative of future trends, which may be lower. Distribution payouts and its frequency are determined by the manager. The payment of distributions should not be confused with the Fund's performance, rate of return or yield. Positive distribution yield does not imply positive return. Annualized yield of MDis Class is calculated as follows: (Latest dividend amount/NAV as at ex-dividend date) x 12. Please refer to the offering document for further details including the distribution policy. <strong>5.</strong> Classification is based on Global Industry Classification Standard (GICS). <strong>6.</strong> Exposure refers to net exposure (long exposure minus short exposure). Derivatives e.g. index futures are calculated based on P/L instead of notional exposure. <strong>7.</strong> Volatility is a measure of the theoretical risk in terms of standard deviation, based on monthly return over the past 3 years. <strong>8.</strong> Performance fee will only be charged if the NAV at the end of the financial year or upon realization of units exceeds the "high watermark", which is the all-time year-end high of the Fund's NAV. If in any one year, the Fund suffers a loss, no performance fee can be charged in subsequent years until the loss is recovered fully (the high-on-high principle). <strong>9.</strong> The award is presented to fund products, fund management institutions, and related fund managers who have raised capital from both public and private overseas sectors. The award honors the long-term and stable performance profitability of institutions and fund managers, while also taking into account the fund performance and risk management capability of fund institutions and fund managers in the medium to long-term (one to three years). <strong>10.</strong> The award reflects performance up to 30 Sep 2018. <strong>11.</strong> The award reflects performance up to 31 Dec 2017. <strong>12.</strong> For Hong Kong investors only.</p>
      <p>Investors should note investment involves risk. The price of units may go down as well as up and past performance is not indicative of future results. Investors should read the explanatory memorandum for details and risk factors in particular those associated with investment in emerging markets. Information in this report has been obtained from sources believed to be reliable but Value Partners Hong Kong Limited does not guarantee the accuracy or completeness of the information provided by third parties. Investors should seek advice from a financial adviser before making any investment. In the event that you choose not to do so, you should consider whether the investment selected is suitable for you.</p>
      <p>For Singapore investors: The Fund is registered as a restricted foreign scheme in Singapore and will only be distributed to (i) institutional investors and (ii) accredited investors and certain other persons in Singapore in accordance with section 304 and 305 of the Securities and Futures Act. Value Partners Asset Management Singapore Pte Ltd, Singapore Company Registration No. 200808225G. This advertisement has not been reviewed by the Monetary Authority of Singapore.</p>
      <p>For UK investors: This material is being issued in the United Kingdom by Value Partners Hong Kong Limited to and/or is directed only at persons who are professional investors for the purposes of the Alternative Investment Fund Managers Regulations 2013 and is accordingly exempt from the financial promotion restriction in Section 21 of the Financial Services and Markets Act 2000 ("FSMA") in accordance with article 29(3) of the FSMA (Financial Promotions) Order 2005. The opportunity to invest in the Fund is only available to such persons in the United Kingdom and this material must not be relied or acted upon by any other persons in the United Kingdom.<br>This document has not been reviewed by the Securities and Futures Commission of Hong Kong. Issuer: Value Partners Hong Kong Limited.</p>
    </div>
    <div class="page-number">2</div>
  </div>
</template>

<style scoped>
.page-break {
  page-break-before: always;
  break-before: page;
}
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
  position: relative;
}
.page2-header {
  background-color: #0b5e41; /* Dark green matching image */
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 38px;
  position: relative;
  overflow: hidden;
}
.page2-header .title {
  font-size: 16px;
  font-weight: bold;
  padding-left: 20px;
  z-index: 2;
}
.date-wrap {
  position: relative;
  height: 100%;
  display: flex;
  align-items: center;
  padding: 0 35px 0 65px;
}
.date-bg {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(90deg, #596b33 0%, #a3b216 100%);
  clip-path: polygon(30px 0, 100% 0, 100% 100%, 0 100%);
  z-index: 1;
}
.date-wrap .date {
  position: relative;
  z-index: 2;
  font-size: 16px;
  font-weight: bold;
}
.main-columns {
  display: flex;
  gap: 30px;
  margin-bottom: 15px;
}
.col-left { flex: 1.05; }
.col-right { flex: 0.95; }
h2 {
  color: #0d6b4d;
  font-size: 15px;
  font-weight: 700;
  border-bottom: 2px solid #a3d900;
  padding-bottom: 3px;
  margin-bottom: 8px;
  margin-top: 0;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 10.5px;
}
.data-table th {
  border-bottom: 1px solid #333;
  text-align: left;
  padding: 4px 2px;
  font-weight: normal;
  color: #0d6b4d;
  vertical-align: bottom;
}
.data-table td {
  border-bottom: 1px solid #ccc;
  padding: 4px 2px;
}
.data-table.bordered-rows td {
  border-bottom: 1px solid #ddd;
}
.right-align { text-align: right !important; }
.center-align { text-align: center !important; }
.border-left-col { border-left: 1px solid #aaa; }
.footnote-under-table {
  font-size: 9px;
  color: #666;
  margin-top: 4px;
  font-style: italic;
}

.bar-chart-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 10.5px;
}
.bar-row {
  display: flex;
  align-items: center;
}
.bar-label {
  width: 130px;
  text-align: right;
  padding-right: 10px;
  color: #333;
}
.bar-track {
  flex: 1;
  display: flex;
  align-items: center;
}
.bar-fill {
  height: 12px;
  background-color: #888;
}
.bar-val {
  margin-left: 6px;
  color: #333;
}

.fact-table {
  width: 100%;
  font-size: 10.5px;
  border-collapse: collapse;
}
.fact-table td {
  padding: 2px 0;
  vertical-align: text-top;
}
.fact-label {
  width: 130px;
  color: #555;
}
.italic-desc {
  font-style: italic;
  font-size: 10px;
  color: #666;
  text-align: justify;
}

.staff-list {
  font-size: 10.5px;
  line-height: 1.5;
}

.awards-container {
  display: flex;
  align-items: flex-start;
  margin-top: 8px;
}
.award-icon-large {
  font-size: 55px;
  line-height: 1;
  margin-right: 15px;
  color: #9a7845; /* Trophy color approximation */
  filter: sepia(0.8) hue-rotate(-20deg) saturate(2);
}
.awards-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.awards-section .award-item {
  font-size: 10px;
}
.awards-section .award-text strong {
  color: #333;
}
.awards-section .award-text em {
  color: #666;
  font-size: 9.5px;
}

.qr-section {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  margin-top: 40px;
  text-align: center;
  font-size: 9.5px;
}
.qr-scan-text {
  font-size: 11px;
  color: #333;
  margin-right: 5px;
}
.qr-item img {
  width: 50px;
  height: 50px;
  margin-bottom: 4px;
}

.footnotes-block {
  margin-top: 20px;
  padding-top: 10px;
  font-size: 7.5px;
  color: #555;
  text-align: justify;
  line-height: 1.3;
}
.footnotes-block p {
  margin: 0 0 4px 0;
}
.page-number {
  position: absolute;
  right: 40px;
  bottom: 10px;
  font-size: 10px;
  font-weight: bold;
}
</style>
