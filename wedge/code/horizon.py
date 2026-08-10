"""
horizon.py
==========
Is 9y1y far enough out that the cycle has washed out?

The risk-neutral n-year yield is the average expected one-year forward over
n years, so the yield loadings translate exactly into FORWARD loadings:

    f_n = n * L_n - (n-1) * L_{n-1}

That gives the implied response of the expected one-year rate n years ahead
to a one-pp pre-meeting wedge, read straight off the estimated maturity
profile.  If the cycle had washed out by year nine, f_9 and f_10 would be
flat and equal to the endpoint response.  Bootstrap the whole path.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm

OUT = "/home/claude/rstar_wedge/results"
RNG = np.random.default_rng(20260810)
ev = pd.read_csv(f"{OUT}/event_panel.csv", parse_dates=["meeting"])


def loadings(d, kind):
    out = []
    for n in range(1, 11):
        s = d[[f"d{kind}{n}_d2", "wedge_acm"]].dropna()
        X = sm.add_constant(s[["wedge_acm"]])
        out.append(sm.OLS(s.iloc[:, 0], X).fit().params["wedge_acm"])
    return np.array(out)


def fwd(L):
    n = np.arange(1, len(L) + 1)
    return n * L - np.concatenate([[0], (n[:-1]) * L[:-1]])


print("Implied response of the expected 1y forward rate, bp per pp of wedge\n")
res = {}
for kind, lab in [("rn", "risk-neutral"), ("tp", "term premium")]:
    L = loadings(ev, kind)
    F = fwd(L)
    # moving-block bootstrap over meetings
    d = ev[[f"d{kind}{n}_d2" for n in range(1, 11)] + ["wedge_acm"]].dropna(
        subset=["wedge_acm", f"d{kind}10_d2"]).reset_index(drop=True)
    Lb = np.empty((3000, 10))
    Lblk, nb = 8, int(np.ceil(len(d) / 8))
    for i in range(3000):
        st = RNG.integers(0, len(d) - Lblk, size=nb)
        idx = np.concatenate([np.arange(s, s + Lblk) for s in st])[:len(d)]
        Lb[i] = loadings(d.iloc[idx].reset_index(drop=True), kind)
    Fb = np.array([fwd(r) for r in Lb])
    lo, hi = np.percentile(Fb, [2.5, 97.5], axis=0)
    res[kind] = (F, lo, hi)
    print(f"  {lab}")
    print("    yr   fwd loading    95% CI")
    for n in range(10):
        print(f"    {n+1:2d}    {F[n]:+7.3f}     [{lo[n]:+6.2f}, {hi[n]:+6.2f}]")
    pk = int(np.argmax(np.abs(F)))
    print(f"    peak at year {pk+1} ({F[pk]:+.2f});  year 10 is "
          f"{abs(F[9]/F[pk]):.0%} of peak")
    # geometric decay rate from the peak to year 10
    if pk < 9 and F[pk] * F[9] > 0:
        rho = (abs(F[9]) / abs(F[pk])) ** (1 / (9 - pk))
        print(f"    implied annual decay from peak to year 10: rho = {rho:.3f}")
        print(f"    -> at that rho, an endpoint claim needs the forward "
              f"horizon where rho^h < 0.1: h = {np.log(0.1)/np.log(rho):.0f} "
              f"years past the peak\n")

# how much of a shock with that persistence survives into the 9y1y forward
print("Sanity: fraction of a cyclical shock surviving to the 9y1y forward")
for rho in [0.80, 0.85, 0.90, 0.906, 0.95]:
    print(f"    rho = {rho:.3f} annual  ->  rho^9 = {rho**9:.3f}")
