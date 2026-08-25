# The open research question

*Drafted 11 August 2026, after the replication, the ACM decomposition, and the literature check.*

---

## The question, in one sentence

When the Fed moves long-term interest rates at scheduled announcements, is it changing **where markets think rates are going**, or **what markets charge for the risk of being wrong about that** — and does the answer depend on how far apart the Fed and the market are about the destination?

## The question, as an empirical test

> Does the pre-meeting gap between the Fed's published longer-run policy rate projection and the market-implied long-run endpoint predict announcement-window changes in the **term premium**, over and above its effect on **expected short rates**?

The state variable is a *level* disagreement about the endpoint, measured strictly before the announcement. The outcome is the decomposed 3-day window response of the long yield. Both halves matter: the signal is new, and the channel is contested.

---

## Why it is open

**1. Hillenbrand rules out the term premium by assertion, not by test.** The RFS paper establishes that the secular decline in long rates accumulates inside 3-day FOMC windows, and attributes it to markets learning a lower r\* from the Fed. Its Internet Appendix reports that ACM and Kim–Wright term premia fall 100–200 bp in those windows, then sets the finding aside on the grounds that the models "do not explicitly account for the secular decline." That objection is correct — stationary affine models book any true endpoint decline as term premium — but it is a reason the measurement is unreliable, not evidence the channel is absent. Nobody has tested it.

**2. The two papers that did test it disagree, and each has a specific, identifiable flaw.** Hofmann, Li & Wu (BIS WP 1252) find the window decline is risk-neutral (US pseudo-R² 96 vs 32) — but their shifting endpoint is *defined as* the first principal component of cumulative FOMC-window yield changes, so the risk-neutral component inherits the very series being explained. Pan & Peng (SSRN 4764451) find the opposite on the largest single day: on t−1 the 10-year falls 0.79 bp, of which 0.71 bp is term premium and 0.08 bp (insignificant) is expectations. Circular endpoint versus single-day ACM. The literature currently contains both answers and no adjudication.

**3. The closest precedent tests a slope, not a level.** Bauer, Pflueger & Sunderam (QJE 2024) show that a pre-meeting subjective-belief variable — the market's perceived policy *reaction-function coefficient* — is related to term premia and to state-dependent announcement-window yield responses. That is the template. What has never been tested is the perceived **endpoint**: not how strongly markets think the Fed responds, but where markets think the Fed is heading, relative to where the Fed says it is heading.

**4. The mechanism has theory but no announcement-window evidence.** Ahonon & Roussellet (FRBNY SR 1187) show that under Bayesian learning about unobserved trends, investor uncertainty about r\* is roughly ±170 bp rather than ±55 bp, and that r\* is the primary long-run driver of bond risk premia. If investors are that uncertain about the destination, a 50–100 bp Fed–market gap about the destination is plausibly *priced as risk*, not merely *resolved as information*. Nobody has taken that to FOMC data.

---

## The two hypotheses and what separates them

**H1 — Information channel.** The Fed's announcement reveals its own view of the endpoint; markets update expectations toward it. This is Hillenbrand's mechanism.

**H2 — Risk channel.** Unresolved disagreement about the endpoint is a risk investors must be compensated for; the scheduled announcement partially resolves it, compressing the premium.

| | H1 predicts | H2 predicts |
|---|---|---|
| Which component responds | risk-neutral | term premium |
| Functional form of the signal | **signed** wedge (market moves toward the Fed) | **magnitude** of disagreement (\|wedge\|, dispersion) |
| Timing within the window | day *t*, when information arrives | day *t−1*, as uncertainty resolves pre-announcement |
| Persistence | permanent; does not reverse | partially reverses as uncertainty rebuilds |
| Cross-maturity loading | flat in maturity (endpoint shock) | rising with duration |

The persistence row is where a second, unexploited tension sits. Hanson, Lucca & Wright (QJE 2021) show that announcement-window long-rate moves substantially reverse within 6–12 months, which they read as evidence of temporary term-premium effects. Hillenbrand's central fact requires that window moves **do not** reverse — they cumulate into a 32-year trend. Those two claims have never been confronted directly. Testing whether the in-window *term premium* component mean-reverts while the *risk-neutral* component does not would reconcile them, and would discriminate H1 from H2 without relying on any single decomposition.

---

## The finding that makes this more than a horse race

Our own preliminary results fit **neither** hypothesis cleanly. The **signed** wedge prices and the absolute wedge gives nothing — an H1 signature. But the response runs through the **term premium** as strongly as through expectations — an H2 signature. And the two components respond to *opposite signs of the same gap*: the term premium responds only when the Fed sits above the market, the expectations component only when the Fed sits below.

That asymmetry is not predicted by either channel as usually stated. The natural reconciliation is that the Fed's longer-run projection is not only a signal about r\*, but a signal about the Fed's own willingness to act on it — so a hawkish gap creates *policy risk* to be compensated, while a dovish gap creates *expectation revision*. If that survives, it is a genuinely new mechanism rather than a new estimate.

The honest caveat, already documented internally: the sample periods where the Fed sits above and below the market barely overlap (2012–2015 versus 2020–2026), so this may be one regime shift observed twice. Establishing that it is not is the first empirical task, not the last.

---

## What answering it requires

1. **A non-circular endpoint.** The market leg must not be constructed from FOMC-window data. Kim–Wright (survey-anchored) or a survey-based term premium in the style of Crump, Eusepi & Moench (SR 775) are the candidates.
2. **Enough variation in the Fed leg.** The SEP longer-run median has 19 changes across 57 meetings; the cross-participant dispersion has 49 distinct values with ρ = 0.80. Power, not novelty, is the binding constraint.
3. **Orthogonalisation against pre-meeting public information.** Bauer & Swanson (NBER Macro Annual 2023) show announcement surprises are predictable from pre-meeting data. The wedge *is* pre-meeting public information, so the Fed-response-to-news channel must be partialled out before any term-premium interpretation.
4. **Detrending.** A slow-moving level wedge regressed on window yield changes will mechanically pick up Hillenbrand's secular trend.

---

## What the question is *not*

Scope discipline, because each of these is taken:

- Not "does the secular decline happen in FOMC windows" — Hillenbrand (2025), extended globally by Hofmann, Li & Wu (2025).
- Not "is the window decline expectations or term premium" as a standalone question — contested by the two above; we can adjudicate it, not open it.
- Not "does forecaster disagreement comove with the term premium" — Cao, Crump, Eusepi & Moench (SR 934).
- Not "does the dot plot move asset prices" — Couture (2021); Engstrom (FEDS 2026-026) on SEP-minus-market gaps predicting forecast errors.
- Not "does a gap between the policy rate and an equilibrium rate predict bond returns" — Favero, Melone & Tamoni (JFQA 2024). Different wedge, similar name; differentiate explicitly.
