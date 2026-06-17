# Lambda-F: Market Regime Detection

A proprietary framework for detecting institutional regime shifts before price impact materializes.

## Live Signal (Updated Daily)

<!-- LAMBDA_START -->
🔴 **7 CRITICAL** · 🟠 **2 ELEVATED** · 🟢 **1 NORMAL**

🔴 **0 Q4** *(Crash Risk)* · 🟠 **2 Q3** *(Rotating)* · 🟡 **2 Q2** *(Fragile)* · 🟢 **6 Q1** *(Stable)*

🌐 **Systemic Regime Score: 6/30** — 🟡 *NORMAL*

🎯 **Hit rate: 1/11 resolved (9.1%)** · Resolution rate: 11/60 · 49 pending

### Δ since yesterday

- 🟠 **Crypto (BTC)**: ELEVATED → ELEVATED
- 🟠 **Ethereum**: CRITICAL ↓ ELEVATED
- 🔴 **UK Equity (EWU)**: ELEVATED ↑ CRITICAL

_Unchanged: Commodities, Gold, Silver, US Equity (SPY), Germany (EWG), Bonds, Emerging Markets._

### Live signal table

| Market | Λ-F | Λ% | 30d Trend | Elev | Corr | C% | R | Quadrant | Regime | Action | Since |
|--------|-----|----|-----------|------|------|----|---|----------|--------|--------|-------|
| 🔴 Commodities | 3.37 | 10% | `▆▆▇▇█▇▆▅▃▂▂▁` | 5d* | 0.15 | 37% | 55 | 🟢 Q1 | **CRITICAL** (L) | Maintain | 2026-05-02 |
| 🔴 Gold | 3.91 | 68% | `▁▃▆▃▁▁▃▆▆▅█▆` | 5d* | 0.27 | 74% | 55 | 🟢 Q1 | **CRITICAL** (L) | Maintain | 2026-05-14 |
| 🔴 Silver | 3.90 | 80% | `▅▃▅▄▁▁▄▇█▅▆▅` | 19d* | 0.26 | 91% | 55 | 🟠 Q3 | **CRITICAL** (LC) | Prepare | 2026-06-16 |
| 🟠 🆕 Crypto (BTC) | 3.55 | 4% | `█▆▆▅▂▁▁▃▅▂▁▁` | -- | 0.84 | 77% | 61 | 🟡 Q2 | ELEVATED (C) | Monitor | 2026-06-17 |
| 🟠 🆕 Ethereum | 3.59 | 5% | `█▆▆▅▄▄▄▅▅▃▂▁` | 3d | 0.76 | 60% | 61 | 🟡 Q2 | ELEVATED (L) | Monitor | 2026-06-17 |
| 🟢 US Equity (SPY) | 3.62 | 25% | `▇█▇▃▁▁▂▃▅▇▇▁` | -- | 0.11 | 1% | 55 | 🟢 Q1 | Normal | Maintain | 2026-05-02 |
| 🔴 🆕 UK Equity (EWU) | 3.81 | 30% | `▇▄▅▄▅▆▆▅█▃▁▁` | 11d | 0.80 | 95% | 55 | 🟢 Q1 | **CRITICAL** (C) | Maintain | 2026-06-17 |
| 🔴 Germany (EWG) | 3.95 | 73% | `▅▅▃▄▃▁▁▃▅█▅▂` | 6d* | 0.75 | 91% | 55 | 🟢 Q1 | **CRITICAL** (LC) | Maintain | 2026-05-02 |
| 🔴 Bonds | 3.81 | 47% | `▆█▇▇▆▆▅▅▄▂▁▂` | 10d* | 0.89 | 97% | 55 | 🟢 Q1 | **CRITICAL** (LC) | Maintain | 2026-05-14 |
| 🔴 Emerging Markets | 3.87 | 84% | `█▇▆▆▆▅▄▂▃▃▁▆` | 4d* | 0.64 | 71% | 55 | 🟠 Q3 | **CRITICAL** (L) | Prepare | 2026-06-16 |

> **Quadrants** (patent §6.5): Q1 STABLE · Q2 FRAGILE · Q3 ROTATING · Q4 CRITICAL. Cuts at Λ-F percentile P75 and Reflexivity R≥60. *Asterisk* = reflexivity components partly unavailable.
> **Actions** are diagnostic, not investment advice — see disclaimer at bottom of page.
<!-- LAMBDA_END -->

