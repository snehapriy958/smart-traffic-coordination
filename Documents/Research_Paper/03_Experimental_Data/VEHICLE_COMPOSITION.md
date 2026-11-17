# Microscopic Vehicle Composition

### Empirical Fleet Breakdown ($T_{\text{sim}} = 900.0\text{ s}$)

| Microscopic Vehicle Class | SUMO `vClass` | Length (m) | Max Speed (m/s) | Active HBEFA4 Model | Departed Fleet ($N=378$) | Share (%) | Corridor Trips ($N=109$) | Share (%) |
| :--- | :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: |
| **Motorcycles / Two-Wheelers** | `motorcycle` | 2.2 | 16.7 | `HBEFA4/MC_4S_gt250cc_preEuro` | 257 | 67.99% | 73 | 66.97% |
| **Passenger Cars** | `passenger` | 4.5 | 16.7 | `HBEFA4/PC_petrol_Euro-4` | 103 | 27.25% | 31 | 28.44% |
| **BMTC Public Transit Buses** | `bus` | 12.0 | 11.1 | `HBEFA4/UBus_Std_gt15-18t_Euro-VI` | 12 | 3.17% | 2 | 1.83% |
| **Commercial Heavy Trucks** | `truck` | 10.0 | 11.1 | `HBEFA4/HDV_D_EU6` | 5 | 1.32% | 2 | 1.83% |
| **Emergency Ambulances** | `emergency` | 5.5 | 22.2 | `HBEFA4/LCV_D_EU6` | 1 | 0.26% | 1 | 0.92% |

*Note: Ambulance operates as an independent priority class (`vClass="emergency"`), receiving green wave priority override.*
