# Literature check — is the decomposition project already done?

Run: 11 August 2026. Searches via web; PDFs read through WebFetch (no raw PDF extraction possible, so quotes are fetch-mediated and worth spot-checking against your own copies).

## Verdict in one line

**The decomposition project (expectations vs term premium in FOMC windows) is done — twice, by two papers that contradict each other. The wedge project is not done.** Pivot toward the wedge; harvest the decomposition work as a reconciliation section, not a paper.

---

## 1. The decomposition question: taken

### Hofmann, Li & Wu, BIS WP 1252 (Mar 2025) — "Monetary policy and the secular decline in long-term interest rates: A global perspective"

https://www.bis.org/publ/work1252.pdf

Extends Hillenbrand to G10, Jun 1989–2023, identical 3-day window. ~70% of the secular decline in long rates across 7 advanced economies occurs in **US** FOMC windows; other central banks' windows do nothing. Decomposes using a **Bauer–Rudebusch observed-shifting-endpoint (OSE) model** — i.e. exactly the "next step" we identified. Concludes the window decline is **risk-neutral, not term premium** (US pseudo-R²: RNY 96, TP 32).

**Fatal weakness, verified verbatim:** *"Our empirical proxy for τ_t is the first principal component of cumulative changes in the yield curve during FOMC windows."* The shifting endpoint **is** the cumulative FOMC-window series. In an OSE model the risk-neutral rate inherits the endpoint, so "the FOMC-window decline is risk-neutral" is close to definitional. They justify it circularly (*"the cumulative changes in yields during the Fed's announcement windows are the best fit for the long-run trends"*).

Also absent: cumulative percentage-point attributions (only pseudo-R² shares), within-window timing, post-2021, ACM/Kim–Wright robustness. Still a working paper.

### Pan & Peng, "The Pre-FOMC Drift in Long-Term Treasury Bonds" (SSRN 4764451, draft 2 Jun 2026)

https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4764451

Sept 1994–Dec 2025, 250 scheduled announcements. Explicitly frames against Hillenbrand: the t−1 day alone contributes **−3.09 pp of the −7.91 pp three-day decline (~40%)**. Uses **ACM** (Kim–Wright as robustness). Day t−1, 10y: yield −0.79 bp (t −2.39), **term premium −0.71 bp (t −2.34)**, expected short rate −0.08 bp (t −0.26).

**This contradicts our §2 result** (t−1: RN −0.67, t −3.15; TP −0.36, t −1.30) on the same model. Difference is almost certainly sample: they start Sep 1994, scheduled only; we start Jun 1989, all 373 meetings. Mechanism: uncertainty-resolution risk premium tied to **labour-market** attention, not policy attention. Working paper; AEA 2026 program.

### Hillenbrand already published the ACM caveat

Internet Appendix reports ACM/Kim–Wright TP declining **100–200 bp** in windows (our −1.33 pp is inside that range) and dismisses it: the models *"might overstate the importance of term premia as the models do not explicitly account for the secular decline."* Our "correction (a)" was his footnote.

### What remains open in the decomposition

1. **Reconciling Hofmann–Li–Wu (96% risk-neutral) with Pan & Peng (90% term premium on the biggest day).** Model or sample? Nobody has asked. This is the sharpest live disagreement.
2. A **non-circular** shifting-endpoint decomposition (Kim–Wright, or Crump–Eusepi–Moench SR775 survey-based term premium) applied to windows.
3. Cumulative pp contributions (neither paper reports the RN/TP level split we computed).
4. **Reconciling with Hanson–Lucca–Wright (QJE 2021):** their mechanism requires window term-premium moves to *reverse* within 6–12 months; Hillenbrand's fact requires they don't. Direct test: does the in-window TP component mean-revert while RN doesn't? Nobody has run it.

Items 1, 2 and 4 together are a paper — but a reconciliation paper, adjudicating others' claims.

---

## 2. The wedge question: NOT done

No paper combines: **(SEP longer-run dot as the Fed leg) × (market-implied long-run endpoint as the market leg) × (FOMC announcement window) × (term premium vs expected-rate split).** Every neighbour drops at least one element.

### Closest neighbours — all must be cited and differentiated