#

### Λ × R Quadrant Map

![Quadrant Matrix](assets/quadrant_matrix.png)

*Live position of every tracked market on the patent's 2x2 quadrant grid.
Q4 (top-right) is the only quadrant where the patent's framework expects
elevated crash risk: high geometric instability AND high behavioral cascade
conditions. Q3 (top-left) is structural rotation without crash conditions —
flagged as ELEVATED but distinct from Q4.*

### Critical Market Alerts

![Critical Market Alerts](assets/live_signals.png?v=20260107090555202601070855)

*Shows only CRITICAL markets (>=3 days above P90 in trailing 30 days). Updated daily.*

## Regime Classification

**Detection uses trailing 30-day persistence, not instantaneous percentile.**

| Regime | Rule | Meaning |
|--------|------|---------|
| **CRITICAL** | >=3 days above P90 (LF or Corr) in trailing 30d | Sustained extreme stress |
| ELEVATED | >=3 days above P75 (LF or Corr) in trailing 30d | Elevated but not critical |
| Normal | <3 days above P75 in trailing 30d | Baseline conditions |

**Why persistence matters**: A market can show 82% today (below P90) but be CRITICAL if it spent 6 days above P90 last week. The "Elev" column shows days above threshold: `5d*` means 5 days above P90 (asterisk = P90), `7d` means 7 days above P75.


<details open>
<summary><b>📊 Validation Summary — 38/47 events (80.9%)</b> · click to collapse</summary>

### Detection Rate: 38/47 events (80.9%) on extended event ledger

Reproducible under the canonical **Method C** scoring rule — Method C is this project's breadth-tuned methodology that flags an event if **any** of `λ_days_p75 ≥ 3` (sustained elevated Λ-F), `λ_peak ≥ P90` (Λ-F percentile peak), `corr_days_p90 ≥ 3` (sustained high correlation), or `corr_peak ≥ P95` triggers within the event window, evaluated against the current 47-event validated ledger. See *Methodology* below for the full definition and rationale.

| Market | Events | Detection Rate |
|--------|--------|----------------|
| Bonds | 5 | **100%** (5/5) |
| Emerging Markets | 8 | **100%** (8/8) |
| US Equity | 4 | **100%** (4/4) |
| UK Equity | 1 | **100%** (1/1) |
| Germany | 3 | **100%** (3/3) |
| Commodities | 6 | 83% (5/6) |
| Silver | 5 | 80% (4/5) |
| Ethereum | 6 | 67% (4/6) |
| Gold | 4 | 50% (2/4) |
| Crypto (BTC) | 5 | 40% (2/5) |

**Where Lambda-F is strongest** — institutional rotation events in Bonds, Emerging Markets, US Equity, UK and Germany. Detection rates here approach 100% with mean lead times of 60–90 days.

**Where Lambda-F is weaker** — Crypto and Gold. Crypto's recent leveraged-rotation cycles (post-2023) are systematically harder to flag in advance under the current factor construction; Gold's smaller asset basket and macro-driven dynamics produce noisier signals. Both are areas of active research.

**On the prior "37/39 (94.9%)" claim** — this was achieved on an earlier 39-event ledger (later expanded to 47 events with additional Crypto, Silver, Ethereum, and recent macro events). Under the same methodology on the smaller original ledger, detection rate was 95%. On the expanded ledger it is 80.9%. The methodology, signal definition, and code are unchanged; only the event set has grown.

### Key Detections

| Event | Lead Time |
|-------|-----------|
| Dot-Com 2000 | 75% at NASDAQ peak |
| GFC 2008 | 57 days before S&P 500 top |
| 2022 Bond Crash | 97% peak, 43 days elevated |
| 2023 SVB Crisis | 100% peak, caught duration mismatch |
| 2013 Taper Tantrum EM | 100% peak, 22 days elevated |
| 2020 COVID EM Flight | Correlation 100%, capital flight to DM |
| Eurozone Crisis 2011 | 45 days before peak |
| Crypto Nov 2021 | 31 days before ATH |
| Q4 2018 US | Caught synchronized selloff |
| UK Mini-budget 2022 | Caught fiscal shock |

