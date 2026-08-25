# r\*, Term Structure, and the FOMC — Reading Map

**Compiled:** 10 August 2026
**Scope:** Everything covered in this conversation. Reference document, not a research proposal.

**Confidence marking:** ✔ = read in full or verified from primary text this session. ○ = from search snippets or abstracts. △ = from memory, unverified. Treat ○ and △ as needing confirmation before citation.

---

## 1. The puzzle

Long-term Treasury yields fell roughly 7pp since 1989. The standard explanations — demographics, slowing productivity growth, safe-asset demand, inequality — are slow-moving and continuous, so they should show up on all trading days. Instead, essentially the entire *permanent* decline is concentrated in a three-day window around FOMC meetings, and movements outside that window mean-revert to zero.

This is doubly backwards. Monetary policy is supposed to move the *cyclical* component (which should wash out of a 30-year cumulative sum), and the secular forces are supposed to move the *trend* (which should accumulate gradually).

Within the window, the decline is roughly split between day −1 and day 0, with day +1 contributing little and not trending. The day-0 portion is a minute-level jump at the 14:00 announcement; the day −1 portion is a gradual drift with no identifiable public information event.

---

## 2. The central paper

**✔ Hillenbrand, "The Fed and the Secular Decline in Interest Rates," *Review of Financial Studies* 38(4), April 2025, 981–1013.** Editor's Choice; WFA Brattle PhD Award.

