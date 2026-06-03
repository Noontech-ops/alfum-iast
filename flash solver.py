import numpy as np
import pandas as pd
import pyiast

# ============================================================
# 1. DSL ISOTHERM PARAMETERS
#    Source: Huang et al. 2022 — Al-Fum at 273K
#    Replace placeholders with real fitted values
# ============================================================

P_points = np.linspace(0.0001, 1.0, 200)

def dual_site_langmuir(P, q1, b1, q2, b2):
    return (q1 * b1 * P) / (1 + b1 * P) + (q2 * b2 * P) / (1 + b2 * P)

# CH4 — placeholder parameters
CH4_q1, CH4_b1, CH4_q2, CH4_b2 = 1.20, 0.80, 0.50, 0.05

# N2 — placeholder parameters
N2_q1,  N2_b1,  N2_q2,  N2_b2  = 0.60, 0.10, 0.20, 0.01

df_ch4 = pd.DataFrame({"P": P_points, "Loading": dual_site_langmuir(P_points, CH4_q1, CH4_b1, CH4_q2, CH4_b2)})
df_n2  = pd.DataFrame({"P": P_points, "Loading": dual_site_langmuir(P_points, N2_q1,  N2_b1,  N2_q2,  N2_b2)})

isotherms = [
    pyiast.ModelIsotherm(df_ch4, loading_key="Loading", pressure_key="P", model="DSLangmuir"),
    pyiast.ModelIsotherm(df_n2,  loading_key="Loading", pressure_key="P", model="DSLangmuir"),
]

# ============================================================
# 2. PROCESS CONDITIONS
# ============================================================

P_total  = 1.0    # bar
n_gas    = 1.0    # mol total gas
m_mof    = 1.0    # g MOF
tol      = 1e-8
max_iter = 200

y_feed = np.array([0.0001, 0.9999])   # [CH4, N2] — 100 ppm CH4
names  = ["CH4", "N2"]

# ============================================================
# 3. FLASH SOLVER
# ============================================================

def run_flash(y_feed, n_gas, m_mof, P_total, isotherms, tol=1e-8, max_iter=200):

    n_feed = y_feed * n_gas
    y_eq   = y_feed.copy()         # initial guess = feed composition

    for i in range(max_iter):

        # partial pressures from current guess
        partial_pressures = y_eq * P_total

        # IAST → adsorbed loadings (mmol/g)
        q_eq = pyiast.iast(partial_pressures, isotherms, verbosity=False)

        # mmol/g → mol adsorbed
        n_adsorbed = (q_eq / 1000.0) * m_mof

        # mass balance → remaining gas
        n_gas_eq       = np.maximum(n_feed - n_adsorbed, 0.0)
        n_gas_total_eq = np.sum(n_gas_eq)

        # new mole fractions
        y_new  = n_gas_eq / n_gas_total_eq
        delta  = np.max(np.abs(y_new - y_eq))
        y_eq   = y_new.copy()

        if delta < tol:
            print(f"Converged in {i+1} iterations")
            break

    n_adsorbed_total = np.sum(n_adsorbed)
    y_adsorbed = n_adsorbed / n_adsorbed_total if n_adsorbed_total > 0 else np.zeros(len(y_feed))

    return {
        "y_gas_eq":       y_eq,
        "y_adsorbed":     y_adsorbed,
        "q_eq_mmol_g":    q_eq,
        "n_adsorbed_mol": n_adsorbed,
        "n_gas_eq_mol":   n_gas_eq,
        "mass_balance":   n_adsorbed + n_gas_eq,   # should equal n_feed
    }

# ============================================================
# 4. RUN & REPORT
# ============================================================

result = run_flash(y_feed, n_gas, m_mof, P_total, isotherms)

print("\n--- Gas phase (remaining) ---")
for i, name in enumerate(names):
    print(f"  {name}: {result['y_gas_eq'][i]:.6f}  ({result['y_gas_eq'][i]*1e6:.1f} ppm)")

print("\n--- Adsorbed phase (product) ---")
for i, name in enumerate(names):
    print(f"  {name}: {result['y_adsorbed'][i]:.6f}  ({result['y_adsorbed'][i]*100:.2f}%)")

print("\n--- Loadings ---")
for i, name in enumerate(names):
    print(f"  {name}: {result['q_eq_mmol_g'][i]:.6f} mmol/g")

print(f"\n  CH4 enrichment: {result['y_adsorbed'][0] / y_feed[0]:.1f}x")

print("\n--- Mass balance check (should match feed) ---")
n_feed = y_feed * n_gas
for i, name in enumerate(names):
    print(f"  {name}: feed={n_feed[i]:.6f} | check={result['mass_balance'][i]:.6f}")
