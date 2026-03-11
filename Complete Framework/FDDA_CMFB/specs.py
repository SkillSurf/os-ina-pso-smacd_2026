import numpy as np
import scipy.constants as sc

# ===============================
# FDDA and CMFB design parameters
# ===============================
VDD = 1.8          # Supply Voltage (V)
CL  = 1e-12        # Differential Load Capacitance (F)
VCM = VDD / 2      # Common Mode Voltage (V)
V_A = 1.5          # Voltage at cascode load node (V)
V_B = 0.3          # Voltage at folding node (V)
freq = 1e3         # Frequency at which CMRR, PSRR, and noise is calculated (Hz)
temp = 300         # Temperature (K)
k = sc.Boltzmann   # Boltzmann's constant (J/K)
M = 4              # Current Ratio (I_T:I_X)

# ===================================
# FDDA and CMFB design specifications
# ===================================
Vicm_spec = (0.8, 1.0)                    # Input Common Mode Range (V)
Gain_dc_spec_dB = 72                      # DC Gain (dB)
GBW_spec = 1e6                            # Gain Bandwidth (Hz)
PM_spec = 60                              # Phase Margin (degrees)
SR_spec = 1e6                             # Slew Rate (V/s)
CMRR_spec_dB = 120                        # Common Mode Rejection Ratio (dB)
PSRR_spec_dB = 60                         # Power Supply Rejection Ratio (dB)
# noise_spec = 0.05e-6                      # Input Referred Noise (V/√Hz)
Power_spec = 40e-6                        # Power Consumption (W)
Area_spec = 5000                          # Area (μm²)

Gain_dc_spec = 10**(Gain_dc_spec_dB/20)   # Convert dB to V/V
CMRR_spec = 10**(CMRR_spec_dB/20)         # Convert dB to V/V
PSRR_spec = 10**(PSRR_spec_dB/20)         # Convert dB to V/V

# ====================================
# Mixed Variable Hybrid-PSO parameters
# ====================================
N_PARTICLES = 10
MAX_ITERATIONS = 20
MAX_VELOCITY_UPDATES = 5

# =========================
# Range of sizing variables
# =========================
gm_ID_1_range = (18, 20)
gm_ID_2_range = (13, 15)
gm_ID_3_range = (12, 14)
gm_ID_4_range = (12, 14)
gm_ID_5_range = (11, 13)
gm_ID_6_range = (11, 13)
L_DISCRETE_VALUES = np.array([0.15, 0.16, 0.17, 0.18, 0.19, 0.20, 0.30, 0.40,
                              0.50, 0.60, 0.70, 0.80, 0.90, 1.00, 2.00, 3.00])