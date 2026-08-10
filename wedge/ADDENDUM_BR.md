# Addendum — Bauer–Rudebusch diagnostic and the identification problem

**Run:** 10 August 2026. Follows `RESULTS.md`.
**New data:** `falling-stars-fig4.csv` (Bauer–Rudebusch, AER 2020), quarterly
1971Q4–**2018Q1**, carrying `istar.rt` (real-time), `istar.ese` (model
estimate) and `istar.lb`/`istar.ub` (bands).
**Code:** `br_diagnostic.py` → `br_stress.py` → `identification.py`.
**Numbers:** `br_diagnostic.json`, `br_stress.json`, `identification.json`,
`flat_fed_fe.json`.

Both BR series and the SEP longer-run median are **nominal** equilibrium
short rates, so the wedge is defined on nominal endpoints and the long-run
inflation constant cancels exactly:
Δ = (i\*<sub>Fed</sub> − π\*) − (i\*<sub>Mkt</sub> − π\*) = i\*<sub>Fed</sub> − i\*<sub>Mkt</sub>.

---

## 1. The good news: the result is not ACM-specific

Matched window, 51 FOMC meetings, 2012-03 → 2018-06. 10y, two-day window,
bp per pp.

| Market-side endpoint | Total | Risk-neutral | Term premium |
|---|---|---|---|
| ACM 9y1y (fixed endpoint) | +3.52 (3.87) | +0.12 (0.24) | **+3.40 (3.93)** |
| BR real-time | +5.39 (2.53) | −0.40 (−0.35) | **+5.79 (3.09)** |
| BR model estimate | +4.64 (3.39) | −0.30 (−0.48) | **+4.94 (3.86)** |

Per standard deviation of the wedge: **+2.71, +2.08, +2.63** bp. Three
different endpoint constructions — one with a fixed endpoint, one real-time,
one a model-estimated shifting endpoint — give the same answer within noise.
The placebo is clean for BR too (non-FOMC days: −0.45 and −0.00 against
+4.44 and +3.75 on announcement days).

**A correction to an earlier claim.** I said the effect required *priced*
disagreement rather than *stated* disagreement, because SPD gave nothing.
That is wrong. BR's real-time measure is survey-based and it works. The
distinguishing feature is not survey-versus-pricing but **how much variation
the measure has that is independent of the Fed's own number**: SPD has
sd 0.169 and corr 0.94 with the Fed side; BR real-time has sd 0.360 and
corr 0.856.

---

## 2. The bad news, and it is worse than the good news is good

On the 2012–2018 window the wedge is **nearly collinear with the Fed's own
longer-run level**. R²(wedge on Fed side) = 0.963. The SEP longer-run median
falls from 4.20 to 2.75 across this window while the market side moves far
less (sd 0.497 versus 0.323).

Control for the Fed level and the term-premium result disappears:

| 2012–2018, 10y term premium | b | t |
|---|---|---|
| wedge alone | +3.40 | **3.93** |
| wedge + Fed level | +3.55 | **0.82** |
| Fed level alone | +5.34 | **3.79** |
| Market level alone | −6.83 | **−3.59** |

Every one of these is the same variable wearing a different hat. You cannot
tell "the market prices the Fed–market gap" from "the market responds to the
SEP longer-run level" on this window, because on this window they are the
same number. This is check 3 — flagged as borderline in the gate — biting
exactly where it was predicted to.

It is also narrow. Dropping the three largest term-premium days cuts the
coefficients ~40%. Restricting to **2014 onward kills all three**
(t = 1.01, 1.22, 1.40). The effect is 2012–2013.

---

## 3. Where the wedge *is* identified

| Era | sd(Fed) | sd(Mkt) | corr | R²(wedge\|Fed) | R²(wedge\|Mkt) | n |
|---|---|---|---|---|---|---|
| 2012–2018 | 0.497 | 0.323 | −0.880 | **0.963** | 0.912 | 51 |
| 2019–2026 | 0.226 | 0.554 | +0.297 | **0.013** | 0.836 | 60 |
| full 2012–2026 | 0.579 | 0.576 | −0.602 | 0.802 | 0.800 | 115 |