A three-day window around FOMC meetings captures the entire cumulative decline in the 10-year yield since 1989 and traces its low-frequency path; non-window changes are transitory. Yields fall when the Fed cuts the short rate *and* when it lowers its longer-run fed funds projection (the dot plot). Reading: the market has been learning about the secular decline from the Fed, possibly because FOMC meetings coordinate attention. Considers and downweights alternatives — risk premia in the Cieslak–Pang sense (unlikely to explain the *majority*), the Nakamura–Steinsson information effect (near-term news shouldn't move long-run expectations), and extrapolation.

Figure 7 gives the daily and intraday decomposition of the window. Data sources include the GSW off-the-run curve, Bloomberg on-the-run, and intraday GovPX.

---

## 3. What actually moves r\*

- **△ Euler-equation baseline.** r\* = ρ + σg. Trend growth is the theoretical anchor; HLW operationalize it as r\* = c·g_t + z_t with c ≈ 1/EIS.
- **△ Hamilton, Harris, Hatzius & West (2016), *IMF Economic Review*.** The empirical growth–r\* link is far weaker than theory implies; enormous estimation uncertainty. Also compute SEP-implied r\* from the longer-run dots.
- **△ Gagnon, Johannsen & López-Salido.** Demographics alone account for ~1.25pp of the US decline. Slow, predictable, exogenous.
- **△ Del Negro, Giannone, Giannoni & Tambalotti (2017), BPEA.** The decline is concentrated in the *convenience yield* on safe liquid assets, not the return on capital. Implication: r\* measured off Treasuries ≠ marginal product of capital.
- **△ Mian, Straub & Sufi.** Rising top-income shares raise aggregate saving and depress r\*; "indebted demand" makes the decline self-reinforcing.
- **△ Fiscal channel.** Debt supply pushes r\* up; leading candidate for the post-2021 rise.
- **○ Reis, "The Four R-Stars" (2025).** Definitional discipline — much apparent disagreement is people measuring different objects.

**Note:** none of these mechanisms predicted the 2021–2025 increase.

---

## 4. Estimating r\*, and the random-walk assumption

- **△ Laubach–Williams (2003); Holston–Laubach–Williams (2017, JIE).** Semi-structural state-space model. g and z are driftless random walks, so r\* is I(1) by construction. Signal-to-noise ratios are *not* freely estimated — MLE piles up at zero (Stock–Watson 1998), so λ_g and λ_z come from a median-unbiased first stage. The smoothness is imposed.
- **○ Buncic, Riksbank WP 397.** The Stage 2 model is misspecified, so the MUE procedure cannot recover the intended ratio and spuriously amplifies λ_z; a simulation with true λ_z = 0 still produces large estimates. Corrected, λ_z is small and insignificant — which would gut the post-1980 downward trend, since that trend is driven by z_t.
- **○ Rogoff, Rossi & Schmelzing (AER 2024; NBER WP 33079).** Seven centuries of real rates: trend stationary around a persistent downward trend. Unit root rejected on 1803–1990 but not on random 45-year windows — postwar non-rejection reflects sample length, not the DGP. Half-lives roughly 1–10 years.
- **○ Morley, Tran & Wong (JBES 2024).** Diagnostic: a true random-walk trend has serially *uncorrelated* first differences. Their own VECM trend fails; the Laubach–Williams filtered estimates pass.
- **○ Kiley (2020, IJCB).** The smoothness of r\* is not well identified in semi-structural models.
- **△ Perron (1989).** The underlying identification problem: a stationary process with breaks and a unit root are not distinguishable in short samples.

**Bottom line:** the random walk is a prior, not a finding. It has a strong economic implication — E_t[r\*_{t+h}] = r\*_t for all h, i.e. zero expected mean reversion — that nobody would defend if stated directly.

---

## 5. One-sided vs. two-sided, and the SEP/HLW level wedge

- **One-sided (filtered):** r\*_{t|t}, data through t only. Real-time.
- **Two-sided (smoothed):** r\*_{t|T}, full sample. More precise, less volatile, but unavailable at the date it describes and rewritten with every new observation. **△ Orphanides–van Norden** on why this matters for evaluating policy.

**The level wedge is not measurement error.** The SEP longer-run dot measures lim_{h→∞} r\*_{t+h}; HLW measures r\*_t. They coincide only under a random walk. The gap is *expected mean reversion*, which is identically zero under HLW's specification.

Empirically the gap **changes sign**: SEP sits ~140bp above alternative estimates in 2012–2015, converges 2016–2019, then sits ~90bp below from 2022. A sign flip is what makes it a disagreement that opens and closes rather than a definitional offset.

---

## 6. Term structure machinery

**The setup.** Small state vector X_t; short rate r_t = δ_0 + δ_1′X_t; VAR(1) dynamics; exponentially affine SDF with prices of risk λ_t = λ_0 + λ_1X_t. Risk-neutral dynamics Φ^Q = Φ − Σλ_1. Yields affine: y_t^(n) = a_n + b_n′X_t via Riccati recursions.

**The decomposition.** y_t^(n) = (1/n)Σ_h E_t[r_{t+h}] + TP_t^(n). Term premium is *not* a fitting residual — the model matches observed yields closely. It is the observed yield minus the *risk-neutral* yield, computed by re-running the fitted model with λ set to zero.

**Where the fragility lives.** Since the model matches y, all TP uncertainty comes from the expectations component, which comes from Φ. Φ is a near-unit-root object estimated on ~60 years of data, and is the worst-identified piece of the system. Persistent Φ → small stable TP; mean-reverting Φ → large volatile TP. The term premium is essentially a function of one persistence parameter, not of the risk specification.

**Foundations**
- **△ Duffie–Kan (1996)** — the affine class.
- **△ Dai–Singleton (2000)** — canonical classification and admissibility.
- **△ Duffee (2002)** — essentially affine risk prices. Before this, λ was proportional to volatility and nearly constant in Gaussian models; this is what made time-varying term premia possible.
- **△ Joslin–Singleton–Zhu (2011)** — normalization separating Q-parameters (from the cross-section) from P-parameters (from the time series); made MLE reliably estimable.

**Production series**
- **△ Adrian, Crump & Moench (2013, JFE) — ACM.** Five yield PCs, three-step regression estimation, published daily by NY Fed. Stationary VAR on yield PCs, so the endpoint is effectively the sample mean — a *constant*.
- **△ Kim & Wright (2005).** Three factors, MLE, with survey forecasts of the short rate as observations. Published by the Board.
- **△ D'Amico, Kim & Wei.** TIPS-inclusive; gives real term premia and inflation risk premia separately.

**Critiques**
- **○ FEDS Note, April 2017, "Robustness of Long-Maturity Term Premium Estimates."** ACM and KW are structurally very similar but diverge materially at times; the main reason is KW's inclusion of Blue Chip surveys. Adding those surveys to ACM makes the two converge. Some features are robust across models (long-maturity premia low by historical standards); the sign and volatility are not.
- **△ Bauer, Rudebusch & Wu (2012).** Small-sample downward bias in Φ inflates term premium variability.
- **△ Duffee (2011), "Information in (and not in) the term structure."** Yield-only factors miss variation in expected returns.
- **△ Joslin, Priebsch & Singleton (2014).** Macro variables carry risk-premium information unspanned by yields.
- **△ Bauer & Hamilton (2018).** Standard tests for macro predictability of bond returns are badly oversized.

---

## 7. Trends and shifting endpoints

- **△ Kozicki & Tinsley (2001).** Shifting endpoints — the original statement that the long-run anchor of the short rate moves.
- **○ Bauer & Rudebusch (2020), "Interest Rates Under Falling Stars," AER.** Adds an I(1) trend i\* = r\* + π\* to a Gaussian ATSM. Four states: three yield factors plus the common stochastic trend. Yields of different maturities share the trend (cointegration with unit loading), which is the statement ∂y^(n)/∂i\* = 1 at every maturity. The trend is **unspanned** — measured externally rather than filtered from yields — because spanned versions require far more parameters. Claim: constant-endpoint models misattribute trend movement to the term premium, producing implausible premia and poor long-horizon forecasts.
- **△ Cieslak & Povala (2015), "Expected Returns in Treasury Bonds," RFS.** Yields decomposed into an inflation-trend component τ_t and maturity-specific cycles orthogonal to it. The *short-maturity* cycle captures real short-rate dynamics; together with expected inflation it forms the EH term, and controlling for that leaves risk premium. Trend inflation accounts for >80% of unconditional yield-level variance since the 1970s.
- **△ Cieslak (2018), RFS.** Errors about the path of the real rate account for ~80% of short-rate forecast error variance at a one-year horizon; over half attributable to the Fed easing more than expected. Business-cycle frequency, not endpoint.

**Note on C–P vs. BR:** C–P project out π\* only; BR project out both stars. If r\* drifted over the sample, its trend has nowhere to go but into the cycles — though because π\* and r\* co-moved after 1980, part of it is also absorbed into the loading on τ_t. The two are not separately identified from that regression alone.

---

## 8. Learning about trends

- **✔/○ Ahonon & Roussellet, "When Long-Run Trends Are Unknown: Bond Pricing Implications," NY Fed SR 1187, March 2026.** (Summary read in full; paper itself not.) Gaussian ATSM where the investor observes aggregates plus a private signal but *not* the trend–cycle split, and must Kalman-filter it. Yields are affine in *subjective* states, so ATSM tractability survives. Delivers both perceived r\* and the investor's uncertainty about it (±168bp 95% band). Estimated price-of-risk factor has equal-and-opposite loadings on i\* and π\*, so r\* is the only trend in the SDF — and this vanishes under the perfect-information benchmark, so it is produced by learning. Reports both one-sided and two-sided estimates. Also: no evidence of a Fed information effect.
- **△ Davis & Segal (2023).** Underreaction to permanent shocks, overreaction to transitory ones. A–R's source for that prediction.
- **△ Farmer, Nakamura & Steinsson.** Slow learning about r\*.

---

## 9. Disagreement and heterogeneous beliefs in bond markets

- **○ Xiong & Yan (2010), RFS.** Investors disagree about future interest rates and take speculative positions; the equilibrium bond price is a wealth-weighted average of the corresponding homogeneous-economy prices. Relative wealth fluctuation amplifies yield volatility and generates time-varying bond premia.
- **○ Ehling, Gallmeyer, Heyerdahl-Larsen & Illeditsch (2018), JFE.** Disagreement about the inflation distribution; on average raises real and nominal yields. Empirical tests on inflation disagreement.
- **○ Cao, Crump, Eusepi & Moench, NY Fed SR 934.** Affine TSM in which investors hold heterogeneous beliefs about the **long-run mean of the level factor**. No-arbitrage implies each investor's price of level risk moves proportionally with her belief about the future level of rates. Estimated on yields plus the term structure of survey forecasts, for top-10 and bottom-10 forecaster groups. ~1/3 of term premium variation driven by short-rate disagreement. Because rates trended down, the low-rate investor's wealth share grows, which removes the usual downward trend from the aggregate term premium.
- **○ Giacoletti, Laursen & Singleton.** Arbitrage-free DTSM in which belief heterogeneity affects market prices of factor risks.
- **○ Bauer & Chernov.** Adopt the Basak / Xiong–Yan / Ehling framework, reinterpreting disagreement as belief bias.
- **○ Molavi (Kellogg).** Generalizes beyond the two-type restriction; notes prior work does not specify the source of belief heterogeneity. Derives regression-based tests.
- **△ Crump, Eusepi & Moench, NY Fed SR 658.** Subjective term premia from long-horizon BCFF forecasts.
- **△ Piazzesi, Salomao & Schneider.** Subjective bond risk premia from surveys; less volatile and less cyclical than statistical measures.
- **○ Nagel & Xu, "Dynamics of Subjective Risk Premia."** Survey-based subjective risk premia are largely acyclical; objective ones countercyclical. Across stocks, bonds, currencies, commodities.
- **○ Leombroni, Pflueger & Sunderam (2026).** Subjective expected excess bond returns against stock-market betas, 1988–2024.
- **○ FEDS 2024-084, "Disagreement About the Term Structure of Inflation Expectations."** Decomposes forecaster disagreement across horizons into long-term beliefs, public information, and private information; heterogeneous individual loadings on the common component.

**Technical note.** Heterogeneous beliefs introduce a wealth-share state that does not evolve affinely, which is why these models need log utility and complete markets (Xiong–Yan) or approximation (Molavi). Adding disagreement to a Gaussian ATSM is not a small extension.

---

## 10. Fed-versus-market disagreement

- **✔ Rungcharoenkitkul & Winkler, "The Natural Rate of Interest Through a Hall of Mirrors." FEDS 2022-010 / BIS WP 974. Published *Journal of Monetary Economics*, January 2026, vol. 157, 103858.**
  Two beliefs about a common exogenous fundamental. r\*\* = σg_t + z_t is the true natural rate and is exogenous; r\*_t ≡ E^h_t[r\*\*_t] is the private sector's expectation and is what actually determines aggregate demand — so the *de facto* natural rate is endogenous to policy through learning. Taylor rule uses the central bank's own estimate: i_t = ρ_i i_{t−1} + (1−ρ_i)(r̂\*_t + φ_π π_t + φ_y ỹ_t + u_ct), r̂\*_t ≡ E^c_t[r\*\*_t]. Output gap ỹ = (1/λ)(r\* − r̂\* + u_h − u_c), so belief disagreement moves the output gap with no shocks. Each side partly reads its own past influence back out of the other's actions — the "hall of mirrors." Section 6 simulates yield curves and matches the excess sensitivity of long forwards; **footnote 14 states the model implicitly assumes term premia are zero.** Empirically they proxy the central bank's belief with HLW and the private sector's with Blue Chip. Unlike Caballero–Simsek, agents do not agree to disagree.
- **△ Caballero & Simsek (2021).** Opinionated markets; a central bank facing investors who disagree with it. The pricing-of-disagreement mechanism.
- **△ Engstrom, FEDS 2026-026.** Stale-signal / anchoring alternative — markets read the dot plot.
- **△ Ochoa & Wiegand.** Decomposing policy-path uncertainty into macro versus reaction-function components.
- **○ Benigno (Substack, early August 2026).** Links hall-of-mirrors to Hillenbrand and to a recent Lustig extension; notes competing explanations imply different **maturity profiles**.

---

## 11. Central bank communication

- **△ Stein (1989), AER.** Cheap talk: why a central bank can only make imprecise announcements credibly.
- **△ Morris & Shin.** Social value of public information; coordination on a public signal.
- **△ Gemmi & Valchev (JME 2026); Hansen, McMahon & Prat (QJE 2018).** Strategic behavior and FOMC communication.

**The structural point:** if the Fed's r\* announcement is credible, the market updates and long real rates move — but that is an informational instrument that stops working the moment it is used as one. Equilibrium informativeness depends on incentive compatibility.

---

## 12. FOMC announcements and asset prices

- **△ Lucca & Moench (2015), JF.** Pre-FOMC announcement drift — abnormal equity returns in roughly the 24 hours before the announcement. Unexplained. Occupies exactly the day −1 window in Hillenbrand's figure.
- **△ Nakamura & Steinsson.** The (near-term) Fed information effect.
- **△ Cieslak, Morse & Vissing-Jorgensen.** Informal communication and the intermeeting cycle.
- **△ Cieslak & Pang.** Risk-premium channel around FOMC announcements; the alternative Hillenbrand downweights.
- **△ Bauer & Swanson (2023).** Against the information effect; the "Fed response to news" channel.
- **△ Gürkaynak, Sack & Swanson (2005).** Excess sensitivity of long-term forward rates to macro news; attributed to a drifting perceived inflation target. Note this cuts *opposite* to underreaction stories.
- **△ Bauer, Pflueger & Sunderam (QJE 2024).** Perceived monetary policy rule; subjective beliefs about the Fed's reaction function.

---

## 13. Useful algebra

**Maturity loadings (κ_n).** With i_t = r\*_t + π\*_t + c_t, c_t AR(1) with persistence ρ, and r\* a random walk:

y_t^(n) = r\*_t + π\*_t + κ_n·c_t + TP_t^(n),  κ_n = (1 − ρ^n) / (n(1 − ρ))

- ∂y^(n)/∂r\* = 1 for all n (flat — no maturity attenuation)
- ∂y^(n)/∂c = κ_n → 0 at rate 1/n

In price space: ∂log P/∂r\* = −n (full duration), while ∂log P/∂c → −1/(1−ρ), a constant. Past ~10y maturity, marginal duration is essentially pure endpoint exposure.

If r\* is instead AR(1) with persistence φ, the endpoint loading becomes κ_n(φ) — so the maturity profile of the response to r\* news is a monotone function of r\*'s persistence.

**The SDF.** No-arbitrage gives *existence* of a positive SDF; *uniqueness* requires complete markets. What a bond model estimates is the projection of the true SDF onto the bond-spanned payoff space (Hansen–Richard). A bond-based and an equity-based estimate can differ without either being wrong. In A–R, the SDF is defined relative to the *investor's* filtration, so it prices correctly under her beliefs and would look misspecified under the econometrician's.

---

## 14. Data sources

| Series | Location | Notes |
|---|---|---|
| GSW nominal yield curve | federalreserve.gov/data/yield-curve-tables/feds200628.csv | Daily 1961–. Skip 9 header rows; missing code −999.99. `SVENY10` = 10y zero-coupon. NSS parameters allow any horizon. Updated ~weekly. Hillenbrand uses the GSW off-the-run curve. |
| ACM term premia | NY Fed, term premia page | Daily; fitted yield, risk-neutral yield, term premium, 1–10y. The only daily source with the component split. |
| Kim–Wright | Board, feds200533 | Survey-disciplined alternative decomposition. |
| GSW TIPS / inflation compensation | Board, "TIPS Yield Curve and Inflation Compensation" (feds200805) | Real curve. |
| SEP projections | federalreserve.gov | De-anonymized with 5-year lag from 2016; 10-year lag 2007–2015. |
| Survey of Primary Dealers | NY Fed | |
| HLW | NY Fed | One-sided and two-sided. |
| FRED DGS10 | H.15 constant maturity | Fine for charts; par not zero-coupon, so wrong for curve work. |

---

## 15. Open factual questions from this conversation

1. Does Hillenbrand report the day −1 / day 0 split as a formal test, or only in Figure 7? (The "roughly half each" reading is from the figure, not from his text.)
2. How does he define day −1 for two-day versus one-day meetings? For two-day meetings, day −1 is the first day of the meeting itself.
3. Does he report the window decomposition by era? A 30-year cumulative sum can hide subperiod heterogeneity.
4. Does he decompose the window into risk-neutral and term-premium components? (Nothing seen so far suggests he does.)
5. Is there a Lustig extension of hall-of-mirrors in paper form?
6. Has anyone added risk premia to Rungcharoenkitkul–Winkler since JME publication?
