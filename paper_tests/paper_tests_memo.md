# Data tests of the §4 predictions — Reaction_Function_Update_Final

**Run:** 11 August 2026.
**Data:** `clean_reactionFunction/` as archived (SEP dots, SPD/SMP surveys, ACM daily curve, GSW nominal curve `feds200628`). Nothing retyped; all numbers from `results_tests.json`.
**Code:** `run_tests.py` → `run_tests2.py` → `run_tests3.py`.

## 0. Setup and conventions

Following the paper's Fact 2 (and `belieffig.py`): Fed side = SEP longer-run funds-rate **mean of dots** at meeting *t*; market side = SPD/SMP longer-run median from the latest survey fielded before *t* (asof-backward, 120-day tolerance). δ = market − Fed (eq. 7). Matched SEP meetings: **48**, 2013-03 → 2026-03; revision sample with price windows n = 46–47.

Replication check of Fact 2 on this build: gap sd **0.105**, range **−0.30 to +0.11** in δ (i.e. −0.11 to +0.30 as Fed−dealers), dealers-on-Fed **β = 0.82 (t 6.86)**, Fed-on-dealers **β = 0.31 (t 3.91)** — the paper's numbers exactly, so the matching convention is the paper's.

Revision variables: dM = dealer revision between consecutive matched meetings (fielded before the window opens), dF = mean-dot revision released **at** the announcement, Δδ = dM − dF. sd(Δδ) = **0.117 pp**. Windows: ACM 2-day [t−1, t+1] (1-day robustness); GSW instantaneous forwards computed the same way.

---

## 1. The power calculation the paper requires before Prediction 2 — **run; the test is underpowered for the ratio, adequately powered for detection**

With sd(Δδ) = 0.117, n = 47, and 2-day 5y5y-forward window noise of σ ≈ 11.1 bp (observed, nominal GSW):

| leg | assumed σ | se(b) | MDE (80% power) |
|---|---|---|---|
| nominal 5y5y fwd | 11.1 bp | 13.9 | **39 bp/pp** |
| real leg (σ = 0.8× nominal) | 8.9 bp | 11.1 | 31 bp/pp |
| breakeven leg (σ = 0.5× nominal) | 5.6 bp | 6.9 | 19 bp/pp |

Model-implied effects (Λ from §4.5, split 1:2 real:BEI at φπ = 1.5): α = 0 gives real ≈ 4, BEI ≈ 7 bp/pp — **undetectable**. α = 0.25 gives real ≈ 26, BEI ≈ 51 — BEI detectable (simulated power 0.99), real marginal (0.27). Simulated power for the **ratio** b_real/b_BEI (5,000 draws): the median se of the ratio is **1.35** at small effects and only reaches 0.15 when the real leg is 40 bp/pp. To separate φπ = 1.5 (ratio 0.5) from φπ = 2 (ratio 1.0) needs se(ratio) ≲ 0.25, which requires effects an order of magnitude above the α = 0 prediction.

**Verdict:** the composition-restriction test is feasible as a *detection* test for the BEI leg under moderate-to-large α, but **the ratio (the identification of perceived φπ) is out of reach at current variance** — consistent with the paper's caution, now quantified. The TIPS regression itself still needs `feds200805.csv` (this sandbox cannot reach federalreserve.gov; drop the file in the repo root and it can be run on the same panel).

---

## 2. Maturity profile (Prediction 4) — **the window prices the dot surprise; the endpoint loading is a hump at 2–5y, not flat at one**

Restricted regression (window changes on Δδ, HAC(4), bp per pp) — ACM expectations component: −11.7 (t −2.4) at 1y, deepening to **−26.0 (t −3.8) at 4–5y**, easing to −22.2 (t −3.8) at 10y. Signs: a rise in δ (Fed below market) sees yields **fall** in the window — the market converges to the Fed's published endpoint, the paper's eq. (13) anchor and Hillenbrand's channel, now visible in the *survey-based* measure (the earlier SPD-median wedge gave nothing; the mean-of-dots revision is what has power — 47 moves vs 19).

Unrestricted split, drn(n) ~ dM + dF:

| n | b_dM (dealer rev) | b_dF (dot rev) | sum | p(b_dM = −b_dF) |
|---|---|---|---|---|
| 2 | −21.3 (t −3.5) | +22.0 (t +2.2) | +0.7 (se 9.5) | 0.94 |
| 5 | −26.0 (t −3.6) | +25.8 (t +2.7) | −0.2 (se 10.0) | 0.99 |
| 10 | −22.2 (t −3.6) | +23.0 (t +2.9) | +0.9 (se 8.3) | 0.92 |

The two coefficients are equal and opposite at every maturity: **the window prices dF − dM, the unanticipated part of the dot**, with dealers' own pre-meeting revision serving as the market's forecast of it. This is a clean, new fact for §3.

