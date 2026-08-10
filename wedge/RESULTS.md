# Fed–Market r\* Disagreement and Bond Pricing — Gate and Post-Gate Results

**Run:** 10 August 2026
**Data:** `ReactionFunctionProject/` as archived, plus the FOMC announcement calendar
retrieved from federalreserve.gov historical pages (2012–2026).
**Code:** `build_wedge.py` → `run_checks.py` → `verify.py` → `robustness.py` → `figures.py`
**Numbers file:** `results/results.json`, `results/verification.json`, `results/robustness.json`.
Nothing below was retyped.

---

## 0. What was actually run

The handoff says "pre-data, no empirical work has been run." The folder disagrees:
the SEP archive is built (57 meetings, 2,748 participant-horizon rows, 36 meetings
de-anonymised), the SPD/SMP archive is parsed (92 surveys), HLW is present, and
`ACMTermPremium.xls` carries the daily ACM curve through 6 August 2026 with
`ACMY`, `ACMRNY` and `ACMTP` at 1–10y. All of data items 1–4 exist. Item 5, the
FOMC calendar, did not, and was retrieved.

Three series were built:

| | Definition | Coverage |
|---|---|---|
| r\*<sub>Fed</sub> | SEP longer-run FFR median − longer-run PCE | 57 SEP meetings, 2012-01 → 2026-03 |
| r\*<sub>Mkt</sub> (SPD) | SPD/SMP longer-run FFR median − longer-run PCE | 92 surveys, 2013-01 → 2026-06 |
| r\*<sub>Mkt</sub> (ACM) | 9y1y risk-neutral forward (10·RNY10 − 9·RNY09) − 2.0 | daily |

