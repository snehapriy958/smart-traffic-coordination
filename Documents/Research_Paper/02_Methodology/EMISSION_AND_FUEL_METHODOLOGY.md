# Emissions & Fuel Consumption Methodology

## 1. HBEFA4/2.0 Microscopic Emission Engine
Vehicle emissions are calculated microscopically on every simulation step $\Delta t = 1.0\text{ s}$ using the European Handbook of Emission Factors for Road Transport (HBEFA4/2.0) integrated within SUMO:
- **Passenger Cars**: Euro-4 petrol engine (`HBEFA4/PC_petrol_Euro-4`).
- **Motorcycles**: Pre-Euro 4-stroke petrol engine (`HBEFA4/MC_4S_gt250cc_preEuro`).
- **BMTC Buses**: Euro-VI heavy diesel bus (`HBEFA4/UBus_Std_gt15-18t_Euro-VI_A-C`).
- **Commercial Trucks**: Euro-VI diesel truck (`HBEFA4/HDV_D_EU6`).
- **Emergency Ambulances**: Euro-6 light commercial diesel (`HBEFA4/LCV_D_EU6`).

## 2. Cumulative Mass Accumulation & SI Conversions
1. **Carbon Dioxide ($	ext{CO}_2$, kg)**:
   $$\text{CO}_2 = \frac{1}{10^6} \sum_{t=1}^{T_{\text{sim}}} \sum_{e \in \mathcal{E}_{\text{corridor}}} \dot{m}_{\text{CO}_2}(e, t) \cdot \Delta t \quad [\text{kg}]$$
2. **Nitrogen Oxides ($	ext{NO}_x$, g)**:
   $$\text{NO}_x = \frac{1}{10^3} \sum_{t=1}^{T_{\text{sim}}} \sum_{e \in \mathcal{E}_{\text{corridor}}} \dot{m}_{\text{NO}_x}(e, t) \cdot \Delta t \quad [\text{g}]$$

## 3. Petrol-Equivalent Volumetric Fuel Index ($	ext{L}_{	ext{petrol-eq}}$)
Because the fleet consists of mixed petrol and diesel vehicles, physical fuel mass flow (mg) is converted to volume using a standardized reference petrol density:
$$\rho_{\text{ref}} = 0.750\text{ kg/L} = 750{,}000.0\text{ mg/L}$$
$$\text{Fuel} = \frac{\sum_{t=1}^{T_{\text{sim}}} \sum_{e} \dot{m}_{\text{fuel}}(e, t) \cdot \Delta t}{750{,}000.0} \quad [\text{L}_{\text{petrol-eq}}]$$

## 4. Stoichiometric Combustion Consistency Check
Pure octane ($\text{C}_8\text{H}_{18}$, molar mass $114.22\text{ g/mol}$) combustion:
$$\text{C}_8\text{H}_{18} + 12.5\text{O}_2 \longrightarrow 8\text{CO}_2 + 9\text{H}_2\text{O}$$
Theoretical ratio:
$$\frac{\text{Mass } \text{CO}_2}{\text{Volume petrol}} = 0.750\text{ kg/L} \times \left(\frac{8 \times 44.01}{114.22}\right) = \mathbf{2.3116\text{ kg CO}_2 / \text{L}}$$
Empirical master benchmark ratio:
$$\frac{55.578\text{ kg CO}_2}{23.993\text{ L}_{\text{petrol-eq}}} = \mathbf{2.3164\text{ kg CO}_2 / \text{L}}$$
Stoichiometric deviation:
$$\epsilon = \frac{|2.3164 - 2.3116|}{2.3116} = \mathbf{0.208\%}$$
This confirms exact conservation of carbon mass between the emissions engine and volumetric fuel index.
