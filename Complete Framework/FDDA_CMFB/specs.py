import numpy as np
import scipy.constants as sc

# ===============================
# FDDA and CMFB design parameters
# ===============================
VDD = 1.8          # Supply Voltage (V)
CL  = 1e-12        # Differential Load Capacitance (F)
VCM = VDD / 2      # Common Mode Voltage (V)
freq = 1e3         # Frequency at which CMRR, PSRR, and noise is calculated (Hz)
temp = 298         # Temperature (K)
k = sc.Boltzmann   # Boltzmann's constant (J/K)

# ===================================
# FDDA and CMFB design specifications
# ===================================
Vicm_spec = (0.8, 1.0)                    # Input Common Mode Range (V)
Gain_dc_spec_dB = 50                      # DC Gain (dB)
GBW_spec = 1e6                            # Gain Bandwidth (Hz)
PM_spec = 56                              # Phase Margin (degrees)
SR_spec = 1e6                             # Slew Rate (V/s)
CMRR_spec_dB = 120                         # Common Mode Rejection Ratio (dB)
PSRR_spec_dB = 60                         # Power Supply Rejection Ratio (dB)
noise_spec = 0.25e-6                      # Input Referred Noise (V/√Hz)
Power_spec = 180e-6                       # Power Consumption (W)
Area_spec = 5000                          # Area (μm^2)

Gain_dc_spec = 10**(Gain_dc_spec_dB/20)   # Convert dB to V/V
CMRR_spec = 10**(CMRR_spec_dB/20)         # Convert dB to V/V
PSRR_spec = 10**(PSRR_spec_dB/20)         # Convert dB to V/V

# ====================================
# Mixed Variable Hybrid-PSO parameters
# ====================================
N_PARTICLES = 3
MAX_ITERATIONS = 2
MAX_VELOCITY_UPDATES = 2

# =========================
# Range of sizing variables
# =========================
gm_ID_range = (3, 23)
V_A_range = ((VCM + 0.15), (VDD - 0.15))
V_B_range = (0, VCM)
L_DISCRETE_VALUES = np.array([0.15, 0.16, 0.17, 0.18, 0.19, 0.20, 
                               0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 
                               0.90, 1.00, 2.00, 3.00])