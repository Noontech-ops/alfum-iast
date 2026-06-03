import numpy as np
import pandas as pd
import pyiast
from pathlib import Path

# ============================================================
# SIMPLE CH4/N2 FLASH SOLVER DEMO USING pyIAST
# ============================================================

P_TOTAL = 1.0      # bar
N_GAS = 1.0        # mol total gas
M_MOF = 1.0        # grams of MOF
TOL = 1e-8
MAX_ITER = 200

NAMES = ["CH4", "N2"]
Y_FEED = np.array([0.0001, 0.9999])  # 100 ppm CH4, balance N2


def dual_site_langmuir(P, q1, b1, q2, b2):
    return (q1 * b1 * P) / (1 + b1 * P) + (q2 * b2 * P) / (1 + b2 * P)


def build_placeholder_isotherms():
    print("WARNING: Placeholder DSL parameters used — not valid for scientific conclusions.")

    P_points = np.linspace(0.0001, 1.0, 200)

    CH4_q1, CH4_b1, CH4_q2, CH4_b2 = 1.20, 0.80, 0.50, 0.05
    N2_q1, N2_b1, N2_q2, N2_b2 = 0.60, 0.10, 0.20, 0.01

    df_ch4 = pd.DataFrame({
        "P": P_points,
        "Loading": dual_site_langmuir(P_points, CH4_q1, CH4_b1, CH4_q2, CH4_b2)
    })

    df_n2 = pd.DataFrame({
        "P": P_points,
        "Loading": dual_site_langmuir(P_points, N2_q1, N2_b1, N2_q2, N2_b2)
    })

    return [
        pyiast.ModelIsotherm(df_ch4, loading_key="Loading", pressure_key="P", model="DSLangmuir"),
        pyiast.ModelIsotherm(df_n2, loading_key="Loading", pressure_key="P", model="DSLangmuir"),
    ]


def load_csv_isotherms(data_dir="data"):
    data_dir = Path(data_dir)

    ch4_path = data_dir / "ch4.csv"
    n2_path = data_dir / "n2.csv"

    if not ch4_path.exists() or not n2_path.exists():
        return None

    df_ch4 = pd.read_csv(ch4_path)
    df_n2 = pd.read_csv(n2_path)

    # Expected columns: pressure and loading
    # Adjust these if your repo uses different names.
    pressure_col = "pressure"
    loading_col = "loading"

    if pressure_col not in df_ch4.columns:
        pressure_col = "P"
    if loading_col not in df_ch4.columns:
        loading_col = "Loading"

    ch4_iso = pyiast.InterpolatorIsotherm(
        df_ch4,
        loading_key=loading_col,
        pressure_key=pressure_col,
        adsorbate="CH4"
    )

    pressure_col = "pressure"
    loading_col = "loading"

    if pressure_col not in df_n2.columns:
        pressure_col = "P"
    if loading_col not in df_n2.columns:
        loading_col = "Loading"

    n2_iso = pyiast.InterpolatorIsotherm(
        df_n2,
        loading_key=loading_col,
        pressure_key=pressure_col,
        adsorbate="N2"
    )

    print("Using real CH4/N2 CSV isotherm data from data/")

    return [ch4_iso, n2_iso]


def build_isotherms():
    isotherms = load_csv_isotherms("data")

    if isotherms is not None:
        return isotherms

    return build_placeholder_isotherms()


def run_flash(y_feed, n_gas, m_mof, p_total, isotherms, tol=1e-8, max_iter=200):
    n_feed = y_feed * n_gas
    y_eq = y_feed.copy()

    for iteration in range(max_iter):
        # 1. Convert current gas composition guess to partial pressures
        partial_pressures = y_eq * p_total

        # 2. Run pyIAST to get mixed-gas adsorbed loadings in mmol/g
        q_eq = np.array(
            pyiast.iast(partial_pressures, isotherms, verbosity=False),
            dtype=float
        )

        # 3. Convert mmol/g to mol adsorbed
        n_adsorbed = (q_eq / 1000.0) * m_mof

        # 4. Mass balance: gas left = gas fed - gas adsorbed
        n_gas_eq = n_feed - n_adsorbed
        n_gas_eq = np.maximum(n_gas_eq, 0.0)

        n_gas_total_eq = np.sum(n_gas_eq)

        if n_gas_total_eq <= 0:
            raise ValueError("All gas adsorbed or invalid mass balance. Reduce MOF mass or check isotherms.")

        # 5. New equilibrium gas composition
        y_new = n_gas_eq / n_gas_total_eq

        # 6. Check convergence
        delta = np.max(np.abs(y_new - y_eq))
        y_eq = y_new.copy()

        if delta < tol:
            print(f"Converged in {iteration + 1} iterations")
            break
    else:
        print("WARNING: Flash solver did not converge.")

    n_adsorbed_total = np.sum(n_adsorbed)
    y_adsorbed = n_adsorbed / n_adsorbed_total if n_adsorbed_total > 0 else np.zeros_like(y_feed)

    mass_balance_check = n_adsorbed + n_gas_eq
    mass_balance_error = np.max(np.abs(mass_balance_check - n_feed))

    return {
        "y_gas_eq": y_eq,
        "y_adsorbed": y_adsorbed,
        "q_eq_mmol_g": q_eq,
        "n_adsorbed_mol": n_adsorbed,
        "n_gas_eq_mol": n_gas_eq,
        "mass_balance_check": mass_balance_check,
        "mass_balance_error": mass_balance_error,
    }


def run_simple_binary_flash_demo():
    isotherms = build_isotherms()

    result = run_flash(
        y_feed=Y_FEED,
        n_gas=N_GAS,
        m_mof=M_MOF,
        p_total=P_TOTAL,
        isotherms=isotherms,
        tol=TOL,
        max_iter=MAX_ITER,
    )

    print("\n--- Feed gas ---")
    for i, name in enumerate(NAMES):
        print(f"{name}: {Y_FEED[i]:.8f} ({Y_FEED[i] * 1e6:.2f} ppm)")

    print("\n--- Gas phase remaining / raffinate ---")
    for i, name in enumerate(NAMES):
        print(f"{name}: {result['y_gas_eq'][i]:.8f} ({result['y_gas_eq'][i] * 1e6:.2f} ppm)")

    print("\n--- Adsorbed phase / desorbed product ---")
    for i, name in enumerate(NAMES):
        print(f"{name}: {result['y_adsorbed'][i]:.8f} ({result['y_adsorbed'][i] * 100:.4f}%)")

    print("\n--- Mixed-gas pyIAST loadings ---")
    for i, name in enumerate(NAMES):
        print(f"{name}: {result['q_eq_mmol_g'][i]:.8f} mmol/g")

    ch4_enrichment = result["y_adsorbed"][0] / Y_FEED[0]

    print(f"\nCH4 enrichment in adsorbed product: {ch4_enrichment:.2f}x")
    print(f"Mass balance error: {result['mass_balance_error']:.3e} mol")

    print("\n--- Mass balance check ---")
    n_feed = Y_FEED * N_GAS
    for i, name in enumerate(NAMES):
        print(
            f"{name}: feed={n_feed[i]:.10f} mol | "
            f"adsorbed+raffinate={result['mass_balance_check'][i]:.10f} mol"
        )


if __name__ == "__main__":
    run_simple_binary_flash_demo()
