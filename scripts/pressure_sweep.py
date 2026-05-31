import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyiast


def load_and_prepare_isotherm(path):
    df = pd.read_csv(path)
    df = df.sort_values(by='Pressure(bar)').reset_index(drop=True)
    df = df.groupby('Pressure(bar)', as_index=False)['Uptake(mmol/g)'].mean()
    return df


def build_isotherms(temperature):
    ch4_path = f'data/ch4_{temperature}K.csv'
    n2_path = f'data/n2_{temperature}K.csv'

    ch4_df = load_and_prepare_isotherm(ch4_path)
    n2_df = load_and_prepare_isotherm(n2_path)

    iso_ch4 = pyiast.ModelIsotherm(
        ch4_df,
        pressure_key='Pressure(bar)',
        loading_key='Uptake(mmol/g)',
        model='Langmuir',
    )

    iso_n2 = pyiast.InterpolatorIsotherm(
        n2_df,
        pressure_key='Pressure(bar)',
        loading_key='Uptake(mmol/g)',
        fill_value=n2_df['Uptake(mmol/g)'].max(),
    )

    return iso_ch4, iso_n2


def run_pressure_sweep():
    temperatures = [273, 298, 313]
    total_pressures = np.linspace(0.01, 1.0, 100)
    results = []

    for temperature in temperatures:
        iso_ch4, iso_n2 = build_isotherms(temperature)

        for total_pressure in total_pressures:
            p_ch4 = total_pressure * 0.50
            p_n2 = total_pressure * 0.50
            q = pyiast.iast(np.array([p_ch4, p_n2]), [iso_ch4, iso_n2], warningoff=True)
            q_ch4, q_n2 = np.asarray(q).tolist()
            selectivity = (q_ch4 / 0.5) / (q_n2 / 0.5)

            results.append(
                {
                    'Temperature_K': temperature,
                    'Total_pressure_bar': total_pressure,
                    'Partial_pressure_CH4_bar': p_ch4,
                    'Partial_pressure_N2_bar': p_n2,
                    'CH4_loading_mmol_g': q_ch4,
                    'N2_loading_mmol_g': q_n2,
                    'CH4_N2_selectivity': selectivity,
                }
            )

    result_df = pd.DataFrame(results)
    result_df.to_csv('results/pressure_sweep_ch4_n2.csv', index=False)
    return result_df


def make_plots(df):
    # Uptake plot for 298 K
    df_298 = df[df['Temperature_K'] == 298]
    plt.figure(figsize=(8, 5))
    plt.plot(df_298['Total_pressure_bar'], df_298['CH4_loading_mmol_g'], label='CH4', marker='o', markersize=4)
    plt.plot(df_298['Total_pressure_bar'], df_298['N2_loading_mmol_g'], label='N2', marker='s', markersize=4)
    plt.title('CH4/N2 IAST Uptake Pressure Sweep at 298 K')
    plt.xlabel('Total pressure (bar)')
    plt.ylabel('Uptake (mmol/g)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('figures/pressure_sweep_uptake_298K.png')
    plt.close()

    # Selectivity vs pressure for all temperatures
    plt.figure(figsize=(8, 5))
    for temperature in sorted(df['Temperature_K'].unique()):
        subset = df[df['Temperature_K'] == temperature]
        plt.plot(subset['Total_pressure_bar'], subset['CH4_N2_selectivity'], label=f'{temperature} K', marker='o', markersize=4)
    plt.title('CH4/N2 IAST Selectivity vs Pressure')
    plt.xlabel('Total pressure (bar)')
    plt.ylabel('CH4/N2 Selectivity')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('figures/selectivity_vs_pressure_all_temps.png')
    plt.close()


def main():
    result_df = run_pressure_sweep()
    print('\nPressure sweep completed. Results written to results/pressure_sweep_ch4_n2.csv')
    print(result_df.head())
    make_plots(result_df)
    print('Figures written to figures/pressure_sweep_uptake_298K.png and figures/selectivity_vs_pressure_all_temps.png')


if __name__ == '__main__':
    main()