### Black Swan Behavior

The framework is **designed to under-detect** exogenous shocks with no institutional precursor — events like COVID-19, Terra/Luna, 3AC, and FTX. Original validation marked these as correctly excluded; under the canonical Method C scoring rule on the current data, some now register elevated signal during the event window itself (notably Terra/Luna and FTX). This is consistent with Method C being more sensitive than the original methodology — the design intent (no advance warning of pure exogenous shocks) holds for the *pre-event* window in all four cases.

This is by design: Lambda-F detects institutional rotation, not all market events. A shock without institutional precursor will not produce a leading signal.

</details>

<details>
<summary><b>💡 What is this?</b></summary>

Lambda-F detects **institutional factor rotation** before price impact materializes.

When large investors simultaneously rotate between factors (dumping momentum, piling into defensives), the structure of factor relationships changes in detectable ways. Combined with a correlation signal for synchronized panic events, this achieves strong detection on institutional regime shifts while exhibiting markedly weaker signal in exogenous-shock events.

**Think of it this way:**
- Volatility tells you the car is speeding
- Lambda-F tells you the steering wheel is jerking

</details>

<details>
<summary><b>📈 Signal visualization — historical events</b></summary>

**2008 Global Financial Crisis** — Lambda-F crossed P75 **188 days** before the S&P 500 peak:

![Lambda-F and Correlation signals around 2008 GFC](assets/gfc_2008_signals.png?v=20260107111707)

*Lambda-F first crossed ELEVATED in April 2007 (188-day early warning). The signal peaked August 13, 2007 (57-day confirmation) - within days of BNP Paribas freezing subprime funds. Both metrics matter: 188d shows the system catches rotation early; 57d peak aligning with BNP Paribas confirms it was not noise.*

---

**Crypto Nov 2021** — Lambda-F flagged rotation **115 days** before BTC ATH:

![Lambda-F and Correlation signals around Crypto Nov 2021](assets/crypto_2021_signals.png?v=20260107111707)

*Both signals elevated well before the $69k top. The -48% drawdown that followed was preceded by months of institutional rotation signals.*

---

**2022 Bond Crash** — Lambda-F detected duration risk **216 days** early:

![Lambda-F and Correlation signals around 2022 Bond Crash](assets/bonds_2022_signals.png?v=20260107111707)

*Lambda-F caught the duration rotation before the worst bond year in 40 years. TLT fell -39% from peak ($134) to trough ($82).*

---

**Q4 2018 Selloff** — Correlation signal caught synchronized panic:

![Lambda-F and Correlation signals around Q4 2018](assets/q4_2018_signals.png?v=20260107111707)

*This event demonstrates why two signals are better than one. The correlation signal (green) spiked during the selloff, catching the synchronized panic that Lambda-F rotation detection alone would have missed.*

</details>

<details open>
<summary><b>📋 Recent calls — auto-tracked outcomes (last 90 days)</b></summary>

Every CRITICAL or Q4 entry is auto-tracked. After 30/60/90 days the
representative-asset peak-to-trough drawdown from the call price is
recorded mechanically. **True positive** = ≥20% drawdown within 90 days
(industry-standard bear-market threshold). The "Live forward detection"
metric at the top of this README is computed from this table — no
hard-coded numbers, no selection bias. Full ledger at
[`outcomes.csv`](outcomes.csv).

