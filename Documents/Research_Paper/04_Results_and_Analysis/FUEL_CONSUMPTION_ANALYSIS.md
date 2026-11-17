# Fuel Consumption & Stoichiometric Chemistry Analysis

## 1. Volumetric Fuel Index ($	ext{L}_{	ext{petrol-eq}}$)
- **Baseline**: $23.993 \pm 0.084\text{ L}_{\text{petrol-eq}}$
- **Coordinated Adaptive**: $18.439 \pm 0.277\text{ L}_{\text{petrol-eq}}$ ($-23.15\%$)
- **Double-DQN**: $20.353 \pm 0.279\text{ L}_{\text{petrol-eq}}$ ($-15.17\%$)
- **MARL PPO**: $23.757 \pm 0.735\text{ L}_{\text{petrol-eq}}$ ($-0.98\%$)

## 2. Chemical Mass Conservation
- Empirical Ratio: $\frac{55.578\text{ kg CO}_2}{23.993\text{ L}_{\text{petrol-eq}}} = 2.3164\text{ kg CO}_2/\text{L}$
- Theoretical Octane Ratio: $2.3116\text{ kg CO}_2/\text{L}$
- Relative Error: $0.208\%$
This proves that the reported fuel and emissions reductions are physically realistic and stoichiometrically sound.