**2019–2026 is the identified window.** The SEP longer-run median sits at
0.50 for ten consecutive SEPs while the market endpoint swings more than a
percentage point, so the wedge is almost pure market-side variation.

And in that window:

| 2019–2026 | wedge alone | wedge + Fed level |
|---|---|---|
| 10y risk-neutral | +4.84 (**4.06**) | +4.49 (**4.01**) |
| 10y term premium | +1.50 (0.79) | +1.32 (0.69) |

The **risk-neutral** result is identified and survives the control. The
**term-premium** result is absent there.

On the full sample the same control kills the term premium (t 2.52 → 0.49)
and weakens the risk-neutral component to marginal (t 2.84 → 1.94).

---

## 4. The cleanest specification, and what it costs

Seven stretches where the SEP longer-run median is literally unchanged
across three or more consecutive SEPs (73 meetings). With **stretch fixed
effects**, the Fed side is absorbed and 100% of the remaining wedge
variation is market-side.

| | b | se | t | block-bootstrap 95% CI |
|---|---|---|---|---|
| 10y total | +4.41 | 6.61 | 0.67 | — |
| 10y risk-neutral | +0.09 | 3.70 | 0.02 | [−17.95, +6.21] |
| 10y term premium | +4.32 | 5.10 | 0.85 | [−12.25, +12.02] |

Nothing is significant, and the standard errors are roughly nine times the
pooled ones. **This does not refute anything — it shows the cleanest
identification has no power in this sample.** It also pools eras with
opposite patterns, which is part of why it is so noisy.

---

## 5. Where this leaves the project

The BR check did its job, and the answer is not the one I expected.

**The term-premium result — the actual contribution — is in serious
trouble.** It is not model-specific, which was the worry the BR check was
built to test, and it passes that test cleanly. But it exists only in the
window where the wedge is not separately identified from the Fed's own
longer-run level, and it vanishes the moment that level is controlled for.
"Not model-specific" and "not identified" are different problems, and it has
the second one.

**The risk-neutral result is the solid one.** It lives in the identified
window, survives the Fed-level control, the placebo, the randomisation test
and the block bootstrap. But it is Hillenbrand's own prediction —
confirmation, not contribution.

So, stated plainly: **the finding that is novel is not identified, and the
finding that is identified is not novel.**

### Three ways forward, in order of cost

1. **Reframe around what is actually identified in 2012–2018.** The Fed-level
   regression is a real result in its own right: during the ZLB the SEP
   longer-run median moved the 10y **term premium** (+5.34, t 3.79) and did
   **not** move the risk-neutral component (−0.11, t −0.14). That is a clean,
   odd, reportable fact, and it is adjacent to Hillenbrand's data with a
   different component. Cheapest path to something defensible.
2. **Get power in the identified window.** 2019–2026 is where the wedge is
   clean and where a term-premium effect would count. It is currently
   t = 0.79. The obvious upgrade is the **U.S. Monetary Policy Event-Study
   Database** (Bauer, Acosta, Ajello, Loria, Miranda-Agrippino; FRBSF,
   updated after each FOMC meeting) — high-frequency intraday windows and a
   proper policy surprise, instead of two-day ACM changes and a Δrn(1y) proxy.
3. **A–R remains the right model** for the reasons in the previous note, but
   it is no longer the binding constraint. Identification is. A better
   market-side measure does not help if the Fed side is not moving
   independently of it.

### What did not work as a test

The BR uncertainty band is too close to constant to be informative:
2012+ mean 4.334, sd 0.491, coefficient of variation 0.113. Scaling the wedge
by it is a rescaling, not a test. The A–R subjective bands would be a real
test; these are not.

---

## Files added

```
results/
  br_diagnostic.json     matched-window comparison of the three endpoints
  br_stress.json         confound, influence, placebo, band-width checks
  identification.json    era-by-era identification and Fed-level controls
  flat_fed_fe.json       flat-SEP stretches with stretch fixed effects
  br_matched_panel.csv   51-meeting matched panel
  code/br_diagnostic.py  code/br_stress.py  code/identification.py
```
