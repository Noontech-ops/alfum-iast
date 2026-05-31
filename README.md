# Al-Fum IAST Modeling

This repository performs Ideal Adsorbed Solution Theory simulations for CH4/N2 adsorption in Al-Fumarate using pyIAST.

## What IAST Does

IAST predicts mixed-gas adsorption from pure-component adsorption isotherms. In this repo, pure CH4 and N2 isotherms are converted into pyIAST isotherm objects, then mixed-gas uptake is predicted from gas-phase partial pressures.

## Core Workflow

1. Load pure-component CH4 and N2 isotherm CSVs.
2. Fit or interpolate each pure-component isotherm.
3. Define gas-phase composition and total pressure.
4. Convert total pressure into partial pressures.
5. Run pyIAST.
6. Output CH4 loading, N2 loading, and CH4/N2 selectivity.
7. Sweep pressure to generate performance curves.

## Literature Benchmark

Huang et al. reported CH4/N2 selectivity of approximately 17.2 at 273 K and 11.7 at 298 K for Al-Fumarate at 1 bar using IAST.

## IAST Conclusion

IAST converts pure-gas adsorption data into mixed-gas separation predictions. Using CH₄ and N₂ isotherms from Huang et al. (2022), the model predicts strong methane preference in Al-Fumarate and reproduces the reported CH₄/N₂ selectivity near ambient conditions (~11.7 at 298 K).

Huang, Z., Hu, P., Liu, X., Shen, Y., Zhang, Z., Chai, Y., Ying, Y., Kang, Z., Zhang, J., & Ji, H. (2022). Enhancing CH₄/N₂ separation performance within aluminum-based metal–organic frameworks: Influence of pore structure and linker polarity. Separation and Purification Technology, 287, 120534. DOI: 10.1016/j.seppur.2022.120534

## Scripts

- scripts/reproduce_huang.py: reproduces literature benchmark selectivities.
- scripts/pressure_sweep.py: runs pressure-dependent CH4/N2 IAST simulations.

## Outputs

- results/reproduce_huang.csv
- results/pressure_sweep_ch4_n2.csv
- figures/pressure_sweep_uptake_298K.png
- figures/selectivity_vs_pressure_all_temps.png

## Key Concept

Pure-gas isotherms in → mixed-gas adsorption predictions out.