In raw GSW forwards the dot-revision loading b_dF(n) is **+47 at 1y, peaking at +74 at 4–5y, falling to +49 at 10y** (all t > 2.3). Prediction 4 says a revision to the published endpoint loads **flat at one**. The level is rejected: at the 10y forward the loading is 0.49 (se 0.21), **t = −2.5 against one**. The shape contrasts individually are not significant (b_dF(4y)−b_dF(1y): t +1.6; 10y−4y: t −1.3) — the hump is suggestive, the sub-unit level is not. Roughly half of a dot revision is priced as far-forward news; the model's full pass-through overstates it by 2×.

## 3. The amplification term Λ(n)·δ — **in-window, exactly zero; α capped**

If any part of the market-belief term were priced *at the announcement*, the sum b_dM + b_dF would pick it up. It is **0.9 bp/pp at 10y (se 8.3; block-bootstrap 95% CI [−14.9, +17.8])** and similarly zero at every maturity. Against the model columns (100·Λ): α = 0 predicts +47 at 2y and +11 at 10y — **rejected at 2y (t −4.8) and 5y (t −2.2)**, not at 10y. Identification caveat, stated plainly: if dealers' revision is already in prices before t−1 (it should be — the survey closes ~2 weeks earlier), the window sum is uninformative about Λ and only says the window prices the *surprise*. The direct test is then intermeeting pricing of dM:

| n | intermeeting b_dM | se | 95% admissible α |
|---|---|---|---|
| 2 | +47.2 | 66.1 | [0.00, 0.97] |
| 5 | +28.4 | 65.7 | [0.00, 0.60] |
| 10 | +20.6 | 53.3 | **[0.00, 0.43]** |

Point estimates are positive and ordered like a small-α model, but the noise is honest: **α is bounded above at ~0.43 (10y, 95%)** and nothing more. Combined statement for the paper: *the steady-state multiplier (α = 1: loading 2.7 at 10y) is rejected everywhere; α ≳ 0.5 is rejected at 5–10y; the data cannot distinguish α = 0 from α ≈ 0.4.* The §4.4 magnitude claim should be presented as an upper bound that the data already discipline, which is what §4.8 half-anticipates.

## 4. Sign symmetry (Prediction 3) — **supported where the model makes it, one flag in the premium**

Levels (δ split at zero, 10y, 2-day window): p(symmetric) = 0.98 (total), 0.79 (risk-neutral), 0.87 (term premium) — **no asymmetry, as the model's linearity requires**, and in contrast to the ACM-wedge asymmetry found earlier (which the gate results already suspected was a regime artefact). One flag: in *revisions*, the 10y term-premium response is asymmetric (extra slope for Δδ > 0: −65.3, t −2.1, p = 0.035) — worth watching, n is small and it is the only rejection among ten tests.

## 5. Dispersion and the premium (Prediction 6, proxy) — **nothing, on this proxy**

Using the dealer longer-run IQR (91 surveys, mean 0.45, AR(1) 0.58) as a stand-in for σ_δ: ACM term-premium loadings are flat zeros in levels (|t| < 0.9 at every maturity) and negative-insignificant in changes. No rise with maturity, no decay — no signal. Caveat: this is forecaster dispersion about i*, not Fed-vs-market δ-uncertainty; the prediction is strictly about the latter. A proper test needs an instrument for σ²_δ; the survey IQR is not it.

---

## What this changes in the draft

1. **Fact 2 gains a third panel**: the announcement window prices dF − dM — the dot surprise measured against the dealers' own prior revision — at ~0.25 loading in ACM-expectations space and ~0.5–0.75 in raw 2–5y forwards. Equal-and-opposite coefficients, p = 0.92–0.99.
2. **Prediction 4 is half-rejected**: far-forward pass-through of a dot revision is ~0.5, not 1, and looks hump-shaped rather than flat (shape not significant, level significantly below one at 10y).
3. **The §4.4–4.5 α discussion can now cite numbers**: α ≤ 0.43 (10y, 95%) from intermeeting pricing; in-window pricing of the belief term is dead-zero (CI ±17 bp/pp around 0).
4. **Prediction 3's linearity survives** its first survey-based test.
5. **Prediction 2 has its mandated power calculation**: detection possible for the BEI leg at α ≳ 0.25; the φπ-identifying ratio is unreachable at sd(Δδ) = 0.117 — the paper's "one equation in two unknowns" is also, in practice, one equation in too little variance.

## Files

```
paper_tests/
  paper_tests_memo.md       this memo
  results_tests.json        all estimates
  rev_panel.csv             48-meeting matched panel with windows
  fig_tests.png             three-panel summary
  run_tests.py  run_tests2.py  run_tests3.py  build_delta.py
```
