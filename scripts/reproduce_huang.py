import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyiast


def load_and_prepare_isotherm(path):
    df = pd.read_csv(path)
    df = df.sort_values(by='Pressure(bar)').reset_index(drop=True)
    df = df.groupby('Pressure(bar)', as_index=False)['Uptake(mmol/g)'].mean()
    return df


def main():
    temperatures = [273, 298, 313]
    literature_selectivity = {273: 17.2, 298: 11.7, 313: None}
    reliability_notes = {
        273: 'validation target but may be sensitive to low-loading N2 interpolation',
        298: 'primary validated ambient case',
        313: 'sensitivity only, not literature validation',
    }

    results = []

    for temperature in temperatures:
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

        P_CH4 = 0.5
        P_N2 = 0.5
        q = pyiast.iast(np.array([P_CH4, P_N2]), [iso_ch4, iso_n2], warningoff=True)

        q_ch4, q_n2 = np.asarray(q).tolist()
        y_ch4 = 0.5
        y_n2 = 0.5
        selectivity = (q_ch4 / y_ch4) / (q_n2 / y_n2)

        lit_selectivity = literature_selectivity[temperature]
        if lit_selectivity is None:
            percent_error = None
        else:
            percent_error = abs(selectivity - lit_selectivity) / lit_selectivity * 100.0

        results.append(
            {
                'Temperature_K': temperature,
                'CH4_loading_mmol_g': q_ch4,
                'N2_loading_mmol_g': q_n2,
                'CH4_N2_selectivity': selectivity,
                'Literature_selectivity': lit_selectivity,
                'Percent_error_vs_literature': percent_error,
                'Reliability_note': reliability_notes[temperature],
            }
        )

    result_df = pd.DataFrame(results)
    result_df.to_csv('results/reproduce_huang.csv', index=False)

    print('\nIAST reproduction results:')
    print(result_df.to_string(index=False))

    # Optional plot for visual inspection
    plt.figure(figsize=(8, 5))
    plt.plot(result_df['Temperature_K'], result_df['CH4_N2_selectivity'], marker='o')
    plt.title('Reproduced CH4/N2 IAST Selectivity vs Temperature')
    plt.xlabel('Temperature (K)')
    plt.ylabel('CH4/N2 Selectivity')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('results/reproduce_huang_selectivity.png')
    plt.close()


if __name__ == '__main__':
    main()