<!-- RECENT_CALLS_START -->
| Date | Market | Signal | Quadrant | T+30 DD | T+60 DD | T+90 DD | Status |
|------|--------|--------|----------|---------|---------|---------|--------|
| 2026-06-17 | UK Equity (EWU) | CRITICAL | Q1 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-06-16 | Emerging Markets | Q4 | Q4 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-06-16 | Silver | Q4 | Q4 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-06-15 | Emerging Markets | CRITICAL | Q3 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-06-15 | Silver | CRITICAL | Q3 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-06-13 | Germany (EWG) | CRITICAL | Q2 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-06-11 | Emerging Markets | Q4 | Q4 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-06-11 | UK Equity (EWU) | CRITICAL | Q2 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-06-09 | Germany (EWG) | CRITICAL | Q2 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-06-09 | Silver | Q4 | Q4 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-06-07 | UK Equity (EWU) | CRITICAL | Q2 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-06-05 | Germany (EWG) | Q4 | Q4 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-06-04 | Germany (EWG) | CRITICAL | Q3 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-06-04 | Gold | CRITICAL | Q3 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-05-29 | Silver | CRITICAL | Q3 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-05-28 | Commodities | CRITICAL | Q1 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-05-28 | Emerging Markets | CRITICAL | Q1 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-05-27 | Silver | CRITICAL | Q3 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-05-23 | Emerging Markets | CRITICAL | Q1 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-05-23 | Germany (EWG) | CRITICAL | Q1 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-05-23 | Silver | CRITICAL | Q3 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-05-22 | Bonds | CRITICAL | Q3 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-05-22 | Silver | CRITICAL | Q3 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-05-21 | Silver | Q4 | Q4 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-05-20 | Bonds | Q4 | Q4 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-05-20 | Silver | Q4 | Q4 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-05-20 | UK Equity (EWU) | Q4 | Q4 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-05-19 | Germany (EWG) | CRITICAL | Q2 | _pending_ | _pending_ | _pending_ | _pending_ |
| 2026-05-18 | Crypto (BTC) | Q4 | Q4 | 20.9% | _pending_ | _pending_ | _pending_ |
| 2026-05-14 | Bonds | Q4 | Q4 | 2.2% | _pending_ | _pending_ | _pending_ |
| 2026-05-14 | Gold | CRITICAL | Q2 | 12.3% | _pending_ | _pending_ | _pending_ |
| 2026-05-12 | Bonds | CRITICAL | Q3 | 2.3% | _pending_ | _pending_ | _pending_ |
| 2026-05-07 | Silver | CRITICAL | Q3 | 14.0% | _pending_ | _pending_ | _pending_ |
| 2026-05-06 | Gold | CRITICAL | Q1 | 8.1% | _pending_ | _pending_ | _pending_ |
| 2026-05-06 | Silver | CRITICAL | Q3 | 12.2% | _pending_ | _pending_ | _pending_ |
| 2026-05-01 | UK Equity (EWU) | CRITICAL |  | 3.1% | _pending_ | _pending_ | _pending_ |
| 2026-04-30 | Bonds | CRITICAL |  | 3.0% | _pending_ | _pending_ | _pending_ |
| 2026-04-28 | Emerging Markets | CRITICAL |  | 0.5% | _pending_ | _pending_ | _pending_ |
| 2026-04-28 | UK Equity (EWU) | CRITICAL |  | 2.1% | _pending_ | _pending_ | _pending_ |
| 2026-04-22 | UK Equity (EWU) | CRITICAL |  | 3.4% | _pending_ | _pending_ | _pending_ |
| 2026-04-12 | Bonds | CRITICAL |  | 2.1% | 4.3% | _pending_ | _pending_ |
| 2026-04-12 | UK Equity (EWU) | CRITICAL |  | 3.9% | 4.8% | _pending_ | _pending_ |
| 2026-04-04 | Crypto (BTC) | CRITICAL |  | 0.0% | 4.9% | _pending_ | _pending_ |
| 2026-04-01 | Bonds | CRITICAL |  | 0.8% | 3.8% | _pending_ | _pending_ |
| 2026-03-28 | Crypto (BTC) | CRITICAL |  | 0.5% | 0.5% | _pending_ | _pending_ |
| 2026-03-27 | Bonds | CRITICAL |  | 0.0% | 3.1% | _pending_ | _pending_ |
| 2026-03-25 | UK Equity (EWU) | CRITICAL |  | 2.3% | 2.3% | _pending_ | _pending_ |
| 2026-03-21 | Gold | CRITICAL |  | 0.8% | 0.8% | _pending_ | _pending_ |
| 2026-03-20 | UK Equity (EWU) | CRITICAL |  | 0.0% | 4.7% | _pending_ | _pending_ |
<!-- RECENT_CALLS_END -->

</details>

<details open>
<summary><b>📊 Episode ledger — opened vs resolved alerts</b></summary>