| Paper                                                                        | What it owns                                                                                                             | What it leaves                                                                                                                                                                                               |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Bauer, Pflueger & Sunderam, QJE 2024** "Perceptions about Monetary Policy" | Pre-meeting subjective-belief state variable → term premia **and** announcement-window long-yield responses (§4.2, §4.3) | State variable is a perceived *slope* (reaction-function coefficient), not a *level* gap vs the Fed's published endpoint. No SEP. **Your paper is an extension of this and referees will read it that way.** |
| **Cao, Crump, Eusepi & Moench, FRBNY SR 934**                                | "Disagreement about short rates comoves with the term premium" — establishes your mechanism in the time series           | Disagreement is forecaster-vs-forecaster dispersion, monthly, no FOMC windows, no SEP                                                                                                                        |
| **Amodeo (2026)**, UCSD JMP "Mind the Gap"                                   | Explicit Fed-minus-market policy-rate gap D^h_t as a state variable                                                      | Fed leg is **Tealbook**, not SEP; quarterly horizons not the endpoint; outcome is macro transmission, not yields/TP                                                                                          |
| **Engstrom, FEDS 2026-026** "Anchored to the Dot Plot"                       | SEP-minus-expectations discrepancy predicts subsequent forecast errors **including market-based ones**                   | No announcement-window event study, no TP split. **Read in full before writing the intro** — this is the one that could narrow your contribution to "new channel" rather than "new signal"                   |
| **Couture, J.Macro 2021**                                                    | Changes in the median FOMC funds-rate projection move asset prices                                                       | Regressor is the Fed-side *change*, not a pre-meeting wedge; no TP split. **Read in full** — an overlapping spec could be in a robustness table                                                              |
| **Cieslak, McMahon & Pang (2024)**, Brookings                                | Fed communication 2020–23 priced through risk premia not expected rates, with Kim–Wright and Cieslak–Pang decompositions | Descriptive; no formal SEP-vs-market gap. Motivation, not preemption                                                                                                                                         |
| **Bauer & Chernov, JF 2024**                                                 | Precedent that a pre-meeting belief variable predicting announcement-window outcomes is JF-publishable                   | Also a competing regressor — show the wedge survives controlling for options-implied skewness                                                                                                                |
| **Favero, Melone & Tamoni, JFQA 2024**                                       | "Gap between policy rate and equilibrium rate → bond returns" — **the name is taken**                                    | Different wedge (actual rate vs demographic y*). Be verbally precise or be mistaken for it                                                                                                                   |

### Identification threats to handle

- **Bauer & Swanson, NBER Macro Annual 2023.** Announcement surprises are predictable from pre-meeting public information. The wedge *is* pre-meeting public information, so a significant coefficient may be the Fed-response-to-news channel through expected rates, mislabelled as term premium. Orthogonalize against their predictor set.
- **Hillenbrand himself.** A slow-moving level wedge regressed on window yield changes can pick up the secular trend mechanically. Detrend.
- **Pan & Peng.** If the window starts at t−1, their pre-FOMC term-premium drift is inside it.
- **Acosta, Ajello, Bauer, Loria & Miranda-Agrippino, FRBSF 2025-30** — the event-study database to use; note they **explicitly decline** to do TP decomposition in event windows on estimation-uncertainty grounds. You will have to defend doing what they refused to do.

### The binding risk is power, not preemption

Hartley (Mercatus 2025) reports survey-based and FOMC r* estimates *"never differed by more than 0.42 percent"* since 2012. That is your gate-doc check 7 confirmed externally. The SEP leg exists only from Jan 2012, quarterly, with 19 median changes. **Use the market-implied forward endpoint for the market leg** — it gives range and daily updating — and consider the dispersion fallback (49 distinct values, ρ = 0.80) for the Fed leg, as the gate doc already recommended.

### Supportive theory for the mechanism

**Ahonon & Roussellet, FRBNY SR 1187 (Mar 2026)** — investor r* uncertainty is ±170 bp under learning vs ±55 bp under full information, and r* is the primary long-run driver of bond risk premia (loading 0.34). If investors are genuinely that uncertain about r*, a 50–100 bp Fed–market wedge is plausibly priced as *risk* rather than as an expectation error. This is your mechanism section, and it is already in the project docs.

---

## 3. Recommended reading before committing

1. Engstrom, FEDS 2026-026 — full text
2. Couture, J.Macro 2021 — full text, especially robustness tables
3. Bauer, Pflueger & Sunderam QJE 2024 §4.2–4.3 — the template to differentiate from
4. Hofmann, Li & Wu — confirm the circularity quote against the PDF
5. Pan & Peng Table 2 — and diagnose the t−1 discrepancy against our numbers