Event panel: **116 scheduled FOMC announcements**, 2012-01-25 → 2026-07-29
(unscheduled calls and notation votes excluded; all 57 SEP dates in `sep_dates.py`
are a subset of the retrieved calendar, which is the calendar's own validation).
The wedge is measured **strictly before** the announcement — the Fed side is the
*previous* SEP, because the current one is released at the announcement itself.

---

## 1. The gate

### Check 1 — π\* dispersion — **FAIL, decisively**

All 594 participant longer-run PCE submissions across 36 de-anonymised meetings
are **exactly 2.0**. Maximum within-meeting standard deviation: **0.000000**.
Meetings with any dispersion at all: **0 of 36**.

The SPD side is the same. The longer-run PCE median is 2.0 in all 91 surveys —
including all 12 where the build script records it as `measured` rather than
`assumed`, so this is not an artefact of the assumption.

**Consequence.** r\*<sub>i,t</sub> is the longer-run dot minus a constant, on both
sides. The "extraction of r\*" is a relabelling of the longer-run *nominal* rate.
This does not break the design — the wedge still exists and still varies — but it
breaks the framing. Everything below is a result about disagreement over the
longer-run nominal policy rate. It should be written that way, and the paper
cannot claim to separate real-rate disagreement from inflation-credibility
disagreement, because there is no inflation disagreement to separate.

### Check 2 — wedge variance decomposition — **PASS both, but for opposite reasons**

| | var(F) | var(M) | cov | var(Δ) | var(F) share | corr(F,M) |
|---|---|---|---|---|---|---|
| SPD (n=80) | 0.235 | 0.236 | **+0.222** | **0.028** | 49.9% | **+0.94** |
| ACM (n=115) | 0.335 | 0.332 | **−0.201** | **1.068** | 50.3% | **−0.60** |

Both clear the 15% threshold, but the threshold is not the informative number.
The SPD wedge has a variance of 0.028 because the two series are 94% correlated —
the market's longer-run dot tracks the SEP's. The ACM wedge has a variance 38×
larger, and it has it because market *pricing* moves **against** the SEP.
That negative correlation is the whole source of identifying variation and is
itself worth a paragraph.

### Check 3 — R² on each side alone — SPD **PASS**, ACM **BORDERLINE**

| | Δ ~ r\*<sub>Fed</sub> | Δ ~ r\*<sub>Mkt</sub> |
|---|---|---|
| SPD | 0.029 | 0.032 |
| ACM | **0.802** | **0.800** |

The ACM numbers are not the degenerate case this check was written to catch
(var(F) ≈ 0). They are the mirror image: because F and M are negatively
correlated, *either one alone* explains 80% of Δ. The wedge is close to a linear
function of either side. Not fatal, but it means the horse race in §3 is
mandatory rather than optional.

### Check 4 — effective sample size — **BINDING, as predicted**

- 57 SEP meetings
- **12 distinct values** of the SEP longer-run r\*: 0.375, 0.5, 0.5625, 0.75, 0.875, 1.0, 1.125, 1.25, 1.5, 1.75, 2.0, 2.2
- **19 meetings at which the median changed**
- longest run without a change: **10 meetings**
- distinct wedge values: 16 (SPD), 115 (ACM — all the variation is market-side)

Effective N for anything driven by the Fed-side level is **19**, not 116. Standard
errors below use HAC and a moving-block bootstrap; neither fully repairs this.

### Check 5 — first differences — **PASS both**

corr(Δr\*<sub>Fed</sub>, Δr\*<sub>Mkt</sub>) at SEP meetings: **+0.600** (SPD, n=41),
**−0.136** (ACM, n=55). The SPD figure is high enough to say the two sides are
partly tracking a common signal; the ACM figure says they are not.

### Check 6 — persistence — SPD **PASS**, ACM **FAIL**

| | AR(1) ρ | se | half-life | mean | sd |
|---|---|---|---|---|---|
| SPD | +0.849 | 0.053 | 4.2 meetings | +0.080 | 0.169 |
| ACM | **+0.979** | 0.011 | **31.9 meetings** | −0.148 | 1.033 |

The ACM wedge is near a unit root over the sample. It is not a definitional level
gap — it changes sign and swings ±1.7pp (Figure 1) — but it is persistent enough
that a level-on-change regression is inference on very few independent
observations. This is the flag that comes back to bite in §3D.

### Check 7 — Mercatus replication — **replicated; the SEP-vs-SPD wedge is dead**

42 SEP meetings with a same-month SPD survey, 2013-03 → 2026-03:

- mean |gap| **13.1 bp**
- median |gap| **13.0 bp**
- max |gap| **25.0 bp** (2014-09-17)
- share ≤ 42 bp: **100%**

The Mercatus finding holds on this panel and is if anything stronger — the maximum
observed gap is 25bp, not 42. The SEP-vs-SPD wedge cannot carry the paper. Recorded
as killed in §3 of the handoff, and now killed on our own data.

### Fallback — cross-sectional dispersion of the SEP panel

Mean SD 0.304, range [0.217, 0.461], **49 distinct values over 57 meetings**,
AR(1) ρ = 0.803. Roughly 2.5× the identifying variation of the median (49 vs 19
effective moves), and not near-unit-root. If the median route stalls, this is the
better-powered object.

### Gate verdict

- The **SPD route is dead** (checks 2 and 7).
- The **ACM route survives**, carrying two flags: check 3 borderline, check 6 failed.
- **Check 1 fails on both routes** and is a framing problem, not a design problem.

---

## 2. Post-gate: the component decomposition (check 8)

2-day announcement window [t−1, t+1], 116 meetings, ACM wedge, HAC(4) standard
errors. Coefficients in **bp per pp of pre-meeting wedge**.

| Maturity | Total yield | Risk-neutral | Term premium |
|---|---|---|---|
| 2y | +2.25 (t 2.57) | +1.46 (t 2.53) | +0.79 (t 1.25) |
| 5y | **+3.34 (t 4.06)** | **+1.72 (t 2.71)** | **+1.62 (t 3.21)** |
| 10y | **+3.14 (t 4.18)** | **+1.49 (t 2.84)** | **+1.65 (t 2.52)** |

Additive identity holds to 1.4 × 10⁻¹⁴ bp.

Sign: when the Fed's longer-run rate sits **above** what the market is pricing,
yields **rise** into the announcement window. The market moves toward the Fed.
That is Hillenbrand's information channel, and the risk-neutral coefficient is
its predicted signature — confirmed.

**The new number is the term premium.** At 10y it is +1.65 bp/pp, slightly larger
than the risk-neutral component and statistically distinguishable from zero on
HAC standard errors. Nobody had a prediction for it. The SPD wedge gives nothing
anywhere (all |t| < 1.3).

Low-revision SEP meetings (38 where the SEP median did not move): risk-neutral
+2.35 (t 2.66), term premium +0.84 (t 1.25). The core identification survives for
the expectations component; the premium component does not.

---

## 3. Verification — is any of this a construction artefact?

The wedge is built from the ACM risk-neutral curve at t−1 and the regressand is
the change in the ACM curve from t−1 to t+1. ACM fits a **stationary** VAR to
yield principal components, which mechanically generates a negative
level-on-change relationship. Applying the handoff's own transferable heuristic:
before believing the result, check whether it is a free parameter of the
construction.

### A. Placebo — the same regression on every non-FOMC trading day

| | FOMC days (n=114) | non-FOMC days (n=3,513) |
|---|---|---|
| 10y total | **+3.20** (t 4.32) | −0.18 (t −1.02) |
| 10y risk-neutral | **+1.47** (t 2.75) | −0.01 (t −0.08) |
| 10y term premium | **+1.73** (t 2.63) | −0.17 (t −1.04) |

The wedge does **nothing** on days without an announcement. Not mean reversion.

### B. Randomisation — 5,000 draws of 114 random non-FOMC days

| | observed | null mean | null sd | percentile | two-sided p |
|---|---|---|---|---|---|
| 10y total | +3.20 | −0.19 | 0.76 | 100.0% | 0.000 |
| 10y risk-neutral | +1.47 | +0.00 | 0.43 | 99.9% | **0.002** |
| 10y term premium | +1.73 | −0.18 | 0.74 | 99.4% | **0.012** |

### C. Horse race — is it the wedge, or just the ACM level?

Entering the two sides separately instead of imposing the −1 coefficient:

| 10y | wedge | Mkt alone | Fed alone | both (Fed / Mkt) | wedge restriction |
|---|---|---|---|---|---|
| total | +3.14 (4.18) | −4.59 (−2.92) | +5.07 (3.65) | +3.27 / −3.00 | F=0.01, **p=0.935** |
| risk-neutral | +1.49 (2.84) | −2.59 (−2.55) | +2.07 (2.40) | +0.71 / −2.28 | F=0.83, **p=0.363** |
| term premium | +1.65 (2.52) | −2.00 (−1.69) | +3.00 (2.56) | +2.57 / −0.72 | F=0.50, **p=0.483** |

The wedge restriction (b<sub>F</sub> = −b<sub>M</sub>) is **not rejected** for any
component — the data are content to be described by a single signed wedge.
But the unrestricted coefficients say something the wedge hides: the **risk-neutral
response is driven by the market side** (Mkt t −1.94, Fed t +0.89) while the
**term-premium response is driven by the Fed side** (Fed t +1.77, Mkt t −0.49).
The two components are responding to different halves of the wedge.

### D. Inference — where it breaks

| 10y | coefficient | block bootstrap 95% CI (L=8) | differenced wedge |
|---|---|---|---|
| risk-neutral | +1.49 | **[+0.34, +3.01]** excludes zero | −3.35 (t −0.92) |
| term premium | +1.65 | **[−0.11, +2.57] INCLUDES zero** | −5.81 (t −1.02) |

**The term-premium result does not survive block-bootstrap inference.** The
risk-neutral result does. And the effect is entirely a *level* effect: the change
in the wedge since the previous meeting predicts nothing. That is check 6 biting —
the identifying variation lives in a near-unit-root level.

---

## 4. Robustness

### Comparable units — is the SPD null just low power?

sd(Δ) is 1.033 for ACM and 0.169 for SPD, so raw coefficients are not comparable.
Per standard deviation of the wedge, at 10y:

| | total | risk-neutral | term premium |
|---|---|---|---|
| ACM | +3.24 | +1.54 | **+1.70** |
| SPD | +0.70 | +0.68 | **+0.01** |

Standardised, the SPD term-premium effect is **0.01 bp per sd**. This is not low
power; it is a zero. The result exists only with the pricing-based measure.

### Beyond the expectations channel

Conditioning on the announcement's own 1y and 2y risk-neutral move — the cleanest
available proxy for the near-term policy surprise — the 10y term-premium
coefficient **rises**:

| specification | b | t | R² |
|---|---|---|---|
| TP ~ wedge | +1.65 | 2.52 | 0.039 |
| TP ~ wedge + Δrn(1y) | **+2.23** | **3.48** | 0.175 |
| TP ~ wedge + Δrn(1y) + Δrn(2y) | +2.17 | 3.55 | 0.177 |

The premium response is not a by-product of the expectations move.

### Subsamples — the biggest problem

| | 10y total | 10y risk-neutral | 10y term premium | n |
|---|---|---|---|---|
| 2012–2015 (ZLB) | +5.44 (2.01) | −0.48 (−0.24) | **+5.92 (2.08)** | 31 |
| 2016–2019 (normalisation) | +0.22 (0.09) | −0.80 (−0.44) | +1.02 (0.76) | 32 |
| 2020–2026 (pandemic on) | +6.71 (2.94) | **+5.07 (4.00)** | +1.64 (0.86) | 52 |

The pooled headline is **two different regimes averaged together**. The
term-premium effect is a 2012–2015 ZLB phenomenon. The risk-neutral effect is a
2020–2026 phenomenon. The middle four years are null on everything. Whatever the
mechanism is, it is not stable across the sample, and a paper that reports only
the pooled coefficient would be reporting an average of two non-overlapping
episodes.

SEP versus non-SEP meetings show no meaningful difference (total +2.73 vs +3.56).

---

## 5. Check 9 — maturity signature

Coefficient on the ACM wedge by maturity, 2-day window (`fig2_maturity.png`,
`maturity_signature.csv`):

| n | total | risk-neutral | term premium |
|---|---|---|---|
| 1 | 1.41 | 0.96 | 0.45 |
| 3 | 2.84 | 1.65 | 1.19 |
| 5 | 3.34 | **1.72** | 1.62 |
| 7 | 3.35 | 1.65 | **1.71** |
| 10 | 3.14 | 1.49 | 1.65 |

Under the κ<sub>n</sub> algebra in §4 of the handoff, a pure endpoint shock loads
**flat at 1** for every maturity and a cyclical shock decays at **1/n**. Neither
profile appears. Both components trace a **hump**, rising to a peak at 5y
(risk-neutral) and 7y (term premium) and then flattening or easing.

Caveat: the wedge is built from `ACMRNY09`/`ACMRNY10`, so the 9–10y risk-neutral
cells share construction with the regressand. The informative cells are 1–5y, and
those are precisely the ones that rise. The hump is not an artefact of the
overlap — the overlap would push the long end up, and the long end is where the
profile turns down.

---

## 6. Check 10 — signed versus absolute

At 10y, ACM wedge:

| | signed | \|wedge\| | positive side | negative side |
|---|---|---|---|---|
| total | +3.14 (4.18) | −0.45 (−0.21) | +2.18 (1.72) | −4.20 (−2.18) |
| risk-neutral | +1.49 (2.84) | −2.14 (−1.96) | −0.81 (−1.22) | **−4.04 (−3.96)** |
| term premium | +1.65 (2.52) | +1.69 (1.15) | **+2.99 (2.50)** | −0.16 (−0.10) |

The **signed** wedge is what prices; the absolute wedge gives nothing. And the
asymmetry is sharp and consistent with §3C: the **term premium responds only when
the Fed sits above the market** (b +2.99, t 2.50; the other side is a clean zero),
while the **risk-neutral component responds only when the Fed sits below the
market**. Disagreement in the two directions is priced through two different
components. That is a genuinely odd result and either the most interesting thing
here or a sample-split artefact of §4's regime instability — 2012–2015 is a
Fed-above-market period and 2020–2026 is a Fed-below-market period (Figure 1,
lower panel), which is very likely the same fact seen twice.

---

## 7. Where this leaves the project

**What is established.** The pre-meeting wedge predicts announcement-window yield
changes, the relationship is absent on non-announcement days (p = 0.002 for the
risk-neutral component in a randomisation test against 3,513 placebo days), and
the risk-neutral coefficient survives block-bootstrap inference. Hillenbrand's
prediction holds on our construction.

**What is not established.** The term-premium coefficient — the actual research
question — is positive and HAC-significant but its block-bootstrap CI includes
zero, it is entirely a 2012–2015 phenomenon, and it exists only with the
ACM-based wedge. It is suggestive. It is not a result.

**What is dead.** The SPD/SEP wedge (check 7, replicating Mercatus on our own
panel). The claim to be measuring *real*-rate disagreement (check 1: π\*
dispersion is identically zero on both sides, at every meeting, without exception).

**What I would do next, in order.**

1. **Confront §4's subsample instability before anything else.** A term-premium
   effect that lives only at the ZLB and a risk-neutral effect that lives only
   post-2020 is either two mechanisms or one badly-specified one. This is the
   binding question, and no amount of extra robustness on the pooled sample
   addresses it.
2. **Get Kim–Wright and re-run §2.** The entire term-premium result is one model's
   term premium. §4 of the handoff already establishes that ACM assumes a constant
   endpoint; the wedge is a statement about the endpoint. A TP measure whose
   endpoint is survey-based is the natural adversarial test, and the FEDS Note
   already tells us where the two differ and why.
3. **Switch the Fed side to the dispersion fallback** (49 distinct values, ρ = 0.80)
   rather than the median (19 changes, ρ ≈ 1). Check 4 is binding and the
   fallback is better-powered on both counts.
4. **Rewrite the framing as longer-run nominal disagreement.** Check 1 makes the
   real-rate language indefensible, and it is better to concede it than to have a
   referee find it.

---

## Files

```
results/
  event_panel.csv          116 FOMC meetings x wedge, components, window changes
  fed_rstar.csv            57 SEP meetings
  spd_rstar.csv            92 SPD/SMP surveys
  acm_derived.csv          daily 9y1y risk-neutral forward and term premium
  mercatus_replication.csv 42 matched SEP-SPD meeting pairs
  maturity_signature.csv   coefficient by maturity and component
  results.json             checks 1-10
  verification.json        placebo, randomisation, horse race, bootstrap
  robustness.json          standardised, conditional, subsample
  checks_log.txt           full console output
  fig1_wedges.png  fig2_maturity.png  fig3_placebo.png
```