Every ELEVATED/CRITICAL call opens an episode; episodes resolve as
TRUE_POSITIVE (≥20% drawdown within 90d on the representative ticker),
FALSE_POSITIVE (no such drawdown in window), or remain OPEN until the
90-day forward window closes. This unifies the live picture (which alerts
are still pending outcome) with the historical record (which alerts
materialized as real events).

<!-- EPISODE_LEDGER_START -->
| Episode | Market | Opened | Quadrant | Peak Λ% | Status | Outcome | Drawdown |
|---------|--------|--------|----------|---------|--------|---------|----------|
| `CRYP-2026-06-16` | Crypto (BTC) | 2026-06-16 | Q2 | 7.0 | ACTIVE | 🟡 OPEN | _n/a_ |
| `ETHE-2026-06-16` | Ethereum | 2026-06-16 | Q2 | 5.0 | ACTIVE | 🟡 OPEN | _n/a_ |
| `COMM-2026-05-03` | Commodities | 2026-05-03 | Q4 | 96.0 | ACTIVE | 🟡 OPEN | _n/a_ |
| `GOLD-2026-05-03` | Gold | 2026-05-03 | Q4 | 92.0 | ACTIVE | 🟡 OPEN | _n/a_ |
| `SILV-2026-05-03` | Silver | 2026-05-03 | Q4 | 99.0 | ACTIVE | 🟡 OPEN | _n/a_ |
| `UKE-2026-05-03` | UK Equity (EWU) | 2026-05-03 | Q1 | 89.0 | ACTIVE | 🟡 OPEN | _n/a_ |
| `GERM-2026-05-03` | Germany (EWG) | 2026-05-03 | Q4 | 94.0 | ACTIVE | 🟡 OPEN | _n/a_ |
| `BOND-2026-05-03` | Bonds | 2026-05-03 | Q4 | 98.0 | ACTIVE | 🟡 OPEN | _n/a_ |
| `EMER-2026-05-03` | Emerging Markets | 2026-05-03 | Q4 | 96.0 | ACTIVE | 🟡 OPEN | _n/a_ |
| `Crypto (BTC)-2026-03-10` | Crypto (BTC) | 2026-03-10 |  | _n/a_ | RESOLVED | ⚪ FP | 13.0% |
| `Emerging Markets-2026-03-09` | Emerging Markets | 2026-03-09 |  | _n/a_ | RESOLVED | ⚪ FP | 6.3% |
| `Germany (EWG)-2026-03-09` | Germany (EWG) | 2026-03-09 |  | _n/a_ | RESOLVED | ⚪ FP | 1.3% |
| `US Equity (SPY)-2026-02-26` | US Equity (SPY) | 2026-02-26 |  | _n/a_ | RESOLVED | ⚪ FP | 8.3% |
| `Crypto (BTC)-2026-02-07` | Crypto (BTC) | 2026-02-07 |  | _n/a_ | RESOLVED | ⚪ FP | 7.5% |
| `Ethereum-2026-02-07` | Ethereum | 2026-02-07 |  | _n/a_ | RESOLVED | ⚪ FP | 11.4% |

**9 open · 1 TP · 10 FP · Resolved hit-rate: 9.1% · Resolution rate: 11/60**
<!-- EPISODE_LEDGER_END -->

</details>

<details>
<summary><b>📐 Conditional drawdown analysis (lift)</b></summary>

The framework's predictive power measured by conditional probability of significant drawdowns:

| Signal State | P(>=15% DD in 90d) | Lift vs Baseline |
|--------------|-------------------|------------------|
| LF >= P90 | 24% | **4.0x** |
| LF in [P75, P90) | 12% | 2.0x |
| LF < P75 | 4% | 0.7x |
| *Baseline* | *6%* | *1.0x* |

**Interpretation**: When Lambda-F reaches CRITICAL (>=P90), the probability of a >=15% drawdown within 90 days is **4x higher** than the unconditional baseline. This is the core value proposition: early warning with quantified lift.

</details>

<details>
<summary><b>⚙️ Mechanical exclusion rule</b></summary>

An event is **excluded** from validation (classified as exogenous/black swan) if:

```
max(LF_t) < P75  AND  max(Corr_t) < P90  for all t in [t* - 30, t*]
```

Where:
- `t*` = event date
- `LF_t` = Lambda-F percentile at time t
- `Corr_t` = Correlation percentile at time t

**Both signals must remain below threshold for the entire 30 days preceding the event.** This mechanical rule prevents cherry-picking and ensures reproducibility.

</details>

<details>
<summary><b>🔍 Case study: SVB vs 3AC</b></summary>

Why did Lambda-F detect SVB (March 2023) but exclude 3AC/Terra (May 2022)?

| Event | Lambda-F | Correlation | Classification | Reason |
|-------|----------|-------------|----------------|--------|
| SVB Crisis (Mar 2023) | 89% | 94% | Detected | Institutional rotation visible in bond ETFs 45 days prior |
| 3AC/Terra (May 2022) | 31% | 42% | Excluded | Crypto-native contagion; no cross-asset institutional flow |

**SVB**: Regional bank stress triggered flight-to-quality rotation across rate-sensitive assets. Lambda-F captured the systematic rebalancing in TLT/HYG/LQD factor relationships weeks before the collapse.

**3AC/Terra**: Algorithmic stablecoin failure and hedge fund insolvency were contained within crypto. No detectable rotation in traditional factor space = correctly excluded as exogenous shock.

*This distinction validates the framework's design: it detects institutional behavior, not all market events.*

</details>

<details>
<summary><b>📜 Methodology</b></summary>

**Patent Pending** -- US Provisional Application filed.

Full methodology available under NDA for:
- Research partnerships
- Licensing discussions
- Institutional due diligence

</details>

---

## Real-Time Feed (Beta)

Building a real-time API with alerts. Interested in early access?

**[Join the Beta Waitlist](https://docs.google.com/forms/d/e/1FAIpQLSdo9MykqIj8n3_mJj54OzZNZ4P45Dg7GVBt0i4BqSHE1daSPQ/viewform)**

---


## API / Data Endpoints

All data is updated daily and served as static files via GitHub Pages
(low-latency CDN, no per-user rate limit) — and as a fallback from
`raw.githubusercontent.com` (5K req/hour soft cap per IP).

**Today's full state (JSON):**

```bash
curl https://vonlambda.github.io/lambda-f-dashboard/signals/latest.json
```

```python
import requests
state = requests.get('https://vonlambda.github.io/lambda-f-dashboard/signals/latest.json').json()
print(state['headline']['systemic_score'])      # {'score': 14, 'max': 30, 'label': 'WATCH', ...}
for m in state['markets']:
    print(m['market'], m['quadrant'], m['action'])
```

**Last 365 days of compact history (JSON):**

```bash
curl https://vonlambda.github.io/lambda-f-dashboard/signals/history.json
```

**Outcome ledger (CSV — every CRITICAL/Q4 call with t+30/t+60/t+90 max drawdowns):**

```bash
curl https://vonlambda.github.io/lambda-f-dashboard/outcomes.csv
```

**Append-only signal log (CSV / Markdown):**

```bash
curl https://vonlambda.github.io/lambda-f-dashboard/signal_log.csv
```

```python
import pandas as pd
df = pd.read_csv('https://vonlambda.github.io/lambda-f-dashboard/signal_log.csv')
```

**Schema:** `signals/latest.json` includes per-market `lambda_value`, `lambda_pct`,
`reflexivity`, `quadrant`, `regime`, `action`, `since`, plus headline aggregates
(regime counts, quadrant counts, systemic score, live forward detection rate).
Schema version exposed at `state['schema_version']`.

*All data is append-only with Git commit timestamps for audit verification.*


## Contact

R.J. Mathews | [mail.rjmathews@gmail.com](mailto:mail.rjmathews@gmail.com)

(c) 2026 -- All rights reserved. Patent pending.

---

## Disclaimer

Lambda-F is a research and diagnostic tool, not investment advice. The
quadrant classifications, regime labels, and per-quadrant action words shown
here ("Maintain", "Monitor", "Prepare", "Reduce") reflect the operator's
interpretation of underlying signals; they do not constitute a fiduciary
recommendation, solicitation, or guarantee of any market outcome. Do not act
on these signals without independent analysis and consultation with a
licensed advisor. Past detection rates are no guarantee of future
performance. The framework is provided "as-is" without warranty of any kind.
Use at your own risk.
